"""Img2img edit workflow and full-frame inpaint redirect."""

from jarvis.comfyui_edit import build_edit_workflow
from jarvis.image_post import inpaint_region


def test_build_edit_workflow_uses_vae_encode_not_inpaint():
    wf = build_edit_workflow("test.png", "make the sky orange", denoise=0.55)
    assert "11" in wf
    assert wf["11"]["class_type"] == "VAEEncode"
    assert wf["3"]["inputs"]["denoise"] == 0.55
    assert "Inpaint" not in str(wf)


def test_inpaint_full_frame_redirects_to_edit(monkeypatch, tmp_path):
    src = tmp_path / "src.png"
    src.write_bytes(b"fake")

    calls = []

    def fake_edit(path, prompt, **kwargs):
        calls.append((str(path), prompt, kwargs))
        return str(tmp_path / "out.png")

    monkeypatch.setattr("jarvis.image_post.edit_image", fake_edit)

    region = {"x": 0, "y": 0, "w": 1, "h": 1}
    inpaint_region(src, None, "add snow", region=region)
    assert len(calls) == 1
    assert calls[0][0] == str(src)
    assert calls[0][1] == "add snow"
