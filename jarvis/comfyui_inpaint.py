"""ComfyUI inpainting — upload image/mask, run workflow, save result."""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from pathlib import Path

from jarvis.comfyui import DEFAULT_NEGATIVE, _find_checkpoint, _sampler_settings, run_workflow, upload_image
from jarvis.config import DATA_DIR, PROJECT_ROOT

DEFAULT_INPAINT_WORKFLOW = PROJECT_ROOT / "data" / "comfyui_workflows" / "inpaint_sdxl.json"


def effective_inpaint_workflow_path() -> Path | None:
    custom = os.getenv("JARVIS_COMFYUI_INPAINT_WORKFLOW", "").strip()
    if custom:
        path = Path(custom).expanduser()
        if path.is_file():
            return path
    if DEFAULT_INPAINT_WORKFLOW.is_file():
        return DEFAULT_INPAINT_WORKFLOW
    return None


def _inpaint_max_dim() -> int:
    try:
        return max(512, min(2048, int(os.getenv("JARVIS_COMFYUI_INPAINT_MAX_DIM", "1024"))))
    except ValueError:
        return 1024


def _prepare_image(path: Path) -> Path:
    """Optionally downscale large images to fit 8GB VRAM."""
    from PIL import Image

    max_dim = _inpaint_max_dim()
    with Image.open(path) as im:
        rgb = im.convert("RGB")
        w, h = rgb.size
        longest = max(w, h)
        if longest <= max_dim:
            return path
        scale = max_dim / longest
        nw, nh = int(w * scale), int(h * scale)
        out = DATA_DIR / "inpaint_masks" / f"prep_{path.stem}_{int(time.time())}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        rgb.resize((nw, nh), Image.Resampling.LANCZOS).save(out, format="PNG", optimize=True)
        return out


def build_inpaint_workflow(
    image_name: str,
    mask_name: str,
    prompt: str,
    negative_prompt: str = "",
    denoise: float | None = None,
    grow_mask_by: int | None = None,
) -> dict:
    """Return ComfyUI API workflow dict for SD/SDXL inpainting."""
    wf_path = effective_inpaint_workflow_path()
    if wf_path:
        wf = json.loads(wf_path.read_text(encoding="utf-8"))
        if wf.get("placeholder"):
            wf = None
        else:
            return _patch_custom_workflow(
                wf,
                image_name=image_name,
                mask_name=mask_name,
                prompt=prompt,
                negative_prompt=negative_prompt,
                denoise=denoise,
                grow_mask_by=grow_mask_by,
            )

    ckpt = _find_checkpoint()
    steps, cfg, sampler_name, scheduler = _sampler_settings(ckpt)
    if denoise is None:
        denoise = float(os.getenv("JARVIS_COMFYUI_INPAINT_DENOISE", "0.85"))
    if grow_mask_by is None:
        grow_mask_by = int(os.getenv("JARVIS_COMFYUI_INPAINT_GROW_MASK", "6"))
    negative = negative_prompt.strip() or DEFAULT_NEGATIVE
    seed = int(time.time()) % (2**32)

    return {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "10": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
            "_meta": {"title": "Source Image"},
        },
        "11": {
            "class_type": "LoadImage",
            "inputs": {"image": mask_name},
            "_meta": {"title": "Mask Image"},
        },
        "12": {"class_type": "ImageToMask", "inputs": {"image": ["11", 0], "channel": "red"}},
        "13": {
            "class_type": "VAEEncodeForInpaint",
            "inputs": {
                "pixels": ["10", 0],
                "vae": ["4", 2],
                "mask": ["12", 0],
                "grow_mask_by": grow_mask_by,
            },
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
                "latent_image": ["13", 0],
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "jarvis_inpaint", "images": ["8", 0]},
        },
    }


def _patch_custom_workflow(
    wf: dict,
    *,
    image_name: str,
    mask_name: str,
    prompt: str,
    negative_prompt: str,
    denoise: float | None,
    grow_mask_by: int | None,
) -> dict:
    wf = deepcopy(wf)
    load_images: list[dict] = []
    for node in wf.values():
        if not isinstance(node, dict):
            continue
        title = (node.get("_meta") or {}).get("title", "")
        class_type = node.get("class_type", "")
        if class_type == "LoadImage":
            load_images.append(node)
        if class_type == "CLIPTextEncode" and title == "Positive":
            node["inputs"]["text"] = prompt
        if class_type == "CLIPTextEncode" and title == "Negative":
            node["inputs"]["text"] = negative_prompt.strip() or DEFAULT_NEGATIVE
        if class_type == "KSampler" and denoise is not None:
            node["inputs"]["denoise"] = denoise
        if class_type == "VAEEncodeForInpaint" and grow_mask_by is not None:
            node["inputs"]["grow_mask_by"] = grow_mask_by

    if load_images:
        load_images[0]["inputs"]["image"] = image_name
    if len(load_images) > 1:
        load_images[1]["inputs"]["image"] = mask_name
    elif len(load_images) == 1:
        # Single LoadImage workflow — mask node may use a different class
        for node in wf.values():
            if isinstance(node, dict) and node.get("class_type") == "LoadImage":
                title = (node.get("_meta") or {}).get("title", "").lower()
                if "mask" in title:
                    node["inputs"]["image"] = mask_name
    return wf


def inpaint(
    image_path: str | Path,
    mask_path: str | Path,
    prompt: str,
    negative_prompt: str = "",
    denoise: float | None = None,
    *,
    skip_vram_prep: bool = False,
) -> str:
    """Inpaint masked region via ComfyUI. Returns output path or ERROR: string."""
    from jarvis.comfyui import is_available
    from jarvis.services import ensure_comfyui

    if not prompt.strip():
        return "ERROR: Inpaint needs a prompt describing what to generate in the masked area"

    if not skip_vram_prep:
        from jarvis.vram_guard import prepare_for_comfyui

        prepare_for_comfyui()
    if not is_available():
        ensure_comfyui(block=True, timeout=30)
    if not is_available():
        return (
            "ERROR: ComfyUI is not running. Start it from the Gallery sidebar or run "
            "~/ComfyUI/venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188"
        )

    src = _prepare_image(Path(image_path).expanduser().resolve())
    mask = Path(mask_path).expanduser().resolve()
    if not mask.is_file():
        return f"ERROR: Mask not found: {mask}"

    try:
        image_name = upload_image(src)
        mask_name = upload_image(mask)
    except Exception as e:
        return f"ERROR: ComfyUI upload failed: {e}"

    wf = build_inpaint_workflow(
        image_name=image_name,
        mask_name=mask_name,
        prompt=prompt.strip(),
        negative_prompt=negative_prompt,
        denoise=denoise,
    )
    return run_workflow(wf, filename_prefix="jarvis_inpaint")
