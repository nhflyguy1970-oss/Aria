"""HTTP/media filesystem confinement — DATA_DIR library roots only."""

from __future__ import annotations

from pathlib import Path

from jarvis.config import DATA_DIR


def under_roots(candidate: Path, roots: tuple[Path, ...]) -> bool:
    for root in roots:
        try:
            candidate.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def resolve_under_roots(path: str | Path, roots: tuple[Path, ...]) -> Path | None:
    try:
        candidate = Path(path).expanduser().resolve()
    except (OSError, RuntimeError):
        return None
    if not candidate.is_file():
        return None
    resolved_roots = tuple(r.resolve() for r in roots)
    if under_roots(candidate, resolved_roots):
        return candidate
    return None


def audio_library_roots() -> tuple[Path, ...]:
    from jarvis.modules.audio import AUDIO_LIBRARY_DIRS

    roots: list[Path] = [d for d in AUDIO_LIBRARY_DIRS.values()]
    roots.append(DATA_DIR / "audio")
    roots.append(DATA_DIR / "uploads")
    try:
        from jarvis.music_gen import MUSIC_DIR

        roots.append(MUSIC_DIR)
    except Exception:
        pass
    try:
        from jarvis.song_studio import SONGS_DIR

        roots.append(SONGS_DIR)
    except Exception:
        pass
    return tuple(roots)


def resolve_audio_library_path(path: str | Path) -> Path | None:
    """Allow only files under audio/music/songs library trees."""
    return resolve_under_roots(path, audio_library_roots())


def document_library_roots() -> tuple[Path, ...]:
    from jarvis.document_pipeline import documents_dir

    return (
        documents_dir().resolve(),
        (DATA_DIR / "uploads").resolve(),
        (DATA_DIR / "documents").resolve(),
    )


def resolve_document_library_path(path: str | Path) -> Path | None:
    """Allow only documents under library/uploads (no arbitrary absolute paths)."""
    text = str(path or "").strip()
    if not text:
        return None
    roots = document_library_roots()
    p = Path(text).expanduser()
    if p.is_absolute():
        return resolve_under_roots(p, roots)
    for root in roots:
        try:
            candidate = (root / text).resolve()
        except (OSError, RuntimeError):
            continue
        if candidate.is_file() and under_roots(candidate, roots):
            return candidate
    return None


def resolve_named_under(dir_path: Path, name: str) -> Path | None:
    """Serve a basename-only file under dir_path with symlink escape protection."""
    safe = Path(name).name
    if not safe or safe in (".", ".."):
        return None
    root = dir_path.resolve()
    try:
        candidate = (root / safe).resolve()
    except (OSError, RuntimeError):
        return None
    if not candidate.is_file():
        return None
    if not under_roots(candidate, (root,)):
        return None
    return candidate


def resolve_image_library_path(path: str | Path) -> Path | None:
    """Allow images under generated/uploads/inpaint_masks only."""
    roots = tuple((DATA_DIR / sub).resolve() for sub in ("generated", "uploads", "inpaint_masks"))
    return resolve_under_roots(path, roots)
