"""Flag file so watchdog/tray know a server restart was intentional."""

from __future__ import annotations

import time
from pathlib import Path

from jarvis.config import DATA_DIR

_FLAG = DATA_DIR / "server_restart.flag"


def mark_restart_started() -> None:
    _FLAG.parent.mkdir(parents=True, exist_ok=True)
    _FLAG.write_text(str(time.time()), encoding="utf-8")


def clear_restart_flag() -> None:
    try:
        _FLAG.unlink(missing_ok=True)
    except OSError:
        return None


def controlled_restart_active(max_age_sec: float = 120) -> bool:
    if not _FLAG.is_file():
        return False
    try:
        started = float(_FLAG.read_text(encoding="utf-8").strip())
        return time.time() - started < float(max_age_sec or 120)
    except (OSError, ValueError):
        return True
