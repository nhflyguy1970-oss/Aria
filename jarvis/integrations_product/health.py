"""Health, diagnostics, recovery for Integrations."""

from __future__ import annotations

from typing import Any

from jarvis.integrations_product.providers import provider_matrix, test_connection
from jarvis.integrations_product.secrets_bus import hygiene_report, storage_info
from jarvis.integrations_product.status_bus import get_integrations_state
from jarvis.integrations_product.usage import list_usage


def health_summary() -> dict[str, Any]:
    items = provider_matrix()
    configured = [i for i in items if i.get("configured")]
    available = [i for i in items if not i.get("configured") and i.get("status") == "available"]
    managed = [i for i in items if i.get("managed_elsewhere")]
    return {
        "ok": True,
        "configured_count": len(configured),
        "available_count": len(available),
        "managed_elsewhere_count": len(managed),
        "total": len(items),
        "storage": storage_info(),
        "hygiene": hygiene_report(),
        "state": get_integrations_state(),
        "recent_failures": [u for u in list_usage(20) if not u.get("ok")][:8],
    }


def diagnostics() -> dict[str, Any]:
    from jarvis.intelligence.connectors import list_connectors

    return {
        "ok": True,
        "health": health_summary(),
        "providers": provider_matrix(),
        "connectors": list_connectors(),
        "usage": list_usage(30),
        "security": {
            "encrypted": False,
            "storage": storage_info(),
            "message": storage_info().get("message"),
        },
    }


def recovery_status() -> dict[str, Any]:
    health = health_summary()
    storage = health.get("storage") or {}
    hygiene = health.get("hygiene") or {}
    steps = [
        {
            "id": "storage",
            "label": "Secret storage reachable",
            "done": True,
            "detail": storage.get("path") or "data/jarvis.env",
        },
        {
            "id": "permissions",
            "label": "Secret file not world-readable",
            "done": not bool(storage.get("world_readable")),
            "detail": storage.get("recommendation") or "",
        },
        {
            "id": "hygiene",
            "label": "No urgent rotation warnings",
            "done": len(hygiene.get("rotation_reminders") or []) == 0,
            "detail": f"{len(hygiene.get('rotation_reminders') or [])} reminder(s)",
        },
        {
            "id": "failures",
            "label": "No recent connection failures",
            "done": len(health.get("recent_failures") or []) == 0,
            "detail": f"{len(health.get('recent_failures') or [])} recent",
        },
    ]
    ready = all(s["done"] for s in steps)
    return {
        "ready": ready,
        "hint": "Integrations healthy." if ready else "Review secret permissions, rotations, or failed tests.",
        "steps": steps,
        "recent_failures": health.get("recent_failures") or [],
    }


def run_all_tests(*, configured_only: bool = True) -> dict[str, Any]:
    items = provider_matrix()
    results = []
    for item in items:
        if item.get("managed_elsewhere"):
            continue
        if configured_only and not item.get("configured") and item.get("kind") not in ("local", "gateway"):
            continue
        if item.get("kind") in ("local", "gateway") or item.get("configured"):
            results.append(test_connection(item["id"]))
    return {"ok": all(r.get("ok") for r in results) if results else True, "results": results}
