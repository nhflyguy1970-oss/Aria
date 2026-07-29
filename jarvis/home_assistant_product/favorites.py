"""Pinned Smart Home favorites (entity_ids) in DATA_DIR JSON."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

FAVORITES_FILE = DATA_DIR / "home_assistant_product" / "favorites.json"


def _load() -> dict[str, Any]:
    if FAVORITES_FILE.is_file():
        try:
            data = json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"entity_ids": [], "groups": {}}


def _save(store: dict[str, Any]) -> None:
    FAVORITES_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAVORITES_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def list_favorites() -> list[str]:
    store = _load()
    ids = [str(e).strip() for e in (store.get("entity_ids") or []) if str(e).strip()]
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for eid in ids:
        if eid not in seen:
            seen.add(eid)
            out.append(eid)
    return out


def pin(entity_id: str) -> list[str]:
    eid = (entity_id or "").strip()
    if not eid:
        raise ValueError("entity_id required")
    store = _load()
    ids = list_favorites()
    if eid not in ids:
        ids.append(eid)
    store["entity_ids"] = ids
    _save(store)
    return ids


def unpin(entity_id: str) -> list[str]:
    eid = (entity_id or "").strip()
    store = _load()
    ids = [e for e in list_favorites() if e != eid]
    store["entity_ids"] = ids
    _save(store)
    return ids


def reorder(entity_ids: list[str]) -> list[str]:
    """Reorder favorites; unknown ids appended at end of previous set are dropped."""
    wanted = [str(e).strip() for e in (entity_ids or []) if str(e).strip()]
    current = set(list_favorites())
    ordered = [e for e in wanted if e in current]
    for e in list_favorites():
        if e not in ordered:
            ordered.append(e)
    store = _load()
    store["entity_ids"] = ordered
    _save(store)
    return ordered


def is_favorite(entity_id: str) -> bool:
    return (entity_id or "").strip() in set(list_favorites())


def favorites_payload() -> dict[str, Any]:
    ids = list_favorites()
    entities: list[dict[str, Any]] = []
    try:
        from jarvis.home_assistant import get_state, ha_enabled

        if ha_enabled():
            for eid in ids:
                st = get_state(eid)
                if st:
                    attrs = st.get("attributes") or {}
                    entities.append(
                        {
                            "entity_id": eid,
                            "state": st.get("state"),
                            "friendly_name": attrs.get("friendly_name") or eid,
                        }
                    )
                else:
                    entities.append({"entity_id": eid, "state": "unknown", "friendly_name": eid})
    except Exception:
        entities = [{"entity_id": eid, "state": "?", "friendly_name": eid} for eid in ids]
    return {"ok": True, "entity_ids": ids, "entities": entities, "count": len(ids)}
