"""AnimateDiff text-to-video via ComfyUI (SD 1.5 + motion module)."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from jarvis import comfyui
from jarvis.comfyui import COMFY_ROOT, COMFY_URL, DEFAULT_NEGATIVE
from jarvis.comfyui_settings import CKPT_DIR

log = logging.getLogger("jarvis")

MOTION_DIRS = (
    COMFY_ROOT / "models" / "animatediff_models",
    COMFY_ROOT / "models" / "animatediff",
    COMFY_ROOT / "custom_nodes" / "ComfyUI-AnimateDiff-Evolved" / "models",
)
MOTION_NAMES = (
    "mm_sd_v15_v3.safetensors",
    "mm_sd_v15_v2.ckpt",
    "mm_sd_v15.ckpt",
    "mm_sd_v14.ckpt",
)
SD15_EXCLUDE = (
    "xl",
    "flux",
    "pony",
    "juggernaut",
    "lustify",
    "realvis",
    "dreamshaper",
    "helloworld",
    "turbo",
    "sd_xl",
)
SD15_PREFER = (
    "realistic_vision",
    "epicrealism",
    "v1-5",
    "sd_v1",
    "deliberate",
    "revAnimated",
)

_NODE_CACHE: dict | None = None
_NODE_CACHE_AT = 0.0


def _object_info() -> dict:
    global _NODE_CACHE, _NODE_CACHE_AT
    if _NODE_CACHE is not None and time.time() - _NODE_CACHE_AT < 120:
        return _NODE_CACHE
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(f"{COMFY_URL}/object_info", timeout=8) as resp:
            _NODE_CACHE = json.loads(resp.read().decode())
            _NODE_CACHE_AT = time.time()
            return _NODE_CACHE
    except Exception:
        return {}


def _pick_node(*candidates: str) -> str | None:
    info = _object_info()
    for name in candidates:
        if name in info:
            return name
    return None


def motion_module_path() -> Path | None:
    env = os.getenv("JARVIS_ANIMATEDIFF_MOTION", "").strip()
    if env:
        for base in MOTION_DIRS:
            path = base / Path(env).name
            if path.is_file():
                return path
        path = Path(env).expanduser()
        if path.is_file():
            return path
    for base in MOTION_DIRS:
        if not base.is_dir():
            continue
        for name in MOTION_NAMES:
            path = base / name
            if path.is_file():
                return path
        for path in sorted(base.glob("mm_sd*")):
            if path.is_file():
                return path
    return None


def motion_module_name() -> str | None:
    path = motion_module_path()
    return path.name if path else None


def _is_sd15_checkpoint(name: str) -> bool:
    lower = name.lower()
    if not lower.endswith((".safetensors", ".ckpt", ".pt")):
        return False
    return not any(marker in lower for marker in SD15_EXCLUDE)


def resolve_checkpoint() -> str | None:
    """SD 1.5 checkpoint for AnimateDiff (not SDXL / Flux)."""
    env = os.getenv("JARVIS_ANIMATEDIFF_CKPT", "").strip()
    if env:
        path = CKPT_DIR / Path(env).name
        if path.is_file() and _is_sd15_checkpoint(path.name):
            return path.name

    from jarvis.video_settings import get_settings

    custom = (get_settings().get("animatediff_checkpoint") or "").strip()
    if custom:
        path = CKPT_DIR / Path(custom).name
        if path.is_file() and _is_sd15_checkpoint(path.name):
            return path.name

    if not CKPT_DIR.is_dir():
        return None
    files = [p.name for p in CKPT_DIR.iterdir() if p.is_file() and _is_sd15_checkpoint(p.name)]
    if not files:
        return None
    lower_map = {f: f.lower() for f in files}
    for pref in SD15_PREFER:
        for name, lower in lower_map.items():
            if pref in lower:
                return name
    return sorted(files)[0]


def custom_nodes_installed() -> bool:
    ade = COMFY_ROOT / "custom_nodes" / "ComfyUI-AnimateDiff-Evolved"
    vhs = COMFY_ROOT / "custom_nodes" / "ComfyUI-VideoHelperSuite"
    return ade.is_dir() and vhs.is_dir()


def nodes_available() -> bool:
    if not comfyui.is_available():
        return False
    return bool(
        _pick_node("ADE_LoadAnimateDiffModel", "ADE_AnimateDiffLoaderGen1")
        and _pick_node("ADE_ApplyAnimateDiffModelSimple", "ADE_ApplyAnimateDiffModel")
        and _pick_node("ADE_UseEvolvedSampling")
        and _pick_node("VHS_VideoCombine")
    )


def readiness() -> dict:
    motion = motion_module_name()
    ckpt = resolve_checkpoint()
    nodes = nodes_available() if comfyui.is_available() else False
    installed = custom_nodes_installed()
    ready = bool(motion and ckpt and nodes)
    missing: list[str] = []
    if not installed:
        missing.append("AnimateDiff custom nodes (run ./scripts/install-animatediff.sh)")
    elif not nodes:
        missing.append("Restart ComfyUI after installing AnimateDiff nodes")
    if not motion:
        missing.append("motion module (mm_sd_v15_v2.ckpt)")
    if not ckpt:
        missing.append("SD 1.5 checkpoint (e.g. Realistic Vision V6 — not SDXL)")
    return {
        "ready": ready,
        "motion_module": motion,
        "checkpoint": ckpt,
        "nodes_installed": installed,
        "nodes_loaded": nodes,
        "missing": missing,
    }


def is_ready() -> bool:
    return readiness()["ready"]


def _animatediff_workflow(
    prompt: str,
    *,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    frames: int = 16,
    fps: int = 8,
    checkpoint: str | None = None,
    motion: str | None = None,
) -> dict | None:
    ckpt = checkpoint or resolve_checkpoint()
    motion_name = motion or motion_module_name()
    if not ckpt or not motion_name:
        return None

    load_motion = _pick_node("ADE_LoadAnimateDiffModel", "ADE_AnimateDiffLoaderGen1")
    apply_motion = _pick_node("ADE_ApplyAnimateDiffModelSimple", "ADE_ApplyAnimateDiffModel")
    evolve = _pick_node("ADE_UseEvolvedSampling")
    combine = _pick_node("VHS_VideoCombine")
    if not load_motion or not apply_motion or not evolve or not combine:
        return None

    steps = int(os.getenv("JARVIS_ANIMATEDIFF_STEPS", "20"))
    cfg = float(os.getenv("JARVIS_ANIMATEDIFF_CFG", "7.0"))
    sampler = os.getenv("JARVIS_ANIMATEDIFF_SAMPLER", "euler")
    scheduler = os.getenv("JARVIS_ANIMATEDIFF_SCHEDULER", "normal")
    seed = int(time.time()) % (2**32)
    negative = negative_prompt.strip() or DEFAULT_NEGATIVE
    frames = max(8, min(int(frames), 32))

    apply_inputs: dict = {
        "motion_model": ["2", 0],
    }
    if apply_motion != "ADE_ApplyAnimateDiffModelSimple":
        apply_inputs.setdefault("start_percent", 0.0)
        apply_inputs.setdefault("end_percent", 1.0)
        apply_inputs["model"] = ["1", 0]

    combine_inputs: dict = {
        "images": ["8", 0],
        "frame_rate": float(fps),
        "loop_count": 0,
        "filename_prefix": "jarvis_ad",
        "format": "video/h264-mp4",
        "pingpong": False,
        "save_output": True,
    }

    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "2": {"class_type": load_motion, "inputs": {"model_name": motion_name}},
        "3": {"class_type": apply_motion, "inputs": apply_inputs},
        "10": {
            "class_type": evolve,
            "inputs": {
                "model": ["1", 0],
                "beta_schedule": "autoselect",
                "m_models": ["3", 0],
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["1", 1]},
            "_meta": {"title": "Positive"},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["1", 1]},
            "_meta": {"title": "Negative"},
        },
        "6": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": frames},
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "denoise": 1,
                "model": ["10", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["6", 0],
            },
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9": {"class_type": combine, "inputs": combine_inputs},
    }


def generate(
    prompt: str,
    *,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 512,
    frames: int = 16,
    fps: int = 8,
) -> tuple[str, str]:
    """
    Run AnimateDiff workflow.
    Returns (video_path, "") on success or (ERROR:..., "") on failure.
    """
    from jarvis.vram_guard import prepare_for_comfyui

    prepare_for_comfyui()
    if not is_ready():
        status = readiness()
        detail = "; ".join(status["missing"]) or "AnimateDiff not ready"
        return f"ERROR: AnimateDiff unavailable — {detail}", ""

    if not comfyui.is_available():
        from jarvis.services import ensure_comfyui_nvidia

        ensure_comfyui_nvidia(block=True, timeout=90)
    if not comfyui.is_available():
        return "ERROR: ComfyUI is not running", ""

    wf = _animatediff_workflow(
        prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        frames=frames,
        fps=fps,
    )
    if not wf:
        return "ERROR: Could not build AnimateDiff workflow — missing ComfyUI nodes", ""

    timeout = int(os.getenv("JARVIS_ANIMATEDIFF_TIMEOUT", "600"))
    result = comfyui.run_workflow(wf, filename_prefix="jarvis_ad", timeout_sec=timeout)
    if result.startswith("ERROR:"):
        return result, ""

    from jarvis.video_ops import ensure_mp4

    mp4 = ensure_mp4(result)
    if mp4.startswith("ERROR:"):
        return mp4, ""
    return mp4, ""
