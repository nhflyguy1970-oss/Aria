"""Pick best torch device (CUDA / ROCm / CPU) for audio ML."""

from __future__ import annotations

import os


def torch_device() -> str:
    """Return 'cuda', 'cpu', or 'mps' for PyTorch (MusicGen, pyannote, etc.)."""
    try:
        from jarvis.gpu_routing import resolve_torch_device

        return resolve_torch_device()
    except Exception:
        pass
    forced = os.getenv("JARVIS_TORCH_DEVICE", "").strip().lower()
    if forced in ("cuda", "cpu", "mps"):
        return forced
    return "cpu"


def whisper_device() -> str:
    """Device for faster-whisper (CTranslate2). NVIDIA CUDA only — not PyTorch ROCm."""
    try:
        from jarvis.gpu_routing import resolve_whisper_device

        return resolve_whisper_device()
    except Exception:
        pass
    forced = os.getenv("JARVIS_WHISPER_DEVICE", "").strip().lower()
    if forced in ("cuda", "cpu", "auto"):
        return forced if forced != "auto" else "cpu"
    return "cpu"


def device_info() -> dict:
    from jarvis.gpu import detect_gpu

    try:
        from jarvis.gpu_routing import routing_status

        routing = routing_status()
    except Exception:
        routing = {}

    gpu = detect_gpu()
    dev = torch_device()
    whisper = whisper_device()
    hint = routing.get("torch_backend", "")
    if (
        gpu.get("vendor") == "amd"
        and os.getenv("JARVIS_GPU_PREFER", "").strip().lower() == "nvidia"
    ):
        hint = (
            "JARVIS_GPU_PREFER=nvidia: PyTorch uses CPU unless CUDA PyTorch is installed; "
            "Whisper uses NVIDIA via CTranslate2; Ollama needs CUDA build (not ROCm)."
        )
    elif dev == "cpu":
        hint = "Using CPU — install CUDA PyTorch for NVIDIA compute or ROCm for AMD"
    return {
        "device": dev,
        "whisper_device": whisper,
        "gpu": gpu,
        "routing": routing,
        "hint": hint,
    }
