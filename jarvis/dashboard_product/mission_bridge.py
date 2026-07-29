"""Mission Control bridge — Home summary only; MC owns ops detail."""

from __future__ import annotations

from typing import Any


def dashboard_mission_panel(*, assistant=None) -> dict[str, Any]:
    from jarvis.dashboard_product.diagnostics import health_summary, recovery_status
    from jarvis.dashboard_product.engine import product_status

    status = product_status(assistant=assistant)
    health = health_summary(assistant=assistant)
    recovery = recovery_status()
    return {
        "product": "Dashboard",
        "operator_name": "Home",
        "state": "ready" if health.get("healthy") else "attention",
        "detail": f"{health.get('widgets_showing', 0)} widgets showing · {health.get('latency_ms', '?')}ms",
        "widgets_showing": health.get("widgets_showing"),
        "widget_defs": health.get("widget_defs"),
        "latency_ms": health.get("latency_ms"),
        "failures": len(health.get("widget_failures") or []),
        "healthy": health.get("healthy"),
        "layout_role": health.get("layout_role"),
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
        },
        "deep_links": {
            "home": "#dashboard",
            "status": "/api/dashboard/product",
            "diagnostics": "/api/dashboard/diagnostics",
            "mission": "/api/dashboard/mission",
            "aggregate": "/api/dashboard/home",
        },
        "note": "Mission Control shows Home summary only. Open Home for the operator glance surface.",
        "status_snapshot": status,
    }
