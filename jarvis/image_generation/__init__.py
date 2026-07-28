"""Image Generation — Aria's still-image diffusion engine (one shared pipeline)."""

from jarvis.image_generation.engine import submit_generation
from jarvis.image_generation.terminology import BOUNDARIES, TERMINOLOGY

__all__ = ["BOUNDARIES", "TERMINOLOGY", "submit_generation"]
