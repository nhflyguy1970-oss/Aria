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


KLEIN_FILES = {
    "diffusion_models": "flux-2-klein-4b-fp8.safetensors",
    "text_encoders": "qwen_3_4b.safetensors",
    "vae": "flux2-vae.safetensors",
}


def klein_installed() -> bool:
    from jarvis.comfyui_settings import COMFY_ROOT

    return all((COMFY_ROOT / "models" / sub / name).is_file() for sub, name in KLEIN_FILES.items())


def _klein_dims(path: Path) -> tuple[int, int]:
    """Source aspect, long side <= 1024, multiples of 16 (Phase 8 qualified sizes)."""
    try:
        from PIL import Image

        with Image.open(path) as im:
            w, h = im.size
    except Exception:  # noqa: BLE001
        return 1024, 768
    scale = min(1.0, 1024 / max(w, h))
    return max(256, int(w * scale) // 16 * 16), max(256, int(h * scale) // 16 * 16)


def build_klein_edit_workflow(image_name: str, prompt: str, width: int, height: int, seed: int | None = None) -> dict:
    """FLUX.2 Klein native reference edit — core nodes only (Phase 8 tournament graph)."""
    seed = secrets.randbelow(2**32) if seed is None else seed
    return {
        "4": {"class_type": "UNETLoader", "inputs": {"unet_name": KLEIN_FILES["diffusion_models"], "weight_dtype": "default"}},
        "20": {"class_type": "CLIPLoader", "inputs": {"clip_name": KLEIN_FILES["text_encoders"], "type": "flux2", "device": "cpu"}},
        "21": {"class_type": "VAELoader", "inputs": {"vae_name": KLEIN_FILES["vae"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["20", 0]}},
        "7": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "10": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["21", 0]}},
        "12": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["6", 0], "latent": ["11", 0]}},
        "13": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["7", 0], "latent": ["11", 0]}},
        "5": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "22": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "23": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "24": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": width, "height": height}},
        "25": {"class_type": "CFGGuider", "inputs": {"model": ["4", 0], "positive": ["12", 0], "negative": ["13", 0], "cfg": 1}},
        "3": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["22", 0], "guider": ["25", 0], "sampler": ["23", 0],
                                                                  "sigmas": ["24", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["21", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "jarvis_edit_klein", "images": ["8", 0]}},
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

    if klein_installed() and denoise is None:
        width, height = _klein_dims(src)
        wf = build_klein_edit_workflow(image_name, prompt.strip(), width, height)
        return run_workflow(wf, filename_prefix="jarvis_edit_klein", timeout_sec=420)
    wf = build_edit_workflow(
        image_name=image_name,
        prompt=prompt.strip(),
        negative_prompt=negative_prompt,
        denoise=denoise,
    )
    return run_workflow(wf, filename_prefix="jarvis_edit", timeout_sec=420)
