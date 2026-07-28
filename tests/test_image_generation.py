"""Image Generation product — pipeline, workflow patch, gallery bridge."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from jarvis.image_generation.params import normalize_params
from jarvis.image_generation.presets import delete_preset, export_presets, save_preset


def test_workflow_patch_honors_seed_steps_cfg():
    from jarvis.comfyui import _patch_workflow_generation

    wf = {
        "3": {
            "class_type": "KSampler",
            "inputs": {"seed": 1, "steps": 20, "cfg": 7, "sampler_name": "euler", "scheduler": "normal"},
        },
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 64, "height": 64, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}, "_meta": {"title": "Positive"}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}, "_meta": {"title": "Negative"}},
    }
    out = _patch_workflow_generation(
        wf,
        prompt="hello",
        negative_prompt="bad",
        width=128,
        height=256,
        seed=777,
        steps=11,
        cfg=3.5,
        sampler="dpmpp_2m",
        scheduler="karras",
    )
    assert out["6"]["inputs"]["text"] == "hello"
    assert out["7"]["inputs"]["text"] == "bad"
    assert out["3"]["inputs"]["seed"] == 777
    assert out["3"]["inputs"]["steps"] == 11
    assert out["3"]["inputs"]["cfg"] == 3.5
    assert out["3"]["inputs"]["sampler_name"] == "dpmpp_2m"
    assert out["5"]["inputs"]["width"] == 128


def test_gallery_submit_uses_shared_engine():
    from jarvis.gallery_product.generate import submit_generate

    assistant = MagicMock()
    with patch("jarvis.image_generation.engine.submit_generation") as sub:
        sub.return_value = {"ok": True, "job_id": "g1", "stay_in_gallery": True}
        out = submit_generate(assistant, "a tree", negative="fog", steps=10)
    assert out["ok"]
    assert sub.called
    args, kwargs = sub.call_args
    assert kwargs.get("source") == "gallery" or (len(args) >= 1)


def test_preset_save_delete_roundtrip(tmp_path, monkeypatch):
    from jarvis.image_generation import presets as presets_mod

    monkeypatch.setattr(presets_mod, "PRESETS_FILE", tmp_path / "presets.json")
    saved = save_preset("My Draft", {"steps": 4, "cfg": 1.0})
    assert saved["ok"]
    pid = saved["id"]
    exported = export_presets()
    assert pid in (exported.get("custom") or {})
    deleted = delete_preset(pid)
    assert deleted["ok"]


def test_normalize_variations_cap():
    assert normalize_params({"prompt": "x", "n": 100})["variations"] == 4


def test_mission_bridge_shape():
    from jarvis.image_generation.mission_bridge import engine_health

    with patch("jarvis.comfyui.is_available", return_value=False):
        h = engine_health()
    assert "running" in h
    assert "deep_links" in h
    assert h["deep_links"].get("mission_control")
