"""Dashboard deep-link router."""

from __future__ import annotations

from typing import Any

from jarvis.dashboard_product.widgets import search_widgets, widget_def


def resolve_deep_link(target: str = "", *, query: str = "") -> dict[str, Any]:
    t = (target or query or "").strip().lower()
    if not t or t in ("home", "dashboard"):
        return {"ok": True, "view": "dashboard", "widget": None, "label": "Home"}
    if t in ("brief", "daily_brief", "briefing", "morning"):
        return {"ok": True, "view": "dashboard", "widget": "daily_brief", "label": "Daily Brief"}
    if t in ("attention", "alerts", "up next"):
        return {"ok": True, "view": "dashboard", "widget": "attention", "label": "Attention"}
    w = widget_def(t)
    if w:
        return {
            "ok": True,
            "view": "dashboard",
            "widget": w["id"],
            "label": w["title"],
            "deep_link": w.get("deep_link"),
        }
    hits = search_widgets(t, limit=1)
    if hits:
        h = hits[0]
        return {
            "ok": True,
            "view": "dashboard",
            "widget": h["id"],
            "label": h["title"],
            "deep_link": h.get("deep_link"),
        }
    return {"ok": False, "view": "dashboard", "message": f"No Home target for {target or query}"}
