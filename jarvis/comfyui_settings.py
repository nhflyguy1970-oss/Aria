"""Persisted ComfyUI device mode (GPU / CPU / auto-fallback) and checkpoint choice."""

from __future__ import annotations

import json
import os
from pathlib import Path

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "comfyui_settings.json"
VALID_MODES = ("auto", "gpu", "cpu")
VALID_CHECKPOINTS = ("flux", "quality", "fast")
UNCENSORED_CHECKPOINTS = (
    "RealVisXL_V5.0_fp16.safetensors",
    "Realistic_Vision_V6.0_NV_B1_fp16.safetensors",
    "ponyDiffusionV6XL_v6StartWithThisOne.safetensors",
    "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors",
    "lustifySDXLNSFWSFW_v10.safetensors",
    "leosamsHelloworldXL_helloworldXL60.safetensors",
    "DreamShaperXL_Turbo_v2.safetensors",
    "epicrealism_naturalSinRC1VAE.safetensors",
)
UNCENSORED_CHECKPOINT_LABELS = {
    "RealVisXL_V5.0_fp16.safetensors": "RealVisXL V5 (photoreal SDXL)",
    "Realistic_Vision_V6.0_NV_B1_fp16.safetensors": "Realistic Vision V6 (photoreal SD 1.5)",
    "ponyDiffusionV6XL_v6StartWithThisOne.safetensors": "Pony Diffusion V6 XL (anime/illustration)",
    "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors": "Juggernaut XL v9 (photoreal SDXL)",
    "lustifySDXLNSFWSFW_v10.safetensors": "Lustify SDXL v10 (photoreal SDXL)",
    "leosamsHelloworldXL_helloworldXL60.safetensors": "HelloWorld XL 6.0 (SDXL)",
    "DreamShaperXL_Turbo_v2.safetensors": "DreamShaper XL Turbo v2 (fast SDXL)",
    "epicrealism_naturalSinRC1VAE.safetensors": "epiCRealism (photoreal SD 1.5)",
}
COMFYUI_PORT = int(os.getenv("JARVIS_COMFYUI_PORT", "8188"))
COMFYUI_URL = os.getenv("JARVIS_COMFYUI_URL", f"http://127.0.0.1:{COMFYUI_PORT}")
COMFY_ROOT = Path(os.getenv("JARVIS_COMFYUI_ROOT", Path.home() / "ComfyUI"))
CKPT_DIR = COMFY_ROOT / "models" / "checkpoints"


def _defaults() -> dict:
    return {"mode": "auto", "runtime_cpu": False, "checkpoint": "quality"}


def load_settings() -> dict:
    data = _defaults()
    if not SETTINGS_FILE.exists():
        return data
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        if raw.get("mode") in VALID_MODES:
            data["mode"] = raw["mode"]
        if raw.get("checkpoint") in VALID_CHECKPOINTS:
            data["checkpoint"] = raw["checkpoint"]
        custom = raw.get("checkpoint_file")
        if isinstance(custom, str) and custom.strip():
            data["checkpoint_file"] = Path(custom.strip()).name
        if raw.get("uncensored_auto_applied"):
            data["uncensored_auto_applied"] = True
        wf = raw.get("workflow_file")
        if isinstance(wf, str) and wf.strip():
            data["workflow_file"] = wf.strip()
        data["runtime_cpu"] = bool(raw.get("runtime_cpu", False))
    except (json.JSONDecodeError, OSError, TypeError):
        pass
    return data


def _save(data: dict) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def save_mode(mode: str) -> dict:
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {VALID_MODES}")
    data = load_settings()
    data["mode"] = mode
    data["runtime_cpu"] = False
    return _save(data)


def save_checkpoint(checkpoint: str) -> dict:
    if checkpoint not in VALID_CHECKPOINTS:
        raise ValueError(f"checkpoint must be one of {VALID_CHECKPOINTS}")
    data = load_settings()
    data["checkpoint"] = checkpoint
    data.pop("checkpoint_file", None)
    return _save(data)


def recommended_uncensored_checkpoint() -> str | None:
    """Best installed NSFW-friendly checkpoint, or None."""
    for name in UNCENSORED_CHECKPOINTS:
        if (CKPT_DIR / name).is_file():
            return name
    return None


def apply_uncensored_defaults() -> dict:
    """Pick an NSFW-friendly checkpoint when uncensored mode is enabled (once)."""
    data = load_settings()
    ckpt = recommended_uncensored_checkpoint()
    if not ckpt:
        data.pop("uncensored_auto_applied", None)
        return _save(data)
    if data.get("uncensored_auto_applied") and data.get("checkpoint_file"):
        return data
    if data.get("checkpoint_file") and not data.get("uncensored_auto_applied"):
        return data
    data["checkpoint_file"] = ckpt
    data["checkpoint"] = "quality"
    data["uncensored_auto_applied"] = True
    return _save(data)


def clear_uncensored_auto_checkpoint() -> dict:
    """Revert auto-selected NSFW checkpoint when leaving uncensored mode."""
    data = load_settings()
    if not data.pop("uncensored_auto_applied", False):
        return data
    auto_ckpt = data.get("checkpoint_file", "")
    if auto_ckpt in UNCENSORED_CHECKPOINTS:
        data.pop("checkpoint_file", None)
    return _save(data)


def mark_checkpoint_manual() -> dict:
    """User picked a checkpoint — don't revert on uncensored toggle off."""
    data = load_settings()
    data["uncensored_auto_applied"] = False
    return _save(data)


def save_checkpoint_file(filename: str) -> dict:
    """Use a specific .safetensors from the checkpoints folder."""
    name = Path(filename).name
    if name != filename or ".." in filename:
        raise ValueError("Invalid checkpoint filename")
    path = CKPT_DIR / name
    if not path.is_file():
        raise ValueError(f"Checkpoint not found: {name}")
    data = load_settings()
    data["checkpoint_file"] = name
    data["uncensored_auto_applied"] = False
    return _save(data)


def clear_checkpoint_file() -> dict:
    data = load_settings()
    data.pop("checkpoint_file", None)
    return _save(data)


def save_workflow_file(path: str) -> dict:
    """Optional custom ComfyUI workflow JSON (absolute path or under ComfyUI)."""
    path = (path or "").strip()
    data = load_settings()
    if not path:
        data.pop("workflow_file", None)
        return _save(data)
    candidate = Path(path).expanduser()
    if not candidate.is_file():
        raise ValueError(f"Workflow file not found: {path}")
    data["workflow_file"] = str(candidate.resolve())
    return _save(data)


def effective_workflow_path() -> str:
    data = load_settings()
    wf = (data.get("workflow_file") or "").strip()
    if wf and Path(wf).is_file():
        return wf
    env = os.getenv("JARVIS_COMFYUI_WORKFLOW", "").strip()
    return env if env and Path(env).is_file() else ""


def mark_runtime_cpu_fallback() -> dict:
    data = load_settings()
    data["runtime_cpu"] = True
    return _save(data)


def clear_runtime_cpu_fallback() -> dict:
    data = load_settings()
    data["runtime_cpu"] = False
    return _save(data)


def effective_cpu_mode() -> bool:
    data = load_settings()
    if data.get("runtime_cpu"):
        return True
    mode = data.get("mode", "auto")
    return mode == "cpu"


def auto_fallback_enabled() -> bool:
    return load_settings().get("mode") == "auto"


def mode_label() -> str:
    data = load_settings()
    cpu = effective_cpu_mode()
    if cpu and data.get("runtime_cpu"):
        return "CPU (auto fallback)"
    if cpu:
        return "CPU"
    return "GPU"


def _glob_ckpt(pattern: str) -> str | None:
    if not CKPT_DIR.exists():
        return None
    for path in sorted(CKPT_DIR.glob(pattern)):
        if path.is_file() and not path.name.startswith("put_"):
            return path.name
    return None


def list_all_checkpoint_files() -> list[dict]:
    """All .safetensors in ComfyUI checkpoints (for picker UI)."""
    if not CKPT_DIR.exists():
        return []
    out: list[dict] = []
    for path in sorted(CKPT_DIR.glob("*.safetensors")):
        if not path.is_file() or path.name.startswith("put_"):
            continue
        lower = path.name.lower()
        if "flux" in lower:
            family = "Flux"
        elif "turbo" in lower:
            family = "SDXL Turbo"
        elif "realvis" in lower or "realistic_vision" in lower or "juggernaut" in lower or "lustify" in lower:
            family = "RealVis"
        elif "helloworld" in lower or "leosams" in lower:
            family = "HelloWorld XL"
        elif "dreamshaper" in lower:
            family = "DreamShaper"
        elif "epicrealism" in lower or "epic realism" in lower:
            family = "epiCRealism"
        elif "pony" in lower:
            family = "Pony XL"
        elif "xl" in lower or "sd_xl" in lower:
            family = "SDXL"
        elif "sd1" in lower or "v1-5" in lower or "dreamshaper" in lower:
            family = "SD 1.5"
        else:
            family = "Other"
        out.append({
            "name": path.name,
            "family": family,
            "size_mb": round(path.stat().st_size / (1024 * 1024)),
        })
    return out


def list_installed_checkpoints() -> dict[str, str | None]:
    return {
        "flux": _glob_ckpt("*flux*schnell*fp8*") or _glob_ckpt("*flux*schnell*"),
        "quality": _glob_ckpt("sd_xl_base_1.0.safetensors") or _glob_ckpt("*base*.safetensors"),
        "fast": _glob_ckpt("*turbo*.safetensors"),
    }


def resolve_checkpoint_name() -> str:
    env = os.getenv("JARVIS_COMFYUI_CKPT", "").strip()
    if env:
        return env

    data = load_settings()
    custom = (data.get("checkpoint_file") or "").strip()
    if custom:
        path = CKPT_DIR / Path(custom).name
        if path.is_file():
            return path.name

    installed = list_installed_checkpoints()
    choice = data.get("checkpoint", "quality")

    if choice == "fast":
        return installed["fast"] or installed["quality"] or "sd_xl_turbo_1.0_fp16.safetensors"

    if choice == "flux":
        return installed["flux"] or installed["quality"] or installed["fast"] or "flux1-schnell-fp8.safetensors"

    return installed["quality"] or installed["flux"] or installed["fast"] or "sd_xl_base_1.0.safetensors"


def checkpoint_label() -> str:
    name = resolve_checkpoint_name()
    lower = name.lower()
    if "flux" in lower and "schnell" in lower:
        return "Flux Schnell"
    if "flux" in lower:
        return "Flux"
    if "turbo" in lower:
        return "SDXL Turbo"
    if "base" in lower:
        return "SDXL 1.0"
    return Path(name).stem


def checkpoint_family() -> str:
    name = resolve_checkpoint_name().lower()
    if "flux" in name:
        return "flux"
    if "turbo" in name:
        return "sdxl_turbo"
    return "sdxl"


def get_settings_dict() -> dict:
    from jarvis.config import is_uncensored
    from jarvis.modules.image import prompt_model_name

    data = load_settings()
    cpu = effective_cpu_mode()
    installed = list_installed_checkpoints()
    all_files = list_all_checkpoint_files()
    rec_ckpt = recommended_uncensored_checkpoint()
    uncensored = is_uncensored()
    return {
        "mode": data["mode"],
        "checkpoint": data["checkpoint"],
        "checkpoint_file": data.get("checkpoint_file", ""),
        "runtime_cpu": data.get("runtime_cpu", False),
        "effective": "cpu" if cpu else "gpu",
        "label": mode_label(),
        "checkpoint_label": checkpoint_label(),
        "checkpoint_file_active": resolve_checkpoint_name(),
        "installed": installed,
        "all_checkpoints": all_files,
        "checkpoints_dir": str(CKPT_DIR),
        "comfyui_url": COMFYUI_URL,
        "auto_fallback": data["mode"] == "auto",
        "uncensored_mode": uncensored,
        "prompt_model": prompt_model_name(),
        "uncensored_auto_applied": bool(data.get("uncensored_auto_applied")),
        "uncensored_recommended_checkpoint": rec_ckpt,
        "uncensored_recommended_label": UNCENSORED_CHECKPOINT_LABELS.get(rec_ckpt or "", ""),
        "uncensored_checkpoints": list(UNCENSORED_CHECKPOINTS),
        "workflow_file": data.get("workflow_file", ""),
        "workflow_file_active": effective_workflow_path(),
        "install_scripts": {
            "quality": "./scripts/install-sdxl-base.sh",
            "flux": "./scripts/install-flux-schnell.sh",
            "nsfw": "./scripts/install-nsfw-checkpoints.sh",
        },
    }
