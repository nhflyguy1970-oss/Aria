"""Video generation and prompt expansion for Jarvis Video studio."""

from __future__ import annotations

import json
import os
import re

from jarvis import llm
from jarvis.comfyui_video import generate_motion_clip
from jarvis.video_ops import ensure_dirs

PROMPT_SYSTEM = """You convert casual video requests into prompts for AI video generation.

Output ONLY valid JSON: {"positive": "...", "negative": "..."}

positive: vivid scene with clear subject action and motion (walking, turning, wind, water, gestures), lighting, composition.
negative: defects to avoid; empty string if none.
"""

PROMPT_UNCENSORED = (
    "\n\nUncensored: preserve all explicit or adult details. No refusal or sanitization."
)


def prompt_model_name() -> str:
    return VideoEngine()._prompt_model()


class VideoEngine:
    def __init__(self) -> None:
        ensure_dirs()
        self.last_enhanced_prompt = ""
        self.last_negative_prompt = ""
        self.last_video = ""
        self.last_keyframe = ""
        self.last_method = "ken_burns"
        self.last_fallback_reason = ""

    def _prompt_model(self) -> str:
        env = os.getenv("JARVIS_VIDEO_PROMPT_MODEL", "").strip()
        if env:
            return env
        try:
            from jarvis.config import is_uncensored
            from jarvis.model_store import get_models

            if is_uncensored():
                return get_models().get("general", "dolphin-mistral:latest")
        except Exception:
            pass
        return "qwen2.5:7b"

    def prepare_prompt(self, user_prompt: str) -> tuple[str, str]:
        from jarvis.config import is_uncensored

        user_prompt = (user_prompt or "").strip()
        if not user_prompt:
            return "", ""
        system = PROMPT_SYSTEM + (PROMPT_UNCENSORED if is_uncensored() else "")
        try:
            raw = llm.ask(
                self._prompt_model(),
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Video request: {user_prompt}\n\nReturn JSON only."},
                ],
            )
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                data = json.loads(m.group(0))
                pos = str(data.get("positive", "")).strip() or user_prompt
                neg = str(data.get("negative", "")).strip()
                self.last_enhanced_prompt = pos
                self.last_negative_prompt = neg
                return pos, neg
        except Exception:
            pass
        self.last_enhanced_prompt = user_prompt
        self.last_negative_prompt = ""
        return user_prompt, ""

    def generate(self, prompt: str) -> str:
        from jarvis.cache_state import invalidate_video_gallery

        pos, neg = self.prepare_prompt(prompt)
        if not pos:
            return "ERROR: Empty video prompt"

        from jarvis.services import ensure_comfyui_nvidia
        from jarvis.vram_guard import prepare_for_comfyui

        prepare_for_comfyui()
        ensure_comfyui_nvidia(block=True, timeout=120)
        result, keyframe, method = generate_motion_clip(pos, negative_prompt=neg)
        if result.startswith("ERROR:"):
            return result
        self.last_video = result
        self.last_keyframe = keyframe
        self.last_method = method
        from jarvis.comfyui_video import last_fallback_reason

        self.last_fallback_reason = last_fallback_reason()
        invalidate_video_gallery()
        return result
