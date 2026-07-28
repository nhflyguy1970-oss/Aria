"""Video settings planning and engine selection."""

from __future__ import annotations

from unittest.mock import patch

from jarvis.video_settings import (
    VALID_ENGINES,
    effective_duration,
    effective_fps,
    plan_animatediff_clip,
    should_try_animatediff,
)


def test_valid_engines():
    assert "auto" in VALID_ENGINES
    assert "animatediff" in VALID_ENGINES
    assert "ken_burns" in VALID_ENGINES


def test_effective_duration_bounds(monkeypatch):
    monkeypatch.setenv("JARVIS_VIDEO_DURATION", "4")
    with patch("jarvis.video_settings.get_settings", return_value={"duration_sec": 4, "fps": 8, "engine": "auto"}):
        d = effective_duration()
    assert 2 <= d <= 12


def test_plan_animatediff_returns_frames():
    with patch("jarvis.video_settings._gpu_max_animatediff_frames", return_value=64):
        with patch("jarvis.video_settings.effective_animatediff_size", return_value=(512, 512)):
            with patch("jarvis.video_settings.get_settings", return_value={"animatediff_frames": 64}):
                plan = plan_animatediff_clip(4, 8)
    assert plan["frames"] >= 8
    assert plan["fps"] >= 4
    assert "actual_duration_sec" in plan


def test_should_try_animatediff_ken_burns_false():
    assert should_try_animatediff("ken_burns") is False


def test_should_try_animatediff_forced():
    with patch("jarvis.comfyui_animatediff.is_ready", return_value=False):
        assert should_try_animatediff("animatediff") is True  # still attempts
