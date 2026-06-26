"""Tests for VRAM guard coordination."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.vram_guard import free_vram, prepare_for_comfyui, recommendations, vram_guard_enabled


def test_vram_guard_enabled_default():
    assert vram_guard_enabled() is True


@patch("jarvis.vram_guard.unload_ollama_models", return_value=["qwen2.5:7b"])
@patch("jarvis.vram_guard.release_torch_memory")
def test_prepare_for_comfyui(mock_release, mock_unload):
    out = prepare_for_comfyui()
    assert out["ok"] is True
    mock_unload.assert_called_once()
    mock_release.assert_called_once()


@patch("jarvis.vram_guard.detect_gpu", return_value={"vram_mb": 8176, "vendor": "amd", "rocm_available": True})
def test_recommendations_low_vram(mock_gpu):
    tips = recommendations()
    assert any("7B" in t or "7b" in t.lower() for t in tips)


@patch("jarvis.vram_guard.unload_ollama_models", return_value=[])
@patch("jarvis.vram_guard.release_torch_memory")
@patch("jarvis.vram_guard.detect_gpu", return_value={"vram_mb": 8192})
def test_free_vram(mock_gpu, mock_release, mock_unload):
    out = free_vram()
    assert out["ok"] is True
    assert out["released_torch"] is True
