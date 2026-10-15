"""Provider progress that is not answer text: a reasoning model's hidden thinking.

deepseek-r1 thinks for up to a minute or more before its first answer token. The chat
stream's first-token budget (45 s) treated that silence as a wedged provider, cancelled the
turn and sent the browser into provider recovery (2026-10-14 16:55, which ended in a watchdog
restart). The Ollama stream notes each thinking chunk here under the request's cancel key,
and the server keeps such a turn alive with heartbeats instead of timing it out.
"""
from __future__ import annotations

import contextvars
import threading
import time

_KEY: contextvars.ContextVar[str] = contextvars.ContextVar("stream_progress_key", default="")
_lock = threading.Lock()
_last: dict[str, float] = {}
_MAX_KEYS = 256


def bind(key: str) -> None:
    """Attribute this thread's (context's) provider progress to ``key``."""
    _KEY.set(key or "")


def note(key: str = "") -> None:
    key = key or _KEY.get()
    if not key:
        return
    with _lock:
        _last[key] = time.monotonic()
        if len(_last) > _MAX_KEYS:
            for old in sorted(_last, key=_last.get)[: len(_last) - _MAX_KEYS]:
                _last.pop(old, None)


def last(key: str) -> float:
    """Monotonic time of the latest progress for ``key`` (0.0 = none)."""
    with _lock:
        return _last.get(key, 0.0)


def clear(key: str) -> None:
    with _lock:
        _last.pop(key, None)
