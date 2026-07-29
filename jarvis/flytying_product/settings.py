"""Unified Fly Tying settings."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "flytying_product" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "region": "Northeast US",
    "min_quality": 0.0,
    "chat_model": "",
    "chat_model_prefs": {},
    "citation_style": "inline",  # inline | footnote | none
    "active_profile": "",
    "warn_before_heavy": True,
    "warn_low_stock": True,
    "warn_missing_blackfly": True,
    "preferred_fly_types": [],
    "favorite_waters": "",
    "preferred_substitutions": True,
    "favorite_hook_types": [],
    "speak_steps": False,
    "inventory_first": True,
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
    if data.get("citation_style") not in ("inline", "footnote", "none"):
        data["citation_style"] = "inline"
    try:
        data["min_quality"] = float(data.get("min_quality") or 0)
    except (TypeError, ValueError):
        data["min_quality"] = 0.0
    return data


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = dict(patch or {})
    data = load_settings()
    data.update({k: v for k, v in patch.items() if v is not None})
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
