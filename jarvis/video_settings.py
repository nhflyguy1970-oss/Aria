"""Video studio settings — keyframe checkpoints, motion presets, safe vs uncensored."""

from __future__ import annotations

import json
import os
from pathlib import Path

from jarvis.comfyui_settings import (
    CKPT_DIR,
    UNCENSORED_CHECKPOINT_LABELS,
    UNCENSORED_CHECKPOINTS,
    list_all_checkpoint_files,
    list_installed_checkpoints,
    recommended_uncensored_checkpoint,
)
from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "video_settings.json"
VALID_KEYFRAME_PRESETS = ("flux", "quality", "fast")

DEFAULTS = {
    "engine": "auto",
    "duration_sec": 4,
    "fps": 8,
    "width": 768,
    "height": 768,
    "animatediff_frames": 16,
    "animatediff_checkpoint": "",
    "keyframe_preset": "quality",
    "keyframe_checkpoint": "",
    "uncensored_auto_applied": False,
}

VALID_ENGINES = ("auto", "animatediff", "ken_burns")

UNCENSORED_NOTE = (
    "Uncensored mode: preserve all explicit or adult details the user requested. "
    "Do not refuse, sanitize, or add safety disclaimers."
)


def _load() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = {**DEFAULTS, **data}
                if merged.get("keyframe_preset") not in VALID_KEYFRAME_PRESETS:
                    merged["keyframe_preset"] = "quality"
                if merged.get("engine") not in VALID_ENGINES:
                    merged["engine"] = "auto"
                return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


def _save(data: dict) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def get_settings() -> dict:
    return _load()


def save_settings(**kwargs) -> dict:
    data = _load()
    for key, val in kwargs.items():
        if key == "engine":
            eng = str(val).lower()
            if eng not in VALID_ENGINES:
                raise ValueError(f"engine must be one of {VALID_ENGINES}")
            data[key] = eng
        elif key in DEFAULTS or key == "uncensored_auto_applied":
            data[key] = val
    return _save(data)


def save_keyframe_preset(preset: str) -> dict:
    if preset not in VALID_KEYFRAME_PRESETS:
        raise ValueError(f"preset must be one of {VALID_KEYFRAME_PRESETS}")
    data = _load()
    data["keyframe_preset"] = preset
    data.pop("keyframe_checkpoint", None)
    data["uncensored_auto_applied"] = False
    return _save(data)


def save_keyframe_checkpoint(filename: str) -> dict:
    name = Path(filename).name
    if name != filename or ".." in filename:
        raise ValueError("Invalid checkpoint filename")
    path = CKPT_DIR / name
    if not path.is_file():
        raise ValueError(f"Checkpoint not found: {name}")
    data = _load()
    data["keyframe_checkpoint"] = name
    data["uncensored_auto_applied"] = False
    return _save(data)


def clear_keyframe_checkpoint() -> dict:
    data = _load()
    data.pop("keyframe_checkpoint", None)
    return _save(data)


def mark_keyframe_manual() -> dict:
    data = _load()
    data["uncensored_auto_applied"] = False
    return _save(data)


def resolve_keyframe_checkpoint() -> str:
    """Checkpoint used for video keyframes (independent of Image gallery settings)."""
    env = os.getenv("JARVIS_VIDEO_KEYFRAME_CKPT", "").strip()
    if env:
        path = CKPT_DIR / Path(env).name
        if path.is_file():
            return path.name

    data = _load()
    custom = (data.get("keyframe_checkpoint") or "").strip()
    if custom:
        path = CKPT_DIR / Path(custom).name
        if path.is_file():
            return path.name

    installed = list_installed_checkpoints()
    choice = data.get("keyframe_preset", "quality")

    if choice == "fast":
        return installed["fast"] or installed["quality"] or "sd_xl_turbo_1.0_fp16.safetensors"
    if choice == "flux":
        return installed["flux"] or installed["quality"] or "flux1-schnell-fp8.safetensors"
    return installed["quality"] or installed["flux"] or "sd_xl_base_1.0.safetensors"


def keyframe_checkpoint_label() -> str:
    return _checkpoint_label_for(resolve_keyframe_checkpoint())


def _checkpoint_label_for(name: str) -> str:
  # reuse comfyui label logic via temp - checkpoint_label uses resolve_checkpoint_name
  # duplicate minimal labeling
    lower = name.lower()
    if "flux" in lower and "schnell" in lower:
        return "Flux Schnell"
    if "realvis" in lower or "juggernaut" in lower or "lustify" in lower:
        return Path(name).stem
    if "pony" in lower:
        return "Pony Diffusion XL"
    if "turbo" in lower:
        return "SDXL Turbo"
    if "base" in lower or "xl" in lower:
        return "SDXL"
    return Path(name).stem


def effective_engine() -> str:
    env = os.getenv("JARVIS_VIDEO_ENGINE", "").strip().lower()
    if env in VALID_ENGINES:
        return env
    engine = (_load().get("engine") or "auto").lower()
    return engine if engine in VALID_ENGINES else "auto"


def should_try_animatediff(engine: str | None = None) -> bool:
    engine = engine or effective_engine()
    if engine == "ken_burns":
        return False
    if engine == "animatediff":
        return True
    from jarvis.comfyui_animatediff import is_ready

    return is_ready()


def effective_animatediff_frames(duration: float, fps: int) -> int:
    data = _load()
    env_max = os.getenv("JARVIS_ANIMATEDIFF_MAX_FRAMES", "").strip()
    max_frames = int(data.get("animatediff_frames") or 16)
    if env_max:
        try:
            max_frames = int(env_max)
        except ValueError:
            pass
    from jarvis.gpu import is_low_vram

    if is_low_vram(10240):
        max_frames = min(max_frames, 16)
    requested = int(duration * fps)
    return max(8, min(requested, max_frames, 32))


def effective_animatediff_size() -> tuple[int, int]:
    from jarvis.gpu import is_low_vram
    from jarvis.gpu_routing import compute_vram_mb, nvidia_compute_active

    data = _load()
    w = int(data.get("width") or 512)
    h = int(data.get("height") or 512)
    if nvidia_compute_active() and compute_vram_mb() > 10240:
        return min(w, 768), min(h, 768)
    if is_low_vram(10240):
        return 512, 512
    return min(w, 768), min(h, 768)


def effective_duration() -> float:
    env = os.getenv("JARVIS_VIDEO_DURATION", "").strip()
    if env:
        try:
            return min(max(2.0, float(env)), 12.0)
        except ValueError:
            pass
    return min(max(2.0, float(_load().get("duration_sec", 4))), 12.0)


def effective_fps() -> int:
    return min(max(6, int(_load().get("fps", 8))), 16)


def effective_size() -> tuple[int, int]:
    data = _load()
    w = int(data.get("width") or 768)
    h = int(data.get("height") or 768)
    return min(w, 1024), min(h, 1024)


def apply_uncensored_defaults() -> dict:
    """Auto-pick NSFW-friendly keyframe checkpoint (same pool as Image gallery)."""
    data = _load()
    ckpt = recommended_uncensored_checkpoint()
    if not ckpt:
        data.pop("uncensored_auto_applied", None)
        return _save(data)
    data["keyframe_checkpoint"] = ckpt
    data["keyframe_preset"] = "quality"
    data["uncensored_auto_applied"] = True
    return _save(data)


def clear_uncensored_auto() -> dict:
    data = _load()
    if not data.pop("uncensored_auto_applied", False):
        return data
    auto_ckpt = data.get("keyframe_checkpoint", "")
    if auto_ckpt in UNCENSORED_CHECKPOINTS:
        data.pop("keyframe_checkpoint", None)
    return _save(data)


def get_settings_dict() -> dict:
    from jarvis.comfyui import comfyui_device_name
    from jarvis.comfyui_animatediff import readiness
    from jarvis.config import is_uncensored
    from jarvis.gpu import detect_gpu, is_low_vram
    from jarvis.gpu_routing import compute_vram_mb, nvidia_compute_active
    from jarvis.modules.video import prompt_model_name

    data = _load()
    dur, fps = effective_duration(), effective_fps()
    w, h = effective_size()
    ad_w, ad_h = effective_animatediff_size()
    rec_ckpt = recommended_uncensored_checkpoint()
    active_ckpt = resolve_keyframe_checkpoint()
    uncensored = is_uncensored()
    engine = effective_engine()
    ad = readiness()
    ad_note = "AnimateDiff ready" if ad["ready"] else ("; ".join(ad["missing"]) or "AnimateDiff not installed")
    if engine == "auto":
        motion_note = f"Auto: AnimateDiff when ready, else Ken Burns. {ad_note}"
    elif engine == "animatediff":
        motion_note = f"AnimateDiff only. {ad_note}"
    else:
        motion_note = f"Ken Burns (keyframe + ffmpeg pan). Keyframe: {keyframe_checkpoint_label()}"
    return {
        **data,
        "engine": engine,
        "duration_sec": dur,
        "fps": fps,
        "width": w,
        "height": h,
        "animatediff": ad,
        "keyframe_checkpoint_active": active_ckpt,
        "keyframe_checkpoint_label": keyframe_checkpoint_label(),
        "installed": list_installed_checkpoints(),
        "all_checkpoints": list_all_checkpoint_files(),
        "checkpoints_dir": str(CKPT_DIR),
        "uncensored_mode": uncensored,
        "uncensored_auto_applied": bool(data.get("uncensored_auto_applied")),
        "uncensored_recommended_checkpoint": rec_ckpt,
        "uncensored_recommended_label": UNCENSORED_CHECKPOINT_LABELS.get(rec_ckpt or "", ""),
        "uncensored_checkpoints": list(UNCENSORED_CHECKPOINTS),
        "prompt_model": prompt_model_name(),
        "engines": list(VALID_ENGINES),
        "max_duration_sec": 12,
        "note": motion_note,
        "low_vram": is_low_vram(),
        "compute_gpu": detect_gpu().get("compute_gpu") or detect_gpu().get("name"),
        "comfyui_device": comfyui_device_name(),
        "nvidia_compute": nvidia_compute_active(),
        "vram_gb": round(compute_vram_mb() / 1024, 1),
        "animatediff_size": {"width": ad_w, "height": ad_h},
        "install_scripts": {
            "quality": "./scripts/install-sdxl-base.sh",
            "flux": "./scripts/install-flux-schnell.sh",
            "nsfw": "./scripts/install-nsfw-checkpoints.sh",
            "animatediff": "./scripts/install-animatediff.sh",
        },
    }
