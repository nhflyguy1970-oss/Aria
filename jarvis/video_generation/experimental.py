"""Experimental Video Generation helpers — careful, non-duplicating pipeline aids."""

from __future__ import annotations

import secrets
from typing import Any


def prompt_coach(prompt: str) -> dict[str, Any]:
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    tips = []
    if len(prompt.split()) < 5:
        tips.append("Add subject, action, and camera motion (pan, zoom, walk).")
    if not any(w in prompt.lower() for w in ("camera", "pan", "zoom", "dolly", "orbit", "walk")):
        tips.append("Mention camera motion for clearer Ken Burns / AnimateDiff motion.")
    if not any(w in prompt.lower() for w in ("second", "sec", "short", "clip")):
        tips.append("Keep clips short (2–6s) on local GPUs.")
    return {
        "ok": True,
        "original": prompt,
        "tips": tips or ["Prompt looks specific enough — pick a preset or preview enhance."],
        "apply_required": True,
    }


def recommend_motion(prompt: str) -> dict[str, Any]:
    p = (prompt or "").lower()
    engine = "auto"
    preset = "cinematic"
    if any(w in p for w in ("pan", "landscape", "vista", "wide")):
        engine, preset = "ken_burns", "landscape_pan"
    elif any(w in p for w in ("portrait", "face", "person", "character")):
        engine, preset = "auto", "portrait_motion"
    elif any(w in p for w in ("draft", "quick", "test")):
        engine, preset = "ken_burns", "fast_draft"
    elif any(w in p for w in ("animate", "walk", "run", "dance", "motion")):
        engine, preset = "animatediff", "animatediff_hq"
    return {
        "ok": True,
        "recommended_engine": engine,
        "recommended_preset": preset,
        "hint": "Apply via Video Generation Presets — does not change settings until you select it.",
    }


def seed_explorer(*, base_seed: int | None = None, count: int = 4) -> dict[str, Any]:
    count = max(1, min(8, int(count or 4)))
    base = int(base_seed) if base_seed is not None else secrets.randbelow(2**32)
    seeds = [base]
    for i in range(1, count):
        seeds.append((base + i * 7919) % (2**32))
    return {"ok": True, "base": base, "seeds": seeds, "hint": "Pick a seed and Generate — same pipeline."}


def shot_planner(prompt: str, *, max_shots: int = 4) -> dict[str, Any]:
    """Suggest shot list — never auto-renders."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    n = max(1, min(4, int(max_shots or 4)))
    shots = []
    for i in range(n):
        shots.append(
            {
                "index": i + 1,
                "prompt": f"{prompt} — shot {i + 1}",
                "suggested_engine": "ken_burns" if i % 2 else "auto",
                "duration": 3,
            }
        )
    return {
        "ok": True,
        "original": prompt,
        "shots": shots,
        "apply_required": True,
        "hint": "Operator must approve each shot — use storyboard or generate separately.",
    }


def camera_explorer() -> dict[str, Any]:
    return {
        "ok": True,
        "moves": [
            {"id": "slow_zoom_in", "label": "Slow zoom in", "hint": "Ken Burns friendly"},
            {"id": "slow_zoom_out", "label": "Slow zoom out", "hint": "Ken Burns friendly"},
            {"id": "pan_left", "label": "Pan left", "hint": "Ken Burns / storyboard"},
            {"id": "orbit", "label": "Orbit subject", "hint": "Prefer AnimateDiff when ready"},
        ],
        "apply_required": True,
    }
