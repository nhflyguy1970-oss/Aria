"""Gallery upload, chat-attachment edits, uncensored whole-image edits, and the uploaded-photo guard."""
from __future__ import annotations

import io

import pytest
from PIL import Image

from jarvis import image_safety
from jarvis.image_safety import REAL_PHOTO_REFUSAL, REFUSAL, edit_refusal_for


@pytest.fixture
def data_dir(monkeypatch, tmp_path):
    (tmp_path / "generated").mkdir()
    monkeypatch.setattr("jarvis.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.gallery_product.upload.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.cache_state.invalidate_gallery", lambda: None)
    return tmp_path


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buf, format="PNG")
    return buf.getvalue()


def test_upload_lands_in_gallery_marked_external(data_dir):
    from jarvis.gallery_product.upload import save_upload

    out = save_upload("My Photo (1).png", _png())
    assert out["ok"] and out["name"].startswith("upload_") and out["name"].endswith("_My_Photo_1.png")
    path = data_dir / "generated" / out["name"]
    assert path.is_file() and image_safety.is_external_image(path)


@pytest.mark.parametrize("content,msg", [(b"", "Empty"), (b"not an image", "Not a readable image")])
def test_upload_rejects_bad_files(data_dir, content, msg):
    from jarvis.gallery_product.upload import save_upload

    assert msg in save_upload("x.png", content)["message"]
    assert not list((data_dir / "generated").iterdir())


def test_generated_images_stay_fully_editable(data_dir):
    gen = data_dir / "generated" / "jarvis_00300_.png"
    gen.write_bytes(_png())
    assert edit_refusal_for(gen, "make her fully nude") is None


@pytest.mark.parametrize("prompt", ["remove her clothes", "make him naked", "undress her", "topless",
                                    "take off her bikini", "make it explicit sex"])
def test_uploaded_photos_refuse_nude_or_sexual_edits(data_dir, prompt):
    up = data_dir / "uploads" / "selfie.jpg"
    assert edit_refusal_for(up, prompt) == REAL_PHOTO_REFUSAL


def test_uploaded_photos_allow_ordinary_edits(data_dir):
    assert edit_refusal_for(data_dir / "uploads" / "selfie.jpg", "make the sky orange") is None


def test_minor_refusal_applies_to_every_image(data_dir):
    gen = data_dir / "generated" / "jarvis_00301_.png"
    assert edit_refusal_for(gen, "make her a nude teen") == REFUSAL


def test_edits_of_uploads_inherit_the_external_mark(data_dir):
    out = data_dir / "generated" / "jarvis_edit_00001_.png"
    image_safety.inherit_provenance(data_dir / "uploads" / "selfie.jpg", str(out))
    assert edit_refusal_for(out, "remove her clothes") == REAL_PHOTO_REFUSAL


def test_edit_refuses_before_comfyui(data_dir, monkeypatch):
    from jarvis import comfyui_edit

    monkeypatch.setattr(comfyui_edit, "run_workflow", lambda *a, **k: pytest.fail("ComfyUI reached"))
    assert comfyui_edit.edit_image(data_dir / "uploads" / "a.jpg", "undress her") == REAL_PHOTO_REFUSAL


@pytest.mark.parametrize("uncensored,expected", [(True, "jarvis_edit"), (False, "jarvis_edit_klein")])
def test_uncensored_whole_image_edits_use_the_active_checkpoint(data_dir, monkeypatch, uncensored, expected):
    from jarvis import comfyui_edit

    src = data_dir / "generated" / "jarvis_00302_.png"
    src.write_bytes(_png())
    used = {}
    monkeypatch.setattr(comfyui_edit, "klein_installed", lambda: True)
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: uncensored)
    monkeypatch.setattr(comfyui_edit, "_prepare_image", lambda p: p)
    monkeypatch.setattr(comfyui_edit, "upload_image", lambda p: "src.png")
    monkeypatch.setattr(comfyui_edit, "_find_checkpoint", lambda c=None: "lustifySDXLNSFWSFW_v10.safetensors")
    monkeypatch.setattr("jarvis.comfyui.is_available", lambda: True)
    monkeypatch.setattr(comfyui_edit, "run_workflow",
                        lambda wf, filename_prefix="", **k: used.setdefault("prefix", filename_prefix) and
                        str(data_dir / "generated" / f"{filename_prefix}_00001_.png"))
    comfyui_edit.edit_image(src, "make the lighting warmer", skip_vram_prep=True)
    assert used["prefix"] == expected


@pytest.mark.parametrize("message,action", [
    ("make the sky orange", "edit_image"),
    ("please change her dress to red", "edit_image"),
    ("remove the background", "edit_image"),
    ("describe this image", "describe_image"),
    ("what is in this photo", None),
    ("read all text in this image", "ocr_image"),
    ("make the bedroom lights orange", "edit_image"),  # attachment present: an image edit
])
def test_attached_image_with_an_instruction_is_edited(message, action, tmp_path):
    from jarvis.router import route
    from jarvis.session import SessionContext

    img = tmp_path / "photo.png"
    img.write_bytes(_png())
    out = route(message, SessionContext(), attachment={"path": str(img), "kind": "image"})
    if action == "edit_image":
        assert out["action"] == "edit_image" and out["params"] == {"path": str(img), "prompt": message}
    elif action:
        assert out["action"] == action
    else:
        assert out["action"] != "edit_image"
