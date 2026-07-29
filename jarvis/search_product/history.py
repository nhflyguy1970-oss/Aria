"""Search history and saved searches."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "search_product" / "history.json"
SAVED_FILE = DATA_DIR / "search_product" / "saved.json"
MAX_HISTORY = 100


def _load_list(path, key: str) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get(key) if isinstance(raw, dict) else raw
        return [x for x in (items or []) if isinstance(x, dict)]
    except (json.JSONDecodeError, OSError):
        return []


def _save_list(path, key: str, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({key: items}, indent=2), encoding="utf-8")


def record_query(
    query: str,
    *,
    facets: list[str] | None = None,
    hit_count: int = 0,
    latency_ms: float = 0.0,
    mode: str = "browse",
) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {}
    entry = {
        "id": uuid.uuid4().hex[:12],
        "query": q,
        "facets": list(facets or []),
        "hit_count": int(hit_count),
        "latency_ms": round(float(latency_ms), 2),
        "mode": mode,
        "ts": time.time(),
    }
    items = _load_list(HISTORY_FILE, "history")
    items = [e for e in items if e.get("query") != q]  # bump duplicate
    items.insert(0, entry)
    _save_list(HISTORY_FILE, "history", items[:MAX_HISTORY])
    return entry


def list_history(limit: int = 30) -> list[dict[str, Any]]:
    return _load_list(HISTORY_FILE, "history")[: max(1, min(limit, MAX_HISTORY))]


def clear_history() -> dict[str, Any]:
    _save_list(HISTORY_FILE, "history", [])
    return {"ok": True, "cleared": True}


def source_frequency(limit: int = 50) -> dict[str, float]:
    """Soft boost map from recent history facets."""
    boost: dict[str, float] = {}
    for e in list_history(limit):
        for f in e.get("facets") or []:
            boost[str(f)] = min(0.1, boost.get(str(f), 0.0) + 0.01)
    return boost


def list_saved() -> list[dict[str, Any]]:
    return _load_list(SAVED_FILE, "saved")


def save_search(query: str, *, name: str = "", facets: list[str] | None = None) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "query required"}
    entry = {
        "id": uuid.uuid4().hex[:12],
        "name": (name or q)[:80],
        "query": q,
        "facets": list(facets or []),
        "ts": time.time(),
    }
    items = list_saved()
    items = [e for e in items if e.get("query") != q]
    items.insert(0, entry)
    _save_list(SAVED_FILE, "saved", items[:50])
    return {"ok": True, "saved": entry}


def delete_saved(saved_id: str) -> dict[str, Any]:
    items = [e for e in list_saved() if e.get("id") != saved_id]
    _save_list(SAVED_FILE, "saved", items)
    return {"ok": True, "deleted": saved_id}
