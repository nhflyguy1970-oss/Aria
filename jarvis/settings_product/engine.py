"""Settings engine — status and Settings Home payloads."""

from __future__ import annotations

from typing import Any

from jarvis.settings_product.appearance import load_appearance, load_global
from jarvis.settings_product.catalog import build_catalog, catalog_by_category, categories, search_catalog
from jarvis.settings_product.coach import coach_warnings
from jarvis.settings_product.diagnostics import diagnostics, health_summary, recovery_status
from jarvis.settings_product.history import list_changes
from jarvis.settings_product.profiles import list_profiles
from jarvis.settings_product.terminology import BOUNDARIES, CATEGORIES, MENTAL_MODEL, TERMINOLOGY


def product_status() -> dict[str, Any]:
    health = health_summary()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "architecture_term": TERMINOLOGY["architecture_term"],
        "terminology": TERMINOLOGY,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "categories": list(CATEGORIES),
        "catalog_count": health.get("catalog_count"),
        "health": health,
        "pipeline": TERMINOLOGY["pipeline"],
    }


def home_payload(*, q: str = "", category: str = "") -> dict[str, Any]:
    if q.strip():
        items = search_catalog(q.strip(), limit=40)
    else:
        items = catalog_by_category(category) if category else build_catalog()
    by_cat: dict[str, list] = {c: [] for c in CATEGORIES}
    for e in items:
        by_cat.setdefault(e.get("category") or "products", []).append(e)
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "mental_model": MENTAL_MODEL,
        "query": q,
        "category": category or "all",
        "categories": categories(),
        "preferences": items,
        "by_category": by_cat,
        "appearance": load_appearance(),
        "global": load_global(),
        "profiles": list_profiles(),
        "recent_changes": list_changes(15),
        "coach": coach_warnings(),
        "health": health_summary(),
        "recovery": recovery_status(),
        "voice_chat_modal": {
            "note": "Speak replies + Server Whisper live in Voice & Chat — not Settings Home.",
            "open": {"action": "voice_chat_modal"},
        },
        "documentation": {"implementation": "docs/SETTINGS_IMPLEMENTATION.md"},
        "tips": [
            "Ctrl+, opens Settings Home",
            "Search preferences or jump by category",
            "Product rows deep-link — products own stores",
            "Secrets → Integrations; PIN → Security",
            "Voice & Chat modal is Speak + Whisper only",
        ],
    }
