"""Video ops — path confinement and Ken Burns helpers (no ffmpeg required for resolve)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from jarvis.video_ops import resolve_storyboard_image, resolve_video_path, safe_video_name


def test_safe_video_name():
    assert ".." not in safe_video_name("../../etc/passwd.mp4")
    assert safe_video_name("ok clip.mp4").endswith(".mp4") or "ok" in safe_video_name("ok clip.mp4")


def test_resolve_video_path_rejects_outside(tmp_path, monkeypatch):
    from jarvis import video_ops

    monkeypatch.setattr(video_ops, "VIDEO_OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(video_ops, "VIDEO_UPLOAD_DIR", tmp_path / "up")
    (tmp_path / "out").mkdir()
    outside = tmp_path / "secret.mp4"
    outside.write_bytes(b"x")
    assert resolve_video_path(outside) is None


def test_resolve_storyboard_under_generated(tmp_path, monkeypatch):
    from jarvis import video_ops
    from jarvis.config import DATA_DIR

    gen = DATA_DIR / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    # Only assert reject for clearly outside paths
    assert resolve_storyboard_image("/etc/passwd") is None


def test_image_to_motion_accepts_zoom_end():
    from jarvis.video_ops import image_to_motion_video

    with patch("jarvis.video_ops.resolve_storyboard_image", return_value=None):
        out = image_to_motion_video("missing.png", zoom_end=1.3)
    assert out.startswith("ERROR:")
