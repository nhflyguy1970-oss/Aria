"""Post-process generated images — upscale (local) and ComfyUI extras."""

from __future__ import annotations

import os
import time
from pathlib import Path

from jarvis.config import DATA_DIR

OUTPUT_DIR = DATA_DIR / "generated"


def upscale_local(path: str | Path, scale: int = 2) -> str:
    """2× upscale with Lanczos (fast, no VRAM). Returns output path or ERROR."""
    from PIL import Image

    scale = max(2, min(4, int(scale)))
    src = Path(path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: File not found: {src}"
    try:
        with Image.open(src) as im:
            rgb = im.convert("RGB")
            w, h = rgb.size
            out = rgb.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
            dest = OUTPUT_DIR / f"jarvis_up{scale}x_{src.stem}_{int(time.time())}.png"
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            out.save(dest, format="PNG", optimize=True)
            return str(dest)
    except Exception as e:
        return f"ERROR: Upscale failed: {e}"


def upscale_comfyui(path: str | Path, scale: int = 2) -> str:
    """Upscale via ComfyUI ImageScale node when server is online."""
    from jarvis.comfyui import is_available

    if not is_available():
        return upscale_local(path, scale)

    src = Path(path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: File not found: {src}"

    scale = max(2, min(4, int(scale)))
    try:
        from PIL import Image

        from jarvis.comfyui import run_workflow, upload_image

        image_name = upload_image(src)
        with Image.open(src) as im:
            w, h = im.size
        wf = {
            "1": {"class_type": "LoadImage", "inputs": {"image": image_name}},
            "2": {
                "class_type": "ImageScale",
                "inputs": {
                    "image": ["1", 0],
                    "upscale_method": "lanczos",
                    "width": w * scale,
                    "height": h * scale,
                    "crop": "disabled",
                },
            },
            "3": {
                "class_type": "SaveImage",
                "inputs": {"images": ["2", 0], "filename_prefix": "jarvis_upscale"},
            },
        }
        result = run_workflow(wf, filename_prefix="jarvis_upscale")
        if result.startswith("ERROR:"):
            return upscale_local(path, scale)
        return result
    except Exception:
        return upscale_local(path, scale)


def inpaint_region(
    image_path: str | Path,
    mask_path: str | Path | None,
    prompt: str,
    *,
    region: dict | None = None,
    negative_prompt: str = "",
    denoise: float | None = None,
) -> str:
    """Inpaint a region, or img2img edit when the whole image is selected."""
    src = Path(image_path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: File not found: {src}"

    full_frame = region is None
    if region is not None:
        try:
            w = float(region.get("w", 1))
            h = float(region.get("h", 1))
            x = float(region.get("x", 0))
            y = float(region.get("y", 0))
            full_frame = w >= 0.99 and h >= 0.99 and x <= 0.01 and y <= 0.01
        except (TypeError, ValueError):
            full_frame = False

    if full_frame:
        return edit_image(src, prompt, negative_prompt=negative_prompt, denoise=denoise)

    from jarvis.comfyui_inpaint import inpaint
    from jarvis.image_masks import mask_from_region, validate_mask_path
    try:
        if mask_path:
            mask = validate_mask_path(mask_path, src)
        elif region is not None:
            mask = mask_from_region(src, region)
        else:
            mask = mask_from_region(src, None)
    except FileNotFoundError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: Mask preparation failed: {e}"

    return inpaint(
        src,
        mask,
        prompt,
        negative_prompt=negative_prompt,
        denoise=denoise,
        skip_vram_prep=True,
    )


def edit_image(
    image_path: str | Path,
    prompt: str,
    *,
    negative_prompt: str = "",
    denoise: float | None = None,
) -> str:
    """Whole-image img2img edit (preserves layout better than full-mask inpaint)."""
    from jarvis.comfyui_edit import edit_image as comfy_edit

    src = Path(image_path).expanduser().resolve()
    if not src.is_file():
        return f"ERROR: File not found: {src}"

    instruction = (prompt or "").strip()
    if not instruction:
        return "ERROR: Edit needs a prompt describing what to change"

    edit_prompt = instruction
    lower = instruction.lower()
    if not any(
        w in lower
        for w in ("same", "keep", "preserve", "maintain", "original", "composition")
    ):
        edit_prompt = (
            f"Same composition, subjects, and camera angle as the source image. {instruction}"
        )

    neg = negative_prompt
    if not neg.strip():
        try:
            from jarvis.modules.image import BASE_NEGATIVE

            neg = BASE_NEGATIVE
        except Exception:
            neg = ""

    result = comfy_edit(
        src,
        edit_prompt,
        negative_prompt=neg,
        denoise=denoise,
        skip_vram_prep=True,
    )
    if not result.startswith("ERROR:"):
        from jarvis.cache_state import invalidate_gallery

        invalidate_gallery()
    return result
