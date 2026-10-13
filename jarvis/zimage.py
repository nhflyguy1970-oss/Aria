"""Z-Image Turbo INT8 generation (Phase 8): a selectable model beside Schnell and Klein.

The installed ComfyUI (0.21.1) cannot run the INT8 checkpoint. The Phase 8 qualified
runtime is a read-only core overlay (ComfyUI v0.27.0 + INT8 ``quantize_input`` fix) and
the pinned comfy_kitchen wheel, run as a separate on-demand ComfyUI worker
(``aria-zimage-worker.service``, port 8189) inside bubblewrap. The worker is started
for a job and stopped afterwards so it holds no idle VRAM. Every job goes through
``comfyui.run_workflow`` and therefore the exclusive RTX 3060 image slot, the 82 C
cutoff and FTR yield.
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import time
import urllib.request
from pathlib import Path

ZIMAGE_URL = os.getenv("JARVIS_ZIMAGE_URL", "http://127.0.0.1:8189").rstrip("/")
UNIT = "aria-zimage-worker.service"
CHECKPOINT = "z_image_turbo_int8_convrot.safetensors"
FILES = {"diffusion_models": CHECKPOINT, "vae": "ae.safetensors", "text_encoders": "qwen_3_4b.safetensors"}
RUNTIME = Path.home() / ".local/share/aria-zimage"
START_TIMEOUT_S = 120


def installed() -> bool:
    from jarvis.comfyui_settings import COMFY_ROOT

    unit = Path.home() / ".config/systemd/user" / UNIT
    return (unit.is_file() and (RUNTIME / "runtime/core/comfy").is_dir()
            and all((COMFY_ROOT / "models" / sub / name).is_file() for sub, name in FILES.items()))


MAX_PIXELS = 1024 * 768  # largest size Z-Image was qualified at in Phase 8 (1024x768, 768x512)


def qualified_size(width: int, height: int) -> tuple[int, int]:
    """Keep the aspect ratio inside the qualified pixel envelope (multiples of 16)."""
    w, h = max(256, int(width)), max(256, int(height))
    scale = min(1.0, (MAX_PIXELS / (w * h)) ** 0.5)
    return max(256, int(w * scale) // 16 * 16), max(256, int(h * scale) // 16 * 16)


def build_workflow(prompt: str, width: int, height: int, seed: int | None = None) -> dict:
    """The Phase 8 qualified graph: INT8 UNet, CPU Qwen3-4B (lumina2), AuraFlow shift 3, 8 steps."""
    seed = secrets.randbelow(2**32) if seed is None else int(seed)
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": CHECKPOINT, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": FILES["text_encoders"], "type": "lumina2", "device": "cpu"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": FILES["vae"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
        "7": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
        "5": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "12": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3}},
        "3": {"class_type": "KSampler", "inputs": {"model": ["12", 0], "positive": ["6", 0], "negative": ["7", 0],
                                                   "latent_image": ["5", 0], "seed": seed, "steps": 8, "cfg": 1,
                                                   "sampler_name": "res_multistep", "scheduler": "simple", "denoise": 1}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "jarvis_zimage"}},
    }


def _ready() -> bool:
    try:
        with urllib.request.urlopen(f"{ZIMAGE_URL}/system_stats", timeout=2):
            return True
    except Exception:  # noqa: BLE001
        return False


def _systemctl(*args: str) -> None:
    subprocess.run(["systemctl", "--user", *args, UNIT], check=True, capture_output=True, timeout=60)


def _free_main_comfyui() -> None:
    """The stock ComfyUI may still hold Schnell/Klein in VRAM; release it before Z-Image loads."""
    from jarvis.comfyui import COMFY_URL

    try:
        req = urllib.request.Request(f"{COMFY_URL}/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=10)
    except Exception:  # noqa: BLE001
        pass


def generate(prompt: str, width: int = 1024, height: int = 1024, *, seed: int | None = None,
             cancel_check=None) -> str:
    """Render one image with Z-Image Turbo INT8; returns the saved path or an ERROR: string."""
    from jarvis import comfyui

    if not installed():
        return "ERROR: Z-Image Turbo is not installed (worker unit, runtime overlay or model files missing)"
    width, height = qualified_size(width, height)
    _free_main_comfyui()
    try:
        _systemctl("start")
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: Z-Image worker failed to start: {exc}"
    try:
        deadline = time.monotonic() + START_TIMEOUT_S
        while not _ready():
            if time.monotonic() > deadline:
                return "ERROR: Z-Image worker did not become ready"
            time.sleep(1)
        with comfyui.target(ZIMAGE_URL):
            from jarvis.gpu_scheduler import ZIMAGE_VRAM_MIB

            return comfyui.run_workflow(build_workflow(prompt, width, height, seed), "jarvis_zimage",
                                        timeout_sec=420, cancel_check=cancel_check, vram_mib=ZIMAGE_VRAM_MIB)
    finally:
        try:
            _systemctl("stop")  # no idle VRAM held between jobs
        except Exception:  # noqa: BLE001
            pass
