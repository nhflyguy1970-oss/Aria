"""Dashboard diagnostics."""

from __future__ import annotations

from typing import Any

from jarvis.dashboard_product.cache import load_last_good, load_layout
from jarvis.dashboard_product.terminology import TERMINOLOGY
from jarvis.dashboard_product.widgets import list_widget_defs


def health_summary(*, assistant=None) -> dict[str, Any]:
    from jarvis.dashboard_product.cache import load_last_good, load_layout
    from jarvis.dashboard_product.widgets import list_widget_defs

    cache = load_last_good() or {}
    diag = cache.get("diagnostics") or {}
    widgets = cache.get("widgets") or []
    showing = sum(1 for w in widgets if isinstance(w, dict) and w.get("render") == "show")
    if not diag and not widgets:
        # Lightweight fallback without rebuilding full aggregate
        return {
            "healthy": True,
            "product": TERMINOLOGY["product"],
            "home": TERMINOLOGY["operator_name"],
            "widget_defs": len(list_widget_defs()),
            "widgets_showing": None,
            "widget_failures": [],
            "latency_ms": None,
            "cache_age_s": None,
            "cache_stale": True,
            "layout_role": (load_layout() or {}).get("role"),
            "version": "1.0.0",
            "note": "No last-good Home cache yet — open Home once to populate.",
        }
    return {
        "healthy": bool(diag.get("healthy", True)),
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["operator_name"],
        "widget_defs": len(list_widget_defs()),
        "widgets_showing": diag.get("widgets_showing", showing),
        "widget_failures": diag.get("widget_failures") or [],
        "latency_ms": diag.get("latency_ms"),
        "cache_age_s": cache.get("cache_age_s"),
        "cache_stale": cache.get("cache_stale"),
        "layout_role": (load_layout() or {}).get("role"),
        "version": diag.get("version") or "1.0.0",
    }


def recovery_status() -> dict[str, Any]:
    cache = load_last_good()
    steps = [
        {"id": "aggregate_api", "label": "Aggregate API", "done": True},
        {"id": "widget_catalog", "label": "Widget catalog", "done": True},
        {"id": "last_good_cache", "label": "Last-good cache", "done": cache is not None},
        {"id": "layout", "label": "Layout prefs", "done": True},
    ]
    return {
        "ready": all(s["done"] for s in steps),
        "hint": "Open Home (Ctrl+Home) and Refresh if widgets look stale.",
        "steps": steps,
    }
