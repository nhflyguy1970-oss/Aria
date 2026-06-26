"""ComfyUI img2img — edit an existing image from a text prompt (not inpaint)."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from jarvis.comfyui import (
    DEFAULT_NEGATIVE,
    _find_checkpoint,
    _sampler_settings,
    run_workflow,
    upload_image,
)
from jarvis.comfyui_inpaint import _prepare_image


def _edit_denoise() -> float:
    try:
        return max(0.25, min(0.92, float(os.getenv("JARVIS_COMFYUI_EDIT_DENOISE", "0.58"))))
    except ValueError:
        return 0.58


def build_edit_workflow(
    image_name: str,
    prompt: str,
    negative_prompt: str = "",
    denoise: float | None = None,
) -> dict:
    ckpt = _find_checkpoint()
    steps, cfg, sampler_name, scheduler = _sampler_settings(ckpt)
    if denoise is None:
        denoise = _edit_denoise()
    negative = negative_prompt.strip() or DEFAULT_NEGATIVE
    seed = secrets.randbelow(2**32)

    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "10": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
            "_meta": {"title": "Source Image"},
        },
        "11": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["10", 0], "vae": ["4", 2]},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]},
            "_meta": {"title": "Positive"},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]},
            "_meta": {"title": "Negative"},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": denoise,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["11", 0],
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "jarvis_edit", "images": ["8", 0]},
        },
    }


def edit_image(
    image_path: str | Path,
    prompt: str,
    negative_prompt: str = "",
    denoise: float | None = None,
    *,
    skip_vram_prep: bool = False,
) -> str:
    """Img2img edit — transform the whole image guided by prompt. Returns path or ERROR:."""
    from jarvis.comfyui import is_available
    from jarvis.services import ensure_comfyui_nvidia

    if not prompt.strip():
        return "ERROR: Edit needs a prompt describing what to change"

    if not skip_vram_prep:
        from jarvis.vram_guard import prepare_for_comfyui

        prepare_for_comfyui()

    if not is_available():
        ensure_comfyui_nvidia(block=True, timeout=30)
    if not is_available():
        return (
            "ERROR: ComfyUI is not running. Start it from the Gallery sidebar or run "
            "~/ComfyUI/venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188"
        )

    src = _prepare_image(Path(image_path).expanduser().resolve())
    try:
        image_name = upload_image(src)
    except Exception as e:
        return f"ERROR: ComfyUI upload failed: {e}"

    wf = build_edit_workflow(
        image_name=image_name,
        prompt=prompt.strip(),
        negative_prompt=negative_prompt,
        denoise=denoise,
    )
    return run_workflow(wf, filename_prefix="jarvis_edit", timeout_sec=420)
