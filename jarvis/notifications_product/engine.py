"""Notifications engine — product status + home payload."""

from __future__ import annotations

from typing import Any

from jarvis.notifications_product.diagnostics import health_summary
from jarvis.notifications_product.digest import build_digest
from jarvis.notifications_product.preferences import load_preferences
from jarvis.notifications_product.schema import SCHEMA_VERSION
from jarvis.notifications_product.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY


def product_status() -> dict[str, Any]:
    health = health_summary()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["operator_name"],
        "inbox": TERMINOLOGY["inbox"],
        "pipeline": TERMINOLOGY["pipeline"],
        "schema_version": SCHEMA_VERSION,
        "settings": load_preferences(),
        "healthy": health.get("healthy"),
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
        "legacy_alias": TERMINOLOGY["legacy_alias"],
    }


def home_payload() -> dict[str, Any]:
    from jarvis.notifications_product.correlation import correlate
    from jarvis.notifications_product.outbox import outbox_status
    from jarvis.notifications_product.pipeline import recent, unread_summary

    return {
        "ok": True,
        "product": "Notifications",
        "home": "Notifications",
        "inbox": "Activity Center",
        "note": (
            "Notifications owns delivery. Activity Center is the durable inbox. "
            "Toasts are transient. Desktop is OS delivery. Products publish; we deliver."
        ),
        "preferences": load_preferences(),
        "summary": unread_summary(),
        "recent": recent(limit=20),
        "digest": build_digest("needs_attention"),
        "correlation": correlate(),
        "outboxes": outbox_status(),
        "diagnostics": health_summary(),
    }
