"""Tests for ComfyUI inpaint helpers (no live ComfyUI required)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.comfyui_inpaint import build_inpaint_workflow, effective_inpaint_workflow_path
from jarvis.image_masks import mask_from_region


def test_mask_from_region_center(tmp_path):
    from PIL import Image

    img = tmp_path / "photo.png"
    Image.new("RGB", (200, 100), "green").save(img)
    mask = mask_from_region(img, {"x": 0.25, "y": 0.25, "w": 0.5, "h": 0.5})
    assert mask.is_file()
    with Image.open(mask) as m:
        assert m.size == (200, 100)
        # center pixel should be white (255)
        assert m.getpixel((100, 50)) == 255
        # corner should be black
        assert m.getpixel((0, 0)) == 0


def test_mask_full_image(tmp_path):
    from PIL import Image

    img = tmp_path / "photo.png"
    Image.new("RGB", (64, 64), "blue").save(img)
    mask = mask_from_region(img, None)
    with Image.open(mask) as m:
        assert m.getpixel((0, 0)) == 255


@patch("jarvis.comfyui_inpaint.effective_inpaint_workflow_path", return_value=None)
@patch("jarvis.comfyui_inpaint._find_checkpoint", return_value="test_ckpt.safetensors")
@patch("jarvis.comfyui_inpaint._sampler_settings", return_value=(20, 7.0, "euler", "normal"))
def test_build_inpaint_workflow_builtin(_sampler, _ckpt, _wf_path):
    wf = build_inpaint_workflow("src.png", "mask.png", "a red ball", denoise=0.75)
    assert wf["10"]["inputs"]["image"] == "src.png"
    assert wf["11"]["inputs"]["image"] == "mask.png"
    assert wf["6"]["inputs"]["text"] == "a red ball"
    assert wf["3"]["inputs"]["denoise"] == 0.75
    assert wf["4"]["inputs"]["ckpt_name"] == "test_ckpt.safetensors"


def test_patch_custom_workflow(tmp_path):
    custom = tmp_path / "custom.json"
    custom.write_text(
        json.dumps(
            {
                "10": {
                    "class_type": "LoadImage",
                    "inputs": {"image": "old.png"},
                    "_meta": {"title": "Source Image"},
                },
                "11": {
                    "class_type": "LoadImage",
                    "inputs": {"image": "old_mask.png"},
                    "_meta": {"title": "Mask Image"},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": "old", "clip": ["4", 1]},
                    "_meta": {"title": "Positive"},
                },
                "3": {"class_type": "KSampler", "inputs": {"denoise": 0.5}},
            }
        ),
        encoding="utf-8",
    )
    with patch.dict("os.environ", {"JARVIS_COMFYUI_INPAINT_WORKFLOW": str(custom)}):
        path = effective_inpaint_workflow_path()
        assert path == custom
        from jarvis.comfyui_inpaint import build_inpaint_workflow

        wf = build_inpaint_workflow("new.png", "new_mask.png", "sunset", denoise=0.9)
    assert wf["10"]["inputs"]["image"] == "new.png"
    assert wf["11"]["inputs"]["image"] == "new_mask.png"
    assert wf["6"]["inputs"]["text"] == "sunset"
    assert wf["3"]["inputs"]["denoise"] == 0.9


@patch("jarvis.comfyui_inpaint.run_workflow", return_value="/tmp/out.png")
@patch("jarvis.comfyui_inpaint.upload_image", side_effect=["img.png", "mask.png"])
@patch("jarvis.comfyui.is_available", return_value=True)
def test_inpaint_calls_workflow(_avail, _upload, _run, tmp_path):
    from PIL import Image

    from jarvis.comfyui_inpaint import inpaint

    img = tmp_path / "a.png"
    mask = tmp_path / "m.png"
    Image.new("RGB", (32, 32), "white").save(img)
    Image.new("L", (32, 32), 255).save(mask)

    result = inpaint(img, mask, "test prompt")
    assert result == "/tmp/out.png"
    _run.assert_called_once()
    wf = _run.call_args[0][0]
    assert wf["6"]["inputs"]["text"] == "test prompt"


def test_inpaint_region_empty_prompt(tmp_path):
    from PIL import Image

    from jarvis.image_post import inpaint_region

    img_path = tmp_path / "real.png"
    Image.new("RGB", (8, 8), "red").save(img_path)
    mask = mask_from_region(img_path, None)
    with patch("jarvis.comfyui_inpaint.inpaint", return_value="ERROR: Inpaint needs a prompt"):
        out = inpaint_region(img_path, mask, "")
    assert "ERROR" in out
