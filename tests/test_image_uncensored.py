"""Censored vs uncensored — one Image Generation pipeline; policy is configuration only."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from jarvis.image_generation.engine import submit_generation
from jarvis.modules.image import ImageEngine


def test_prepare_prompt_same_engine_both_modes():
    eng = ImageEngine()
    with patch("jarvis.modules.image._llm_enhance_enabled", return_value=False):
        with patch("jarvis.config.is_uncensored", return_value=False):
            a = eng.prepare_prompt("a quiet lake")
        with patch("jarvis.config.is_uncensored", return_value=True):
            b = eng.prepare_prompt("a quiet lake")
    assert "positive" in a and "positive" in b
    # Same code path keys — policy may change content of system prompt, not the return shape
    assert set(a.keys()) == set(b.keys())


def test_submit_generation_identical_action_censored_uncensored():
    actions = []
    for unc in (False, True):
        assistant = MagicMock()
        assistant._enqueue_media.return_value = {"ok": True, "job_id": "x"}
        with patch("jarvis.config.is_uncensored", return_value=unc):
            submit_generation(assistant, {"prompt": "portrait", "enhance": False}, source="chat")
        actions.append(assistant._enqueue_media.call_args[0][0])
    assert actions == ["generate_image", "generate_image"]


def test_restricted_visibility_does_not_regenerate():
    """Gallery visibility rules must not modify generation history."""
    from jarvis.gallery_product.visibility import is_restricted_for_viewer

    with patch("jarvis.gallery_product.visibility.get_meta", return_value={"uncensored": True}):
        with patch("jarvis.config.is_uncensored", return_value=False):
            assert is_restricted_for_viewer("foo.png") is True
    with patch("jarvis.gallery_product.visibility.get_meta", return_value={"uncensored": True}):
        with patch("jarvis.config.is_uncensored", return_value=True):
            assert is_restricted_for_viewer("foo.png") is False


def test_mark_generation_preserves_seed_and_uncensored_flag(tmp_path, monkeypatch):
    from jarvis.gallery_product import metadata as meta_mod

    monkeypatch.setattr(meta_mod, "META_FILE", tmp_path / "metadata.json")
    out = meta_mod.mark_generation(
        "img.png",
        prompt="p",
        enhanced="e",
        negative="n",
        checkpoint="ckpt",
        uncensored=True,
        seed="123",
    )
    assert out.get("ok") is not False
    got = meta_mod.get_meta("img.png")
    assert got.get("seed") == "123"
    assert got.get("uncensored") is True
    assert got.get("prompt") == "p"
