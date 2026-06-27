"""Confidence-weighted autonomy — track action outcomes and gate confirmations."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

STORE_FILE = DATA_DIR / "action_confidence.json"
_lock = threading.Lock()
_stats: dict[str, dict[str, int]] = {}
_loaded = False

MIN_SAMPLES = max(3, int(os.getenv("JARVIS_CONFIDENCE_MIN_SAMPLES", "5")))
HIGH_THRESHOLD = float(os.getenv("JARVIS_CONFIDENCE_HIGH", "0.75"))
LOW_THRESHOLD = float(os.getenv("JARVIS_CONFIDENCE_LOW", "0.45"))

TRACKED_ACTIONS = frozenset({
    "ha_control",
    "ha_scene",
    "scene_recall",
    "workflow_run",
    "scene_preset",
})


def _load() -> None:
    global _stats, _loaded
    if _loaded:
        return
    _loaded = True
    if not STORE_FILE.is_file():
        _stats = {}
        return
    try:
        data = json.loads(STORE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _stats = {k: v for k, v in data.items() if isinstance(v, dict)}
    except (json.JSONDecodeError, OSError):
        _stats = {}


def _save() -> None:
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(STORE_FILE)
    with _lock:
        STORE_FILE.write_text(json.dumps(_stats, indent=2), encoding="utf-8")


def record_outcome(action_type: str, *, ok: bool) -> None:
    """Record success/failure for an action type."""
    key = (action_type or "").strip().lower()
    if not key:
        return
    _load()
    with _lock:
        row = _stats.setdefault(key, {"success": 0, "failure": 0})
        if ok:
            row["success"] = int(row.get("success") or 0) + 1
        else:
            row["failure"] = int(row.get("failure") or 0) + 1
    _save()


def confidence_for(action_type: str) -> float:
    """Return 0–1 success rate; 0.5 when insufficient samples."""
    key = (action_type or "").strip().lower()
    if not key:
        return 0.5
    _load()
    with _lock:
        row = _stats.get(key) or {}
        success = int(row.get("success") or 0)
        failure = int(row.get("failure") or 0)
    total = success + failure
    if total < MIN_SAMPLES:
        return 0.5
    return success / total


def confidence_tier(action_type: str) -> str:
    """high | medium | low based on confidence_for."""
    c = confidence_for(action_type)
    if c >= HIGH_THRESHOLD:
        return "high"
    if c <= LOW_THRESHOLD:
        return "low"
    return "medium"


def autonomy_decision(action_type: str) -> dict[str, Any]:
    """Decision for whether to confirm, explain, or proceed silently."""
    tier = confidence_tier(action_type)
    c = confidence_for(action_type)
    needs_confirm = tier == "low"
    explain = tier == "medium"
    return {
        "action_type": action_type,
        "confidence": round(c, 3),
        "tier": tier,
        "needs_confirm": needs_confirm,
        "explain": explain,
        "brief_note": tier == "high",
    }


def snapshot() -> dict[str, Any]:
    _load()
    with _lock:
        rows = {
            k: {
                **v,
                "confidence": round(confidence_for(k), 3),
                "tier": confidence_tier(k),
            }
            for k, v in _stats.items()
        }
    return {"actions": rows, "min_samples": MIN_SAMPLES}
