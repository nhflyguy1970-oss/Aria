"""Coordinate GPU VRAM between Ollama, ComfyUI, and PyTorch on 8GB cards."""

from __future__ import annotations

import os

from jarvis.gpu import detect_gpu, is_low_vram
from jarvis.ml_memory import release_torch_memory, unload_ollama_models


def vram_guard_enabled() -> bool:
    return os.getenv("JARVIS_VRAM_GUARD", "1").lower() not in ("0", "false", "no", "off")


def prepare_for_comfyui() -> dict:
    """Unload Ollama + PyTorch cache before ComfyUI image work."""
    if not vram_guard_enabled():
        return {"ok": True, "skipped": True}
    unloaded = unload_ollama_models()
    release_torch_memory()
    return {"ok": True, "unloaded_ollama": unloaded, "released_torch": True}


def prepare_for_torch_ml() -> dict:
    """Free VRAM before MusicGen / diarization / other torch jobs."""
    if not vram_guard_enabled():
        return {"ok": True, "skipped": True}
    unloaded = unload_ollama_models()
    release_torch_memory()
    return {"ok": True, "unloaded_ollama": unloaded, "released_torch": True}


def free_vram() -> dict:
    """Manual / API: drop Ollama models and clear PyTorch cache."""
    unloaded = unload_ollama_models()
    release_torch_memory()
    gpu = detect_gpu()
    return {
        "ok": True,
        "unloaded_ollama": unloaded,
        "released_torch": True,
        "vram_mb": gpu.get("vram_mb"),
        "ollama_using_gpu": gpu.get("ollama_using_gpu"),
    }


def recommendations() -> list[str]:
    """Actionable tips for the current machine."""
    gpu = detect_gpu()
    vram = int(gpu.get("vram_mb") or 0)
    tips: list[str] = []
    try:
        from jarvis.gpu_routing import nvidia_compute_active

        if nvidia_compute_active():
            name = gpu.get("compute_gpu") or gpu.get("name") or "NVIDIA GPU"
            tips.append(f"Compute GPU: {name} — ComfyUI image/video use NVIDIA when started via ARIA.")
    except Exception:
        pass
    if is_low_vram(10240):
        tips.append("Use 7B chat/code models (not 14B+) — switch profile to Gaming or run optimize-rx7600-8gb.sh")
        tips.append("Vision: moondream or llama3.2-vision:11b — avoid llava:13b on 8GB")
        tips.append("Whisper: small on CPU (AMD) — set JARVIS_WHISPER_MODEL=small")
        tips.append("Unload Ollama before ComfyUI/Song Studio (JARVIS_VRAM_GUARD=1, default on)")
    if gpu.get("vendor") == "amd" and gpu.get("rocm_available") and gpu.get("compute_vendor") != "nvidia":
        tips.append("RX 7600: keep HSA_OVERRIDE_GFX_VERSION=11.0.0 for ComfyUI GPU")
    if gpu.get("ollama_using_gpu") and vram and vram <= 10240:
        tips.append("Ollama is using GPU — click Free VRAM before image gen if you hit OOM")
    if not tips:
        tips.append("VRAM looks comfortable — JARVIS_VRAM_GUARD still helps when mixing Ollama + ComfyUI")
    return tips


def status() -> dict:
    gpu = detect_gpu()
    return {
        "guard_enabled": vram_guard_enabled(),
        "low_vram": is_low_vram(10240),
        "vram_mb": gpu.get("vram_mb"),
        "gpu_name": gpu.get("name"),
        "compute_gpu": gpu.get("compute_gpu") or gpu.get("name"),
        "display_gpu": gpu.get("display_gpu"),
        "ollama_using_gpu": gpu.get("ollama_using_gpu"),
        "ollama_processor": gpu.get("ollama_processor"),
        "recommendations": recommendations(),
    }
