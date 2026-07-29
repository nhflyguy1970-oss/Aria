"""Room cards — name → entity_ids mapping (DATA_DIR + optional HA area seed)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from jarvis.config import DATA_DIR

ROOMS_FILE = DATA_DIR / "home_assistant_product" / "rooms.json"


def _norm(s: str) -> str:
    return re.sub(r"[\s_]+", " ", (s or "").lower()).strip()


def _load() -> dict[str, Any]:
    if ROOMS_FILE.is_file():
        try:
            data = json.loads(ROOMS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"rooms": [], "seeded": False}


def _save(store: dict[str, Any]) -> None:
    ROOMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ROOMS_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _seed_from_ha_areas(store: dict[str, Any]) -> dict[str, Any]:
    """Seed room cards from entity area_id / area_name attributes when available."""
    if store.get("seeded") and store.get("rooms"):
        return store
    try:
        from jarvis.home_assistant import ha_enabled, list_states
        from jarvis.ha_entity_filter import filter_visible_entities

        if not ha_enabled():
            return store
        buckets: dict[str, list[str]] = {}
        for st in filter_visible_entities(list_states()):
            attrs = st.get("attributes") or {}
            area = attrs.get("area_id") or attrs.get("area_name") or ""
            area = str(area).strip()
            if not area:
                continue
            eid = (st.get("entity_id") or "").strip()
            if not eid:
                continue
            key = _norm(area)
            buckets.setdefault(key, [])
            if eid not in buckets[key]:
                buckets[key].append(eid)
        if not buckets:
            store["seeded"] = True
            return store
        existing = {_norm(str(r.get("name") or "")) for r in (store.get("rooms") or [])}
        rooms = list(store.get("rooms") or [])
        for key, eids in sorted(buckets.items()):
            if key in existing:
                continue
            rooms.append(
                {
                    "id": uuid.uuid4().hex[:12],
                    "name": key.replace("_", " ").title(),
                    "entity_ids": eids[:40],
                    "seeded": True,
                }
            )
        store["rooms"] = rooms
        store["seeded"] = True
        _save(store)
    except Exception:
        store["seeded"] = True
    return store


def list_rooms(*, seed: bool = True) -> list[dict[str, Any]]:
    store = _load()
    if seed:
        store = _seed_from_ha_areas(store)
    return list(store.get("rooms") or [])


def get_room(room_id: str) -> dict[str, Any] | None:
    rid = (room_id or "").strip()
    for room in list_rooms():
        if room.get("id") == rid or _norm(str(room.get("name") or "")) == _norm(rid):
            return dict(room)
    return None


def upsert_room(body: dict[str, Any]) -> dict[str, Any]:
    store = _load()
    rooms = list(store.get("rooms") or [])
    rid = str(body.get("id") or "").strip()
    name = str(body.get("name") or "").strip()
    entity_ids = [str(e).strip() for e in (body.get("entity_ids") or []) if str(e).strip()]
    if rid:
        for i, room in enumerate(rooms):
            if room.get("id") == rid:
                room = dict(room)
                if name:
                    room["name"] = name
                if "entity_ids" in body:
                    room["entity_ids"] = entity_ids
                if body.get("notes") is not None:
                    room["notes"] = str(body.get("notes") or "")
                rooms[i] = room
                store["rooms"] = rooms
                _save(store)
                return room
    if not name:
        raise ValueError("name required")
    room = {
        "id": rid or uuid.uuid4().hex[:12],
        "name": name,
        "entity_ids": entity_ids,
        "notes": str(body.get("notes") or ""),
        "seeded": False,
    }
    rooms.append(room)
    store["rooms"] = rooms
    _save(store)
    return room


def delete_room(room_id: str) -> bool:
    store = _load()
    before = list(store.get("rooms") or [])
    after = [r for r in before if r.get("id") != room_id]
    if len(after) == len(before):
        return False
    store["rooms"] = after
    _save(store)
    return True


def room_entity_ids(room_name_or_id: str) -> list[str]:
    room = get_room(room_name_or_id)
    if not room:
        return []
    return list(room.get("entity_ids") or [])
