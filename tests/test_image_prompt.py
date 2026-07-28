"""Prompt processing, enhancement, params, presets, and shared pipeline tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from jarvis.image_generation.enhance import preview_enhance
from jarvis.image_generation.fallback import recovery_options
from jarvis.image_generation.params import ASPECT_PRESETS, coerce_seed, normalize_params
from jarvis.image_generation.presets import BUILTINS, apply_preset_to_params, list_presets
from jarvis.modules.image import ImageEngine, normalize_image_prompt


def test_normalize_image_prompt_strips_generate_prefix():
    assert "cat" in normalize_image_prompt("generate an image of a cat").lower()


def test_coerce_seed_random_and_int():
    assert coerce_seed(None, randomize=True) is None
    assert coerce_seed("random") is None
    assert coerce_seed(42) == 42
    assert coerce_seed("99") == 99


def test_normalize_params_aspect_and_negative():
    p = normalize_params(
        {
            "prompt": "a fox",
            "negative_prompt": "blurry",
            "aspect_ratio": "portrait",
            "steps": "20",
            "cfg": "7",
            "enhance": "true",
            "variations": 9,
        }
    )
    assert p["prompt"] == "a fox"
    assert p["negative"] == "blurry"
    assert p["width"] == ASPECT_PRESETS["portrait"][0]
    assert p["height"] == ASPECT_PRESETS["portrait"][1]
    assert p["steps"] == 20
    assert p["cfg"] == 7.0
    assert p["enhance"] is True
    assert p["variations"] == 4  # capped


def test_reuse_seed():
    p = normalize_params({"prompt": "x", "reuse_seed": True, "last_seed": 12345})
    assert p["seed"] == 12345


def test_builtin_presets_complete():
    listed = list_presets()
    assert listed["ok"]
    ids = {i["id"] for i in listed["items"]}
    for key in BUILTINS:
        assert key in ids
    applied = apply_preset_to_params({"prompt": "hero"}, "photoreal_portrait")
    assert applied["aspect_ratio"] == "portrait"
    assert "photorealistic" in applied["prompt"].lower() or "portrait" in applied["prompt"].lower()


def test_preview_enhance_disabled_is_identity():
    out = preview_enhance("a red bird", enhance=False)
    assert out["ok"]
    assert out["original"] == out["enhanced"]
    assert out["enhance_applied"] is False


def test_preview_enhance_with_prepare():
    with patch.object(ImageEngine, "prepare_prompt", return_value={"positive": "enhanced bird", "negative": "blur"}):
        out = preview_enhance("bird", enhance=True)
    assert out["enhanced"] == "enhanced bird"
    assert out["changed"] is True


def test_recovery_options_gpu():
    out = recovery_options("CUDA out of memory", gpu_failure=True)
    assert out["gpu_failure"]
    labels = [a["label"] for a in out["actions"]]
    assert "Retry on CPU" in labels
    assert any("Mission Control" in a["label"] for a in out["actions"])


def test_image_engine_honors_negative_and_seed():
    eng = ImageEngine()
    with patch("jarvis.comfyui.generate", return_value="ERROR: skip file copy") as gen:
        result = eng.generate(
            "test scene",
            enhance=False,
            negative_prompt="no watermark",
            seed=4242,
            steps=12,
            cfg=5.5,
            width=512,
            height=512,
        )
    assert result.startswith("ERROR:")
    call_kw = gen.call_args.kwargs
    assert call_kw.get("seed") == 4242
    assert call_kw.get("steps") == 12
    assert call_kw.get("cfg") == 5.5
    assert call_kw.get("negative_prompt") == "no watermark"


def test_submit_generation_requires_prompt():
    from jarvis.image_generation.engine import submit_generation

    out = submit_generation(None, {"prompt": ""})
    assert out["ok"] is False


def test_submit_generation_enqueues_same_action():
    from jarvis.image_generation.engine import submit_generation

    assistant = MagicMock()
    assistant._enqueue_media.return_value = {"ok": True, "job_id": "j1", "message": "queued"}
    out = submit_generation(
        assistant,
        {"prompt": "a lighthouse", "negative": "blur", "seed": 7, "enhance": False},
        source="gallery",
    )
    assert out["ok"]
    assert out["job_id"] == "j1"
    assert out["stay_in_gallery"] is True
    action, params, _msg = assistant._enqueue_media.call_args[0]
    assert action == "generate_image"
    assert params["prompt"] == "a lighthouse"
    assert params["negative"] == "blur"
    assert params["seed"] == 7


def test_media_handler_passes_params():
    from jarvis.handlers.media import MediaHandler

    assistant = MagicMock()
    assistant.image.generate.return_value = "/data/generated/t.png"
    assistant.image.last_enhanced_prompt = "enhanced"
    assistant.image.last_negative_prompt = "neg"
    assistant.image.last_seed = 99
    with patch("jarvis.prompt_history.add_entry"):
        with patch("jarvis.gallery_product.metadata.mark_generation") as mark:
            with patch("jarvis.config.is_uncensored", return_value=False):
                with patch("jarvis.comfyui_settings.checkpoint_label", return_value="test"):
                    with patch("jarvis.image_generation.engine.save_last_settings"):
                        h = MediaHandler(assistant)
                        out = h.generate_image(
                            {
                                "prompt": "moon",
                                "negative": "fog",
                                "enhance": False,
                                "seed": 99,
                                "steps": 8,
                            },
                            "",
                        )
    assert out["ok"]
    assert out.get("seed") == 99
    call_kw = assistant.image.generate.call_args.kwargs
    assert call_kw["negative_prompt"] == "fog"
    assert call_kw["seed"] == 99
    assert call_kw["steps"] == 8
    mark.assert_called()
    assert mark.call_args.kwargs.get("seed") == "99"


def test_fallback_comfyui_to_cpu_exists():
    from jarvis.services import fallback_comfyui_to_cpu

    assert callable(fallback_comfyui_to_cpu)


def test_gpu_failure_offers_recovery_message():
    from jarvis import comfyui

    with patch.object(comfyui, "_generate_once", return_value="ERROR: HIP error invalid device function"):
        with patch("jarvis.comfyui_settings.auto_fallback_enabled", return_value=True):
            with patch("jarvis.comfyui_settings.effective_cpu_mode", return_value=False):
                with patch("jarvis.services.fallback_comfyui_to_cpu", return_value=False):
                    result = comfyui.generate("x", width=64, height=64)
    assert "ERROR" in result
    assert "Mission Control" in result or "CPU" in result


def test_censored_uncensored_same_enqueue_path():
    """Policy must not fork the queue action."""
    from jarvis.image_generation.engine import submit_generation

    for unc in (True, False):
        assistant = MagicMock()
        assistant._enqueue_media.return_value = {"ok": True, "job_id": f"j-{unc}"}
        with patch("jarvis.config.is_uncensored", return_value=unc):
            out = submit_generation(assistant, {"prompt": "scene"}, source="mcp")
        assert out["ok"]
        assert assistant._enqueue_media.call_args[0][0] == "generate_image"


def test_experimental_helpers():
    from jarvis.image_generation.experimental import prompt_coach, recommend_style_workflow, seed_explorer

    assert prompt_coach("cat").get("ok")
    assert recommend_style_workflow("anime girl")["recommended_preset"] == "anime"
    seeds = seed_explorer(base_seed=1, count=3)
    assert len(seeds["seeds"]) == 3
