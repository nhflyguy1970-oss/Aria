"""Search sessions — lightweight query sessions for Home / deep links."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

SESSIONS_FILE = DATA_DIR / "search_product" / "sessions.json"
MAX_SESSIONS = 40


def _load() -> list[dict[str, Any]]:
    if not SESSIONS_FILE.is_file():
        return []
    try:
        raw = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        items = raw.get("sessions") if isinstance(raw, dict) else raw
        return [x for x in (items or []) if isinstance(x, dict)]
    except (json.JSONDecodeError, OSError):
        return []


def _save(items: list[dict[str, Any]]) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps({"sessions": items}, indent=2), encoding="utf-8")


def start_session(query: str, *, facets: list[str] | None = None, mode: str = "browse") -> dict[str, Any]:
    session = {
        "id": uuid.uuid4().hex[:12],
        "query": (query or "").strip(),
        "facets": list(facets or []),
        "mode": mode,
        "created": time.time(),
        "updated": time.time(),
        "result_ids": [],
    }
    items = _load()
    items.insert(0, session)
    _save(items[:MAX_SESSIONS])
    return session


def touch_session(session_id: str, *, result_ids: list[str] | None = None) -> dict[str, Any] | None:
    items = _load()
    for s in items:
        if s.get("id") == session_id:
            s["updated"] = time.time()
            if result_ids is not None:
                s["result_ids"] = list(result_ids)[:40]
            _save(items)
            return s
    return None


def get_session(session_id: str) -> dict[str, Any] | None:
    for s in _load():
        if s.get("id") == session_id:
            return s
    return None


def list_sessions(limit: int = 10) -> list[dict[str, Any]]:
    return _load()[: max(1, min(limit, MAX_SESSIONS))]
