"""Search runtime status bus."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_state: dict[str, Any] = {
    "state": "idle",
    "detail": "",
    "error": "",
    "last_query": "",
    "last_latency_ms": 0.0,
    "last_hit_count": 0,
    "updated": 0.0,
}


def set_search_state(state: str, *, detail: str = "", error: str = "", **extra: Any) -> dict[str, Any]:
    with _lock:
        _state["state"] = state
        _state["detail"] = detail
        _state["error"] = error
        _state["updated"] = time.time()
        for k, v in extra.items():
            _state[k] = v
        return dict(_state)


def get_search_state() -> dict[str, Any]:
    with _lock:
        return dict(_state)
