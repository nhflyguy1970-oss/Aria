"""Tests for meme text overlay."""

from pathlib import Path

import pytest

from jarvis.meme_ops import compose_meme, list_memes, solid_background


@pytest.fixture
def meme_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.meme_ops.MEME_DIR", tmp_path)
    return tmp_path


def test_overlay_meme_text(meme_dir):
    bg = meme_dir / "bg.png"
    solid_background(400, 300).save(bg)
    out = compose_meme(bg, top="WHEN TESTS", bottom="PASS", output=meme_dir / "meme.png")
    assert Path(out).is_file()
    assert Path(out).stat().st_size > 1000


def test_list_memes_empty(meme_dir):
    assert list_memes() == []
