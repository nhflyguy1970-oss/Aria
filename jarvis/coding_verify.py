"""Verify Python files after apply — syntax, run, pytest."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from jarvis import fs
from jarvis.code_context import _find_test_files
from jarvis.project_runner import run_pytest, run_script
from jarvis.sandbox import run_sandboxed

_PYTHON = sys.executable

_FIREJAIL_NOISE = re.compile(
    r"^(Warning: not remounting|Child process initialized|Parent is shutting down)",
)


def _pytest_available() -> bool:
    check = subprocess.run(
        [_PYTHON, "-m", "pytest", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return check.returncode == 0


def _pytest_targets(py_files: list[Path], base: Path) -> list[Path]:
    """Resolve pytest files for edited sources (shared rules with code_context)."""
    targets: list[Path] = []
    seen: set[Path] = set()

    for pf in py_files:
        try:
            rel = pf.relative_to(base)
            rel_str = str(rel).replace("\\", "/")
        except ValueError:
            rel_str = str(pf).replace("\\", "/")
        for rel_test in _find_test_files(rel_str, base):
            path = base / rel_test
            resolved = path.resolve()
            if resolved not in seen and path.exists():
                seen.add(resolved)
                targets.append(path)

    return targets


def _clean_pytest_output(text: str) -> str:
    lines = [ln for ln in text.splitlines() if not _FIREJAIL_NOISE.match(ln.strip())]
    return "\n".join(lines).strip()


def _pytest_excerpt(combined: str, *, max_chars: int = 700) -> str:
    cleaned = _clean_pytest_output(combined)
    if not cleaned:
        return "(no pytest output)"
    for marker in ("= FAILURES =", "FAILED ", "short test summary", "ERROR "):
        idx = cleaned.find(marker)
        if idx >= 0:
            chunk = cleaned[idx:]
            return chunk[:max_chars] + ("…" if len(chunk) > max_chars else "")
    return cleaned[:max_chars] + ("…" if len(cleaned) > max_chars else "")


def collect_test_failures(py_file: Path, base: Path, *, max_chars: int = 4000) -> str:
    """Run pytest for a file's tests; return failure output or empty if all pass."""
    if py_file.suffix != ".py" or not _pytest_available():
        return ""
    targets = _pytest_targets([py_file], base)
    if not targets:
        return ""
    chunks: list[str] = []
    for target in targets:
        result = run_pytest(
            target,
            base,
            timeout=90,
            extra_args=["--tb=short", "-q", "--no-header"],
        )
        if result.returncode == 0:
            continue
        combined = _clean_pytest_output(
            ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        )
        if not combined or "no tests ran" in combined.lower():
            continue
        label = target.relative_to(base) if target.is_relative_to(base) else target.name
        excerpt = _pytest_excerpt(combined, max_chars=max_chars)
        chunks.append(f"pytest failures ({label}):\n{excerpt}")
    return "\n\n".join(chunks)


def verify_python_files(
    py_files: list[Path],
    base: Path,
    *,
    run_scripts: bool = False,
) -> str:
    """Return markdown-ish status lines to append after apply."""
    if not py_files:
        return ""

    parts: list[str] = []

    for pf in py_files:
        rel = pf.relative_to(base) if pf.is_relative_to(base) else pf.name
        check = run_sandboxed(
            [_PYTHON, "-m", "py_compile", str(pf)],
            cwd=str(base),
            timeout=15,
        )
        if check.returncode != 0:
            err = (check.stderr or check.stdout or "syntax error").strip()[-400:]
            parts.append(f"**Syntax check failed** (`{rel}`):\n```\n{err}\n```")
            continue

        parts.append(f"**Syntax:** OK (`{rel}`)")

        if run_scripts:
            run = run_script(pf, base, timeout=30)
            out = (run.stdout or "").strip()
            if out:
                parts.append(f"**Output:**\n```\n{out[:1000]}\n```")
            if run.returncode != 0:
                err = (run.stderr or run.stdout or "run failed").strip()[-400:]
                parts.append(f"**Run failed:**\n```\n{err}\n```")

    if not _pytest_available():
        return "\n\n".join(parts)

    targets = _pytest_targets(py_files, base)
    if not targets:
        return "\n\n".join(parts)

    for target in targets:
        label = target.relative_to(base) if target.is_relative_to(base) else target.name
        test = run_pytest(
            target,
            base,
            timeout=90,
            extra_args=["--tb=line", "-q", "--no-header"],
        )
        combined = _clean_pytest_output(
            ((test.stdout or "") + "\n" + (test.stderr or "")).strip()
        )
        if test.returncode == 0:
            parts.append(f"**pytest:** passed (`{label}`)")
        elif not combined or "no tests ran" in combined.lower():
            continue
        else:
            parts.append(
                f"**pytest:** failed (`{label}`)\n```\n{_pytest_excerpt(combined)}\n```"
            )

    return "\n\n".join(parts)


def verify_candidate_pytest(source_rel: str, new_code: str, base: Path) -> tuple[bool, str]:
    """Run paired test file(s) against candidate source in an isolated temp dir."""
    import shutil
    import tempfile

    if not _pytest_available():
        return True, ""
    test_rels = _find_test_files(source_rel.replace("\\", "/"), base)
    if not test_rels:
        return True, ""

    source_name = Path(source_rel.replace("\\", "/")).name
    with tempfile.TemporaryDirectory(prefix="jarvis-pytest-") as td:
        td_path = Path(td)
        (td_path / source_name).write_text(new_code, encoding="utf-8")
        targets: list[Path] = []
        for rel_test in test_rels[:2]:
            src = base / rel_test
            if not src.exists():
                continue
            dest = td_path / Path(rel_test).name
            shutil.copy2(src, dest)
            targets.append(dest)
        if not targets:
            return True, ""

        for target in targets:
            result = run_pytest(target.name, td_path, timeout=90, extra_args=["--tb=line", "-q"])
            combined = _clean_pytest_output(
                ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
            )
            if result.returncode != 0:
                return False, combined or "pytest failed"
    return True, ""


def _scaffold_pytest_fixtures(file_items: list[dict], td_path: Path) -> None:
    """Create minimal fixture dirs/files referenced by generated tests."""
    test_code = "\n".join(
        item.get("code", "")
        for item in file_items
        if Path(item.get("path", "")).name.startswith("test_")
    )
    if not test_code.strip():
        return

    if "test_data" in test_code:
        fixture = td_path / "test_data"
        fixture.mkdir(exist_ok=True)
        defaults = {
            "sample1.txt": "This is a line containing Brown Trout\nOther line\n",
            "sample2.txt": "This is another line with Brown Trout\n",
        }
        for name, text in defaults.items():
            path = fixture / name
            if not path.exists():
                path.write_text(text, encoding="utf-8")

    for match in re.finditer(r'["\']([^"\']+\.txt)["\']', test_code):
        rel = match.group(1).lstrip("./")
        if rel.startswith("test_data/"):
            path = td_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("This is a line containing Brown Trout\n", encoding="utf-8")


def verify_proposed_files(file_items: list[dict], base: Path) -> tuple[bool, str]:
    """Run pytest in a temp dir for proposed script + test file pairs."""
    import tempfile

    if not file_items:
        return True, ""
    writable = [f for f in file_items if not f.get("delete") and f.get("code")]
    if not writable:
        return True, ""

    from jarvis.syntax_check import check_file, has_errors

    with tempfile.TemporaryDirectory(prefix="jarvis-propose-") as td:
        td_path = Path(td)
        for item in writable:
            name = Path(item["path"]).name
            (td_path / name).write_text(item["code"], encoding="utf-8")

        _scaffold_pytest_fixtures(writable, td_path)

        for item in writable:
            path = item["path"]
            if not path.endswith(".py"):
                continue
            diags = check_file(Path(path), content=item["code"], deep=True, skip_typecheck=True)
            if has_errors(diags):
                return False, f"Syntax error in `{path}`: {diags[0].message if diags else 'invalid'}"

        test_names = [
            Path(f["path"]).name
            for f in writable
            if Path(f.get("path", "")).name.startswith("test_") and f["path"].endswith(".py")
        ]
        if test_names and _pytest_available():
            for name in test_names:
                result = run_pytest(name, td_path, timeout=90, extra_args=["--tb=line", "-q"])
                combined = _clean_pytest_output(
                    ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
                )
                if result.returncode != 0:
                    return False, combined or f"pytest failed for {name}"
            return True, "pytest passed in proposal preview"

        for item in writable:
            path = item["path"]
            if path.endswith((".js", ".mjs", ".cjs", ".ts", ".tsx")):
                diags = check_file(Path(path), content=item["code"], deep=True, skip_typecheck=True)
                if has_errors(diags):
                    return False, f"Syntax error in `{path}`"

    return True, "syntax OK"


def verify_file_changes(
    file_items: list[dict],
    base: Path,
    *,
    mode: str = "agent",
) -> tuple[bool, str]:
    """Verify proposed edits — pytest in temp dir, on-disk tests, or syntax-only."""
    if not file_items:
        return True, ""

    has_test_in_proposal = any(
        Path(f.get("path", "")).name.startswith("test_") for f in file_items
    )
    if mode == "create" or has_test_in_proposal or len(file_items) > 1:
        ok, detail = verify_proposed_files(file_items, base)
        if not ok:
            return False, f"**Verify failed:**\n```\n{detail[:1200]}\n```"
        if detail:
            return True, f"**Verify:** {detail}"
        return True, ""

    py_paths: list[Path] = []
    for f in file_items:
        p = f.get("path", "")
        if p.endswith(".py") and not Path(p).name.startswith("test_") and not f.get("delete"):
            py_paths.append(fs.resolve_path(p, base=base))

    msg = verify_python_files(py_paths, base, run_scripts=False)
    lower = msg.lower()
    if "syntax check failed" in lower or "**pytest:** failed" in lower or "run failed" in lower:
        return False, msg

    for pf in py_paths:
        try:
            rel = str(pf.relative_to(base)).replace("\\", "/")
        except ValueError:
            rel = pf.name
        paired = _find_test_files(rel, base)
        if paired and "**pytest:** passed" not in msg and "**pytest:** failed" not in msg:
            return False, msg + "\n\n**pytest:** tests exist but did not run — verification incomplete."

    return True, msg
