"""Mission Control bridge — Layouts health summary only."""

from __future__ import annotations

from typing import Any


def layouts_mission_panel() -> dict[str, Any]:
    from jarvis.layouts_product.diagnostics import health_summary
    from jarvis.layouts_product.restore import recovery_status

    health = health_summary()
    recovery = recovery_status()
    return {
        "product": "Layouts",
        "operator_name": "Layouts",
        "state": "ready" if health.get("healthy") else "attention",
        "detail": (
            f"{health.get('builtin_count', 0)} starters · "
            f"{health.get('custom_count', 0)} custom · "
            f"schema v{health.get('schema_version')}"
        ),
        "schema_version": health.get("schema_version"),
        "active_layout": health.get("active_layout"),
        "restore_on_boot": health.get("restore_on_boot"),
        "failures": len(health.get("recent_failures") or []),
        "healthy": health.get("healthy"),
        "undo_available": health.get("undo_available"),
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
        },
        "deep_links": {
            "home": "#",  # opens modal via client
            "status": "/api/layouts/product",
            "diagnostics": "/api/layouts/diagnostics",
            "mission": "/api/layouts/mission",
            "catalog": "/api/layouts/catalog",
        },
        "note": "Mission Control shows Layouts health only — edit layouts from the Layouts UI.",
    }
