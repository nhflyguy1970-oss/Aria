"""Persisted browser gesture mode + calibration thresholds."""

from __future__ import annotations

import json
from pathlib import Path

from jarvis.config import DATA_DIR

GESTURES_FILE = DATA_DIR / "security" / "gestures.json"


def load_gesture_settings(path: Path | None = None) -> dict:
    p = path or GESTURES_FILE
    if not p.is_file():
        return {"mode": "off", "calibration": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"mode": "off", "calibration": {}}
    return {
        "mode": data.get("mode") or "off",
        "calibration": data.get("calibration") or {},
    }


def merge_gesture_settings(body: dict, existing: dict | None = None) -> dict:
    base = existing or {"mode": "off", "calibration": {}}
    mode = body.get("mode", base.get("mode") or "off")
    calibration = dict(base.get("calibration") or {})
    incoming = body.get("calibration")
    if isinstance(incoming, dict) and incoming:
        calibration.update(incoming)
    return {"mode": mode, "calibration": calibration}


def save_gesture_settings(body: dict, path: Path | None = None) -> dict:
    p = path or GESTURES_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    merged = merge_gesture_settings(body, load_gesture_settings(p))
    p.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged
