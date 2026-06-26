"""Unified syntax and lint checker — py_compile, ruff, pyright, mypy, multi-language."""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

_PYTHON = sys.executable

LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".sh": "shell",
    ".bash": "shell",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".rs": "rust",
    ".go": "go",
}


@dataclass
class Diagnostic:
    path: str
    line: int
    column: int
    severity: str  # error | warning | info
    message: str
    source: str  # py_compile | ruff | pyright | mypy | node | shell | json | ...

    def format(self) -> str:
        loc = f"{self.path}:{self.line}"
        if self.column:
            loc += f":{self.column}"
        return f"{loc} [{self.severity}] ({self.source}) {self.message}"


def _is_sandbox_script(path: Path) -> bool:
    """Flat scripts under data/scripts/ — mypy cannot resolve sibling imports."""
    parts = path.parts
    try:
        i = parts.index("data")
    except ValueError:
        return False
    return i + 1 < len(parts) and parts[i + 1] == "scripts"


def _skip_typecheck(path: Path, content: str | None) -> bool:
    if content is not None:
        return True
    if _is_sandbox_script(path):
        return True
    stem = path.stem
    if stem.startswith("test_") and path.suffix == ".py":
        return True
    return False


def _run(cmd: list[str], *, cwd: str | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)


def _write_temp(content: str, suffix: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    path = Path(name)
    path.write_text(content, encoding="utf-8")
    return path


def _syntax_error_location(exc: BaseException) -> tuple[int, int]:
    if isinstance(exc, SyntaxError):
        return exc.lineno or 1, exc.offset or 0
    return 1, 0


def check_python_syntax(path: Path, content: str | None = None) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    rel = str(path)
    if content is not None:
        tmp = _write_temp(content, path.suffix or ".py")
        try:
            py_compile.compile(str(tmp), doraise=True)
        except py_compile.PyCompileError as e:
            lineno, offset = _syntax_error_location(e.exc_value)
            diags.append(Diagnostic(rel, lineno, offset, "error", str(e), "py_compile"))
        finally:
            tmp.unlink(missing_ok=True)
    else:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            lineno, offset = _syntax_error_location(e.exc_value)
            diags.append(Diagnostic(rel, lineno, offset, "error", str(e), "py_compile"))
    return diags


def check_ruff(path: Path, content: str | None = None) -> list[Diagnostic]:
    if not shutil.which("ruff"):
        return []
    diags: list[Diagnostic] = []
    rel = str(path)
    target = path
    tmp: Path | None = None
    if content is not None:
        tmp = _write_temp(content, path.suffix or ".py")
        target = tmp
    try:
        r = _run(["ruff", "check", "--output-format=json", str(target)], timeout=45)
        if r.stdout.strip():
            try:
                items = json.loads(r.stdout)
                for item in items[:25]:
                    loc = item.get("location", {})
                code = item.get("code", "")
                sev = (
                    "error"
                    if code.startswith("E") or code in ("F821", "F822", "F823", "F811")
                    else "warning"
                )
                diags.append(Diagnostic(
                    rel,
                    loc.get("row", 1),
                    loc.get("column", 0),
                    sev,
                    f"{code}: {item.get('message', '')}".strip(": "),
                    "ruff",
                ))
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    return diags


def check_pyright(path: Path, content: str | None = None) -> list[Diagnostic]:
    if not shutil.which("pyright"):
        return []
    diags: list[Diagnostic] = []
    rel = str(path)
    target = path
    tmp: Path | None = None
    if content is not None:
        tmp = _write_temp(content, path.suffix or ".py")
        target = tmp
    try:
        r = _run(["pyright", str(target), "--outputjson"], timeout=90)
        if r.stdout.strip():
            data = json.loads(r.stdout)
            for d in data.get("generalDiagnostics", [])[:20]:
                start = d.get("range", {}).get("start", {})
                sev = d.get("severity", "error")
                sev_name = {1: "error", 2: "warning", 3: "info"}.get(sev, "error")
                diags.append(Diagnostic(
                    rel, start.get("line", 0) + 1, start.get("character", 0) + 1,
                    sev_name, d.get("message", ""), "pyright",
                ))
    except Exception:
        pass
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    return diags


def check_mypy(path: Path, content: str | None = None) -> list[Diagnostic]:
    if not shutil.which("mypy"):
        return []
    diags: list[Diagnostic] = []
    rel = str(path)
    target = path
    tmp: Path | None = None
    if content is not None:
        tmp = _write_temp(content, path.suffix or ".py")
        target = tmp
    try:
        r = _run([_PYTHON, "-m", "mypy", str(target), "--no-color-output", "--show-error-codes"], timeout=90)
        for line in (r.stdout or "").splitlines()[:20]:
            if ": error:" in line or ": warning:" in line:
                if "import-not-found" in line or "import-untyped" in line:
                    continue
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    try:
                        diags.append(Diagnostic(
                            rel, int(parts[1]), int(parts[2]),
                            "error" if "error" in parts[3] else "warning",
                            parts[3].strip(), "mypy",
                        ))
                    except ValueError:
                        diags.append(Diagnostic(rel, 1, 0, "error", line, "mypy"))
    except Exception:
        pass
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    return diags


def check_typescript(path: Path, content: str | None = None) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    rel = str(path)
    if shutil.which("npx"):
        target = path
        tmp: Path | None = None
        if content is not None:
            tmp = _write_temp(content, path.suffix or ".ts")
            target = tmp
        try:
            r = _run(["npx", "--yes", "typescript", "--noEmit", str(target)], timeout=60)
            for line in (r.stdout or "").splitlines()[:15]:
                if "error TS" in line:
                    diags.append(Diagnostic(rel, 1, 0, "error", line.strip()[:400], "tsc"))
        except Exception:
            pass
        finally:
            if tmp:
                tmp.unlink(missing_ok=True)
    return diags


def check_javascript(path: Path, content: str | None = None) -> list[Diagnostic]:
    if path.suffix in {".ts", ".tsx"}:
        return check_typescript(path, content)
    if not shutil.which("node"):
        return []
    diags: list[Diagnostic] = []
    rel = str(path)
    target = path
    tmp: Path | None = None
    if content is not None:
        tmp = _write_temp(content, path.suffix or ".js")
        target = tmp
    try:
        r = _run(["node", "--check", str(target)], timeout=30)
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or "syntax error").strip()[:500]
            diags.append(Diagnostic(rel, 1, 0, "error", msg, "node"))
    except Exception:
        pass
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    return diags


def check_shell(path: Path, content: str | None = None) -> list[Diagnostic]:
    bash = shutil.which("bash")
    if not bash:
        return []
    diags: list[Diagnostic] = []
    rel = str(path)
    text = content if content is not None else path.read_text(encoding="utf-8", errors="ignore")
    tmp = _write_temp(text, ".sh")
    try:
        r = _run([bash, "-n", str(tmp)], timeout=15)
        if r.returncode != 0:
            diags.append(Diagnostic(rel, 1, 0, "error", (r.stderr or r.stdout or "syntax error").strip()[:400], "bash"))
    except Exception:
        pass
    finally:
        tmp.unlink(missing_ok=True)
    return diags


def check_json(path: Path, content: str | None = None) -> list[Diagnostic]:
    rel = str(path)
    text = content if content is not None else path.read_text(encoding="utf-8", errors="ignore")
    try:
        json.loads(text)
        return []
    except json.JSONDecodeError as e:
        return [Diagnostic(rel, e.lineno or 1, e.colno or 0, "error", e.msg, "json")]


def check_yaml(path: Path, content: str | None = None) -> list[Diagnostic]:
    rel = str(path)
    text = content if content is not None else path.read_text(encoding="utf-8", errors="ignore")
    try:
        import yaml
        yaml.safe_load(text)
        return []
    except ImportError:
        return []
    except Exception as e:
        return [Diagnostic(rel, 1, 0, "error", str(e)[:300], "yaml")]


def check_file(
    path: Path | str,
    *,
    content: str | None = None,
    deep: bool = True,
    skip_typecheck: bool | None = None,
) -> list[Diagnostic]:
    """Run all applicable checks for a file path."""
    path = Path(path)
    if skip_typecheck is None:
        skip_typecheck = _skip_typecheck(path, content)
    ext = path.suffix.lower()
    lang = LANG_BY_EXT.get(ext)
    diags: list[Diagnostic] = []

    if lang == "python" or ext == ".py":
        diags.extend(check_python_syntax(path, content))
        if deep and not any(d.severity == "error" for d in diags):
            diags.extend(check_ruff(path, content))
            if not skip_typecheck:
                diags.extend(check_pyright(path, content))
                diags.extend(check_mypy(path, content))
    elif lang in ("javascript", "typescript"):
        diags.extend(check_javascript(path, content))
    elif lang == "shell":
        diags.extend(check_shell(path, content))
    elif lang == "json":
        diags.extend(check_json(path, content))
    elif lang in ("yaml",):
        diags.extend(check_yaml(path, content))

    return diags


def check_files(
    items: list[dict],
    base: Path,
    *,
    deep: bool = True,
    skip_typecheck: bool | None = None,
) -> list[Diagnostic]:
    """Check multiple {path, code?} items."""
    all_diags: list[Diagnostic] = []
    for item in items:
        p = item.get("path", "")
        if not p:
            continue
        from jarvis import fs
        try:
            resolved = fs.resolve_path(p, base=base)
        except (ValueError, OSError):
            resolved = base / p if not Path(p).is_absolute() else Path(p)
        code = item.get("code")
        typecheck = skip_typecheck
        if typecheck is None and code is not None:
            typecheck = True
        all_diags.extend(
            check_file(resolved, content=code, deep=deep, skip_typecheck=typecheck)
        )
    return all_diags


def has_errors(diags: list[Diagnostic]) -> bool:
    return any(d.severity == "error" for d in diags)


def format_diagnostics(diags: list[Diagnostic], *, max_items: int = 20) -> str:
    if not diags:
        return "No issues found."
    lines = [d.format() for d in diags[:max_items]]
    if len(diags) > max_items:
        lines.append(f"… and {len(diags) - max_items} more")
    return "\n".join(lines)


def diagnostics_to_dicts(diags: list[Diagnostic]) -> list[dict]:
    return [asdict(d) for d in diags]


def available_tools() -> dict[str, bool]:
    return {
        "py_compile": True,
        "ruff": bool(shutil.which("ruff")),
        "pyright": bool(shutil.which("pyright")),
        "mypy": bool(shutil.which("mypy")),
        "node": bool(shutil.which("node")),
        "bash": bool(shutil.which("bash")),
        "typescript": bool(shutil.which("npx")),
    }
