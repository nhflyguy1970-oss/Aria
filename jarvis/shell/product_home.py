"""Product Home compliance checklist — every Home should satisfy these."""

from __future__ import annotations

from typing import Any

PRODUCT_HOME_CHECKLIST: list[str] = [
    "header",
    "breadcrumbs",
    "health",
    "actions",
    "search_or_filter",
    "deep_links",
    "status",
    "loading",
    "errors",
    "empty_state",
    "help",
    "esc_behavior",
    "accessibility",
    "consistent_spacing",
    "consistent_toolbar",
]

# Views that are first-class Product Homes / shell surfaces
PRODUCT_VIEWS: list[str] = [
    "dashboard",
    "search",
    "settings",
    "models",
    "coding",
    "automation",
    "gallery",
    "browser",
    "voice",
    "vision",
    "flytying",
    "planner",
    "calendar",
    "journal",
    "projects",
    "memory",
    "documents",
    "workstation",
    "chat",
    "maker",
    "audio",
    "video",
    "meme",
    "connections",
    "capabilities",
    "integrations",
    # Shell surfaces (modal / chrome products)
    "notifications",
    "layouts",
    "jobs",
]


def checklist_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "checklist": list(PRODUCT_HOME_CHECKLIST),
        "views": list(PRODUCT_VIEWS),
        "note": "Shell defines the checklist; each product implements it in its Home UI.",
    }
