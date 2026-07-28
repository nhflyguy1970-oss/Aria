"""Normalized video generation parameters — one schema for Studio/Chat/MCP/Automation."""

from __future__ import annotations

from typing import Any

VALID_ENGINES = ("auto", "animatediff", "ken_burns")
MAX_STORYBOARD_SLIDES = 12


def coerce_seed(raw: Any, *, randomize: bool = False) -> int | None:
    if randomize or raw in (None, "", "random", -1, "-1"):
        return None
    try:
        return int(raw) % (2**32)
    except (TypeError, ValueError):
        return None


def _float(raw: Any, default: float | None = None) -> float | None:
    if raw in (None, ""):
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _int(raw: Any, default: int | None = None) -> int | None:
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def normalize_params(raw: dict[str, Any] | None, *, message: str = "") -> dict[str, Any]:
    """Flatten operator params into a single dict honored end-to-end."""
    p = dict(raw or {})
    prompt = str(p.get("prompt") or message or "").strip()
    enhance = p.get("enhance")
    if enhance is None:
        enhance = p.get("enhance_prompt")
    if isinstance(enhance, str):
        enhance = enhance.lower() in ("1", "true", "yes", "on")

    engine = str(p.get("engine") or "").strip().lower() or None
    if engine and engine not in VALID_ENGINES:
        engine = "auto"

    seed = coerce_seed(p.get("seed"), randomize=bool(p.get("random_seed")))
    if p.get("reuse_seed") and p.get("last_seed") is not None:
        seed = coerce_seed(p.get("last_seed"))

    duration = _float(p.get("duration") if p.get("duration") is not None else p.get("duration_sec"))
    if duration is not None:
        duration = max(2.0, min(12.0, duration))
    fps = _int(p.get("fps"))
    if fps is not None:
        fps = max(4, min(16, fps))
    width = _int(p.get("width"))
    height = _int(p.get("height"))
    if width is not None:
        width = max(256, min(1024, width))
    if height is not None:
        height = max(256, min(1024, height))
    frames = _int(p.get("frames") if p.get("frames") is not None else p.get("animatediff_frames"))
    if frames is not None:
        frames = max(8, min(128, frames))
    motion = _float(p.get("motion_strength") if p.get("motion_strength") is not None else p.get("denoise"))
    sec = _float(p.get("sec_per_slide"), None)
    if sec is not None:
        sec = max(1.0, min(8.0, sec))

    paths = p.get("paths") or p.get("storyboard_paths") or []
    if isinstance(paths, str):
        paths = [x.strip() for x in paths.split(",") if x.strip()]
    elif not isinstance(paths, list):
        paths = []

    return {
        "prompt": prompt,
        "negative": str(p.get("negative") or p.get("negative_prompt") or "").strip(),
        "enhance": enhance,
        "engine": engine,
        "seed": seed,
        "duration": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "frames": frames,
        "checkpoint": str(p.get("checkpoint") or p.get("keyframe_checkpoint") or "").strip() or None,
        "keyframe_preset": str(p.get("keyframe_preset") or "").strip() or None,
        "animatediff_checkpoint": str(p.get("animatediff_checkpoint") or "").strip() or None,
        "workflow": str(p.get("workflow") or p.get("workflow_file") or "").strip() or None,
        "motion_strength": motion,
        "fallback": str(p.get("fallback") or p.get("preferred_fallback") or "").strip() or None,
        "style_preset": str(p.get("style_preset") or p.get("preset") or "").strip() or None,
        "safety_mode": str(p.get("safety_mode") or "").strip() or None,
        "reference_path": str(p.get("reference_path") or "").strip() or None,
        "paths": [str(x) for x in paths][:MAX_STORYBOARD_SLIDES],
        "sec_per_slide": sec,
        "transition": str(p.get("transition") or "ken_burns").strip().lower() or "ken_burns",
    }
