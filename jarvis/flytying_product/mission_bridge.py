"""Mission Control bridge for Fly Tying."""

from __future__ import annotations

from typing import Any


def flytying_mission_panel() -> dict[str, Any]:
    from jarvis.flytying_product.engine import product_status, recovery_status
    from jarvis.flytying_product.inventory import inventory_summary
    from jarvis.flytying_product.sessions import active_session
    from jarvis.flytying_product.status_bus import get_flytying_state

    status = product_status()
    recovery = recovery_status()
    state = get_flytying_state()
    bridge = status.get("bridge") or {}
    inv: dict[str, Any] = {}
    try:
        inv = inventory_summary()
    except Exception:
        inv = {"ok": False, "count": 0}
    session = None
    try:
        session = active_session()
    except Exception:
        session = None

    nightly = bridge.get("nightly") or {}
    try:
        from jarvis.flytying.nightly import nightly_status

        nightly = nightly_status()
    except Exception:
        pass

    errors: list[dict[str, Any]] = []
    if not recovery.get("ready"):
        errors.append({"severity": "warning", "message": recovery.get("hint") or "Blackfly not ready"})
    if state.get("state") == "error" and state.get("error"):
        errors.append({"severity": "error", "message": state.get("error")})

    return {
        "product": "Fly Tying",
        "state": state.get("state") or "idle",
        "detail": state.get("detail") or "",
        "corpus_loaded": bool(bridge.get("loaded") or bridge.get("blackfly_loaded") or recovery.get("ready")),
        "record_count": bridge.get("record_count") or (recovery.get("enablement") or {}).get("record_count"),
        "rag": bool((recovery.get("enablement") or {}).get("rag_available") or bridge.get("semantic_usable")),
        "recipe_source": bridge.get("recipe_source") or "",
        "nightly": nightly,
        "inventory": {
            "count": inv.get("count") or 0,
            "low_stock": len(inv.get("low_stock") or []),
            "recent_scans": len(inv.get("recent_scans") or []),
        },
        "session": {
            "active": bool(session and session.get("status") == "active"),
            "id": (session or {}).get("id") or "",
            "recipe_id": (session or {}).get("recipe_id") or "",
            "recipe_name": (session or {}).get("recipe_name") or "",
            "step_idx": (session or {}).get("step_idx"),
        },
        "queue": {"pending": len(inv.get("queue") or [])},
        "profiles": status.get("profiles"),
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "steps_done": sum(1 for s in (recovery.get("steps") or []) if s.get("done")),
            "steps_total": len(recovery.get("steps") or []),
        },
        "errors": errors[:5],
        "deep_links": {
            "flytying_home": "#flytying",
            "status": "/api/flytying/product",
            "recovery": "/api/flytying/product/recovery",
            "mission": "/api/flytying/product/mission",
            "history": "/api/flytying/product/history",
            "library": "/api/flytying/library/status",
        },
    }
