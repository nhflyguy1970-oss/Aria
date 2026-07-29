"""Mission Control bridge for Capabilities."""

from __future__ import annotations

from typing import Any


def capabilities_mission_panel() -> dict[str, Any]:
    from jarvis.capabilities_product.engine import product_status
    from jarvis.capabilities_product.health import recovery_status
    from jarvis.capabilities_product.history import list_activity
    from jarvis.capabilities_product.status_bus import get_capabilities_state

    status = product_status()
    recovery = recovery_status()
    state = get_capabilities_state()
    recent_fail = [
        a
        for a in list_activity(20)
        if a.get("kind") in ("load_failed", "fail") or "fail" in str(a.get("kind") or "")
    ]
    warnings = []
    if status.get("failed"):
        warnings.append(f"{status['failed']} failed capability load(s)")
    if recovery.get("quarantined"):
        warnings.append(f"{len(recovery['quarantined'])} quarantined")

    return {
        "product": "Capabilities",
        "state": state.get("state") or status.get("state") or "idle",
        "detail": state.get("detail") or "",
        "count": status.get("count") or 0,
        "enabled": status.get("enabled") or 0,
        "disabled": status.get("disabled") or 0,
        "failed": status.get("failed") or 0,
        "experimental": status.get("experimental") or 0,
        "by_trust": status.get("by_trust") or {},
        "by_layer": status.get("by_layer") or {},
        "health": status.get("health") or {},
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "steps_done": sum(1 for s in (recovery.get("steps") or []) if s.get("done")),
            "steps_total": len(recovery.get("steps") or []),
        },
        "warnings": warnings,
        "recent_failures": recent_fail[:5],
        "isolation": "none",
        "isolation_note": status.get("isolation_policy"),
        "errors": (
            [{"severity": "error", "message": state.get("error")}]
            if state.get("error")
            else ([{"severity": "warning", "message": w} for w in warnings[:3]])
        ),
        "deep_links": {
            "home": "#capabilities",
            "status": "/api/capabilities/product",
            "recovery": "/api/capabilities/product/recovery",
            "mission": "/api/capabilities/product/mission",
            "diagnostics": "/api/capabilities/product/diagnostics",
            "registry": "/api/capabilities/product/registry",
        },
    }
