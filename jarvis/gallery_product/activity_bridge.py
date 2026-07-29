"""Activity Center bridge for Gallery events."""

from __future__ import annotations

import json
import time
from typing import Any

_RECENT: list[dict[str, Any]] = []


def emit_gallery_event(event_type: str, message: str = "", **detail: Any) -> dict[str, Any]:
    evt = {
        "id": f"gallery-{int(time.time() * 1000)}",
        "timestamp": time.time(),
        "category": "gallery",
        "type": event_type,
        "severity": "info",
        "title": event_type.replace("_", " ").title(),
        "message": message or event_type.replace("_", " "),
        "action": "Open Gallery",
        "deepLink": "gallery",
        "product": "gallery",
        "detail": detail or {},
    }
    _RECENT.insert(0, evt)
    del _RECENT[100:]
    try:
        from jarvis.config import DATA_DIR

        path = DATA_DIR / "gallery_product" / "activity_outbox.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(evt) + "\n")
    except Exception:
        pass
    return evt


def drain_outbox(*, limit: int = 50) -> list[dict[str, Any]]:
    from jarvis.config import DATA_DIR
    import json

    path = DATA_DIR / "gallery_product" / "activity_outbox.jsonl"
    if not path.is_file():
        return list(_RECENT)[:limit]
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    try:
        path.write_text("", encoding="utf-8")
    except Exception:
        pass
    return list(reversed(events))


def recent_events(*, limit: int = 30) -> list[dict[str, Any]]:
    return list(_RECENT)[:limit]
