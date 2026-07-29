"""Realtime Vision status bus."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "state": "idle",
    "detail": "",
    "model": "",
    "task": "",
    "progress": 0,
    "error": "",
    "ts": 0.0,
}


def get_vision_state() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def set_vision_state(
    state: str,
    *,
    detail: str = "",
    model: str = "",
    task: str = "",
    progress: float | int = 0,
    error: str = "",
    publish: bool = True,
) -> dict[str, Any]:
    state = (state or "idle").strip().lower()
    if state not in (
        "idle",
        "preparing",
        "analyzing",
        "ocr",
        "comparing",
        "importing",
        "batch",
        "error",
    ):
        state = "idle"
    with _lock:
        _state.update(
            {
                "state": state,
                "detail": detail or "",
                "model": model or _state.get("model") or "",
                "task": task or "",
                "progress": float(progress or 0),
                "error": error or "",
                "ts": time.time(),
            }
        )
        snapshot = dict(_state)
    try:
        from jarvis.events import emit

        emit("vision_state", **snapshot)
    except Exception:
        pass
    if publish:
        try:
            from jarvis.ws_hub import publish as ws_publish

            ws_publish("vision_state", **snapshot)
        except Exception:
            pass
    return snapshot
