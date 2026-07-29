"""Unified Capabilities registry facade."""

from __future__ import annotations

from typing import Any

from jarvis.capabilities_product.adapters import discover_all_layers
from jarvis.capabilities_product.settings import load_settings


def list_capabilities(
    *,
    q: str = "",
    layer: str = "",
    category: str = "",
    trust: str = "",
    enabled: bool | None = None,
    status: str = "",
    include_unavailable: bool = True,
) -> list[dict[str, Any]]:
    settings = load_settings()
    records = discover_all_layers(
        include_platform=bool(settings.get("show_platform_layers", True)),
        include_acm=bool(settings.get("show_acm_layers", True)),
    )
    out: list[dict[str, Any]] = []
    ql = (q or "").strip().lower()
    for rec in records:
        if not include_unavailable and rec.id.endswith("__unavailable__"):
            continue
        if not settings.get("show_experimental", True) and rec.experimental:
            continue
        if layer and rec.layer != layer:
            continue
        if category and rec.category.lower() != category.lower():
            continue
        if trust and rec.trust != trust:
            continue
        if enabled is not None and bool(rec.enabled) != bool(enabled):
            continue
        if status and rec.status != status:
            continue
        d = rec.to_dict()
        if ql:
            blob = " ".join(
                [
                    rec.id,
                    rec.name,
                    rec.description,
                    rec.category,
                    rec.layer,
                    " ".join(rec.tags),
                    " ".join(rec.permissions),
                ]
            ).lower()
            if ql not in blob:
                continue
        out.append(d)
    out.sort(key=lambda x: (x.get("layer") or "", x.get("name") or ""))
    return out


def get_capability(cap_id: str) -> dict[str, Any] | None:
    for item in list_capabilities(include_unavailable=True):
        if item.get("id") == cap_id:
            return item
    return None


def registry_snapshot() -> dict[str, Any]:
    items = list_capabilities(include_unavailable=True)
    by_status: dict[str, int] = {}
    by_trust: dict[str, int] = {}
    by_layer: dict[str, int] = {}
    failed = 0
    disabled = 0
    enabled = 0
    experimental = 0
    for i in items:
        st = str(i.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        tr = str(i.get("trust") or "unknown")
        by_trust[tr] = by_trust.get(tr, 0) + 1
        ly = str(i.get("layer") or "unknown")
        by_layer[ly] = by_layer.get(ly, 0) + 1
        if st == "failed" or i.get("health") == "failed":
            failed += 1
        if not i.get("enabled"):
            disabled += 1
        else:
            enabled += 1
        if i.get("experimental"):
            experimental += 1
    return {
        "ok": True,
        "product": "Capabilities",
        "count": len(items),
        "enabled": enabled,
        "disabled": disabled,
        "failed": failed,
        "experimental": experimental,
        "by_status": by_status,
        "by_trust": by_trust,
        "by_layer": by_layer,
        "items": items,
        "isolation_policy": (
            "Aria Capabilities do not provide OS-level sandboxing. "
            "Trust levels and permission previews communicate risk honestly."
        ),
    }


def host_extensions_payload() -> dict[str, Any]:
    """Backward-compatible /api/registry/extensions shape."""
    from jarvis.capabilities_product import policy as cap_policy
    from jarvis.extensibility.loader import list_extensions

    exts = list_extensions()
    enriched = []
    for e in exts:
        name = e.get("name")
        cap_id = f"host:{name}"
        enriched.append(
            {
                **e,
                "id": cap_id,
                "enabled": cap_policy.is_enabled(cap_id, trust="first_party", default=True),
                "quarantined": cap_policy.is_quarantined(cap_id),
                "layer": "host",
            }
        )
    return {"ok": True, "extensions": enriched, "count": len(enriched)}
