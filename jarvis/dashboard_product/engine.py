"""Dashboard engine — product status and Home payload."""

from __future__ import annotations

from typing import Any

from jarvis.dashboard_product.cache import load_last_good, load_layout
from jarvis.dashboard_product.terminology import BOUNDARIES, MENTAL_MODEL, ROLE_LAYOUTS, TERMINOLOGY
from jarvis.dashboard_product.widgets import list_widget_defs


def product_status(*, assistant: Any = None) -> dict[str, Any]:
    defs = list_widget_defs()
    layout = load_layout()
    cache = load_last_good()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["operator_name"],
        "pipeline": TERMINOLOGY["pipeline"],
        "widget_count": len(defs),
        "roles": list(ROLE_LAYOUTS),
        "layout": layout,
        "cache_present": cache is not None,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
    }


def home_payload(
    *,
    assistant: Any = None,
    news_category: str = "",
    stale_ok: bool = False,
) -> dict[str, Any]:
    from jarvis.dashboard_product.aggregate import build_home_aggregate

    try:
        return build_home_aggregate(assistant=assistant, news_category=news_category)
    except Exception as exc:
        if stale_ok:
            cached = load_last_good()
            if cached:
                cached["ok"] = True
                cached["degraded"] = True
                cached["error"] = str(exc)
                return cached
        return {
            "ok": False,
            "product": "Dashboard",
            "home": "Home",
            "error": str(exc),
            "widgets": [],
            "attention": {"items": [], "empty": True, "count": 0},
            "daily_brief": {"available": False, "coach": "Home aggregate failed."},
            "greeting": {"greeting": "Hello", "welcome": "Welcome back"},
        }
