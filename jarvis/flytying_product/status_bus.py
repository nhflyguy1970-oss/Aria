"""Realtime Fly Tying status bus."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "state": "idle",
    "detail": "",
    "recipe_id": "",
    "session_id": "",
    "task": "",
    "progress": 0,
    "error": "",
    "ts": 0.0,
}


def get_flytying_state() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def set_flytying_state(
    state: str,
    *,
    detail: str = "",
    recipe_id: str = "",
    session_id: str = "",
    task: str = "",
    progress: float | int = 0,
    error: str = "",
    publish: bool = True,
) -> dict[str, Any]:
    state = (state or "idle").strip().lower()
    if state not in (
        "idle",
        "searching",
        "suggesting",
        "session",
        "scanning",
        "recovering",
        "nightly",
        "error",
    ):
        state = "idle"
    with _lock:
        _state.update(
            {
                "state": state,
                "detail": detail or "",
                "recipe_id": recipe_id or _state.get("recipe_id") or "",
                "session_id": session_id or _state.get("session_id") or "",
                "task": task or "",
                "progress": float(progress or 0),
                "error": error or "",
                "ts": time.time(),
            }
        )
        snapshot = dict(_state)
    try:
        from jarvis.events import emit

        emit("flytying_state", **snapshot)
    except Exception:
        pass
    if publish:
        try:
            from jarvis.ws_hub import publish as ws_publish

            ws_publish("flytying_state", **snapshot)
        except Exception:
            pass
    return snapshot
