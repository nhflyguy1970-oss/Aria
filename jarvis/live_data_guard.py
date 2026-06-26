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
