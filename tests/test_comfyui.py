"""Tests for ComfyUI client helpers."""

from unittest.mock import patch

from jarvis import comfyui


def test_is_available_false_when_unreachable():
    with patch("urllib.request.urlopen", side_effect=OSError("down")):
        assert comfyui.is_available() is False


def test_generate_returns_error_when_unavailable():
    with patch("jarvis.comfyui.is_available", return_value=False), patch(
        "jarvis.services.ensure_comfyui", return_value=False,
    ):
        out = comfyui.generate("test prompt")
        assert out.startswith("ERROR:")
