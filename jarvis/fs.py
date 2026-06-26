import os
from datetime import datetime
from pathlib import Path

from jarvis.config import DATA_DIR, PROJECT_ROOT, SECRET_BLOCKLIST, SKIP_DIRS


class PathError(Exception):
    pass


def resolve_path(path: str, *, base: Path | None = None) -> Path:
    """Resolve and validate a path stays within allowed roots."""
    base = (base or PROJECT_ROOT).resolve()
    resolved = Path(path).expanduser()
    if not resolved.is_absolute():
        resolved = (base / resolved).resolve()
    else:
        resolved = resolved.resolve()

    allowed_roots = [
        base.resolve(),
        PROJECT_ROOT.resolve(),
        DATA_DIR.resolve(),
        Path.home().resolve(),
    ]
    if not any(
        resolved == root or root in resolved.parents
        for root in allowed_roots
    ):
        raise PathError(f"Path outside allowed directories: {resolved}")

    return resolved


def read_file(path: str, *, base: Path | None = None) -> str:
    try:
        resolved = resolve_path(path, base=base)
        return resolved.read_text(encoding="utf-8", errors="ignore")
    except PathError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


def write_file(path: str, content: str, *, base: Path | None = None) -> None:
    resolved = resolve_path(path, base=base)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(content, encoding="utf-8")


def backup_file(path: str, *, base: Path | None = None) -> str:
    resolved = resolve_path(path, base=base)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"{resolved}.bak.{timestamp}")
    backup_path.write_text(
        resolved.read_text(encoding="utf-8", errors="ignore"),
        encoding="utf-8",
    )
    return str(backup_path)


def replace_text(path: str, old_text: str, new_text: str, *, base: Path | None = None) -> str:
    content = read_file(path, base=base)
    if content.startswith("ERROR:"):
        return content
    if old_text not in content:
        return "TEXT NOT FOUND"
    backup = backup_file(path, base=base)
    write_file(path, content.replace(old_text, new_text), base=base)
    return backup


def _walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        yield dirpath, filenames


def _is_blocked(path: Path) -> bool:
    low = path.name.lower()
    return any(b in low for b in SECRET_BLOCKLIST)


def find_files(name: str, root: str | Path) -> list[str]:
    root = Path(root).resolve()
    matches = []
    for dirpath, filenames in _walk(root):
        for filename in filenames:
            if _is_blocked(Path(filename)):
                continue
            if name.lower() in filename.lower():
                matches.append(str(Path(dirpath) / filename))
    return matches


def search_files(text: str, root: str | Path) -> list[tuple[str, int, str]]:
    root = Path(root).resolve()
    results = []
    for dirpath, filenames in _walk(root):
        for filename in filenames:
            if _is_blocked(Path(filename)):
                continue
            path = Path(dirpath) / filename
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        if text.lower() in line.lower():
                            results.append((str(path), line_num, line.strip()))
            except OSError:
                pass
    return results


def scan_project(root: str | Path) -> tuple[Path, list[str]]:
    root = Path(root).resolve()
    files = []
    for dirpath, filenames in _walk(root):
        for filename in filenames:
            full = Path(dirpath) / filename
            files.append(str(full.relative_to(root)))
    return root, files


def show_file(path: str, *, base: Path | None = None) -> None:
    try:
        resolved = resolve_path(path, base=base)
        with open(resolved, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                print(f"{line_num}: {line.rstrip()}")
    except Exception as e:
        print(f"\nERROR: {e}\n")
