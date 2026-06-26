from pathlib import Path

import pytest

from jarvis import comfyui_settings as cs


@pytest.fixture
def comfy_settings(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    ckpt_dir = tmp_path / "ComfyUI" / "models" / "checkpoints"
    ckpt_dir.mkdir(parents=True)
    monkeypatch.setattr(cs, "DATA_DIR", data_dir)
    monkeypatch.setattr(cs, "SETTINGS_FILE", data_dir / "comfyui_settings.json")
    monkeypatch.setattr(cs, "CKPT_DIR", ckpt_dir)
    monkeypatch.delenv("JARVIS_COMFYUI_CKPT", raising=False)
    return ckpt_dir


def test_save_checkpoint_clears_custom_file(comfy_settings):
    ckpt = comfy_settings / "custom.safetensors"
    ckpt.write_bytes(b"x" * 64)
    cs.save_checkpoint_file("custom.safetensors")
    assert cs.load_settings()["checkpoint_file"] == "custom.safetensors"

    cs.save_checkpoint("flux")
    data = cs.load_settings()
    assert data["checkpoint"] == "flux"
    assert "checkpoint_file" not in data


def test_resolve_checkpoint_prefers_custom_file(comfy_settings):
    (comfy_settings / "my_model.safetensors").write_bytes(b"x" * 64)
    cs.save_checkpoint("quality")
    cs.save_checkpoint_file("my_model.safetensors")
    assert cs.resolve_checkpoint_name() == "my_model.safetensors"


def test_resolve_checkpoint_preset_fast(comfy_settings):
    (comfy_settings / "sd_xl_turbo_1.0_fp16.safetensors").write_bytes(b"x" * 64)
    cs.save_checkpoint("fast")
    assert cs.resolve_checkpoint_name() == "sd_xl_turbo_1.0_fp16.safetensors"


def test_list_all_checkpoint_files(comfy_settings):
    (comfy_settings / "sd_xl_base_1.0.safetensors").write_bytes(b"x" * (1024 * 1024))
    files = cs.list_all_checkpoint_files()
    assert len(files) == 1
    assert files[0]["name"] == "sd_xl_base_1.0.safetensors"
    assert files[0]["family"] == "SDXL"


def test_save_checkpoint_file_rejects_missing(comfy_settings):
    with pytest.raises(ValueError, match="not found"):
        cs.save_checkpoint_file("missing.safetensors")


def test_get_settings_dict_includes_checkpoints(comfy_settings):
    (comfy_settings / "flux1-schnell-fp8.safetensors").write_bytes(b"x" * 64)
    cs.save_checkpoint("flux")
    data = cs.get_settings_dict()
    assert data["checkpoint"] == "flux"
    assert data["comfyui_url"].startswith("http")
    assert any(f["name"].startswith("flux") for f in data["all_checkpoints"])


def test_apply_uncensored_defaults(comfy_settings, monkeypatch):
    (comfy_settings / "RealVisXL_V5.0_fp16.safetensors").write_bytes(b"x" * 64)
    (comfy_settings / "ponyDiffusionV6XL_v6StartWithThisOne.safetensors").write_bytes(b"x" * 64)
    cs.apply_uncensored_defaults()
    data = cs.load_settings()
    assert data["checkpoint_file"] == "RealVisXL_V5.0_fp16.safetensors"
    assert data["uncensored_auto_applied"] is True


def test_clear_uncensored_auto_checkpoint(comfy_settings):
    (comfy_settings / "RealVisXL_V5.0_fp16.safetensors").write_bytes(b"x" * 64)
    cs.apply_uncensored_defaults()
    cs.clear_uncensored_auto_checkpoint()
    data = cs.load_settings()
    assert "checkpoint_file" not in data
    assert "uncensored_auto_applied" not in data
