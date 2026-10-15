"""Block accidental writes to live data/ during pytest."""

from __future__ import annotations

import os
from pathlib import Path

from jarvis.config import PROJECT_ROOT

# Fixed at import — tests monkeypatch jarvis.config.DATA_DIR but must not weaken this guard.
_LIVE_DATA_ROOT = (PROJECT_ROOT / "data").resolve()

_guard_active = False


def enable_test_guard() -> None:
    global _guard_active
    _guard_active = True


def disable_test_guard() -> None:
    global _guard_active
    _guard_active = False


def guard_active() -> bool:
    return _guard_active and os.environ.get("JARVIS_ALLOW_LIVE_DATA") != "1"


def assert_live_write_allowed(path: Path | str) -> None:
    """Raise if a test is about to write under the project data/ directory."""
    if not guard_active():
        return

    target = Path(path).resolve()
    if target == _LIVE_DATA_ROOT or _LIVE_DATA_ROOT in target.parents:
        raise RuntimeError(
            f"Test attempted to write live Jarvis data: {target}. "
            "Use the data_dir fixture and patch DATA_DIR / JOURNAL_FILE / MEMORY_FILE."
        )


# --- Process-wide write barrier (tests only) -----------------------------------
#
# assert_live_write_allowed() protects only the writers that remember to call it.
# Writers that built their path from PROJECT_ROOT instead of DATA_DIR slipped past
# it for months (document parse cache, platform notifications, activity log). The
# barrier below sees every file write at the interpreter level through an audit
# hook, so a new writer cannot reintroduce the leak unnoticed. It is installed
# only by tests/conftest.py and only acts while the per-test guard is enabled.

_O_WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC

# audit event -> positions of the path arguments it creates, changes or removes
_PATH_EVENTS = {
    "os.mkdir": (0,),
    "os.remove": (0,),
    "os.rmdir": (0,),
    "os.rename": (0, 1),
    "os.replace": (0, 1),
    "os.truncate": (0,),
    "os.symlink": (1,),
    "os.link": (1,),
    "os.utime": (0,),
    "os.chmod": (0,),
    "shutil.rmtree": (0,),
    "shutil.copyfile": (1,),
    "shutil.copytree": (1,),
    "shutil.move": (0, 1),
}

_protected_roots: tuple[str, ...] = ()
_violations: list[str] = []
_barrier_installed = False


def _abs(p: object) -> str | None:
    if p is None or isinstance(p, int):
        return None
    try:
        text = os.fsdecode(os.fspath(p))  # type: ignore[arg-type]
    except TypeError:
        return None
    if text.startswith("file:"):  # sqlite URI
        text = text[5:].split("?", 1)[0]
    if not text or text == ":memory:":
        return None
    return os.path.abspath(text)


def _protected(p: object) -> str | None:
    ap = _abs(p)
    if ap is None:
        return None
    for root in _protected_roots:
        if ap == root or ap.startswith(root + os.sep):
            return ap
    return None


def _sqlite_read_only(database: object) -> bool:
    text = os.fsdecode(database) if isinstance(database, (str, bytes)) else ""
    return text.startswith("file:") and ("mode=ro" in text or "immutable=1" in text)


def _barrier(event: str, args: tuple) -> None:
    if not _protected_roots or not guard_active():
        return
    hits: list[str] = []
    if event == "open":
        path, mode, flags = (tuple(args) + (None, None, None))[:3]
        writing = (isinstance(flags, int) and flags & _O_WRITE) or (
            isinstance(mode, str) and any(c in mode for c in "wax+")
        )
        if writing and (hit := _protected(path)):
            hits.append(hit)
    elif event == "sqlite3.connect":
        database = args[0] if args else None
        if not _sqlite_read_only(database) and (hit := _protected(database)):
            hits.append(hit)
    elif event in _PATH_EVENTS:
        for i in _PATH_EVENTS[event]:
            if i < len(args) and (hit := _protected(args[i])):
                hits.append(hit)
    if hits:
        message = f"{event}: {', '.join(hits)}"
        _violations.append(message)
        raise PermissionError(f"Test attempted to modify production data ({message})")


def install_write_barrier(roots: list[Path | str]) -> None:
    """Block writes under *roots* while the test guard is active (call once, from conftest)."""
    global _protected_roots, _barrier_installed
    _protected_roots = tuple(sorted({os.path.abspath(os.fspath(r)) for r in roots}))
    if not _barrier_installed:
        import sys

        sys.addaudithook(_barrier)
        _barrier_installed = True


def take_write_violations() -> list[str]:
    """Return and clear the writes the barrier refused since the last call."""
    out = list(_violations)
    _violations.clear()
    return out
