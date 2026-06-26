"""Video keyframe checkpoint settings (uncensored parity with image)."""

from pathlib import Path

import pytest

from jarvis import video_settings as vs


@pytest.fixture
def video_settings(tmp_path, monkeypatch):
    from jarvis import comfyui_settings as cs

    monkeypatch.setattr(vs, "SETTINGS_FILE", tmp_path / "video_settings.json")
    monkeypatch.setattr(vs, "DATA_DIR", tmp_path)
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    monkeypatch.setattr(cs, "CKPT_DIR", ckpt_dir)
    monkeypatch.setattr(vs, "CKPT_DIR", ckpt_dir)
    (ckpt_dir / "sd_xl_base_1.0.safetensors").write_bytes(b"x")
    (ckpt_dir / "RealVisXL_V5.0_fp16.safetensors").write_bytes(b"x")
    return vs


def test_resolve_keyframe_preset(video_settings):
    vs.save_keyframe_preset("quality")
    assert vs.resolve_keyframe_checkpoint() == "sd_xl_base_1.0.safetensors"


def test_apply_uncensored_defaults(video_settings):
    vs.apply_uncensored_defaults()
    data = vs.get_settings()
    assert data["keyframe_checkpoint"] == "RealVisXL_V5.0_fp16.safetensors"
    assert data["uncensored_auto_applied"] is True


def test_clear_uncensored_auto(video_settings):
    vs.apply_uncensored_defaults()
    vs.clear_uncensored_auto()
    data = vs.get_settings()
    assert not data.get("keyframe_checkpoint")
    assert not data.get("uncensored_auto_applied")
