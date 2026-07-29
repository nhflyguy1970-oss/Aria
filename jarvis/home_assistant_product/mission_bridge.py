"""Mission Control bridge for Smart Home."""

from __future__ import annotations

from typing import Any


def smarthome_mission_panel() -> dict[str, Any]:
    from jarvis.home_assistant_product.engine import product_status, recovery_status
    from jarvis.home_assistant_product.favorites import list_favorites
    from jarvis.home_assistant_product.rooms import list_rooms
    from jarvis.home_assistant_product.status_bus import get_smarthome_state

    status = product_status()
    recovery = recovery_status()
    state = get_smarthome_state()
    ha = status.get("ha") or {}
    conn = recovery.get("connection") or {}

    entity_count = None
    try:
        from jarvis.home_assistant import ha_enabled, list_states
        from jarvis.ha_entity_filter import filter_visible_entities

        if ha_enabled():
            entity_count = len(filter_visible_entities(list_states()))
    except Exception:
        entity_count = None

    favs = []
    rooms = []
    try:
        favs = list_favorites()
    except Exception:
        favs = []
    try:
        rooms = list_rooms(seed=False)
    except Exception:
        rooms = []

    errors: list[dict[str, Any]] = []
    if not recovery.get("ready"):
        errors.append({"severity": "warning", "message": recovery.get("hint") or "HA not ready"})
    if state.get("state") == "error" and state.get("error"):
        errors.append({"severity": "error", "message": state.get("error")})

    return {
        "product": "Smart Home",
        "state": state.get("state") or "idle",
        "detail": state.get("detail") or "",
        "connected": bool(conn.get("ok") or ha.get("connected")),
        "url": ha.get("url") or "",
        "version": (conn.get("version") if isinstance(conn, dict) else None) or None,
        "entity_count": entity_count,
        "rooms": {"count": len(rooms)},
        "favorites": {"count": len(favs)},
        "queue": {"pending": 0},
        "webhook": {
            "set": bool(ha.get("automation_secret_set")),
            "url": ha.get("automation_webhook_url") or ha.get("automation_webhook") or "",
        },
        "latency": None,
        "permissions": "ha_control",
        "health": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "feature_on": ha.get("feature_on") or ha.get("enabled"),
            "token_set": ha.get("token_set"),
        },
        "profiles": status.get("profiles"),
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "steps_done": sum(1 for s in (recovery.get("steps") or []) if s.get("done")),
            "steps_total": len(recovery.get("steps") or []),
        },
        "errors": errors[:5],
        "deep_links": {
            "smarthome_home": "#smarthome",
            "status": "/api/smarthome/product",
            "recovery": "/api/smarthome/product/recovery",
            "mission": "/api/smarthome/product/mission",
            "history": "/api/smarthome/product/history",
            "ha_status": "/api/homeassistant/status",
        },
    }


# Alias matching flytying/vision naming
def home_assistant_mission_panel() -> dict[str, Any]:
    return smarthome_mission_panel()
