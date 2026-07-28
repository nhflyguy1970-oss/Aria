"""Activity Center bridge for Browser events."""

from __future__ import annotations

import json
import time
from typing import Any

_RECENT: list[dict[str, Any]] = []


def emit_browser_event(event_type: str, message: str = "", detail: dict | None = None) -> dict[str, Any]:
    evt = {
        "id": f"browser-{int(time.time() * 1000)}",
        "timestamp": time.time(),
        "category": "browser",
        "type": event_type,
        "severity": _severity(event_type),
        "title": _title(event_type),
        "message": message or event_type.replace("_", " "),
        "fix": "Open Browser",
        "deepLink": "browser",
        "product": "browser",
        "detail": detail or {},
    }
    _RECENT.insert(0, evt)
    del _RECENT[100:]
    try:
        from jarvis.config import DATA_DIR

        path = DATA_DIR / "browser_product" / "activity_outbox.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(evt) + "\n")
    except Exception:
        pass
    return evt


def recent_events(*, limit: int = 30) -> list[dict[str, Any]]:
    return list(_RECENT)[:limit]


def _severity(event_type: str) -> str:
    if "fail" in event_type or "blocked" in event_type or "error" in event_type:
        return "warning"
    if "takeover" in event_type or "download" in event_type:
        return "info"
    return "info"


def _title(event_type: str) -> str:
    return {
        "browser_navigated": "Navigated",
        "browser_navigate_failed": "Navigation failed",
        "browser_blocked_url": "URL blocked",
        "browser_task_start": "Browser task started",
        "browser_task_complete": "Browser task complete",
        "browser_task_failed": "Browser task failed",
        "browser_takeover": "Takeover",
        "browser_paused": "Paused",
        "browser_resumed": "Resumed",
        "browser_stopped": "Stopped",
        "browser_download_blocked": "Download blocked",
    }.get(event_type, event_type.replace("_", " ").title())
