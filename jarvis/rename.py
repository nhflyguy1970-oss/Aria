"""Project-wide symbol rename."""

import re
from pathlib import Path

from jarvis import fs
from jarvis.config import PROJECT_ROOT, SKIP_DIRS

CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".c", ".cpp", ".h"}


def _word_pattern(symbol: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(symbol)}\b")


def find_symbol_usages(symbol: str, root: Path | None = None) -> list[tuple[str, int, str]]:
    root = root or PROJECT_ROOT
    pattern = _word_pattern(symbol)
    hits = []
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if Path(filename).suffix.lower() not in CODE_EXTENSIONS:
                continue
            if fs._is_blocked(Path(filename)):
                continue
            path = Path(dirpath) / filename
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append((str(path.relative_to(root)), i, line.strip()))
    return hits


def rename_symbol(symbol: str, new_name: str, root: Path | None = None, dry_run: bool = False) -> dict:
    root = root or PROJECT_ROOT
    if not symbol or not new_name or symbol == new_name:
        return {"error": "Invalid symbol names", "changed": []}
    pattern = _word_pattern(symbol)
    changed = []
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if Path(filename).suffix.lower() not in CODE_EXTENSIONS:
                continue
            if fs._is_blocked(Path(filename)):
                continue
            path = Path(dirpath) / filename
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if not pattern.search(content):
                continue
            new_content = pattern.sub(new_name, content)
            rel = str(path.relative_to(root))
            if dry_run:
                changed.append({"path": rel, "preview": True})
            else:
                fs.backup_file(str(path), base=root)
                path.write_text(new_content, encoding="utf-8")
                changed.append({"path": rel, "preview": False})
    return {"symbol": symbol, "new_name": new_name, "files_changed": len(changed), "changed": changed}


def rename_symbol_preview(symbol: str, new_name: str, root: Path | None = None) -> list[dict]:
    """Return {path, code} items for a project-wide text rename."""
    root = root or PROJECT_ROOT
    if not symbol or not new_name or symbol == new_name:
        return []
    pattern = _word_pattern(symbol)
    files: list[dict] = []
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if Path(filename).suffix.lower() not in CODE_EXTENSIONS:
                continue
            if fs._is_blocked(Path(filename)):
                continue
            path = Path(dirpath) / filename
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if not pattern.search(content):
                continue
            new_content = pattern.sub(new_name, content)
            rel = str(path.relative_to(root))
            files.append({"path": rel, "code": new_content})
    return files
