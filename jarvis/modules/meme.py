"""Meme generator: LLM captions + optional ComfyUI background."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from jarvis import llm
from jarvis.meme_ops import MEME_DIR, compose_meme, overlay_meme_text, solid_background
from jarvis.modules.image import BASE_NEGATIVE, ImageEngine

PROMPT_UNCENSORED_NOTE = (
    "\n\nUncensored mode: keep edgy, adult, or NSFW humor the user asked for. "
    "Do not sanitize or refuse."
)

CAPTION_SYSTEM = """You write classic internet meme captions from a user idea.

Output ONLY valid JSON with keys "top", "bottom", and "image_prompt". No markdown.

Rules:
- top and bottom: short IMPACT-style captions (often ALL CAPS), max ~10 words each
- One may be empty if the joke works with a single caption
- image_prompt: vivid scene for the meme background — NO text, letters, or watermarks in the scene
- Match the user's tone (wholesome, sarcastic, absurd, etc.)
""" + PROMPT_UNCENSORED_NOTE

CAPTION_USER = """Meme idea: {idea}

Return JSON only."""


def _parse_caption_json(raw: str) -> dict[str, str] | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    return {
        "top": str(data.get("top", "")).strip(),
        "bottom": str(data.get("bottom", "")).strip(),
        "image_prompt": str(data.get("image_prompt", "")).strip(),
    }


class MemeEngine:
    def __init__(self) -> None:
        self.image = ImageEngine()
        self.last_meme: str = ""
        self.last_top: str = ""
        self.last_bottom: str = ""
        self.last_image_prompt: str = ""
        self.last_background: str = ""

    def prepare_captions(self, idea: str) -> dict[str, str]:
        fallback_prompt = f"funny meme scene, {idea}, expressive, high contrast, no text"
        fallback = {"top": idea[:40].upper(), "bottom": "", "image_prompt": fallback_prompt}
        try:
            from jarvis.modules.image import prompt_model_name

            model = prompt_model_name()
            raw = llm.ask_with_system(
                model,
                CAPTION_SYSTEM,
                CAPTION_USER.format(idea=idea),
                options={"num_predict": 220, "temperature": 0.75},
            )
            parsed = _parse_caption_json(raw)
            if parsed and (parsed["top"] or parsed["bottom"]):
                self.last_top = parsed["top"]
                self.last_bottom = parsed["bottom"]
                self.last_image_prompt = parsed["image_prompt"] or fallback_prompt
                return dict(parsed)
        except Exception:
            pass
        self.last_top = fallback["top"]
        self.last_bottom = fallback["bottom"]
        self.last_image_prompt = fallback["image_prompt"]
        return fallback

    def generate(
        self,
        *,
        top: str = "",
        bottom: str = "",
        idea: str = "",
        image_prompt: str = "",
        background_path: str | None = None,
        use_ai_image: bool = True,
    ) -> str:
        """Build a meme PNG. Returns path or 'ERROR: …'."""
        MEME_DIR.mkdir(parents=True, exist_ok=True)

        if idea and not (top.strip() or bottom.strip()):
            caps = self.prepare_captions(idea)
            top = caps.get("top", top)
            bottom = caps.get("bottom", bottom)
            if not image_prompt:
                image_prompt = caps.get("image_prompt", "")

        self.last_top = top.strip()
        self.last_bottom = bottom.strip()
        self.last_image_prompt = image_prompt.strip()

        if not self.last_top and not self.last_bottom:
            return "ERROR: Need top text, bottom text, or a meme idea."

        bg_path = background_path
        if bg_path and Path(bg_path).is_file():
            self.last_background = bg_path
        elif use_ai_image:
            prompt = image_prompt or idea or f"{top} {bottom}".strip()
            if not prompt:
                prompt = "funny meme background scene, expressive, no text"
            prompt = f"{prompt}, meme template photo, bold composition, no text, no watermark"
            neg = f"{BASE_NEGATIVE}, text, words, letters, caption, watermark, meme text"
            result = self.image.generate(prompt, negative_prompt=neg, enhance=False)
            if result.startswith("ERROR:"):
                return result
            bg_path = result
            self.last_background = bg_path
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plain = MEME_DIR / f"meme_bg_{stamp}.png"
            solid_background().save(plain)
            bg_path = str(plain)
            self.last_background = bg_path

        try:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = MEME_DIR / f"meme_{stamp}.png"
            path = compose_meme(bg_path, top=self.last_top, bottom=self.last_bottom, output=out)
            self.last_meme = path
            from jarvis.cache_state import invalidate_meme_gallery

            invalidate_meme_gallery()
            return path
        except Exception as exc:
            return f"ERROR: Meme compose failed — {exc}"

    def preview_text_only(self, top: str, bottom: str, width: int = 800, height: int = 600) -> str:
        """Fast preview without AI — gray slab + captions."""
        img = overlay_meme_text(solid_background(width, height), top=top, bottom=bottom)
        MEME_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = MEME_DIR / f"meme_preview_{stamp}.png"
        img.save(out, format="PNG")
        self.last_meme = str(out.resolve())
        return str(out.resolve())
