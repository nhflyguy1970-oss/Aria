"""Notification preferences — Settings indexes; Notifications enforces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

ROOT = Path(DATA_DIR) / "notifications_product"
PREFS_FILE = ROOT / "preferences.json"

DEFAULT_PREFS: dict[str, Any] = {
    "enabled": True,
    "toast_enabled": True,
    "desktop_enabled": True,
    "activity_enabled": True,
    "soft_tips": True,
    "critical_only": False,
    "digest_enabled": True,
    "voice_summaries": False,
    "quiet_hours_enabled": False,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00",
    "dnd": False,
    "retention_days": 30,
    "history_enabled": True,
    "muted_sources": [],
    "muted_categories": [],
    "desktop_min_severity": "warning",
    "toast_min_severity": "warning",
}


def _ensure() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)


def load_preferences() -> dict[str, Any]:
    data = dict(DEFAULT_PREFS)
    if PREFS_FILE.is_file():
        try:
            raw = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if k in DEFAULT_PREFS or k.startswith("experimental_")})
        except Exception:
            pass
    if not isinstance(data.get("muted_sources"), list):
        data["muted_sources"] = []
    if not isinstance(data.get("muted_categories"), list):
        data["muted_categories"] = []
    return data


def save_preferences(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_preferences()
    if isinstance(patch, dict):
        for k, v in patch.items():
            if k in DEFAULT_PREFS or str(k).startswith("experimental_"):
                data[k] = v
    _ensure()
    PREFS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return data


def _parse_hhmm(value: str) -> int | None:
    try:
        parts = str(value or "").strip().split(":")
        h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h * 60 + m
    except Exception:
        return None
    return None


def in_quiet_hours(prefs: dict[str, Any] | None = None, *, now_minutes: int | None = None) -> bool:
    prefs = prefs or load_preferences()
    if prefs.get("dnd"):
        return True
    if not prefs.get("quiet_hours_enabled"):
        return False
    start = _parse_hhmm(str(prefs.get("quiet_hours_start") or "22:00"))
    end = _parse_hhmm(str(prefs.get("quiet_hours_end") or "07:00"))
    if start is None or end is None:
        return False
    if now_minutes is None:
        import datetime as dt

        now = dt.datetime.now()
        now_minutes = now.hour * 60 + now.minute
    if start == end:
        return False
    if start < end:
        return start <= now_minutes < end
    # wraps midnight
    return now_minutes >= start or now_minutes < end


SEVERITY_RANK = {"critical": 4, "error": 3, "warning": 2, "info": 1, "success": 0}


def severity_allows(sev: str, minimum: str) -> bool:
    return SEVERITY_RANK.get(str(sev).lower(), 0) >= SEVERITY_RANK.get(str(minimum).lower(), 0)


def route_decision(evt: dict[str, Any], prefs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decide activity / toast / desktop delivery from preferences."""
    prefs = prefs or load_preferences()
    sev = str(evt.get("severity") or "info").lower()
    critical = sev in ("critical", "error")
    source = str(evt.get("source") or "")
    category = str(evt.get("category") or "")

    if not prefs.get("enabled"):
        return {
            "deliver": False,
            "activity": False,
            "toast": False,
            "desktop": False,
            "voice": False,
            "reason": "notifications_disabled",
        }

    if source in (prefs.get("muted_sources") or []) or category in (prefs.get("muted_categories") or []):
        return {
            "deliver": False,
            "activity": False,
            "toast": False,
            "desktop": False,
            "voice": False,
            "reason": "muted_source",
        }

    quiet = in_quiet_hours(prefs)
    critical_only = bool(prefs.get("critical_only"))
    if critical_only and not critical:
        return {
            "deliver": False,
            "activity": False,
            "toast": False,
            "desktop": False,
            "voice": False,
            "reason": "critical_only",
        }

    activity = bool(prefs.get("activity_enabled", True))
    # Quiet hours: suppress toast/desktop/voice unless critical override
    toast = bool(prefs.get("toast_enabled", True)) and severity_allows(
        sev, str(prefs.get("toast_min_severity") or "warning")
    )
    desktop = bool(prefs.get("desktop_enabled", True)) and severity_allows(
        sev, str(prefs.get("desktop_min_severity") or "warning")
    )
    voice = bool(prefs.get("voice_summaries")) and critical

    if prefs.get("dnd"):
        toast = False
        desktop = False
        voice = False
    elif quiet and not critical:
        toast = False
        desktop = False
        voice = False
    elif quiet and critical:
        # critical overrides quiet for desktop/activity; toast still optional
        desktop = bool(prefs.get("desktop_enabled", True))
        activity = True

    # Event-level flags can further restrict
    if evt.get("toast") is False:
        toast = False
    if evt.get("desktop") is False:
        desktop = False
    if evt.get("voice") is False:
        voice = False

    return {
        "deliver": activity or toast or desktop,
        "activity": activity,
        "toast": toast,
        "desktop": desktop,
        "voice": voice,
        "quiet": quiet,
        "reason": "ok",
    }
