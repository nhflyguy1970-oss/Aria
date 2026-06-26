"""Tests for NVIDIA / AMD GPU routing."""

from __future__ import annotations

import jarvis.gpu_routing as gpu_routing


def test_parse_nvidia_smi(monkeypatch):
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
    monkeypatch.setenv("JARVIS_GPU_PREFER", "nvidia")
    monkeypatch.setenv("JARVIS_WHISPER_DEVICE", "")
    monkeypatch.setattr(gpu_routing, "ctranslate2_cuda_count", lambda: 1)
    assert gpu_routing.resolve_whisper_device() == "cuda"


def test_resolve_functiongemma_cpu_when_rocm_and_nvidia_pref(monkeypatch):
    monkeypatch.setenv("JARVIS_GPU_PREFER", "nvidia")
    monkeypatch.setenv("JARVIS_FUNCTIONGEMMA_DEVICE", "auto")
    monkeypatch.setattr(gpu_routing, "torch_backend", lambda: "cuda_rocm")
    assert gpu_routing.resolve_functiongemma_device() == "cpu"


def test_resolve_functiongemma_cpu_when_rocm_and_nvidia_available(monkeypatch):
    monkeypatch.setenv("JARVIS_GPU_PREFER", "amd")
    monkeypatch.setenv("JARVIS_FUNCTIONGEMMA_DEVICE", "auto")
    monkeypatch.setattr(gpu_routing, "torch_backend", lambda: "cuda_rocm")
    monkeypatch.setattr(gpu_routing, "nvidia_available", lambda: True)
    assert gpu_routing.resolve_functiongemma_device() == "cpu"


def test_gpu_env_for_subprocess_nvidia(monkeypatch):
    monkeypatch.setenv("JARVIS_GPU_PREFER", "nvidia")
    monkeypatch.setenv("JARVIS_CUDA_DEVICE", "0")
    monkeypatch.setattr(gpu_routing, "nvidia_available", lambda: True)
    env = gpu_routing.gpu_env_for_subprocess()
    assert env["CUDA_VISIBLE_DEVICES"] == "0"
    assert env["HIP_VISIBLE_DEVICES"] == "-1"
