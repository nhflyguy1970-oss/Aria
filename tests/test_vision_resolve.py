"""Tests for vision image path resolution."""

from pathlib import Path

from jarvis.modules.vision import _resolve_image_path
from PIL import Image


def test_resolve_upload_by_basename(data_dir: Path, monkeypatch):
    monkeypatch.setattr("jarvis.modules.vision.DATA_DIR", data_dir)
    monkeypatch.setattr("jarvis.fs.DATA_DIR", data_dir)
    img = data_dir / "uploads" / "clip.png"
    Image.new("RGB", (4, 4), "blue").save(img)
    resolved = _resolve_image_path("clip.png")
    assert resolved == img.resolve()


def test_resolve_distinct_upload_paths(data_dir: Path, monkeypatch):
    monkeypatch.setattr("jarvis.modules.vision.DATA_DIR", data_dir)
    monkeypatch.setattr("jarvis.fs.DATA_DIR", data_dir)
    img1 = data_dir / "uploads" / "shot.png"
    img2 = data_dir / "uploads" / "shot_2.png"
    Image.new("RGB", (4, 4), "red").save(img1)
    Image.new("RGB", (4, 4), "blue").save(img2)
    assert _resolve_image_path(str(img1)) == img1.resolve()
    assert _resolve_image_path(str(img2)) == img2.resolve()
    assert _resolve_image_path(str(img1)) != _resolve_image_path(str(img2))
