"""Cooperative cancellation for in-flight chat streams."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_cancelled: set[str] = set()


def begin(request_id: str) -> None:
    if not request_id:
        return
    with _lock:
        _cancelled.discard(request_id)


def cancel(request_id: str) -> bool:
    if not request_id:
        return False
    with _lock:
        _cancelled.add(request_id)
    return True


def is_cancelled(request_id: str) -> bool:
    if not request_id:
        return False
    with _lock:
        return request_id in _cancelled


def finish(request_id: str) -> None:
    if not request_id:
        return
    with _lock:
        _cancelled.discard(request_id)
