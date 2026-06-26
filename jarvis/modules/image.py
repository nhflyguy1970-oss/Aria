import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from jarvis import fs, llm
from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.image")

IMAGE_DIR = DATA_DIR / "generated"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

BASE_NEGATIVE = (
    "blurry, low quality, watermark, text, logo, signature, deformed, bad anatomy, "
    "extra limbs, fused animals, wrong species, mutant, disfigured, duplicate subject"
)

STYLE_NEGATIVE = (
    "painting, oil painting, watercolor, illustration, digital art, cartoon, anime, "
    "stylized, artistic rendering, CGI, 3d render, fantasy art, oversaturated, plastic look"
)

PHOTO_POSITIVE = (
    "photorealistic RAW photograph, natural lighting, natural colors, "
    "sharp focus, realistic textures, high detail"
)

PROMPT_UNCENSORED_NOTE = (
    "\n\nUncensored mode: copy every explicit, adult, anatomical, or NSFW term from the user "
    "verbatim into positive. Never refuse, sanitize, euphemize, censor, or add safety disclaimers. "
    "Never put nudity, nsfw, explicit, or sexual content in negative."
)

PROMPT_SYSTEM_SDXL = """You convert casual image requests into Stable Diffusion XL prompts.

Output ONLY valid JSON with keys "positive" and "negative". No markdown, no explanation.

positive rules:
- Preserve every subject, action, relationship, and style the user asked for
- Expand vague words into concrete visual details (species, materials, lighting, camera angle)
- When multiple subjects exist, describe spatial layout (above/below/in front/background)
- Match style: photorealistic vs illustration vs painting based on user words
- Use comma-separated descriptive phrases; use (subject:1.2) emphasis sparingly for key subjects

negative rules:
- Quality defects plus scene-specific mistakes to avoid for THIS request
- If user asked for photorealistic, reject painted/stylized/CGI looks
- Do not invent subjects the user did not ask for
""" + PROMPT_UNCENSORED_NOTE

PROMPT_SYSTEM_FLUX = """You convert casual image requests into FLUX text-to-image prompts.

Output ONLY valid JSON with keys "positive" and "negative". No markdown, no explanation.

positive rules:
- Write a clear natural-language scene description, not a tag soup
- Preserve every subject, action, relationship, and style the user asked for
- Expand vague terms into concrete visual details (species, materials, lighting, composition)
- When multiple subjects exist, describe where each one is in the frame
- For photorealistic requests, describe it as a photograph (lighting, lens, mood)

negative rules:
- FLUX barely uses negatives — return "" unless the user explicitly wants to avoid something
""" + PROMPT_UNCENSORED_NOTE

PROMPT_USER = """Image request: {prompt}

Model family: {family}

Return JSON only."""


def _auto_enhance_enabled() -> bool:
    return os.getenv("JARVIS_IMAGE_AUTO_ENHANCE", "1").lower() not in ("0", "false", "no", "off")


def _llm_enhance_enabled() -> bool:
    env = os.getenv("JARVIS_IMAGE_LLM_ENHANCE", "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    try:
        from jarvis.config import is_uncensored

        # Uncensored: expand with dolphin (see _prompt_model), not qwen — on by default.
        if is_uncensored():
            return True
    except Exception:
        pass
    return True


def _standard_prompt_model() -> str:
    env = os.getenv("JARVIS_IMAGE_PROMPT_MODEL", "").strip()
    return env or "qwen2.5:7b"


def _uncensored_prompt_model() -> str:
    env = os.getenv("JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED", "").strip()
    if env:
        return env
    from jarvis.model_store import get_models

    return get_models().get("general", "dolphin-mistral:latest")


def normalize_image_prompt(prompt: str) -> str:
    """Strip chat boilerplate so ComfyUI gets the subject the user meant."""
    p = (prompt or "").strip()
    if not p:
        return p
    p = re.sub(r"^(?:generate\s+image|create\s+image)\s*[:\-]\s*", "", p, flags=re.I)
    p = re.sub(r"^[:\-\s]+", "", p)
    p = re.sub(
        r"^(please\s+)?(create|generate|make|draw|paint)\s+(?:an?\s+)?"
        r"(?:[\w-]+\s+){0,4}(?:image|picture|photo|pic|illustration|artwork|wallpaper|portrait)s?\s+"
        r"(?:of\s+)?",
        "",
        p,
        flags=re.I,
    ).strip()
    return p or prompt.strip()


def prompt_model_name() -> str:
    """LLM used to expand image prompts before ComfyUI."""
    return _prompt_model()


def _prompt_model() -> str:
    try:
        from jarvis.config import is_uncensored

        if is_uncensored():
            return _uncensored_prompt_model()
    except Exception:
        pass
    return _standard_prompt_model()


def _active_model_family() -> str:
    try:
        from jarvis.comfyui_settings import resolve_checkpoint_name

        ckpt = resolve_checkpoint_name().lower()
    except Exception:
        ckpt = ""
    if "flux" in ckpt:
        return "flux"
    if "turbo" in ckpt:
        return "sdxl_turbo"
    if "realistic_vision" in ckpt or ("realistic" in ckpt and "vision" in ckpt):
        return "sd15"
    if "dreamshaper" in ckpt and "xl" not in ckpt:
        return "sd15"
    if "xl" in ckpt or "sd_xl" in ckpt or "realvis" in ckpt or "pony" in ckpt:
        return "sdxl"
    return "sdxl"


def _wants_photorealistic(text: str) -> bool:
    return bool(
        re.search(
            r"photo\s*realistic|photorealistic|realistic\s+photo|lifelike|hyper\s*real|looks?\s+real",
            text,
            re.I,
        )
    )


def _scene_dimensions(user: str) -> tuple[int, int]:
    w = int(os.getenv("JARVIS_IMAGE_WIDTH", "0"))
    h = int(os.getenv("JARVIS_IMAGE_HEIGHT", "0"))
    if w > 0 and h > 0:
        return w, h

    family = _active_model_family()
    if family == "sd15":
        if re.search(r"portrait|vertical|tall|full.?body", user.lower()):
            return 512, 768
        if re.search(r"landscape|wide|panorama|cinematic|wallpaper", user.lower()):
            return 768, 512
        return 512, 512

    lower = user.lower()
    if re.search(r"portrait|vertical|tall|full.?body", lower):
        return 832, 1216
    if re.search(r"landscape|wide|panorama|cinematic|wallpaper", lower):
        return 1216, 832
    return 1024, 1024


def _fallback_enhance(user: str, family: str) -> dict[str, str]:
    """Minimal generic fallback when the prompt LLM is unavailable."""
    positive = user.strip()
    if _wants_photorealistic(user):
        positive = f"{positive}, {PHOTO_POSITIVE}"
    elif family == "sdxl":
        positive = f"{positive}, highly detailed, sharp focus"

    if family == "flux":
        return {"positive": positive, "negative": ""}

    negative = ", ".join(dict.fromkeys([BASE_NEGATIVE, STYLE_NEGATIVE]))
    if _wants_photorealistic(user):
        negative = f"{negative}, painting, illustration, cartoon, stylized, CGI"
    return {"positive": positive, "negative": negative}


def _prompt_system(family: str) -> str:
    base = PROMPT_SYSTEM_FLUX if family == "flux" else PROMPT_SYSTEM_SDXL
    try:
        from jarvis.config import is_uncensored
        if is_uncensored():
            return base
    except Exception:
        pass
    return base.replace(PROMPT_UNCENSORED_NOTE, "")


def _merge_negative(family: str, llm_negative: str, fallback_negative: str) -> str:
    llm_negative = (llm_negative or "").strip()
    if family == "flux":
        return llm_negative
    if llm_negative and fallback_negative:
        return f"{fallback_negative}, {llm_negative}"
    return llm_negative or fallback_negative or BASE_NEGATIVE


def _parse_prompt_json(text: str) -> dict | None:
    text = text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("positive"):
            return data
    except json.JSONDecodeError:
        pass
    return None


_PROMPT_CACHE: dict[str, dict[str, str]] = {}
_PROMPT_CACHE_MAX = 48
_PROMPT_CACHE_LOCK = __import__("threading").Lock()


def _default_negative(family: str) -> str:
    return "" if family == "flux" else BASE_NEGATIVE


def _cache_get(key: str) -> dict[str, str] | None:
    with _PROMPT_CACHE_LOCK:
        hit = _PROMPT_CACHE.get(key)
        return dict(hit) if hit is not None else None


def _cache_put(key: str, value: dict[str, str]) -> None:
    with _PROMPT_CACHE_LOCK:
        if len(_PROMPT_CACHE) >= _PROMPT_CACHE_MAX:
            _PROMPT_CACHE.pop(next(iter(_PROMPT_CACHE)))
        _PROMPT_CACHE[key] = value


def clear_prompt_cache() -> None:
    with _PROMPT_CACHE_LOCK:
        _PROMPT_CACHE.clear()


def _prompt_cache_key(prompt: str, family: str) -> str:
    from jarvis.config import is_uncensored

    return f"{family}:{int(is_uncensored())}:{prompt.strip().lower()}"


class ImageEngine:
    def __init__(self):
        self.last_prompt: str = ""
        self.last_enhanced_prompt: str = ""
        self.last_negative_prompt: str = ""
        self.last_image: str = ""

    def prepare_prompt(self, prompt: str) -> dict[str, str]:
        """Expand any casual request into model-appropriate prompts."""
        prompt = normalize_image_prompt(prompt)
        family = _active_model_family()
        cache_key = _prompt_cache_key(prompt, family)
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

        fallback = _fallback_enhance(prompt, family)

        if not _auto_enhance_enabled():
            result = {"positive": prompt, "negative": _default_negative(family)}
            _cache_put(cache_key, result)
            return result

        if _llm_enhance_enabled():
            try:
                raw = llm.ask_with_system(
                    _prompt_model(),
                    _prompt_system(family),
                    PROMPT_USER.format(prompt=prompt, family=family),
                    options={"num_predict": 320, "temperature": 0.35},
                )
                parsed = _parse_prompt_json(raw)
                if parsed:
                    positive = str(parsed["positive"]).strip()
                    negative = _merge_negative(
                        family,
                        str(parsed.get("negative", "")).strip(),
                        fallback.get("negative", ""),
                    )
                    result = {"positive": positive, "negative": negative}
                    _cache_put(cache_key, result)
                    return result
            except Exception as exc:
                logger.warning("Image prompt LLM enhance failed: %s", exc)

        _cache_put(cache_key, fallback)
        return fallback

    def enhance_prompt(self, prompt: str) -> str:
        prepared = self.prepare_prompt(prompt)
        return prepared["positive"]

    def generate(self, prompt: str, output: str | None = None, *, enhance: bool | None = None, negative_prompt: str | None = None) -> str:
        """Generate image via ComfyUI (primary on Linux)."""
        prompt = normalize_image_prompt(prompt)
        self.last_prompt = prompt
        self.last_enhanced_prompt = prompt
        self.last_negative_prompt = negative_prompt or BASE_NEGATIVE
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        if output:
            dest = fs.resolve_path(output, base=IMAGE_DIR)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = IMAGE_DIR / f"image_{timestamp}.png"

        use_enhance = _auto_enhance_enabled() if enhance is None else enhance
        family = _active_model_family()
        pos_prompt = prompt
        neg_prompt = negative_prompt if negative_prompt is not None else _default_negative(family)
        if use_enhance and negative_prompt is None:
            prepared = self.prepare_prompt(prompt)
            pos_prompt = prepared["positive"]
            neg_prompt = prepared.get("negative") or _default_negative(family)
            self.last_enhanced_prompt = pos_prompt
            self.last_negative_prompt = neg_prompt
        elif negative_prompt is not None:
            self.last_enhanced_prompt = pos_prompt
            self.last_negative_prompt = neg_prompt

        from jarvis import comfyui

        width, height = _scene_dimensions(prompt)
        from jarvis.cache_state import invalidate_gallery

        result = comfyui.generate(
            pos_prompt,
            width=width,
            height=height,
            negative_prompt=neg_prompt,
        )
        if not result.startswith("ERROR:") and Path(result).suffix.lower() in IMAGE_EXTENSIONS:
            src = Path(result)
            if dest and src.resolve() != dest.resolve():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                result = str(dest)
            self.last_image = result
            invalidate_gallery()
            return result

        if result.startswith("ERROR:"):
            return result

        return (
            "ERROR: Image generation failed. ComfyUI is required on Linux — "
            "ensure ~/ComfyUI is installed and Jarvis shows ComfyUI as online in the sidebar. "
            f"Detail: {result}"
        )

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            return False

        if prompt.startswith("generate "):
            text = prompt[9:].strip()
            result = self.generate(text)
            print(f"\nResult: {result}\n")
            return True

        if prompt.startswith("enhance "):
            text = prompt[8:].strip()
            enhanced = self.enhance_prompt(text)
            print("\nEnhanced prompt:\n")
            print(enhanced)
            print()
            return True

        if prompt.startswith("enhance-generate "):
            text = prompt[17:].strip()
            enhanced = self.enhance_prompt(text)
            print("\nEnhanced prompt:\n")
            print(enhanced)
            print()
            result = self.generate(enhanced, enhance=False)
            print(f"Result: {result}\n")
            return True

        if prompt == "list":
            IMAGE_DIR.mkdir(parents=True, exist_ok=True)
            files = sorted(IMAGE_DIR.iterdir())
            if files:
                print("\nGenerated files:\n")
                for f in files:
                    print(f"  {f.name}")
                print()
            else:
                print("\nNo generated files.\n")
            return True

        if prompt == "last":
            if self.last_prompt:
                print(f"\nLast prompt: {self.last_prompt}\n")
            else:
                print("\nNo prompts yet.\n")
            return True

        result = self.generate(prompt)
        print(f"\nResult: {result}\n")
        return True


def main():
    engine = ImageEngine()
    print("\nJarvis Image Generation (ComfyUI)")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            prompt = input("Image > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
