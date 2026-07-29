"""Status bus for Capabilities product."""

from __future__ import annotations

import time
from typing import Any

_STATE: dict[str, Any] = {
    "state": "idle",
    "detail": "",
    "error": "",
    "updated_at": 0.0,
}


def set_capabilities_state(state: str, *, detail: str = "", error: str = "") -> dict[str, Any]:
    _STATE["state"] = state
    _STATE["detail"] = detail
    _STATE["error"] = error
    _STATE["updated_at"] = time.time()
    return get_capabilities_state()


def get_capabilities_state() -> dict[str, Any]:
    return dict(_STATE)
