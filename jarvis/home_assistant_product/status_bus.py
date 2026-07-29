"""Realtime Smart Home status bus."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "state": "idle",
    "detail": "",
    "entity_id": "",
    "scene": "",
    "task": "",
    "progress": 0,
    "error": "",
    "ts": 0.0,
}


def get_smarthome_state() -> dict[str, Any]:
    with _lock:
        return dict(_state)


def set_smarthome_state(
    state: str,
    *,
    detail: str = "",
    entity_id: str = "",
    scene: str = "",
    task: str = "",
    progress: float | int = 0,
    error: str = "",
    publish: bool = True,
) -> dict[str, Any]:
    state = (state or "idle").strip().lower()
    if state not in (
        "idle",
        "connecting",
        "searching",
        "controlling",
        "scene",
        "recovering",
        "scanning",
        "error",
    ):
        state = "idle"
    with _lock:
        _state.update(
            {
                "state": state,
                "detail": detail or "",
                "entity_id": entity_id or _state.get("entity_id") or "",
                "scene": scene or _state.get("scene") or "",
                "task": task or "",
                "progress": float(progress or 0),
                "error": error or "",
                "ts": time.time(),
            }
        )
        snapshot = dict(_state)
    try:
        from jarvis.events import emit

        emit("smarthome_state", **snapshot)
    except Exception:
        pass
    if publish:
        try:
            from jarvis.ws_hub import publish as ws_publish

            ws_publish("smarthome_state", **snapshot)
        except Exception:
            pass
    return snapshot
