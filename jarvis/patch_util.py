"""Apply patch-style edits (search/replace hunks and unified diffs)."""

from __future__ import annotations

import re


def apply_search_replace(content: str, old: str, new: str, *, replace_all: bool = False) -> str | None:
    """Apply one search/replace hunk. Returns None if old text not found."""
    if not old:
        return None
    if old not in content:
        return None
    if replace_all:
        return content.replace(old, new)
    return content.replace(old, new, 1)


def apply_unified_diff(original: str, diff_text: str) -> str | None:
    """Apply a unified diff via system patch when available, else manual merge."""
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    if shutil.which("patch"):
        try:
            with tempfile.TemporaryDirectory() as td:
                td_path = Path(td)
                orig_file = td_path / "file"
                orig_file.write_text(original, encoding="utf-8")
                patch_file = td_path / "change.patch"
                patch_file.write_text(diff_text, encoding="utf-8")
                r = subprocess.run(
                    ["patch", "-p0", str(orig_file), str(patch_file)],
                    capture_output=True, text=True, timeout=15,
                )
                if r.returncode == 0:
                    return orig_file.read_text(encoding="utf-8")
        except Exception:
            pass

    try:
        orig_lines = original.splitlines(keepends=True)
        if not orig_lines and original:
            orig_lines = [original + ("\n" if not original.endswith("\n") else "")]

        result_lines: list[str] = []
        orig_idx = 0
        in_hunk = False

        for raw in diff_text.splitlines(keepends=True):
            line = raw if raw.endswith("\n") else raw + "\n"
            if line.startswith("@@"):
                in_hunk = True
                m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if m:
                    target = int(m.group(1)) - 1
                    while orig_idx < target and orig_idx < len(orig_lines):
                        result_lines.append(orig_lines[orig_idx])
                        orig_idx += 1
                continue
            if not in_hunk:
                continue
            if line.startswith(("---", "+++")):
                continue
            if line.startswith(" "):
                if orig_idx < len(orig_lines):
                    result_lines.append(orig_lines[orig_idx])
                    orig_idx += 1
            elif line.startswith("-"):
                orig_idx += 1
            elif line.startswith("+"):
                result_lines.append(line[1:])

        while orig_idx < len(orig_lines):
            result_lines.append(orig_lines[orig_idx])
            orig_idx += 1

        out = "".join(result_lines)
        return out if out != original else None
    except Exception:
        return None


def parse_search_replace_blocks(text: str) -> list[dict]:
    """Parse FILE/SEARCH/REPLACE blocks from LLM output."""
    files: list[dict] = []
    if "FILE:" not in text:
        return files

    chunks = re.split(r"\nFILE:\s*", text.strip())
    chunks[0]
    for chunk in chunks[1:]:
        chunk = chunk.strip()
        if not chunk:
            continue
        path = chunk.splitlines()[0].strip()
        body = "\n".join(chunk.splitlines()[1:])
        hunks: list[dict] = []
        for m in re.finditer(
            r"SEARCH:\s*\n(.*?)\nREPLACE:\s*\n(.*?)(?=\nSEARCH:|\Z)",
            body,
            re.DOTALL,
        ):
            hunks.append({"search": m.group(1).rstrip("\n"), "replace": m.group(2).rstrip("\n")})
        if path and hunks:
            files.append({"path": path, "hunks": hunks})
    return files


def apply_hunks_to_content(content: str, hunks: list[dict]) -> tuple[str, list[str]]:
    """Apply search/replace hunks in order. Returns (new_content, errors)."""
    errors: list[str] = []
    current = content
    for i, hunk in enumerate(hunks, 1):
        old = hunk.get("search", "")
        new = hunk.get("replace", "")
        result = apply_search_replace(current, old, new)
        if result is None:
            errors.append(f"Hunk {i}: search text not found")
            continue
        current = result
    return current, errors


def merge_file_change(path: str, original: str, new_content: str, hunks: list[dict] | None) -> str:
    """Prefer hunks when valid; fall back to full replacement."""
    if hunks:
        patched, errors = apply_hunks_to_content(original, hunks)
        if not errors:
            return patched
    return new_content
