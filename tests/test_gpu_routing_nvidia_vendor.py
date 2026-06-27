"""NVIDIA vendor detection in detect_gpu."""

from __future__ import annotations


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
