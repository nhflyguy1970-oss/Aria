"""Mission Control bridge — promote critical health; never a second inbox."""

from __future__ import annotations

from typing import Any


def notifications_mission_panel() -> dict[str, Any]:
    from jarvis.notifications_product.diagnostics import health_summary
    from jarvis.notifications_product.pipeline import unread_summary

    health = health_summary()
    summary = unread_summary()
    return {
        "product": "Notifications",
        "operator_name": "Notifications",
        "inbox": "Activity Center",
        "state": "ready" if health.get("healthy") else "attention",
        "detail": (
            f"schema v{health.get('schema_version')} · "
            f"outbox pending {health.get('outbox_pending', 0)} · "
            f"recent {health.get('recent_count', 0)}"
        ),
        "unread_proxy": summary.get("unread"),
        "critical_proxy": summary.get("critical"),
        "enabled": health.get("enabled"),
        "dnd": health.get("dnd"),
        "deep_links": {
            "inbox": "#activityCenter",
            "status": "/api/notifications/product",
            "diagnostics": "/api/notifications/diagnostics",
            "mission": "/api/notifications/mission",
        },
        "note": (
            "Mission Control shows health and may promote critical events. "
            "Operator inbox lives in Notifications (Activity Center)."
        ),
    }


def promote_critical_health(message: str, *, component: str = "mission") -> dict[str, Any]:
    from jarvis.notifications_product.pipeline import publish

    return publish(
        {
            "title": message[:120] or "Mission Control alert",
            "summary": message,
            "severity": "error",
            "source": "mission_control",
            "category": "providers",
            "type": "health_promote",
            "deepLink": "providers",
            "product": "mission_control",
            "desktop": True,
            "toast": True,
        }
    )
