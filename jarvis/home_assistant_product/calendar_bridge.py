"""Calendar bridge — meeting/focus/travel mode candidates (preview only)."""

from __future__ import annotations

from typing import Any


def calendar_candidates(*, kind: str = "meeting", title: str = "", notes: str = "") -> dict[str, Any]:
    kind = (kind or "meeting").strip().lower()
    preset_map = {
        "meeting": "focus mode",
        "focus": "focus mode",
        "travel": "leaving",
        "off": "",
    }
    preset = preset_map.get(kind, "focus mode")
    return {
        "ok": True,
        "product": "Smart Home",
        "target": "Calendar",
        "requires_confirmation": True,
        "kind": kind,
        "candidates": [
            {
                "title": title or f"Calendar HA mode: {kind}",
                "notes": notes or f"Would set Smart Home mode / preset `{preset or 'off'}`",
                "kind": kind,
                "preset": preset,
                "source": "smarthome_calendar",
                "selected": True,
                "api": "/api/calendar/ha-mode",
            }
        ],
        "message": "Preview only — confirm via Calendar ha-mode.",
        "pipeline": "smarthome_calendar_bridge",
    }
