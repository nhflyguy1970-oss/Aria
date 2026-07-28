"""Gallery product — library, inventory, soft-delete, search, visibility."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def gallery_dir(tmp_path, monkeypatch):
    gen = tmp_path / "generated"
    gen.mkdir()
    monkeypatch.setattr("jarvis.gallery_product.library.GENERATED", gen)
    monkeypatch.setattr("jarvis.gallery_product.library.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.config.DATA_DIR", tmp_path)
    monkeypatch.setattr("jarvis.gallery_product.soft_delete.TRASH_DIR", tmp_path / "gallery_trash")
    monkeypatch.setattr(
        "jarvis.gallery_product.soft_delete.TRASH_META",
        tmp_path / "gallery_trash" / "index.json",
    )
    monkeypatch.setattr(
        "jarvis.gallery_product.metadata.META_FILE",
        tmp_path / "gallery_product" / "metadata.json",
    )
    monkeypatch.setattr(
        "jarvis.gallery_product.collections.FAVORITES_FILE",
        tmp_path / "gallery_product" / "favorites.json",
    )
    monkeypatch.setattr(
        "jarvis.gallery_product.collections.COLLECTIONS_FILE",
        tmp_path / "gallery_product" / "collections.json",
    )
    return gen


def _touch(gen: Path, name: str) -> Path:
    p = gen / name
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    return p


def test_inventory_classifies_artifacts():
    from jarvis.gallery_product.inventory import classify_name, is_intentional_still

    assert classify_name("image_20260101_120000.png") == "still"
    assert classify_name("keyframe_01.png") == "keyframe"
    assert classify_name("jarvis_up2x_foo.png") == "upscale"
    assert classify_name("meme_bg_x.png") == "meme_bg"
    assert is_intentional_still("image_20260101_120000.png")
    assert not is_intentional_still("storyboard_slide.png")


def test_list_excludes_artifacts_by_default(gallery_dir):
    _touch(gallery_dir, "image_20260101_120000.png")
    _touch(gallery_dir, "keyframe_01.png")
    from jarvis.gallery_product.library import list_images

    out = list_images(limit=50)
    names = [i["name"] for i in out["images"]]
    assert "image_20260101_120000.png" in names
    assert "keyframe_01.png" not in names
    assert out["total"] == 1


def test_pagination(gallery_dir):
    for i in range(5):
        _touch(gallery_dir, f"image_20260101_12000{i}.png")
    from jarvis.gallery_product.library import list_images

    page1 = list_images(offset=0, limit=2)
    page2 = list_images(offset=2, limit=2)
    assert page1["has_more"] is True
    assert len(page1["images"]) == 2
    assert len(page2["images"]) == 2
    assert page1["total"] == 5


def test_soft_delete_restore(gallery_dir):
    path = _touch(gallery_dir, "image_20260101_120000.png")
    from jarvis.gallery_product.soft_delete import list_trash, restore, soft_delete

    out = soft_delete(path)
    assert out["ok"] is True
    assert not path.exists()
    assert list_trash()["items"]
    restored = restore(out["trash_id"])
    assert restored["ok"] is True
    assert (gallery_dir / restored["restored"]).exists() or Path(restored["path"]).exists()


def test_search_matches_prompt_meta(gallery_dir, monkeypatch):
    _touch(gallery_dir, "image_20260101_120000.png")
    from jarvis.gallery_product.metadata import set_meta
    from jarvis.gallery_product.library import list_images

    set_meta("image_20260101_120000.png", {"prompt": "red sports car at night"})
    hit = list_images(query="sports car")
    miss = list_images(query="dragon")
    assert hit["total"] >= 1
    assert miss["total"] == 0


def test_restricted_visibility(gallery_dir, monkeypatch):
    _touch(gallery_dir, "image_20260101_120000.png")
    from jarvis.gallery_product.metadata import mark_generation
    from jarvis.gallery_product.visibility import apply_visibility, is_restricted_for_viewer

    mark_generation("image_20260101_120000.png", prompt="nsfw", uncensored=True)
    assert is_restricted_for_viewer("image_20260101_120000.png", viewer_uncensored=False) is True
    assert is_restricted_for_viewer("image_20260101_120000.png", viewer_uncensored=True) is False
    row = apply_visibility(
        {"name": "image_20260101_120000.png", "prompt": "secret", "caption": "leak"},
        viewer_uncensored=False,
    )
    assert row["restricted"] is True
    assert row["prompt"] is None


def test_favorites_and_collections(gallery_dir):
    from jarvis.gallery_product.collections import (
        create_collection,
        is_favorite,
        list_collections,
        toggle_favorite,
    )

    assert toggle_favorite("image_a.png")["favorite"] is True
    assert is_favorite("image_a.png")
    col = create_collection("Cars", names=["image_a.png"])
    assert col["ok"]
    assert list_collections()["items"]


def test_storyboard_suggest():
    from jarvis.gallery_product.storyboard import suggest_storyboard_order

    out = suggest_storyboard_order(["b.png", "a.png"])
    assert out["ok"] is True
    assert out["auto_create_video"] is False


def test_voice_blocks_purchase():
    from jarvis.gallery_product.voice_bridge import handle_voice_command

    out = handle_voice_command("buy this image")
    assert out.get("blocked") is True


def test_home_snapshot(gallery_dir, monkeypatch):
    monkeypatch.setattr(
        "jarvis.media_jobs.busy_state",
        lambda: {"busy": False, "pending": 0},
    )
    from jarvis.gallery_product.home import gallery_home_snapshot

    snap = gallery_home_snapshot()
    assert snap["ok"] is True
    assert snap["product"] == "gallery"
    assert "Ctrl+Shift+G" in snap["shortcut"]


def test_boundaries():
    from jarvis.gallery_product.terminology import BOUNDARIES

    assert "image_generation" in BOUNDARIES["owns"]
    assert "video_studio" in BOUNDARIES["does_not_own"]


def test_resolve_rejects_traversal(gallery_dir):
    from jarvis.gallery_product.library import resolve_image

    assert resolve_image("../etc/passwd") is None
    _touch(gallery_dir, "image_20260101_120000.png")
    assert resolve_image("image_20260101_120000.png") is not None


def test_ui_wiring_markers():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    js = Path("jarvis/gui/static/gallery_view.js").read_text(encoding="utf-8")
    assert 'id="galleryView"' in html
    assert "Ctrl+Shift+G" in html
    assert "gallerySearchInput" in html
    assert "/api/gallery/generate" in js
    assert "pollGalleryJob" in js
    assert "Loading library" in js


def test_submit_generate_requires_prompt():
    from jarvis.gallery_product.generate import submit_generate

    assert submit_generate(None, "")["ok"] is False
