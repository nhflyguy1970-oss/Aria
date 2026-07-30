"""Search settings — opt-in corpora and operator preferences."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "search_product" / "settings.json"

# Always-on cores vs privacy-sensitive opt-ins
DEFAULT_ENABLED = [
    "documents",
    "memory",
    "projects",
    "journal",
    "code",
    "graph",
    "connections",
    "audio",
    "learned",
    "planner",
    "calendar",
    "web",
    "flytying",
    "automation",
    "settings",
    "dashboard",
    "layouts",
    "notifications",
    "provider_health",
    "latency",
]

OPT_IN_DEFAULT_OFF = ["gallery", "home_assistant"]

DEFAULTS: dict[str, Any] = {
    "enabled_corpora": DEFAULT_ENABLED,
    "opt_in_corpora": {k: False for k in OPT_IN_DEFAULT_OFF},
    "code_mode": "auto",  # auto | semantic | grep
    "default_mode": "browse",  # browse | answer
    "record_history": True,
    "parallel_retrieval": True,
    "keyboard_hints": True,
    "max_results": 24,
    "palette_limit": 8,
}


def load_settings() -> dict[str, Any]:
    data = dict(DEFAULTS)
    data["opt_in_corpora"] = dict(DEFAULTS["opt_in_corpora"])
    data["enabled_corpora"] = list(DEFAULTS["enabled_corpora"])
    if SETTINGS_FILE.is_file():
        try:
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if v is None:
                        continue
                    if k == "opt_in_corpora" and isinstance(v, dict):
                        data["opt_in_corpora"].update({str(a): bool(b) for a, b in v.items()})
                    elif k == "enabled_corpora" and isinstance(v, list):
                        data["enabled_corpora"] = [str(x) for x in v]
                    else:
                        data[k] = v
        except (json.JSONDecodeError, OSError):
            pass
    try:
        data["max_results"] = max(4, min(50, int(data.get("max_results") or 24)))
        data["palette_limit"] = max(4, min(20, int(data.get("palette_limit") or 8)))
    except (TypeError, ValueError):
        data["max_results"] = 24
        data["palette_limit"] = 8
    return data


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_settings()
    for k, v in (patch or {}).items():
        if v is None:
            continue
        if k == "opt_in_corpora" and isinstance(v, dict):
            data.setdefault("opt_in_corpora", {}).update({str(a): bool(b) for a, b in v.items()})
        else:
            data[k] = v
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def enabled_corpora_set(settings: dict[str, Any] | None = None) -> set[str]:
    s = settings or load_settings()
    enabled = set(s.get("enabled_corpora") or DEFAULT_ENABLED)
    for corp, on in (s.get("opt_in_corpora") or {}).items():
        if on:
            enabled.add(str(corp))
        else:
            enabled.discard(str(corp))
    return enabled
