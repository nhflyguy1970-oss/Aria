"""Global + appearance preferences — Settings-owned chrome (server mirror)."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

APPEARANCE_FILE = DATA_DIR / "settings_product" / "appearance.json"
GLOBAL_FILE = DATA_DIR / "settings_product" / "global.json"

APPEARANCE_DEFAULTS: dict[str, Any] = {
    "theme": "dark",  # dark | light — single source; clients migrate from aria_theme
    "accent": "gold",
    "dock_hidden": False,
    "status_bar_hidden": False,
    "mini_chat_hidden": False,
    "split_enabled": False,
    "split_ratio": 0.55,
    "sidebar_collapsed": False,
    "sidebar_width": 260,
    "reduced_motion": False,
    "high_contrast": False,
}

GLOBAL_DEFAULTS: dict[str, Any] = {
    "language": "en",
    "keyboard_hints": True,
    "notifications_enabled": True,
    "soft_tips": True,
}


def _load(path, defaults: dict[str, Any]) -> dict[str, Any]:
    data = dict(defaults)
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if v is not None})
        except (json.JSONDecodeError, OSError):
            pass
    return data


def _save(path, defaults: dict[str, Any], patch: dict[str, Any] | None) -> dict[str, Any]:
    data = _load(path, defaults)
    data.update({k: v for k, v in (patch or {}).items() if v is not None})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def load_appearance() -> dict[str, Any]:
    return _load(APPEARANCE_FILE, APPEARANCE_DEFAULTS)


def save_appearance(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    return _save(APPEARANCE_FILE, APPEARANCE_DEFAULTS, patch)


def load_global() -> dict[str, Any]:
    return _load(GLOBAL_FILE, GLOBAL_DEFAULTS)


def save_global(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    return _save(GLOBAL_FILE, GLOBAL_DEFAULTS, patch)


def migrate_theme_hint(client_theme: str | None = None) -> dict[str, Any]:
    """Accept client migration from legacy aria_theme localStorage."""
    appearance = load_appearance()
    if client_theme in ("light", "dark") and appearance.get("theme") != client_theme:
        return save_appearance({"theme": client_theme, "migrated_from_aria_theme": True})
    return appearance
