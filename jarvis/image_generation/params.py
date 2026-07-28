"""Normalized generation parameters — one schema for Gallery/Chat/MCP/Automation."""

from __future__ import annotations

import secrets
from typing import Any

ASPECT_PRESETS: dict[str, tuple[int, int]] = {
    "square": (1024, 1024),
    "portrait": (832, 1216),
    "landscape": (1216, 832),
    "sd15_square": (512, 512),
    "sd15_portrait": (512, 768),
    "sd15_landscape": (768, 512),
}

MAX_VARIATIONS = 4


def coerce_seed(raw: Any, *, randomize: bool = False) -> int | None:
    if randomize or raw in (None, "", "random", -1, "-1"):
        return None  # engine picks random
    try:
        return int(raw) % (2**32)
    except (TypeError, ValueError):
        return None


def normalize_params(raw: dict[str, Any] | None, *, message: str = "") -> dict[str, Any]:
    """Flatten operator params into a single dict honored end-to-end."""
    p = dict(raw or {})
    prompt = str(p.get("prompt") or message or "").strip()
    enhance = p.get("enhance")
    if enhance is None:
        enhance = p.get("enhance_prompt")
    if isinstance(enhance, str):
        enhance = enhance.lower() in ("1", "true", "yes", "on")

    aspect = str(p.get("aspect_ratio") or p.get("aspect") or "").strip().lower()
    width = p.get("width")
    height = p.get("height")
    if aspect in ASPECT_PRESETS and not (width and height):
        width, height = ASPECT_PRESETS[aspect]

    seed = coerce_seed(p.get("seed"), randomize=bool(p.get("random_seed")))
    if p.get("reuse_seed") and p.get("last_seed") is not None:
        seed = coerce_seed(p.get("last_seed"))

    try:
        steps = int(p["steps"]) if p.get("steps") not in (None, "") else None
    except (TypeError, ValueError):
        steps = None
    try:
        cfg = float(p["cfg"]) if p.get("cfg") not in (None, "") else None
    except (TypeError, ValueError):
        cfg = None

    n = 1
    try:
        n = max(1, min(MAX_VARIATIONS, int(p.get("variations") or p.get("n") or 1)))
    except (TypeError, ValueError):
        n = 1

    return {
        "prompt": prompt,
        "negative": str(p.get("negative") or p.get("negative_prompt") or "").strip(),
        "enhance": enhance,  # None = use env default
        "seed": seed,
        "steps": steps,
        "cfg": cfg,
        "sampler": str(p.get("sampler") or "").strip() or None,
        "scheduler": str(p.get("scheduler") or "").strip() or None,
        "width": int(width) if width else None,
        "height": int(height) if height else None,
        "aspect_ratio": aspect or None,
        "checkpoint": str(p.get("checkpoint") or "").strip() or None,
        "workflow": str(p.get("workflow") or p.get("workflow_file") or "").strip() or None,
        "device": str(p.get("device") or p.get("preferred_device") or "").strip() or None,
        "style_preset": str(p.get("style_preset") or p.get("preset") or "").strip() or None,
        "safety_mode": str(p.get("safety_mode") or "").strip() or None,
        "variations": n,
        "variation_strength": str(p.get("variation_strength") or "minor").strip().lower(),
        "reference_path": str(p.get("reference_path") or p.get("path") or "").strip() or None,
    }
