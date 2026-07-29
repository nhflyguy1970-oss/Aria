"""Recent preference change history (Settings-owned chrome only)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "settings_product" / "history.json"
MAX = 80


def record_change(pref_id: str, *, detail: str = "", category: str = "") -> dict[str, Any]:
    entry = {
        "id": uuid.uuid4().hex[:10],
        "pref_id": pref_id,
        "detail": detail[:200],
        "category": category,
        "ts": time.time(),
    }
    items = list_changes(MAX)
    items.insert(0, entry)
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps({"history": items[:MAX]}, indent=2), encoding="utf-8")
    return entry


def list_changes(limit: int = 30) -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    try:
        raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        items = raw.get("history") if isinstance(raw, dict) else raw
        return [x for x in (items or []) if isinstance(x, dict)][:limit]
    except (json.JSONDecodeError, OSError):
        return []
