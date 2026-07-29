"""Settings for Capabilities product."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "capabilities_product" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "show_experimental": True,
    "show_platform_layers": True,
    "show_acm_layers": True,
    "auto_load_trusted": True,
    "confirm_enable_untrusted": True,
    "keyboard_hints": True,
    "reduced_motion": False,
    "default_category_filter": "",
    "search_include_disabled": True,
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
    return data


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_settings()
    data.update({k: v for k, v in (patch or {}).items() if v is not None})
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
