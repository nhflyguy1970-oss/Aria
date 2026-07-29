"""Unified Smart Home settings."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "home_assistant_product" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "active_profile": "",
    "control_first": True,  # Smart Home Home: control before config (inventory_first → control_first)
    "warn_before_heavy": True,
    "warn_unreachable": True,
    "warn_before_away": True,
    "confirmation_policy": "ask",  # ask | auto | never
    "speak_status": False,
    "favorite_rooms": [],
    "favorite_devices": [],
    "preferred_scenes": [],
    "default_brightness": 60,
    "default_color_temp_kelvin": 2700,
    "voice_confirm": True,
    "project_id": "",
}


def load_settings() -> dict[str, Any]:
    data = dict(DEFAULTS)
    if SETTINGS_FILE.is_file():
        try:
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if v is not None})
        except (json.JSONDecodeError, OSError):
            pass
    # Legacy key from flytying-style naming
    if "inventory_first" in data and "control_first" not in data:
        data["control_first"] = not bool(data.get("inventory_first"))
    data.pop("inventory_first", None)
    policy = str(data.get("confirmation_policy") or "ask").strip().lower()
    if policy not in ("ask", "auto", "never"):
        policy = "ask"
    data["confirmation_policy"] = policy
    data["control_first"] = bool(data.get("control_first", True))
    try:
        data["default_brightness"] = max(1, min(100, int(data.get("default_brightness") or 60)))
    except (TypeError, ValueError):
        data["default_brightness"] = 60
    try:
        data["default_color_temp_kelvin"] = max(
            2000, min(6500, int(data.get("default_color_temp_kelvin") or 2700))
        )
    except (TypeError, ValueError):
        data["default_color_temp_kelvin"] = 2700
    return data


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = dict(patch or {})
    if "inventory_first" in patch and "control_first" not in patch:
        patch["control_first"] = not bool(patch.pop("inventory_first"))
    else:
        patch.pop("inventory_first", None)
    data = load_settings()
    data.update({k: v for k, v in patch.items() if v is not None})
    data.pop("inventory_first", None)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
