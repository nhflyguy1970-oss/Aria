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

positive: Keep every specific detail the user asked for (subjects, actions, poses, setting, clothing, camera).
Do not generalize, sanitize, or replace specifics with vague scenery. One vivid paragraph.
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
        self.last_prompt = ""
        self.last_enhanced_prompt = ""
        self.last_negative_prompt = ""
        self.last_video = ""
        self.last_keyframe = ""
        self.last_method = "ken_burns"
        self.last_fallback_reason = ""
        self.last_clip_plan: dict = {}
        self.last_seed: int | None = None

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
        if os.getenv("JARVIS_VIDEO_RAW_PROMPT", "").lower() in ("1", "true", "yes", "on"):
            self.last_enhanced_prompt = user_prompt
            self.last_negative_prompt = ""
            return user_prompt, ""
        system = PROMPT_SYSTEM + (PROMPT_UNCENSORED if is_uncensored() else "")
        try:
            raw = llm.ask(
                self._prompt_model(),
                [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": f"Video request: {user_prompt}\n\nReturn JSON only.",
                    },
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

    def generate(
        self,
        prompt: str,
        *,
        enhance: bool | None = None,
        negative_prompt: str | None = None,
        enhanced_prompt: str | None = None,
        engine: str | None = None,
        seed: int | None = None,
        duration: float | None = None,
        fps: int | None = None,
        width: int | None = None,
        height: int | None = None,
        frames: int | None = None,
        checkpoint: str | None = None,
        animatediff_checkpoint: str | None = None,
        motion_strength: float | None = None,
    ) -> str:
        from jarvis.cache_state import invalidate_video_gallery

        prompt = (prompt or "").strip()
        self.last_prompt = prompt
        self.last_seed = seed
        if not prompt and not enhanced_prompt:
            return "ERROR: Empty video prompt"

        use_enhance = True if enhance is None else bool(enhance)
        if os.getenv("JARVIS_VIDEO_RAW_PROMPT", "").lower() in ("1", "true", "yes", "on"):
            use_enhance = False

        if enhanced_prompt and str(enhanced_prompt).strip():
            pos = str(enhanced_prompt).strip()
            neg = negative_prompt if negative_prompt is not None else ""
            self.last_enhanced_prompt = pos
            self.last_negative_prompt = neg or ""
        elif use_enhance:
            pos, neg = self.prepare_prompt(prompt)
            if negative_prompt is not None and str(negative_prompt).strip():
                neg = negative_prompt
            self.last_enhanced_prompt = pos
            self.last_negative_prompt = neg or ""
        else:
            pos = prompt
            neg = negative_prompt if negative_prompt is not None else ""
            self.last_enhanced_prompt = pos
            self.last_negative_prompt = neg or ""

        if not pos:
            return "ERROR: Empty video prompt"

        from jarvis.services import ensure_comfyui_nvidia
        from jarvis.vram_guard import prepare_for_comfyui

        prepare_for_comfyui()
        ensure_comfyui_nvidia(block=True, timeout=120)
        result, keyframe, method = generate_motion_clip(
            pos,
            negative_prompt=neg or "",
            width=width,
            height=height,
            duration=duration,
            fps=fps,
            engine=engine,
            seed=seed,
            frames=frames,
            checkpoint=checkpoint,
            animatediff_checkpoint=animatediff_checkpoint,
            motion_strength=motion_strength,
        )
        if result.startswith("ERROR:"):
            return result
        self.last_video = result
        self.last_keyframe = keyframe
        self.last_method = method
        from jarvis.comfyui_video import last_clip_plan, last_fallback_reason, last_seed

        self.last_clip_plan = last_clip_plan()
        self.last_fallback_reason = last_fallback_reason()
        try:
            self.last_seed = last_seed() if last_seed() is not None else seed
        except Exception:
            self.last_seed = seed
        invalidate_video_gallery()
        return result
