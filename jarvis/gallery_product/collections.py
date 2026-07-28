"""Collections + per-image favorites."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

COLLECTIONS_FILE = DATA_DIR / "gallery_product" / "collections.json"
FAVORITES_FILE = DATA_DIR / "gallery_product" / "favorites.json"


def _load(path) -> Any:
    if not path.exists():
        return [] if "favorite" in path.name else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [] if "favorite" in path.name else {}


def _save(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_favorites() -> dict[str, Any]:
    rows = _load(FAVORITES_FILE)
    if not isinstance(rows, list):
        rows = []
    return {"ok": True, "items": rows}


def toggle_favorite(name: str) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        return {"ok": False, "message": "name required"}
    rows = _load(FAVORITES_FILE)
    if not isinstance(rows, list):
        rows = []
    names = {r.get("name") for r in rows}
    if name in names:
        rows = [r for r in rows if r.get("name") != name]
        fav = False
    else:
        rows.insert(0, {"name": name, "ts": time.time()})
        fav = True
    _save(FAVORITES_FILE, rows[:500])
    return {"ok": True, "favorite": fav, "name": name}


def is_favorite(name: str) -> bool:
    rows = _load(FAVORITES_FILE)
    if not isinstance(rows, list):
        return False
    return any(r.get("name") == name for r in rows)


def list_collections() -> dict[str, Any]:
    store = _load(COLLECTIONS_FILE)
    if not isinstance(store, dict):
        store = {}
    items = [{"id": k, **v} for k, v in store.items()]
    items.sort(key=lambda x: float(x.get("ts") or 0), reverse=True)
    return {"ok": True, "items": items}


def create_collection(title: str, *, names: list[str] | None = None) -> dict[str, Any]:
    title = (title or "").strip() or "Collection"
    store = _load(COLLECTIONS_FILE)
    if not isinstance(store, dict):
        store = {}
    cid = str(uuid.uuid4())[:8]
    store[cid] = {
        "title": title[:120],
        "names": list(names or [])[:200],
        "ts": time.time(),
        "notes": "",
    }
    _save(COLLECTIONS_FILE, store)
    return {"ok": True, "id": cid, "collection": store[cid]}


def add_to_collection(collection_id: str, name: str) -> dict[str, Any]:
    store = _load(COLLECTIONS_FILE)
    if not isinstance(store, dict) or collection_id not in store:
        return {"ok": False, "message": "Collection not found"}
    names = list(store[collection_id].get("names") or [])
    if name not in names:
        names.insert(0, name)
    store[collection_id]["names"] = names[:200]
    _save(COLLECTIONS_FILE, store)
    return {"ok": True, "collection": store[collection_id]}


def remove_collection(collection_id: str) -> dict[str, Any]:
    store = _load(COLLECTIONS_FILE)
    if not isinstance(store, dict):
        return {"ok": False}
    store.pop(collection_id, None)
    _save(COLLECTIONS_FILE, store)
    return {"ok": True}
