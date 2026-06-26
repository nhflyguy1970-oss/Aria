"""Tests for video_ops helpers."""

from jarvis.video_ops import safe_video_name


def test_safe_video_name():
    assert safe_video_name("../../evil.mp4") == "evil.mp4"
    assert "/" not in safe_video_name("foo/bar clip.mp4")
