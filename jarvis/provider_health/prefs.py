"""Provider Health preferences — local JSON store (Settings indexes; PH owns)."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

PREFS_FILE = DATA_DIR / "provider_health" / "preferences.json"

DEFAULTS: dict[str, Any] = {
    "idle_timeout_ms": 90000,
    "first_progress_ms": 45000,
    "recovery_attempts": 3,
    "retry_delay_ms": 1200,
    "auto_restart": True,
    "auto_model_switch": False,
    "auto_provider_switch": False,
    "diagnostics_verbosity": "normal",  # quiet | normal | debug
    "debug_logging": False,
    "notify_recoveries": True,
    "heartbeat_sec": 5.0,
}


def load_preferences() -> dict[str, Any]:
    data = dict(DEFAULTS)
    if PREFS_FILE.is_file():
        try:
            raw = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if k in DEFAULTS or k.startswith("extra_")})
        except (json.JSONDecodeError, OSError):
            pass
    return data


def save_preferences(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_preferences()
    for k, v in (patch or {}).items():
        if v is None:
            continue
        data[k] = v
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
