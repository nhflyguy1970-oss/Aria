"""Cooperative cancellation for in-flight chat streams and dispatched actions.

Cancellation used to be honoured only inside ``llm.ask_stream``. Actions that
run through ``dispatch_action`` (web_search and friends) never looked at the
flag, so a cancelled research request kept running — holding the global request
lock — long after the consumer had gone away. The active-request registry here
lets "stop" find that work and close its stream.
"""

from __future__ import annotations

import contextvars
import threading
from collections.abc import Callable

_lock = threading.Lock()
_cancelled: set[str] = set()
# request_id -> closers (bridge.close and friends) to run when it is cancelled.
_active: dict[str, list[Callable[[], None]]] = {}

# Bound inside the worker thread that runs a request, so dispatched actions can
# ask "was I cancelled?" without threading a request_id through every handler.
_CURRENT: contextvars.ContextVar[str] = contextvars.ContextVar("chat_cancel_current", default="")


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
        closers = list(_active.get(request_id) or ())
    for close in closers:
        try:
            close()
        except Exception:
            pass
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


# --- active-request registry ------------------------------------------------


def register_active(request_id: str, closer: Callable[[], None] | None = None) -> None:
    """Mark a request as in flight, optionally with a closer to stop its stream."""
    if not request_id:
        return
    with _lock:
        closers = _active.setdefault(request_id, [])
        if closer is not None and closer not in closers:
            closers.append(closer)


def unregister_active(request_id: str) -> None:
    if not request_id:
        return
    with _lock:
        _active.pop(request_id, None)


def active_ids() -> list[str]:
    with _lock:
        return list(_active)


def cancel_active(exclude: str = "") -> list[str]:
    """Cancel every in-flight request except ``exclude``. Returns the ids cancelled.

    "stop" arrives as its own request, so it must not cancel itself.
    """
    with _lock:
        targets = [r for r in _active if r and r != exclude]
    for request_id in targets:
        cancel(request_id)
    return targets


# --- current-request binding ------------------------------------------------


def bind_current(request_id: str):
    """Bind the request id for this execution context; returns the reset token."""
    return _CURRENT.set(request_id or "")


def reset_current(token) -> None:
    try:
        _CURRENT.reset(token)
    except Exception:
        pass


def current_request_id() -> str:
    return _CURRENT.get() or ""


def current_cancelled() -> bool:
    """True when the request running in this context has been cancelled."""
    return is_cancelled(current_request_id())


class CancelledRequest(Exception):
    """Raised by raise_if_cancelled when the active request was stopped."""


def raise_if_cancelled() -> None:
    """Checkpoint for long dispatched actions (web_search, research, …)."""
    if current_cancelled():
        raise CancelledRequest("Request was stopped.")
