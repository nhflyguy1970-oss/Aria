"""Experimental Home features — research carefully; never auto-apply."""

from __future__ import annotations

from typing import Any


def voice_home_brief_script(home: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a short speakable Home brief — Voice owns TTS."""
    home = home or {}
    greet = (home.get("greeting") or {}).get("greeting") or "Hello"
    attention = home.get("attention") or {}
    items = attention.get("items") or []
    brief = home.get("daily_brief") or {}
    lines = [greet + "."]
    if items:
        top = items[0]
        lines.append(f"Attention: {top.get('title')}.")
    elif attention.get("empty"):
        lines.append("Nothing urgent on your attention strip.")
    preview = brief.get("preview") or brief.get("weather_line") or ""
    if preview:
        lines.append(str(preview)[:180])
    lines.append("Say open planner, open calendar, or open mission control to continue.")
    return {
        "ok": True,
        "experimental": True,
        "script": " ".join(lines),
        "note": "Dashboard provides the script; Voice owns speech. Not auto-spoken.",
    }


def kiosk_hints() -> dict[str, Any]:
    return {
        "experimental": True,
        "mode": "kiosk",
        "recommendations": [
            "Use density=compact layout role=operations",
            "Hide suggestions and search shortcuts",
            "Show attention + daily_brief + scenes + provider_health",
            "Prefer Ctrl+Home to return to Home",
        ],
        "note": "Kiosk mode is a layout policy hint — not a second Dashboard app.",
    }


def memory_ranked_resume_hints(*, assistant=None) -> dict[str, Any]:
    return {
        "experimental": True,
        "items": [],
        "note": "Memory-ranked resume stays client-assisted; Memory owns recall. No invented continue targets.",
        "coach": "Use recent views + Memory Home for continue suggestions.",
    }


def policy_layouts() -> dict[str, Any]:
    return {
        "experimental": True,
        "roles": {
            "default": ["attention", "daily_brief", "resume", "quick_launch", "today_glance", "scenes"],
            "maker": ["attention", "daily_brief", "projects", "scenes", "quick_launch"],
            "developer": ["attention", "projects", "today_glance", "provider_health", "search_shortcuts"],
            "media": ["attention", "daily_brief", "news", "scenes", "suggestions"],
            "operations": ["attention", "provider_health", "diagnostics", "scenes", "today_glance"],
            "research": ["daily_brief", "memory_highlights", "search_shortcuts", "journal_reminder", "news"],
        },
        "note": "Policy layouts set default order/visibility — never AI auto-reflow.",
    }
