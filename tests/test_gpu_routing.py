"""Tests for NVIDIA / AMD GPU routing."""

from __future__ import annotations


def test_parse_nvidia_smi(monkeypatch):
    from jarvis import gpu_routing

    def fake_run(cmd, timeout=8):
        if "nvidia-smi" in cmd[0]:
            return "NVIDIA GeForce RTX 3060, 12288, 1024, 595.71.05, 12\n"
        return ""

    monkeypatch.setattr(gpu_routing, "_run", fake_run)
    info = gpu_routing.parse_nvidia_smi()
    assert info["nvidia_available"] is True
    assert info["vram_mb"] == 12288
    assert "RTX 3060" in info["name"]


def test_resolve_whisper_cuda_when_nvidia(monkeypatch):
    from jarvis import gpu_routing

    monkeypatch.setenv("JARVIS_GPU_PREFER", "nvidia")
    monkeypatch.setenv("JARVIS_WHISPER_DEVICE", "")
    monkeypatch.setattr(gpu_routing, "ctranslate2_cuda_count", lambda: 1)
    assert gpu_routing.resolve_whisper_device() == "cuda"


def test_resolve_functiongemma_cpu_when_rocm_and_nvidia_pref(monkeypatch):
    from jarvis import gpu_routing

    monkeypatch.setenv("JARVIS_GPU_PREFER", "nvidia")
    monkeypatch.setenv("JARVIS_FUNCTIONGEMMA_DEVICE", "auto")
    monkeypatch.setattr(gpu_routing, "torch_backend", lambda: "cuda_rocm")
    assert gpu_routing.resolve_functiongemma_device() == "cpu"


def test_detect_gpu_nvidia_vendor(monkeypatch):
    from jarvis.gpu import detect_gpu

    monkeypatch.setattr(
        "jarvis.gpu_routing.parse_nvidia_smi",
        lambda: {
            "name": "NVIDIA GeForce RTX 3060",
            "vram_mb": 12288,
            "vram_used_mb": 512,
            "free_vram_mb": 11776,
            "driver": "595.71",
            "nvidia_available": True,
        },
    )
    monkeypatch.setattr("jarvis.gpu_routing.gpu_preference", lambda: "nvidia")
    monkeypatch.setattr("jarvis.gpu_routing.nvidia_available", lambda: True)
    monkeypatch.setattr("jarvis.gpu._run", lambda cmd, timeout=10: "")
    info = detect_gpu(force=True)
    assert info["vendor"] == "nvidia"
    assert info["nvidia_available"] is True
    assert info["vram_mb"] == 12288
