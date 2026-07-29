"""Layouts engine."""

from __future__ import annotations

from typing import Any

from jarvis.layouts_product.apply import catalog_payload
from jarvis.layouts_product.diagnostics import health_summary
from jarvis.layouts_product.schema import SCHEMA_VERSION
from jarvis.layouts_product.store import load_settings
from jarvis.layouts_product.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY


def product_status() -> dict[str, Any]:
    cat = catalog_payload()
    health = health_summary()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["operator_name"],
        "pipeline": TERMINOLOGY["pipeline"],
        "schema_version": SCHEMA_VERSION,
        "builtin_count": len(cat.get("builtins") or []),
        "custom_count": len(cat.get("customs") or []),
        "settings": load_settings(),
        "healthy": health.get("healthy"),
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
        "legacy_alias": TERMINOLOGY["legacy_alias"],
    }


def home_payload() -> dict[str, Any]:
    cat = catalog_payload()
    return {
        "ok": True,
        "product": "Layouts",
        "home": "Layouts",
        "note": (
            "Layouts are shell presentation profiles. "
            "Starter layouts are full frozen snapshots. "
            "Projects own identity — Layouts never force a project switch."
        ),
        **cat,
        "diagnostics": health_summary(),
    }
