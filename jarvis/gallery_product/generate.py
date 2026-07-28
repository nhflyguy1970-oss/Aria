"""Stay-in-Gallery generation — shared media job queue (no Chat hop required)."""

from __future__ import annotations

from typing import Any


def submit_generate(assistant, prompt: str, *, negative: str = "") -> dict[str, Any]:
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "message": "Prompt required"}
    if not assistant:
        return {"ok": False, "message": "Assistant unavailable", "recovery": "Restart Aria"}
    params: dict[str, Any] = {"prompt": prompt}
    if negative:
        params["negative"] = negative
    # Reuse the same queue Chat uses — shared Job Center state
    result = assistant._enqueue_media("generate_image", params, f"generate image: {prompt}")
    if not result.get("ok"):
        return result
    return {
        "ok": True,
        "pending": True,
        "job_id": result.get("job_id"),
        "message": result.get("message") or "Image generation queued",
        "action": "generate_image",
        "stay_in_gallery": True,
        "status": "queued",
    }


def submit_variation(assistant, *, path: str, prompt: str = "") -> dict[str, Any]:
    """Img2img-style variation via edit_image job."""
    from jarvis.gallery_product.metadata import get_meta
    from pathlib import Path

    name = Path(path).name
    meta = get_meta(name)
    base_prompt = (prompt or meta.get("prompt") or meta.get("enhanced_prompt") or "").strip()
    if not base_prompt:
        base_prompt = "variation of the reference image"
    if not assistant:
        return {"ok": False, "message": "Assistant unavailable"}
    result = assistant._enqueue_media(
        "edit_image",
        {"path": path, "prompt": base_prompt, "denoise": 0.55},
        f"variation of {name}",
    )
    if not result.get("ok"):
        return result
    return {
        "ok": True,
        "pending": True,
        "job_id": result.get("job_id"),
        "message": result.get("message") or "Variation queued",
        "action": "edit_image",
        "stay_in_gallery": True,
        "status": "queued",
    }
