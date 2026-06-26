"""AnimateDiff integration and Ken Burns fallback."""

from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis import comfyui_animatediff as ad
from jarvis import video_settings as vs


@pytest.fixture
def video_env(tmp_path, monkeypatch):
    from jarvis import comfyui_settings as cs

    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    motion_dir = tmp_path / "animatediff_models"
    motion_dir.mkdir()
    (ckpt_dir / "Realistic_Vision_V6.0_NV_B1_fp16.safetensors").write_bytes(b"x")
    (ckpt_dir / "sd_xl_base_1.0.safetensors").write_bytes(b"x")
    (motion_dir / "mm_sd_v15_v2.ckpt").write_bytes(b"x" * 100)

    monkeypatch.setattr(vs, "SETTINGS_FILE", tmp_path / "video_settings.json")
    monkeypatch.setattr(vs, "DATA_DIR", tmp_path)
    monkeypatch.setattr(vs, "CKPT_DIR", ckpt_dir)
    monkeypatch.setattr(cs, "CKPT_DIR", ckpt_dir)
    monkeypatch.setattr(ad, "COMFY_ROOT", tmp_path)
    monkeypatch.setattr(ad, "CKPT_DIR", ckpt_dir)

    def _motion():
        p = motion_dir / "mm_sd_v15_v2.ckpt"
        return p if p.is_file() else None

    monkeypatch.setattr(ad, "motion_module_path", _motion)
    monkeypatch.setattr(ad, "motion_module_name", lambda: "mm_sd_v15_v2.ckpt")
    monkeypatch.setattr(ad, "custom_nodes_installed", lambda: True)
    monkeypatch.setattr(
        ad,
        "_pick_node",
        lambda *names: names[0] if names else None,
    )
    return tmp_path


def test_resolve_checkpoint_prefers_sd15(video_env):
    assert ad.resolve_checkpoint() == "Realistic_Vision_V6.0_NV_B1_fp16.safetensors"


def test_animatediff_workflow_builds(video_env):
    wf = ad._animatediff_workflow(
        "a cat walking",
        negative_prompt="blurry",
        width=512,
        height=512,
        frames=16,
        fps=8,
        checkpoint="Realistic_Vision_V6.0_NV_B1_fp16.safetensors",
        motion="mm_sd_v15_v2.ckpt",
    )
    assert wf is not None
    assert wf["7"]["inputs"]["model"] == ["10", 0]
    assert wf["10"]["class_type"] == "ADE_UseEvolvedSampling"
    assert wf["4"]["inputs"]["text"] == "a cat walking"


def test_readiness_lists_missing_nodes(tmp_path, monkeypatch):
    monkeypatch.setattr(ad, "COMFY_ROOT", tmp_path)
    monkeypatch.setattr(ad, "custom_nodes_installed", lambda: False)
    monkeypatch.setattr(ad, "motion_module_path", lambda: None)
    monkeypatch.setattr(ad, "resolve_checkpoint", lambda: None)
    monkeypatch.setattr(ad.comfyui, "is_available", lambda: False)
    status = ad.readiness()
    assert not status["ready"]
    assert status["missing"]


def test_auto_engine_skips_when_not_ready(video_env, monkeypatch):
    monkeypatch.setattr(vs, "effective_engine", lambda: "auto")
    monkeypatch.setattr(ad, "is_ready", lambda: False)
    assert vs.should_try_animatediff("auto") is False


def test_generate_motion_clip_fallback_on_animatediff_error(video_env, monkeypatch):
    from jarvis import comfyui_video as cv

    monkeypatch.setattr(vs, "effective_engine", lambda: "auto")
    monkeypatch.setattr("jarvis.comfyui_animatediff.is_ready", lambda: True)
    monkeypatch.setattr(
        "jarvis.comfyui_animatediff.generate",
        lambda *a, **k: ("ERROR: GPU OOM", ""),
    )
    monkeypatch.setattr(
        cv,
        "generate_ken_burns_clip",
        lambda *a, **k: ("/tmp/out.mp4", "/tmp/key.png"),
    )
    monkeypatch.setattr(vs, "effective_duration", lambda: 4.0)
    monkeypatch.setattr(vs, "effective_fps", lambda: 8)
    monkeypatch.setattr(vs, "effective_size", lambda: (768, 768))
    monkeypatch.setattr(vs, "effective_animatediff_frames", lambda d, f: 16)
    monkeypatch.setattr(vs, "effective_animatediff_size", lambda: (512, 512))

    path, key, method = cv.generate_motion_clip("test prompt")
    assert path == "/tmp/out.mp4"
    assert method == "ken_burns"
    assert cv.last_fallback_reason()
