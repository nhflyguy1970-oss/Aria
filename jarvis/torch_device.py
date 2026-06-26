"""Pick best torch device (CUDA / ROCm / CPU) for audio ML."""

from __future__ import annotations

import os


def _rocm_pytorch_gpu() -> bool:
    """True when PyTorch ROCm exposes a GPU via the cuda API."""
    try:
        import torch

        if not torch.cuda.is_available():
            return False
        return bool(getattr(torch.version, "hip", None))
    except ImportError:
        return False


def torch_device() -> str:
    """Return 'cuda', 'cpu', or env override for PyTorch (MusicGen, pyannote, etc.)."""
    forced = os.getenv("JARVIS_TORCH_DEVICE", "").strip().lower()
    if forced in ("cuda", "cpu", "mps"):
        return forced
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def whisper_device() -> str:
    """Device for faster-whisper (CTranslate2). NVIDIA CUDA only — not PyTorch ROCm."""
    forced = os.getenv("JARVIS_WHISPER_DEVICE", "").strip().lower()
    if forced in ("cuda", "cpu", "auto"):
        return forced
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def device_info() -> dict:
    from jarvis.gpu import detect_gpu

    gpu = detect_gpu()
    dev = torch_device()
    whisper = whisper_device()
    hint = ""
    if gpu.get("vendor") == "amd" and gpu.get("rocm_available"):
        if dev == "cuda" and _rocm_pytorch_gpu():
            hint = (
                "PyTorch ROCm uses device name 'cuda' on AMD — that is normal. "
                "Whisper uses CPU unless CTranslate2 has NVIDIA CUDA."
            )
        elif dev == "cpu":
            hint = "Using CPU — install ROCm PyTorch for faster MusicGen/diarization"
    elif dev == "cpu":
        hint = "Using CPU — install CUDA/ROCm PyTorch for faster MusicGen/Whisper"
    return {
        "device": dev,
        "whisper_device": whisper,
        "gpu": gpu,
        "hint": hint,
    }
