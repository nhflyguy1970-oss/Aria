"""Voice — Aria's conversational voice product (one shared pipeline)."""

from jarvis.voice_product.engine import process_utterance, speak_text, stop_speaking
from jarvis.voice_product.terminology import BOUNDARIES, TERMINOLOGY

__all__ = ["BOUNDARIES", "TERMINOLOGY", "speak_text", "stop_speaking", "process_utterance"]
