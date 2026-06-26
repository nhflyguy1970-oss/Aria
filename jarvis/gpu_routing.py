"""GPU vendor preference — NVIDIA CUDA vs AMD ROCm vs hybrid."""

from __future__ import annotations

import os
import subprocess


def gpu_preference() -> str:
    """Return nvidia | amd | both | auto."""
    raw = (os.getenv("JARVIS_GPU_PREFER") or "auto").strip().lower()
    if raw in ("both", "hybrid"):
        return "both"
    if raw in ("nvidia", "amd", "auto"):
        return raw
    return "auto"


def _run(cmd: list[str], timeout: float = 8) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return ""


def parse_nvidia_smi() -> dict:
    """Return NVIDIA GPU info from nvidia-smi, or empty dict."""
    out = _run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,driver_version,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    if not out.strip() or "failed" in out.lower() or "not found" in out.lower():
        return {}
    line = out.strip().splitlines()[0]
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return {}
    try:
        vram_mb = int(float(parts[1]))
        vram_used_mb = int(float(parts[2])) if len(parts) > 2 else 0
    except ValueError:
        vram_mb = 0
        vram_used_mb = 0
    return {
        "name": parts[0],
        "vram_mb": vram_mb,
        "vram_used_mb": vram_used_mb,
        "free_vram_mb": max(0, vram_mb - vram_used_mb),
        "driver": parts[3] if len(parts) > 3 else "",
        "nvidia_available": True,
    }


def nvidia_available() -> bool:
    if os.getenv("JARVIS_NVIDIA_AVAILABLE", "").strip().lower() in ("0", "false", "no"):
        return False
    return bool(parse_nvidia_smi())


def ctranslate2_cuda_count() -> int:
    try:
        import ctranslate2

        return int(ctranslate2.get_cuda_device_count())
    except Exception:
        return 0


def torch_backend() -> str:
    """cuda_nvidia | cuda_rocm | cpu"""
    try:
        import torch

        if not torch.cuda.is_available():
            return "cpu"
        if getattr(torch.version, "hip", None):
            return "cuda_rocm"
        try:
            name = (torch.cuda.get_device_name(0) or "").lower()
        except Exception:
            name = ""
        if any(token in name for token in ("nvidia", "geforce", "rtx", "quadro", "tesla")):
            return "cuda_nvidia"
        if any(token in name for token in ("radeon", "amd")):
            return "cuda_rocm"
        if nvidia_available():
            return "cuda_nvidia"
        return "cuda_nvidia"
    except ImportError:
        return "cpu"


def resolve_torch_device() -> str:
    forced = (os.getenv("JARVIS_TORCH_DEVICE") or "").strip().lower()
    if forced in ("cuda", "cpu", "mps"):
        if forced == "cuda" and torch_backend() == "cuda_rocm" and gpu_preference() == "nvidia":
            return "cpu"
        return forced
    pref = gpu_preference()
    backend = torch_backend()
    if pref == "amd":
        return "cuda" if backend == "cuda_rocm" else "cpu"
    if pref in ("nvidia", "both", "auto"):
        if backend == "cuda_nvidia":
            return "cuda"
        return "cpu"
    return "cpu"


def resolve_whisper_device() -> str:
    forced = (os.getenv("JARVIS_WHISPER_DEVICE") or "").strip().lower()
    if forced in ("cuda", "cpu"):
        return forced
    pref = gpu_preference()
    if ctranslate2_cuda_count() > 0 and pref in ("nvidia", "both", "auto"):
        if pref == "both" and os.getenv("JARVIS_WHISPER_ON_GPU", "1") != "1":
            return "cpu"
        return "cuda"
    return "cpu"


def resolve_functiongemma_device() -> str:
    forced = (os.getenv("JARVIS_FUNCTIONGEMMA_DEVICE") or "auto").strip().lower()
    if forced in ("cuda", "cpu"):
        if forced == "cuda" and torch_backend() != "cuda_nvidia":
            return "cpu"
        return forced
    backend = torch_backend()
    if backend == "cuda_rocm" and nvidia_available():
        return "cpu"
    if gpu_preference() in ("nvidia", "both", "auto") and backend == "cuda_nvidia":
        return "cuda"
    if gpu_preference() == "amd" and backend == "cuda_rocm":
        return "cuda"
    if gpu_preference() == "auto" and backend == "cuda_rocm":
        return "cpu"
    return "cpu"


def gpu_env_for_subprocess() -> dict[str, str]:
    """Env overrides for child processes (Ollama, ComfyUI, etc.)."""
    env: dict[str, str] = {}
    pref = gpu_preference()
    if pref in ("nvidia", "both", "auto") and nvidia_available():
        idx = (os.getenv("JARVIS_CUDA_DEVICE") or "0").strip()
        env["CUDA_VISIBLE_DEVICES"] = idx
        env.setdefault("HIP_VISIBLE_DEVICES", "-1")
        for rocm_key in (
            "HSA_OVERRIDE_GFX_VERSION",
            "ROCR_VISIBLE_DEVICES",
            "GPU_DEVICE_ORDINAL",
            "HIP_FORCE_DEV_KERNARG",
        ):
            env[rocm_key] = ""
        return env
    if pref == "amd":
        env.pop("CUDA_VISIBLE_DEVICES", None)
    return env


def nvidia_compute_active() -> bool:
    """True when NVIDIA is the preferred compute GPU and is available."""
    return gpu_preference() in ("nvidia", "both", "auto") and nvidia_available()


def compute_vram_mb() -> int:
    """VRAM of the compute GPU (NVIDIA when preferred, else display/ROCm)."""
    if nvidia_compute_active():
        nv = parse_nvidia_smi()
        if nv.get("vram_mb"):
            return int(nv["vram_mb"])
    from jarvis.gpu import detect_gpu

    return int(detect_gpu(force=True).get("vram_mb") or 0)


def is_compute_low_vram(threshold_mb: int = 10240) -> bool:
    vram = compute_vram_mb()
    return 0 < vram <= threshold_mb


def apply_gpu_env_to_os() -> None:
    """Apply subprocess GPU routing to the current process environment."""
    pref = gpu_preference()
    if nvidia_compute_active():
        for key, value in gpu_env_for_subprocess().items():
            if value == "":
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    elif pref == "nvidia":
        os.environ.pop("HSA_OVERRIDE_GFX_VERSION", None)


def routing_status() -> dict:
    nvidia = parse_nvidia_smi()
    return {
        "preference": gpu_preference(),
        "nvidia": nvidia,
        "nvidia_available": bool(nvidia),
        "ctranslate2_cuda_devices": ctranslate2_cuda_count(),
        "torch_backend": torch_backend(),
        "resolved_torch_device": resolve_torch_device(),
        "resolved_whisper_device": resolve_whisper_device(),
        "resolved_functiongemma_device": resolve_functiongemma_device(),
        "nvidia_compute_active": nvidia_compute_active(),
        "compute_vram_mb": compute_vram_mb(),
        "compute_low_vram": is_compute_low_vram(),
    }
