"""Reusable Generation Presets — global + per-project + built-ins."""

from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from typing import Any

from jarvis.config import DATA_DIR

PRESETS_FILE = DATA_DIR / "image_generation" / "presets.json"

BUILTINS: dict[str, dict[str, Any]] = {
    "fast_draft": {
        "title": "Fast Draft",
        "checkpoint": "fast",
        "aspect_ratio": "square",
        "steps": 4,
        "cfg": 1.0,
        "enhance": True,
        "negative": "",
    },
    "high_quality": {
        "title": "High Quality",
        "checkpoint": "quality",
        "aspect_ratio": "square",
        "steps": 30,
        "cfg": 7.5,
        "enhance": True,
        "sampler": "dpmpp_2m",
        "scheduler": "karras",
    },
    "photoreal_portrait": {
        "title": "Photoreal Portrait",
        "checkpoint": "quality",
        "aspect_ratio": "portrait",
        "enhance": True,
        "negative": "cartoon, illustration, painting, deformed hands",
        "style_template": "photorealistic portrait, natural light, sharp focus",
    },
    "landscape": {
        "title": "Landscape",
        "checkpoint": "quality",
        "aspect_ratio": "landscape",
        "enhance": True,
        "style_template": "cinematic landscape, wide vista",
    },
    "anime": {
        "title": "Anime",
        "checkpoint": "quality",
        "aspect_ratio": "portrait",
        "enhance": True,
        "style_template": "anime style, clean lines, vibrant colors",
        "negative": "photorealistic, photo",
    },
    "pixel_art": {
        "title": "Pixel Art",
        "aspect_ratio": "square",
        "enhance": True,
        "style_template": "pixel art, 16-bit, limited palette",
    },
    "product_photo": {
        "title": "Product Photography",
        "aspect_ratio": "square",
        "enhance": True,
        "style_template": "product photography, studio lighting, clean background",
    },
    "concept_art": {
        "title": "Concept Art",
        "aspect_ratio": "landscape",
        "enhance": True,
        "style_template": "concept art, detailed environment, dramatic lighting",
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
        "checkpoint",
        "workflow",
        "aspect_ratio",
        "steps",
        "cfg",
        "sampler",
        "scheduler",
        "enhance",
        "negative",
        "device",
        "safety_mode",
        "width",
        "height",
    ):
        if preset.get(key) not in (None, "") and out.get(key) in (None, ""):
            out[key] = preset[key]
    style = (preset.get("style_template") or "").strip()
    if style and out.get("prompt"):
        if style.lower() not in out["prompt"].lower():
            out["prompt"] = f"{out['prompt']}, {style}"
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
