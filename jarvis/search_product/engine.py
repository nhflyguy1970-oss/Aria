"""Search engine — status and Search Home payloads."""

from __future__ import annotations

from typing import Any

from jarvis.search_product.diagnostics import corpus_matrix, diagnostics, health_summary, recovery_status
from jarvis.search_product.history import list_history, list_saved
from jarvis.search_product.sessions import list_sessions
from jarvis.search_product.settings import load_settings
from jarvis.search_product.status_bus import get_search_state
from jarvis.search_product.terminology import BOUNDARIES, FACETS, MENTAL_MODEL, TERMINOLOGY


def product_status() -> dict[str, Any]:
    health = health_summary()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "architecture_term": TERMINOLOGY["architecture_term"],
        "terminology": TERMINOLOGY,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "state": get_search_state().get("state") or "idle",
        "facets": list(FACETS),
        "health": health,
        "settings": load_settings(),
        "pipeline": TERMINOLOGY["pipeline"],
    }


def home_payload(*, q: str = "", facet: str = "") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    search_meta: dict[str, Any] = {}
    if q.strip():
        from jarvis.search_product.pipeline import run_search

        facets = [facet] if facet and facet != "everything" else None
        search_meta = run_search(q.strip(), facets=facets, session=True)
        results = search_meta.get("results") or []
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "mental_model": MENTAL_MODEL,
        "query": q,
        "facet": facet or "everything",
        "facets": list(FACETS),
        "corpora": corpus_matrix(),
        "results": results,
        "search": search_meta if q.strip() else None,
        "history": list_history(20),
        "saved": list_saved(),
        "sessions": list_sessions(8),
        "health": health_summary(),
        "recovery": recovery_status(),
        "diagnostics_summary": {
            "state": get_search_state().get("state"),
            "last_latency_ms": get_search_state().get("last_latency_ms"),
        },
        "tips": [
            "Sidebar → navigation filter",
            "Ctrl+K → commands + quick search",
            "Search Home → browse everything",
            "Chat → answer + web synthesis",
            "Products → scoped search; they own the data",
        ],
        "documentation": {"implementation": "docs/SEARCH_IMPLEMENTATION.md"},
        "settings": load_settings(),
    }
