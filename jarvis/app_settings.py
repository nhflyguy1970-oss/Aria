"""Persisted GUI preferences (survives server restart)."""

from __future__ import annotations

import json
import logging

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis")
SETTINGS_FILE = DATA_DIR / "app_settings.json"


def load() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError, TypeError) as exc:
        log.warning("Could not read %s: %s", SETTINGS_FILE, exc)
        return {}


def save(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        SETTINGS_FILE.chmod(0o600)
    except OSError:
        pass


def get_uncensored() -> bool:
    return bool(load().get("uncensored"))


def set_uncensored_pref(enabled: bool) -> None:
    data = load()
    data["uncensored"] = bool(enabled)
    save(data)
