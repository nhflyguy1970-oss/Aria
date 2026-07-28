"""Video Generation — params, presets, shared pipeline, recovery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from jarvis.video_generation.enhance import preview_enhance
from jarvis.video_generation.fallback import recovery_options
from jarvis.video_generation.params import coerce_seed, normalize_params
from jarvis.video_generation.presets import BUILTINS, apply_preset_to_params, list_presets


def test_normalize_video_params():
    p = normalize_params(
        {
            "prompt": "a fox running",
            "engine": "ken_burns",
            "duration": 20,
            "fps": 30,
            "frames": 200,
            "enhance": "true",
            "negative_prompt": "blur",
        }
    )
    assert p["prompt"] == "a fox running"
    assert p["engine"] == "ken_burns"
    assert p["duration"] == 12.0  # capped
    assert p["fps"] == 16  # capped
    assert p["frames"] == 128  # capped
    assert p["enhance"] is True
    assert p["negative"] == "blur"


def test_coerce_seed():
    assert coerce_seed("random") is None
    assert coerce_seed(42) == 42


def test_builtin_video_presets():
    listed = list_presets()
    assert listed["ok"]
    ids = {i["id"] for i in listed["items"]}
    for key in BUILTINS:
        assert key in ids
    applied = apply_preset_to_params({"prompt": "hero"}, "landscape_pan")
    assert applied["engine"] == "ken_burns"
    assert applied["duration"] == 6


def test_preview_enhance_disabled():
    out = preview_enhance("ocean waves", enhance=False)
    assert out["ok"]
    assert out["original"] == out["enhanced"]
    assert out["enhance_applied"] is False


def test_recovery_options_vram():
    out = recovery_options("CUDA out of memory", gpu_failure=True)
    assert out["gpu_failure"]
    labels = [a["label"] for a in out["actions"]]
    assert any("Ken Burns" in x for x in labels)
    assert any("Mission Control" in x for x in labels)


def test_submit_video_requires_prompt():
    from jarvis.video_generation.engine import submit_video

    assert submit_video(None, {"prompt": ""})["ok"] is False


def test_submit_video_enqueues_generate_video():
    from jarvis.video_generation.engine import submit_video

    assistant = MagicMock()
    assistant._enqueue_media.return_value = {"ok": True, "job_id": "v1", "message": "queued"}
    out = submit_video(
        assistant,
        {"prompt": "sunset over water", "engine": "auto", "duration": 4, "enhance": False},
        source="studio",
    )
    assert out["ok"]
    assert out["stay_in_studio"] is True
    action, params, _msg = assistant._enqueue_media.call_args[0]
    assert action == "generate_video"
    assert params["prompt"] == "sunset over water"
    assert params["engine"] == "auto"
    assert params["duration"] == 4.0


def test_submit_storyboard_media_queue():
    from jarvis.video_generation.engine import submit_storyboard

    assistant = MagicMock()
    assistant._enqueue_media.return_value = {"ok": True, "job_id": "s1"}
    out = submit_storyboard(assistant, {"paths": ["a.png", "b.png"], "sec_per_slide": 2.5})
    assert out["ok"]
    assert assistant._enqueue_media.call_args[0][0] == "storyboard_video"
    assert out["action"] == "storyboard_video"


def test_media_handler_passes_video_params():
    from jarvis.handlers.media import MediaHandler

    assistant = MagicMock()
    assistant.video.generate.return_value = "/data/generated_videos/t.mp4"
    assistant.video.last_enhanced_prompt = "enhanced"
    assistant.video.last_negative_prompt = "neg"
    assistant.video.last_method = "ken_burns"
    assistant.video.last_clip_plan = {"fps": 8}
    assistant.video.last_seed = 11
    assistant.video.last_keyframe = ""
    assistant.video.last_fallback_reason = ""
    with patch("jarvis.video_settings.keyframe_checkpoint_label", return_value="ckpt"):
        with patch("jarvis.config.is_uncensored", return_value=False):
            with patch("jarvis.video_generation.metadata.mark_generation"):
                with patch("jarvis.video_generation.engine.save_last_settings"):
                    h = MediaHandler(assistant)
                    out = h.generate_video(
                        {
                            "prompt": "moon",
                            "engine": "ken_burns",
                            "duration": 3,
                            "fps": 8,
                            "enhance": False,
                            "seed": 11,
                        },
                        "",
                    )
    assert out["ok"]
    kw = assistant.video.generate.call_args.kwargs
    assert kw["engine"] == "ken_burns"
    assert kw["duration"] == 3.0
    assert kw["seed"] == 11


def test_storyboard_handler_invalidates_cache():
    from jarvis.handlers.media import MediaHandler

    assistant = MagicMock()
    with patch("jarvis.video_ops.resolve_storyboard_image", side_effect=lambda p: p):
        with patch("jarvis.video_ops.storyboard_ken_burns", return_value="/data/generated_videos/sb.mp4"):
            with patch("jarvis.cache_state.invalidate_video_gallery") as inv:
                with patch("jarvis.config.is_uncensored", return_value=False):
                    with patch("jarvis.video_generation.metadata.mark_generation"):
                        h = MediaHandler(assistant)
                        out = h.storyboard_video({"paths": ["/tmp/a.png"], "sec_per_slide": 2}, "")
    assert out["ok"]
    inv.assert_called()


def test_censored_uncensored_same_video_action():
    from jarvis.video_generation.engine import submit_video

    for unc in (False, True):
        assistant = MagicMock()
        assistant._enqueue_media.return_value = {"ok": True, "job_id": "x"}
        with patch("jarvis.config.is_uncensored", return_value=unc):
            submit_video(assistant, {"prompt": "scene"}, source="mcp")
        assert assistant._enqueue_media.call_args[0][0] == "generate_video"


def test_experimental_helpers():
    from jarvis.video_generation.experimental import prompt_coach, recommend_motion, shot_planner

    assert prompt_coach("cat").get("ok")
    assert recommend_motion("landscape pan")["recommended_preset"] == "landscape_pan"
    assert len(shot_planner("adventure", max_shots=3)["shots"]) == 3


def test_motion_clip_honors_engine_override():
    from jarvis import comfyui_video

    with patch.object(comfyui_video, "should_try_animatediff", return_value=False):
        with patch.object(
            comfyui_video,
            "generate_ken_burns_clip",
            return_value=("/tmp/v.mp4", "/tmp/k.png"),
        ) as kb:
            with patch("jarvis.services.ensure_comfyui_nvidia", return_value=True):
                path, key, method = comfyui_video.generate_motion_clip(
                    "test",
                    engine="ken_burns",
                    duration=3,
                    fps=8,
                    width=512,
                    height=512,
                    seed=99,
                )
    assert method == "ken_burns"
    assert path.endswith(".mp4")
    assert kb.called
    assert kb.call_args.kwargs.get("seed") == 99


def test_metadata_visibility(tmp_path, monkeypatch):
    from jarvis.video_generation import metadata as meta

    monkeypatch.setattr(meta, "META_FILE", tmp_path / "meta.json")
    meta.mark_generation("clip.mp4", prompt="p", method="ken_burns", uncensored=True, seed="5")
    with patch("jarvis.config.is_uncensored", return_value=False):
        assert meta.is_restricted_for_viewer("clip.mp4") is True
    with patch("jarvis.config.is_uncensored", return_value=True):
        assert meta.is_restricted_for_viewer("clip.mp4") is False
