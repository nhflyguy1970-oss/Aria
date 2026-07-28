"""Transparent video prompt enhancement — view / edit / disable / re-run."""

from __future__ import annotations

from typing import Any


def preview_enhance(prompt: str, *, enhance: bool | None = True, negative: str = "") -> dict[str, Any]:
    from jarvis.modules.video import VideoEngine

    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    if enhance is False:
        return {
            "ok": True,
            "original": prompt,
            "enhanced": prompt,
            "negative": negative or "",
            "enhance_applied": False,
            "changed": False,
        }
    engine = VideoEngine()
    pos, neg = engine.prepare_prompt(prompt)
    neg_out = negative or neg or ""
    return {
        "ok": True,
        "original": prompt,
        "enhanced": pos or prompt,
        "negative": neg_out,
        "enhance_applied": (pos or prompt) != prompt,
        "changed": (pos or prompt) != prompt,
    }
