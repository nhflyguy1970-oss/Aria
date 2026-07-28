"""Reusable Video Generation Presets — global + per-project + built-ins."""

from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from typing import Any

from jarvis.config import DATA_DIR

PRESETS_FILE = DATA_DIR / "video_generation" / "presets.json"

BUILTINS: dict[str, dict[str, Any]] = {
    "fast_draft": {
        "title": "Fast Draft",
        "engine": "ken_burns",
        "duration": 3,
        "fps": 8,
        "width": 512,
        "height": 512,
        "enhance": True,
        "keyframe_preset": "fast",
    },
    "portrait_motion": {
        "title": "Portrait Motion",
        "engine": "auto",
        "duration": 4,
        "fps": 8,
        "width": 512,
        "height": 768,
        "enhance": True,
        "frames": 24,
    },
    "landscape_pan": {
        "title": "Landscape Pan",
        "engine": "ken_burns",
        "duration": 6,
        "fps": 10,
        "width": 768,
        "height": 512,
        "enhance": True,
        "keyframe_preset": "quality",
    },
    "storyboard_preview": {
        "title": "Storyboard Preview",
        "engine": "ken_burns",
        "sec_per_slide": 2.5,
        "enhance": False,
        "transition": "ken_burns",
    },
    "cinematic": {
        "title": "Cinematic",
        "engine": "auto",
        "duration": 5,
        "fps": 12,
        "width": 768,
        "height": 512,
        "enhance": True,
        "frames": 48,
        "negative": "blurry, low quality, watermark, text",
    },
    "social_clip": {
        "title": "Social Clip",
        "engine": "auto",
        "duration": 4,
        "fps": 10,
        "width": 512,
        "height": 768,
        "enhance": True,
        "frames": 32,
    },
    "animatediff_hq": {
        "title": "AnimateDiff HQ",
        "engine": "animatediff",
        "duration": 4,
        "fps": 8,
        "frames": 64,
        "width": 512,
        "height": 512,
        "enhance": True,
    },
    "ken_burns_fast": {
        "title": "Ken Burns Fast",
        "engine": "ken_burns",
        "duration": 3,
        "fps": 8,
        "keyframe_preset": "fast",
        "enhance": True,
        "preferred_fallback": "ken_burns",
    },
}


def _load() -> dict[str, Any]:
    if not PRESETS_FILE.exists():
        return {"custom": {}, "project": {}}
    try:
        data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("custom", {})
            data.setdefault("project", {})
            return data
    except Exception:
        pass
    return {"custom": {}, "project": {}}


def _save(data: dict[str, Any]) -> None:
    PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRESETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_presets(*, project: str = "") -> dict[str, Any]:
    store = _load()
    items = []
    for key, meta in BUILTINS.items():
        items.append({"id": key, "builtin": True, "scope": "global", **meta})
    for key, meta in (store.get("custom") or {}).items():
        items.append({"id": key, "builtin": False, "scope": "global", **meta})
    if project:
        for key, meta in (store.get("project") or {}).get(project, {}).items():
            items.append({"id": key, "builtin": False, "scope": "project", "project": project, **meta})
    return {"ok": True, "items": items}


def get_preset(preset_id: str, *, project: str = "") -> dict[str, Any] | None:
    if preset_id in BUILTINS:
        return {"id": preset_id, "builtin": True, **deepcopy(BUILTINS[preset_id])}
    store = _load()
    if project and preset_id in (store.get("project") or {}).get(project, {}):
        return {"id": preset_id, **deepcopy(store["project"][project][preset_id])}
    if preset_id in (store.get("custom") or {}):
        return {"id": preset_id, **deepcopy(store["custom"][preset_id])}
    return None


def apply_preset_to_params(params: dict[str, Any], preset_id: str, *, project: str = "") -> dict[str, Any]:
    preset = get_preset(preset_id, project=project)
    if not preset:
        return params
    out = dict(params)
    for key in (
        "engine",
        "duration",
        "fps",
        "width",
        "height",
        "frames",
        "enhance",
        "negative",
        "checkpoint",
        "keyframe_preset",
        "animatediff_checkpoint",
        "workflow",
        "motion_strength",
        "preferred_fallback",
        "sec_per_slide",
        "transition",
    ):
        if preset.get(key) not in (None, "") and out.get(key) in (None, ""):
            out[key] = preset[key]
    if preset.get("preferred_fallback") and not out.get("fallback"):
        out["fallback"] = preset["preferred_fallback"]
    out["style_preset"] = preset_id
    return out


def save_preset(
    title: str,
    fields: dict[str, Any],
    *,
    preset_id: str = "",
    project: str = "",
) -> dict[str, Any]:
    store = _load()
    pid = (preset_id or str(uuid.uuid4())[:8]).strip()
    entry = {
        "title": (title or "Preset")[:120],
        "ts": time.time(),
        **{k: v for k, v in (fields or {}).items() if v is not None},
    }
    if project:
        store.setdefault("project", {}).setdefault(project, {})[pid] = entry
    else:
        store.setdefault("custom", {})[pid] = entry
    _save(store)
    return {"ok": True, "id": pid, "preset": entry}


def delete_preset(preset_id: str, *, project: str = "") -> dict[str, Any]:
    if preset_id in BUILTINS:
        return {"ok": False, "message": "Cannot delete built-in preset"}
    store = _load()
    if project:
        (store.get("project") or {}).get(project, {}).pop(preset_id, None)
    else:
        (store.get("custom") or {}).pop(preset_id, None)
    _save(store)
    return {"ok": True, "deleted": preset_id}


def export_presets() -> dict[str, Any]:
    return {"ok": True, "builtins": BUILTINS, **_load()}
