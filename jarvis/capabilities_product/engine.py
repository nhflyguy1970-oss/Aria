"""Capabilities engine — status, home payload, bundles."""

from __future__ import annotations

import json
from typing import Any

from jarvis.capabilities_product.health import diagnostics, health_summary, recovery_status
from jarvis.capabilities_product.history import list_activity
from jarvis.capabilities_product.registry import list_capabilities, registry_snapshot
from jarvis.capabilities_product.settings import load_settings
from jarvis.capabilities_product.status_bus import get_capabilities_state
from jarvis.capabilities_product.terminology import BOUNDARIES, CATEGORIES, TERMINOLOGY


def product_status() -> dict[str, Any]:
    snap = registry_snapshot()
    health = health_summary()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "terminology": TERMINOLOGY,
        "boundaries": BOUNDARIES,
        "state": get_capabilities_state().get("state") or "idle",
        "count": snap["count"],
        "enabled": snap["enabled"],
        "disabled": snap["disabled"],
        "failed": snap["failed"],
        "experimental": snap["experimental"],
        "by_layer": snap["by_layer"],
        "by_trust": snap["by_trust"],
        "health": health,
        "isolation_policy": snap["isolation_policy"],
        "categories": list(CATEGORIES),
        "settings": load_settings(),
    }


def home_payload(
    *,
    q: str = "",
    layer: str = "",
    category: str = "",
    trust: str = "",
) -> dict[str, Any]:
    items = list_capabilities(q=q, layer=layer, category=category, trust=trust)
    installed = items
    built_in = [i for i in items if i.get("trust") in ("built_in", "first_party") or i.get("layer") == "host"]
    enabled = [i for i in items if i.get("enabled")]
    disabled = [i for i in items if not i.get("enabled")]
    failed = [i for i in items if i.get("status") == "failed" or i.get("health") == "failed"]
    experimental = [i for i in items if i.get("experimental") or i.get("trust") == "experimental"]
    updates = [i for i in items if i.get("update_available")]
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "summary": {
            "installed": len(installed),
            "built_in": len(built_in),
            "enabled": len(enabled),
            "disabled": len(disabled),
            "failed": len(failed),
            "experimental": len(experimental),
            "updates": len(updates),
        },
        "items": items,
        "built_in": built_in,
        "enabled_items": enabled[:50],
        "disabled_items": disabled[:50],
        "failed_items": failed,
        "experimental_items": experimental,
        "updates": updates,
        "health": health_summary(),
        "recovery": recovery_status(),
        "activity": list_activity(15),
        "categories": list(CATEGORIES),
        "permissions_legend": _permissions_legend(),
        "trust_legend": _trust_legend(),
        "documentation": {
            "implementation": "docs/CAPABILITIES_IMPLEMENTATION.md",
            "operator": "Open Capabilities Home · review trust · enable deliberately",
        },
        "security": {
            "sandbox": False,
            "isolation": "none",
            "message": (
                "Capabilities does not isolate third-party code. "
                "In-process execution shares Aria's privileges. Review permissions before enabling."
            ),
        },
    }


def _permissions_legend() -> list[dict[str, str]]:
    from jarvis.capabilities_product.models import PERMISSION_LABELS

    return [{"id": k, "label": v} for k, v in PERMISSION_LABELS.items()]


def _trust_legend() -> list[dict[str, str]]:
    from jarvis.capabilities_product.models import TRUST_LABELS

    return [{"id": k, "label": v} for k, v in TRUST_LABELS.items()]


def export_bundle(cap_ids: list[str] | None = None) -> dict[str, Any]:
    items = list_capabilities()
    if cap_ids:
        want = set(cap_ids)
        items = [i for i in items if i.get("id") in want]
    from jarvis.capabilities_product import policy as cap_policy

    return {
        "ok": True,
        "format": "aria_capabilities_bundle_v1",
        "items": items,
        "policy_entries": {
            i["id"]: cap_policy.get_entry(i["id"]) for i in items if cap_policy.get_entry(i["id"])
        },
    }


def import_bundle(data: dict[str, Any], *, merge_policy: bool = True) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("format") != "aria_capabilities_bundle_v1":
        return {"ok": False, "message": "unsupported bundle format"}
    from jarvis.capabilities_product import policy as cap_policy

    entries = data.get("policy_entries") or {}
    if merge_policy and isinstance(entries, dict):
        cap_policy.import_policy({"entries": entries}, merge=True)
    return {"ok": True, "imported_policy_entries": len(entries), "items_listed": len(data.get("items") or [])}
