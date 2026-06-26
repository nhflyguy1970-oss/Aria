"""Track in-flight assistant requests so restarts/watchdog defer during coding/chat."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_active = 0


def begin() -> None:
    global _active
    with _lock:
        _active += 1


def end() -> None:
    global _active
    with _lock:
        _active = max(0, _active - 1)


def active() -> bool:
    with _lock:
        return _active > 0


def count() -> int:
    with _lock:
        return _active
