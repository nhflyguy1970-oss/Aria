"""Optional coding preference memory — suggestions only, never silent behavior change."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

PREFS_FILE = DATA_DIR / "coding_preferences.json"

DEFAULTS: dict[str, Any] = {
    "enabled": False,
    "style": "",
    "formatter": "",
    "test_runner": "pytest",
    "verification_preferences": ["syntax", "tests"],
    "notes": "",
}


def load_preferences() -> dict[str, Any]:
    if not PREFS_FILE.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(DEFAULTS)
        out = dict(DEFAULTS)
        out.update({k: v for k, v in data.items() if k in DEFAULTS or k in ("updated_at",)})
        return out
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save_preferences(updates: dict[str, Any], *, merge: bool = True) -> dict[str, Any]:
    current = load_preferences() if merge else dict(DEFAULTS)
    for key, val in (updates or {}).items():
        if key in DEFAULTS:
            current[key] = val
    current["updated_at"] = time.time()
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current


def preference_suggestions() -> dict[str, Any]:
    """Return prefs as suggestions for the UI/agent — never auto-applied."""
    prefs = load_preferences()
    suggestions: list[str] = []
    if not prefs.get("enabled"):
        return {
            "ok": True,
            "enabled": False,
            "suggestions": [],
            "preferences": prefs,
            "note": "Coding preference memory is off. Enable to store style/formatter/test suggestions.",
        }
    if prefs.get("style"):
        suggestions.append(f"Preferred style: {prefs['style']}")
    if prefs.get("formatter"):
        suggestions.append(f"Preferred formatter: {prefs['formatter']}")
    if prefs.get("test_runner"):
        suggestions.append(f"Preferred test runner: {prefs['test_runner']}")
    if prefs.get("verification_preferences"):
        suggestions.append(
            "Suggested verify steps: " + ", ".join(prefs["verification_preferences"])
        )
    if prefs.get("notes"):
        suggestions.append(f"Operator notes: {prefs['notes']}")
    return {
        "ok": True,
        "enabled": True,
        "suggestions": suggestions,
        "preferences": prefs,
        "note": "Suggestions only — never silently change coding behavior.",
    }
