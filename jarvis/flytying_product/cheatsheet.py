"""Fly Tying keyboard / voice / workflow cheatsheet."""

from __future__ import annotations

from typing import Any


def cheatsheet_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Fly Tying",
        "keyboard": [
            {"keys": "/", "action": "Focus pattern search"},
            {"keys": "n", "action": "Voice bench — next step"},
            {"keys": "p", "action": "Voice bench — previous step"},
        ],
        "voice_bench": [
            "next / next step",
            "previous / prev",
            "repeat / again",
            "read / read recipe",
            "pause",
            "resume",
        ],
        "workflow": [
            "Inventory first — scan materials, then Suggest a fly",
            "Start a tying session from a selected pattern",
            "Use Voice bench mode for hands-free step reading",
            "Vision identify material → confirm into inventory",
            "Link finished-fly photos in Gallery with recipe id",
        ],
        "profiles": [
            "Beginner",
            "Competition",
            "Bass",
            "Trout",
            "Saltwater",
            "Travel Kit",
            "Minimal Bench",
        ],
        "deep_links": {
            "home": "/api/flytying/product/home",
            "recovery": "/api/flytying/product/recovery",
            "mission": "/api/flytying/product/mission",
            "ui": "#flytying",
        },
    }
