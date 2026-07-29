"""Smart Home keyboard / voice / workflow cheatsheet."""

from __future__ import annotations

from typing import Any


def cheatsheet_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Smart Home",
        "keyboard": [
            {"keys": "/", "action": "Focus entity search"},
            {"keys": "f", "action": "Toggle favorite on focused entity"},
            {"keys": "s", "action": "Activate preferred scene"},
        ],
        "voice_home": [
            "turn on / turn off / toggle <device>",
            "dim / brighten <device>",
            "set scene / activate <scene>",
            "house status / home status",
            "goodnight / good morning / heading out",
        ],
        "workflow": [
            "Control first — favorites and rooms before config",
            "Connect via guided recovery: URL → Token → Test → Save",
            "Search entities (aliases + fuzzy) — never scroll huge lists",
            "Voice Home Mode speaks via Voice product; engine owns control",
            "Vision camera analysis is confirm-gated — never always-on",
            "Planner / Calendar / Automation bridges are preview-only",
        ],
        "profiles": [
            "Home",
            "Away",
            "Office",
            "Workshop",
            "Night",
            "Vacation",
            "Quiet Hours",
        ],
        "deep_links": {
            "home": "/api/smarthome/product/home",
            "recovery": "/api/smarthome/product/recovery",
            "mission": "/api/smarthome/product/mission",
            "ui": "#smarthome",
        },
    }
