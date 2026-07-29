"""Health, diagnostics, recovery for Capabilities."""

from __future__ import annotations

from typing import Any

from jarvis.capabilities_product import policy as cap_policy
from jarvis.capabilities_product.history import list_activity
from jarvis.capabilities_product.registry import registry_snapshot
from jarvis.capabilities_product.status_bus import get_capabilities_state


def health_summary() -> dict[str, Any]:
    snap = registry_snapshot()
    failed_items = [i for i in snap["items"] if i.get("status") == "failed" or i.get("health") == "failed"]
    quarantined = [i for i in snap["items"] if i.get("status") == "quarantined" or i.get("trust") == "quarantined"]
    return {
        "ok": snap["failed"] == 0,
        "count": snap["count"],
        "enabled": snap["enabled"],
        "disabled": snap["disabled"],
        "failed": snap["failed"],
        "failed_items": failed_items[:20],
        "quarantined": quarantined[:20],
        "by_trust": snap["by_trust"],
        "state": get_capabilities_state(),
        "isolation": "none",
        "isolation_note": snap["isolation_policy"],
    }


def diagnostics() -> dict[str, Any]:
    snap = registry_snapshot()
    return {
        "ok": True,
        "registry": {k: snap[k] for k in ("count", "enabled", "disabled", "failed", "by_layer", "by_trust", "by_status")},
        "policy": cap_policy.export_policy(),
        "recent_activity": list_activity(20),
        "state": get_capabilities_state(),
        "contributions": _contrib_diag(),
        "security": {
            "sandbox": False,
            "isolation": "none",
            "honest": True,
            "message": (
                "Capabilities does not sandbox third-party code. "
                "Trust levels and permission previews are the safety communication model."
            ),
        },
    }


def _contrib_diag() -> dict[str, Any]:
    try:
        from jarvis.capabilities_product import contributions as c

        return {
            "routes": len(c.contribution_routes()),
            "tools": len(c.list_agent_tools()),
            "voice_intents": len(c.list_voice_intents()),
            "workflow_steps": len(c.list_workflow_steps()),
            "automation_actions": len(c.list_automation_actions()),
        }
    except Exception as exc:
        return {"error": str(exc)}


def recovery_status() -> dict[str, Any]:
    health = health_summary()
    steps = [
        {
            "id": "registry",
            "label": "Registry available",
            "done": health["count"] > 0,
            "detail": f"{health['count']} capabilities discovered",
        },
        {
            "id": "failures",
            "label": "No failed loads",
            "done": health["failed"] == 0,
            "detail": f"{health['failed']} failed" if health["failed"] else "All clear",
        },
        {
            "id": "quarantine",
            "label": "No unacknowledged quarantine",
            "done": len(health["quarantined"]) == 0,
            "detail": f"{len(health['quarantined'])} quarantined" if health["quarantined"] else "None",
        },
        {
            "id": "trust",
            "label": "Trust model active",
            "done": True,
            "detail": "Built-in / First-party / Trusted Local / Experimental / Untrusted",
        },
    ]
    ready = all(s["done"] for s in steps[:3])
    hint = "Capabilities healthy." if ready else "Review failed or quarantined capabilities in Capabilities Home."
    return {
        "ready": ready,
        "hint": hint,
        "steps": steps,
        "failed_items": health["failed_items"],
        "quarantined": health["quarantined"],
    }


def acknowledge(cap_id: str, *, reenable: bool = False) -> dict[str, Any]:
    entry = cap_policy.acknowledge_quarantine(cap_id, reenable=reenable)
    from jarvis.capabilities_product.history import record_activity

    record_activity("acknowledge", capability_id=cap_id, message="Quarantine acknowledged")
    return {"ok": True, "id": cap_id, "entry": entry}
