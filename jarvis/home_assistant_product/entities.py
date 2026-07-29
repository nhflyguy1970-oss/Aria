"""Entity manager — search / resolve via aliases + fuzzy + filter_visible."""

from __future__ import annotations

import re
from typing import Any


def _norm(s: str) -> str:
    return re.sub(r"[\s_]+", " ", (s or "").lower()).strip()


def _domain_of(eid: str) -> str:
    eid = eid or ""
    return eid.split(".", 1)[0] if "." in eid else ""


def _entity_card(st: dict[str, Any]) -> dict[str, Any]:
    eid = st.get("entity_id") or ""
    attrs = st.get("attributes") or {}
    return {
        "entity_id": eid,
        "domain": _domain_of(eid),
        "state": st.get("state"),
        "friendly_name": attrs.get("friendly_name") or eid,
        "area_id": attrs.get("area_id") or attrs.get("area_name") or "",
        "attributes": {
            k: attrs.get(k)
            for k in ("brightness", "color_temp_kelvin", "rgb_color", "hs_color", "unit_of_measurement")
            if k in attrs
        },
    }


def search(
    *,
    q: str = "",
    domain: str = "",
    room: str = "",
    favorites_only: bool = False,
    recent: bool = False,
    limit: int = 40,
) -> dict[str, Any]:
    """Search visible HA entities with optional room / favorites / recent filters."""
    from jarvis.ha_entity_filter import filter_visible_entities
    from jarvis.home_assistant import ha_enabled, list_states
    from jarvis.home_assistant_product.favorites import list_favorites
    from jarvis.home_assistant_product.history import list_history
    from jarvis.home_assistant_product.rooms import room_entity_ids

    if not ha_enabled():
        return {"ok": False, "message": "Home Assistant not enabled", "results": [], "count": 0}

    try:
        states = filter_visible_entities(list_states())
    except Exception as exc:
        return {"ok": False, "message": str(exc), "results": [], "count": 0}

    fav_set = set(list_favorites())
    room_set: set[str] = set()
    if room:
        room_set = set(room_entity_ids(room))
    recent_ids: list[str] = []
    if recent:
        for row in list_history(limit=80, kind="control"):
            eid = str(row.get("entity_id") or "").strip()
            if eid and eid not in recent_ids:
                recent_ids.append(eid)

    qn = _norm(q)
    words = [w for w in qn.split() if len(w) > 1]
    dom = (domain or "").strip().lower()
    scored: list[tuple[float, dict[str, Any]]] = []

    for st in states:
        eid = (st.get("entity_id") or "").strip()
        if not eid:
            continue
        if dom and not eid.startswith(f"{dom}."):
            continue
        if favorites_only and eid not in fav_set:
            continue
        if room_set and eid not in room_set:
            continue
        if recent and recent_ids and eid not in set(recent_ids):
            continue

        card = _entity_card(st)
        attrs = st.get("attributes") or {}
        friendly = _norm(attrs.get("friendly_name") or "")
        hay = _norm(f"{eid} {friendly} {attrs.get('area_id') or ''}")
        score = 1.0 if not qn else 0.0
        if qn:
            if qn in hay or qn.replace(" ", "_") in eid:
                score += 10
            for w in words:
                if w in hay or w in eid:
                    score += 2
            if eid.endswith(qn.replace(" ", "_")):
                score += 3
            if score <= 0:
                continue
        if eid in fav_set:
            score += 1.5
        if recent_ids and eid in recent_ids:
            score += 1.0 + max(0, (20 - recent_ids.index(eid)) * 0.05)
        scored.append((score, card))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [c for _, c in scored[: max(1, min(limit, 200))]]
    return {
        "ok": True,
        "q": q,
        "domain": dom,
        "room": room,
        "favorites_only": favorites_only,
        "recent": recent,
        "results": results,
        "count": len(results),
    }


def resolve(
    query: str,
    *,
    domain: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Resolve a natural-language target to entity_ids using aliases, fuzzy search,
    and filter_visible — one control pipeline entry point.
    """
    from jarvis.ha_aliases import resolve_alias
    from jarvis.ha_entity_filter import filter_visible_entities
    from jarvis.home_assistant import find_entities, ha_enabled, list_states

    q = (query or "").strip()
    if not q:
        return {"ok": False, "message": "query required", "entity_ids": [], "matches": []}

    alias_ids = resolve_alias(q)
    if alias_ids:
        matches: list[dict[str, Any]] = []
        try:
            if ha_enabled():
                by_id = {
                    (st.get("entity_id") or ""): st
                    for st in filter_visible_entities(list_states())
                }
                for eid in alias_ids:
                    st = by_id.get(eid)
                    if st:
                        matches.append(_entity_card(st))
                    else:
                        matches.append(
                            {
                                "entity_id": eid,
                                "domain": _domain_of(eid),
                                "state": "?",
                                "friendly_name": eid,
                                "area_id": "",
                                "attributes": {},
                            }
                        )
        except Exception:
            matches = [
                {
                    "entity_id": eid,
                    "domain": _domain_of(eid),
                    "state": "?",
                    "friendly_name": eid,
                    "area_id": "",
                    "attributes": {},
                }
                for eid in alias_ids
            ]
        return {
            "ok": True,
            "query": q,
            "source": "alias",
            "entity_ids": alias_ids,
            "matches": matches[:limit],
        }

    if not ha_enabled():
        return {"ok": False, "message": "Home Assistant not enabled", "entity_ids": [], "matches": []}

    try:
        found = find_entities(q, domain=domain, limit=limit)
        found = filter_visible_entities(found)
    except Exception as exc:
        return {"ok": False, "message": str(exc), "entity_ids": [], "matches": []}

    matches = [_entity_card(st) for st in found]
    return {
        "ok": True,
        "query": q,
        "source": "fuzzy",
        "entity_ids": [m["entity_id"] for m in matches],
        "matches": matches,
    }
