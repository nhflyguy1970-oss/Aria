"""Images made in Uncensored mode must not stay visible after switching back to Regular."""
from __future__ import annotations

import io

import pytest
from PIL import Image


@pytest.fixture
def gallery(chat_app, data_dir, monkeypatch):
    gen = data_dir / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.gallery_product.metadata.META_FILE", data_dir / "gallery_product" / "metadata.json")
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buf, format="PNG")
    for name in ("jarvis_00900_.png", "jarvis_00901_.png", "jarvis_edit_00900_.png"):
        (gen / name).write_bytes(buf.getvalue())
    from jarvis.gallery_product.metadata import mark_generation

    mark_generation("jarvis_00900_.png", prompt="x", uncensored=True)
    mark_generation("jarvis_00901_.png", prompt="x", uncensored=False)
    return chat_app


def _mode(monkeypatch, uncensored: bool):
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: uncensored)


def test_uncensored_image_is_restricted_and_never_cached_in_regular_mode(gallery, monkeypatch):
    _mode(monkeypatch, False)
    r = gallery.get("/api/gallery/jarvis_00900_.png")
    assert r.headers["content-type"].startswith("image/svg") and b"Restricted" in r.content
    assert r.headers["cache-control"] == "no-store"


def test_uncensored_image_shows_in_uncensored_mode_without_caching(gallery, monkeypatch):
    _mode(monkeypatch, True)
    r = gallery.get("/api/gallery/jarvis_00900_.png")
    assert r.headers["content-type"] == "image/png"
    assert r.headers["cache-control"] == "no-store"  # a later switch to Regular must refetch


def test_regular_images_keep_normal_caching(gallery, monkeypatch):
    _mode(monkeypatch, False)
    r = gallery.get("/api/gallery/jarvis_00901_.png")
    assert r.headers["content-type"] == "image/png"
    assert r.headers.get("cache-control") != "no-store"


@pytest.mark.parametrize("viewer,source_uncensored,expected", [
    (True, False, True),   # edited in Uncensored mode
    (False, True, True),   # Regular-mode edit of an Uncensored image inherits the restriction
    (False, False, False),
])
def test_edit_outputs_record_uncensored_provenance(gallery, data_dir, monkeypatch, viewer, source_uncensored, expected):
    from jarvis.gallery_product.metadata import get_meta
    from jarvis.handlers.media import _mark_edit_output

    _mode(monkeypatch, viewer)
    source = "jarvis_00900_.png" if source_uncensored else "jarvis_00901_.png"
    _mark_edit_output(str(data_dir / "generated" / "jarvis_edit_00900_.png"), str(data_dir / "generated" / source), "edit")
    assert get_meta("jarvis_edit_00900_.png")["uncensored"] is expected


def test_mode_badge_refreshes_on_screen_media():
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "jarvis/gui/static/workspace/mode_badge.js").read_text()
    assert "refreshMedia" in js and "aria:mode-changed" in js and "video-gallery" in js
