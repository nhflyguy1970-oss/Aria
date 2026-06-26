"""Tests for config profiles."""

import pytest
from jarvis.profiles import PROFILE_DEFS, apply_profile, list_profiles, web_search_disabled


def test_list_profiles():
    names = {p["id"] for p in list_profiles()}
    assert names == set(PROFILE_DEFS.keys())


def test_apply_offline_disables_web_search(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.config.CHAT_SETTINGS_FILE", data_dir / "chat_settings.json")
    monkeypatch.setattr("jarvis.profiles._load_chat_settings", __import__("jarvis.config", fromlist=["config"])._load_chat_settings)
    monkeypatch.setattr("jarvis.profiles._write_chat_settings", __import__("jarvis.config", fromlist=["config"])._write_chat_settings)
    monkeypatch.setattr("jarvis.profiles.save_personality_preset", lambda p: None)
    monkeypatch.setattr("jarvis.profiles.save_vision_quality", lambda m: None)
    monkeypatch.setattr("jarvis.profiles.apply_preset", lambda p: {"ok": True})
    monkeypatch.setattr("jarvis.comfyui_settings.save_mode", lambda m: {"ok": True})
    result = apply_profile("offline")
    assert result["profile"] == "offline"
    assert web_search_disabled() is True


def test_apply_unknown_raises():
    with pytest.raises(ValueError):
        apply_profile("nope")
