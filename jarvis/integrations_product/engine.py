"""Integrations engine — status and home payloads."""

from __future__ import annotations

from typing import Any

from jarvis.integrations_product.health import diagnostics, health_summary, recovery_status
from jarvis.integrations_product.providers import provider_matrix
from jarvis.integrations_product.secrets_bus import hygiene_report, secrets_status, storage_info
from jarvis.integrations_product.settings import load_settings
from jarvis.integrations_product.status_bus import get_integrations_state
from jarvis.integrations_product.terminology import BOUNDARIES, CATEGORIES, TERMINOLOGY
from jarvis.integrations_product.usage import list_usage


def product_status() -> dict[str, Any]:
    health = health_summary()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "architecture_term": TERMINOLOGY["architecture_term"],
        "terminology": TERMINOLOGY,
        "boundaries": BOUNDARIES,
        "state": get_integrations_state().get("state") or "idle",
        "configured": health.get("configured_count"),
        "available": health.get("available_count"),
        "total": health.get("total"),
        "health": health,
        "storage": storage_info(),
        "categories": list(CATEGORIES),
        "settings": load_settings(),
    }


def home_payload(*, q: str = "", category: str = "") -> dict[str, Any]:
    items = provider_matrix(q=q, category=category)
    configured = [i for i in items if i.get("configured")]
    available = [i for i in items if i.get("status") == "available"]
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "summary": {
            "configured": len(configured),
            "available": len(available),
            "total": len(items),
            "managed_elsewhere": len([i for i in items if i.get("managed_elsewhere")]),
        },
        "providers": items,
        "configured_providers": configured,
        "available_providers": available,
        "secrets": secrets_status(last4=True),
        "security": storage_info(),
        "hygiene": hygiene_report(),
        "health": health_summary(),
        "recovery": recovery_status(),
        "usage": list_usage(15),
        "categories": list(CATEGORIES),
        "documentation": {
            "implementation": "docs/INTEGRATIONS_IMPLEMENTATION.md",
            "operator": "Add keys → Test Connection → open unlocked product",
        },
        "webhooks": {
            "inbound": next((i for i in items if i["id"] == "automation_webhook"), None),
            "note": "Automation owns webhook execution; Integrations shows visibility and health.",
        },
    }
