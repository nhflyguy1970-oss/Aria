"""Experimental Settings features — researched carefully, gated."""

from __future__ import annotations

from typing import Any

from jarvis.settings_product.catalog import search_catalog
from jarvis.settings_product.router import resolve_deep_link


def experimental_status() -> dict[str, Any]:
    return {
        "ok": True,
        "features": [
            {
                "id": "nl_configure",
                "name": "Natural language configuration",
                "status": "suggest_only",
                "note": "Suggests deep links; never auto-applies security changes.",
            },
            {
                "id": "hardware_defaults",
                "name": "Hardware-aware defaults",
                "status": "suggest_only",
                "note": "Suggests appearance/performance tips from VRAM hints.",
            },
            {
                "id": "policy_profiles",
                "name": "Policy profiles (Work / Lab / Locked)",
                "status": "partial",
                "note": "Preference profiles cover chrome/global; security policy stays manual.",
            },
            {
                "id": "setup_assistant",
                "name": "Setup assistant",
                "status": "coach",
                "note": "Settings coach warnings — no automatic changes.",
            },
        ],
    }


def nl_configure_suggest(prompt: str) -> dict[str, Any]:
    q = (prompt or "").strip()
    if not q:
        return {"ok": False, "error": "prompt required"}
    hits = search_catalog(q, limit=5)
    suggestions = []
    for h in hits:
        resolved = resolve_deep_link(h["id"])
        suggestions.append(
            {
                "preference": h,
                "open": resolved.get("open"),
                "action": "confirm_then_open",
                "auto_apply": False,
            }
        )
    return {
        "ok": True,
        "prompt": q,
        "suggestions": suggestions,
        "note": "Review and confirm. Security-sensitive prefs never auto-apply.",
    }


def hardware_aware_defaults() -> dict[str, Any]:
    tips = []
    vram = None
    try:
        from jarvis.platform_runtime import snapshot

        snap = snapshot() if callable(snapshot) else {}
        vram = (snap or {}).get("free_vram_mb") or (snap or {}).get("vram_mb")
    except Exception:
        pass
    if isinstance(vram, (int, float)) and vram < 4000:
        tips.append(
            {
                "id": "low_vram",
                "title": "Low VRAM detected",
                "suggest": "Prefer smaller vision/chat models in Models Home.",
                "deep_link": {"view": "models"},
                "auto_apply": False,
            }
        )
    tips.append(
        {
            "id": "theme_default",
            "title": "Appearance",
            "suggest": "Keep dark theme for OLED/long sessions; use Settings → Appearance.",
            "deep_link": {"view": "settings", "section": "appearance"},
            "auto_apply": False,
        }
    )
    return {"ok": True, "vram_mb": vram, "tips": tips}
