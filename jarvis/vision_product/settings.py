"""Unified Vision settings."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR, load_vision_quality, save_vision_quality

SETTINGS_FILE = DATA_DIR / "vision_product" / "settings.json"

DEFAULTS: dict[str, Any] = {
    "quality_mode": "fast",  # custom | fast | quality
    "ocr_mode": "auto",  # classic | vlm | hybrid | auto
    "confidence_threshold": 0.55,
    "compare_auto": True,
    "output_style": "balanced",  # brief | balanced | detailed
    "auto_enhancement": False,
    "region_default": "",
    "active_profile": "",
    "warn_before_heavy": True,
    "speak_results": False,
}


def load_settings() -> dict[str, Any]:
    data = dict(DEFAULTS)
    try:
        data["quality_mode"] = load_vision_quality() or "fast"
    except Exception:
        pass
    if SETTINGS_FILE.is_file():
        try:
            raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if v is not None})
        except (json.JSONDecodeError, OSError):
            pass
    if data.get("quality_mode") not in ("custom", "fast", "quality"):
        data["quality_mode"] = "fast"
    if data.get("ocr_mode") not in ("classic", "vlm", "hybrid", "auto"):
        data["ocr_mode"] = "auto"
    return data


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = dict(patch or {})
    data = load_settings()
    data.update({k: v for k, v in patch.items() if v is not None})
    if "quality_mode" in patch:
        try:
            save_vision_quality(str(data["quality_mode"]))
        except Exception:
            pass
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
