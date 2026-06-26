"""Tests for 8GB hardware tuning helpers."""

from __future__ import annotations

from jarvis.hardware_tune import ENV_8GB_DEFAULTS, patch_env_file


def test_patch_env_file_updates_and_appends(tmp_path):
    env = tmp_path / "jarvis.env"
    env.write_text('export JARVIS_WHISPER_MODEL="base"\n', encoding="utf-8")
    changed = patch_env_file(env, {"JARVIS_WHISPER_MODEL": "small", "JARVIS_VRAM_GUARD": "1"})
    text = env.read_text(encoding="utf-8")
    assert 'JARVIS_WHISPER_MODEL="small"' in text
    assert 'JARVIS_VRAM_GUARD="1"' in text
    assert "JARVIS_WHISPER_MODEL" in changed


def test_env_defaults_keys():
    assert ENV_8GB_DEFAULTS["JARVIS_WHISPER_MODEL"] == "small"
    assert ENV_8GB_DEFAULTS["JARVIS_VRAM_GUARD"] == "1"
