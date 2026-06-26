"""Per-request flags for chat/coding (native lite UI, etc.)."""

from __future__ import annotations

from contextvars import ContextVar

_lite_ui: ContextVar[bool] = ContextVar("lite_ui", default=False)


def set_lite_ui(enabled: bool) -> None:
    _lite_ui.set(bool(enabled))


def lite_ui() -> bool:
    return _lite_ui.get()


def reset_lite_ui() -> None:
    _lite_ui.set(False)
