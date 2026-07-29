"""Integrations settings."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "integrations_product" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "show_local_providers": True,
    "show_managed_elsewhere": True,
    "show_experimental": True,
    "rotation_reminder_days": 90,
    "confirm_clear": True,
    "keyboard_hints": True,
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
    try:
        data["rotation_reminder_days"] = max(7, int(data.get("rotation_reminder_days") or 90))
    except (TypeError, ValueError):
        data["rotation_reminder_days"] = 90
    return data


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_settings()
    data.update({k: v for k, v in (patch or {}).items() if v is not None})
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
