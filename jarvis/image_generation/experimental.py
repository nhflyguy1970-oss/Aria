"""Experimental Image Generation helpers — careful, non-duplicating pipeline aids."""

from __future__ import annotations

import secrets
from typing import Any


def prompt_coach(prompt: str) -> dict[str, Any]:
    """Suggest improvements without silently rewriting — operator must apply."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    tips = []
    if len(prompt.split()) < 4:
        tips.append("Add subject details (who/what), setting, and lighting.")
    if not any(w in prompt.lower() for w in ("light", "lighting", "sun", "lamp", "studio")):
        tips.append("Mention lighting for more consistent results.")
    if not any(w in prompt.lower() for w in ("photo", "illustration", "anime", "painting", "render")):
        tips.append("Specify style (photograph, illustration, anime, etc.).")
    return {
        "ok": True,
        "original": prompt,
        "tips": tips or ["Prompt looks specific enough — try a preset or enhance preview."],
        "apply_required": True,
    }


def recommend_style_workflow(prompt: str) -> dict[str, Any]:
    p = (prompt or "").lower()
    preset = "high_quality"
    if any(w in p for w in ("anime", "manga", "waifu")):
        preset = "anime"
    elif any(w in p for w in ("pixel", "8-bit", "16-bit")):
        preset = "pixel_art"
    elif any(w in p for w in ("product", "packshot", "studio shot")):
        preset = "product_photo"
    elif any(w in p for w in ("landscape", "mountain", "vista", "horizon")):
        preset = "landscape"
    elif any(w in p for w in ("portrait", "face", "headshot")):
        preset = "photoreal_portrait"
    elif any(w in p for w in ("concept", "environment art")):
        preset = "concept_art"
    elif any(w in p for w in ("draft", "sketch", "quick")):
        preset = "fast_draft"
    return {
        "ok": True,
        "recommended_preset": preset,
        "hint": "Apply via Generation Presets — does not change settings until you select it.",
    }


def seed_explorer(*, base_seed: int | None = None, count: int = 4) -> dict[str, Any]:
    count = max(1, min(8, int(count or 4)))
    base = int(base_seed) if base_seed is not None else secrets.randbelow(2**32)
    seeds = [base]
    for i in range(1, count):
        seeds.append((base + i * 9973) % (2**32))
    return {"ok": True, "base": base, "seeds": seeds, "hint": "Pick a seed and Generate — same pipeline."}


def evolve_prompt(prompt: str, *, direction: str = "detail") -> dict[str, Any]:
    """Offer alternate prompt phrasings — never applied silently."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    variants = [prompt]
    if direction == "detail":
        variants.append(f"{prompt}, intricate detail, sharp focus")
        variants.append(f"{prompt}, cinematic composition, rich texture")
    elif direction == "simpler":
        variants.append(" ".join(prompt.split()[:12]))
    else:
        variants.append(f"{prompt}, subtle variation")
    return {"ok": True, "original": prompt, "variants": variants, "apply_required": True}
