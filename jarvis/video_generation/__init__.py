"""Video Generation — Aria's local motion engine (one shared pipeline)."""

from jarvis.video_generation.engine import submit_storyboard, submit_video
from jarvis.video_generation.terminology import BOUNDARIES, TERMINOLOGY

__all__ = ["BOUNDARIES", "TERMINOLOGY", "submit_video", "submit_storyboard"]
