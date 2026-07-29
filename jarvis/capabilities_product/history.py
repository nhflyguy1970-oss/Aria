"""Activity / history log for Capabilities."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "capabilities_product" / "activity.json"
MAX_EVENTS = 200


def _load() -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    try:
        raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [e for e in raw if isinstance(e, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save(events: list[dict[str, Any]]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(events[-MAX_EVENTS:], indent=2), encoding="utf-8")


def record_activity(
    kind: str,
    *,
    capability_id: str = "",
    message: str = "",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        "capability_id": capability_id,
        "message": message,
        "detail": detail or {},
    }
    events = _load()
    events.append(event)
    _save(events)
    return event


def list_activity(limit: int = 50) -> list[dict[str, Any]]:
    events = _load()
    return list(reversed(events[-max(1, limit) :]))


def clear_activity() -> None:
    _save([])
