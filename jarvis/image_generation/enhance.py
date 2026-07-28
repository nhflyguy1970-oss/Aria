"""Transparent prompt enhancement — view / edit / disable / re-run."""

from __future__ import annotations

from typing import Any


def preview_enhance(prompt: str, *, enhance: bool | None = True, negative: str = "") -> dict[str, Any]:
    """Return original vs enhanced without generating an image."""
    from jarvis.modules.image import ImageEngine, normalize_image_prompt

    prompt = normalize_image_prompt(prompt)
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    engine = ImageEngine()
    if enhance is False:
        return {
            "ok": True,
            "original": prompt,
            "enhanced": prompt,
            "negative": negative or "",
            "enhance_applied": False,
        }
    prepared = engine.prepare_prompt(prompt)
    pos = prepared.get("positive") or prompt
    neg = negative or prepared.get("negative") or ""
    return {
        "ok": True,
        "original": prompt,
        "enhanced": pos,
        "negative": neg,
        "enhance_applied": pos != prompt,
        "changed": pos != prompt,
    }
