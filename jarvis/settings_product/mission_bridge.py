"""Mission Control bridge for Settings."""

from __future__ import annotations

from typing import Any


def settings_mission_panel() -> dict[str, Any]:
    from jarvis.settings_product.diagnostics import health_summary, recovery_status
    from jarvis.settings_product.engine import product_status
    from jarvis.settings_product.coach import coach_warnings

    status = product_status()
    health = health_summary()
    recovery = recovery_status()
    warnings = coach_warnings()
    return {
        "product": "Settings",
        "state": "ready" if health.get("healthy") else "attention",
        "detail": f"{health.get('catalog_count', 0)} preferences indexed",
        "catalog_count": health.get("catalog_count") or 0,
        "stores_present": health.get("stores_present") or 0,
        "stores_tracked": health.get("stores_tracked") or 0,
        "corrupt_count": health.get("corrupt_count") or 0,
        "warnings": [w.get("title") for w in warnings[:5]],
        "active_profile": health.get("active_profile"),
        "healthy": recovery.get("ready"),
        "migration": {"theme_unified": True},
        "sync": {"note": "Chrome prefs: browser + optional server appearance mirror"},
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "steps_done": sum(1 for s in (recovery.get("steps") or []) if s.get("done")),
            "steps_total": len(recovery.get("steps") or []),
        },
        "errors": [{"severity": w.get("severity"), "message": w.get("title")} for w in warnings[:4]],
        "deep_links": {
            "home": "#settings",
            "status": "/api/settings/product",
            "diagnostics": "/api/settings/product/diagnostics",
            "recovery": "/api/settings/product/recovery",
            "mission": "/api/settings/product/mission",
            "catalog": "/api/settings/product/catalog",
        },
        "runtime_config_note": (
            "Mission Control tab 'Runtime config' shows ops snapshots — not editable operator preferences."
        ),
    }
