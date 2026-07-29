"""Local calendar data: weekly work schedule blocks."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.calendar")
SCHEDULE_FILE = DATA_DIR / "calendar_work_schedule.json"
PREFS_FILE = DATA_DIR / "calendar_prefs.json"
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
ISO_WEEKDAY_TO_KEY = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

_PREFS_DEFAULTS: dict[str, Any] = {
    "ha_calendar_modes": True,
    "ha_calendar_active_mode": None,
}


def load_prefs() -> dict[str, Any]:
    data = dict(_PREFS_DEFAULTS)
    if PREFS_FILE.is_file():
        try:
            raw = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update(raw)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Corrupt calendar prefs: %s", exc)
    return data


def get_pref(key: str, default: Any = None) -> Any:
    prefs = load_prefs()
    return prefs[key] if key in prefs else default


def set_pref(key: str, value: Any) -> dict[str, Any]:
    prefs = load_prefs()
    prefs[key] = value
    PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREFS_FILE.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
    return prefs


def _default_schedule() -> dict[str, Any]:
    block = {"start": "09:00", "end": "17:00", "label": "Work"}
    return {
        "enabled": True,
        "days": {
            "mon": [block.copy()],
            "tue": [block.copy()],
            "wed": [block.copy()],
            "thu": [block.copy()],
            "fri": [block.copy()],
            "sat": [],
            "sun": [],
        },
    }


def load_work_schedule() -> dict[str, Any]:
    if not SCHEDULE_FILE.is_file():
        return _default_schedule()
    try:
        data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("enabled", True)
            data.setdefault("days", _default_schedule()["days"])
            for key in WEEKDAYS:
                data["days"].setdefault(key, [])
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt work schedule: %s", exc)
    return _default_schedule()


def save_work_schedule(data: dict[str, Any]) -> dict[str, Any]:
    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    clean: dict[str, Any] = {"enabled": bool(data.get("enabled", True)), "days": {}}
    for key in WEEKDAYS:
        blocks: list[dict[str, str]] = []
        for block in data.get("days", {}).get(key, []) or []:
            if not isinstance(block, dict):
                continue
            start = str(block.get("start", "")).strip()[:5]
            end = str(block.get("end", "")).strip()[:5]
            label = str(block.get("label", "Work")).strip()[:80] or "Work"
            if not start or not end:
                continue
            blocks.append({"start": start, "end": end, "label": label})
        clean["days"][key] = blocks
    SCHEDULE_FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    return clean


def work_blocks_for_day(day: date | str) -> list[dict[str, str]]:
    if isinstance(day, str):
        day = date.fromisoformat(day)
    sched = load_work_schedule()
    if not sched.get("enabled"):
        return []
    key = ISO_WEEKDAY_TO_KEY.get(day.weekday(), "mon")
    return list(sched.get("days", {}).get(key, []))
