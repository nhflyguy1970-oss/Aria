"""Stay-in-Gallery generation — bridges to the shared Image Generation pipeline."""

from __future__ import annotations

from typing import Any


def submit_generate(assistant, prompt: str = "", *, negative: str = "", **extra) -> dict[str, Any]:
    """Enqueue via the one Image Generation engine (never a separate Gallery stack)."""
    from jarvis.image_generation.engine import submit_generation

    params = dict(extra or {})
    if prompt:
        params["prompt"] = prompt
    if negative:
        params.setdefault("negative", negative)
    return submit_generation(assistant, params, message=prompt or "", source="gallery")


def submit_variation(
    assistant,
    *,
    path: str,
    prompt: str = "",
    strength: str = "minor",
    reuse_seed: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    """Generate Another / variation — still the shared generate_image pipeline when text-only;
    img2img edit_image only when operator provides a reference path for conditioning.
    """
    from pathlib import Path

    from jarvis.gallery_product.metadata import get_meta
    from jarvis.image_generation.engine import submit_generation

    name = Path(path).name if path else ""
    meta = get_meta(name) if name else {}
    base_prompt = (prompt or meta.get("prompt") or meta.get("enhanced_prompt") or "").strip()
    if not base_prompt:
        base_prompt = "variation of the reference image"

    last_seed = seed
    if last_seed is None and meta.get("seed") not in (None, ""):
        try:
            last_seed = int(meta["seed"])
        except (TypeError, ValueError):
            last_seed = None

    # Text/prompt variations stay on generate_image (one pipeline)
    if strength in ("new_seed", "reuse_seed", "minor", "major", "variation") or not path:
        params: dict[str, Any] = {
            "prompt": base_prompt,
            "negative": meta.get("negative_prompt") or "",
            "checkpoint": meta.get("checkpoint") or "",
            "variation_strength": strength if strength != "new_seed" else "minor",
            "variations": 1,
        }
        if reuse_seed or strength == "reuse_seed":
            params["reuse_seed"] = True
            params["last_seed"] = last_seed
            params["seed"] = last_seed
        elif strength == "new_seed":
            params["random_seed"] = True
        if strength == "major":
            params["variations"] = 1
        return submit_generation(assistant, params, message=base_prompt, source="gallery")

    # Reference-image conditioning (experimental) uses edit_image job on same media queue
    if not assistant:
        return {"ok": False, "message": "Assistant unavailable"}
    denoise = 0.45 if strength == "minor" else 0.65
    result = assistant._enqueue_media(
        "edit_image",
        {"path": path, "prompt": base_prompt, "denoise": denoise},
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
        "source": "gallery",
    }
