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

    return get_models().get("general", "huihui_ai/gemma-4-abliterated:12b")


def normalize_image_prompt(prompt: str) -> str:
    """Strip chat boilerplate so ComfyUI gets the subject the user meant."""
    from jarvis.image_request import clean_image_prompt

    p = clean_image_prompt(prompt or "")
    if not p:
        return (prompt or "").strip()
    p = re.sub(r"^(?:generate\s+image|create\s+image)\s*[:\-]\s*", "", p, flags=re.I)
    p = re.sub(r"^[:\-\s]+", "", p)

    def _keep_style(m: re.Match) -> str:
        # "Create a photorealistic, cinematic image of …" keeps "Photorealistic, cinematic image of";
        # "Create an image of a cat" becomes "a cat".
        style = (m.group("style") or "").strip(" ,")
        if not style or re.fullmatch(r"(?i)(?:new|another|original|single|quick|nice|good|cool)", style):
            return ""
        joiner = f" {m.group('of').strip()} " if m.group("of") else (". " if m.string[m.end():][:1].isupper() else " ")
        return f"{style[0].upper()}{style[1:]} {m.group('noun')}{joiner}"

    p = re.sub(
        r"^(?:please\s+)?(?:create|generate|make|draw|paint|render|produce)\s+(?:me\s+)?(?:an?\s+)?"
        r"(?P<style>(?:[\w'-]+,?\s+){0,6}?)(?P<noun>(?:image|picture|photograph|photo|pic|illustration|artwork|wallpaper|portrait|painting|drawing|rendering|render)s?)[.:,]?\s+"
        r"(?P<of>(?:of|showing|depicting|featuring)\s+)?",
        _keep_style,
        p,
        count=1,
        flags=re.I,
    ).strip()
    return p or prompt.strip()


HELPER_CTX = 4096  # the RX 7600 helper lane's qualified context


def _helper_prompt_model() -> str:
    """Small Regular-mode prompt model for the RX 7600 helper ("" = off). Uncensored rewrites
    keep the abliterated 12B on the RTX: it is too large for the helper lane."""
    env = os.getenv("JARVIS_IMAGE_PROMPT_MODEL_HELPER", "qwen3.5:4b").strip()
    return "" if env.lower() in ("", "0", "off", "false", "no") else env


def _rewrite_llm(system: str, user: str, *, num_predict: int, temperature: float) -> str:
    """Prompt preparation call. In Regular mode it runs on the RX 7600 helper when that lane
    is up and the request fits its 4K context: the RTX image job that follows then starts
    without evicting a prompt model (measured 2026-10-14). Otherwise: the usual prompt model."""
    options = {"num_predict": num_predict, "temperature": temperature}
    helper = _helper_prompt_model()
    try:
        from jarvis.config import is_uncensored

        uncensored = is_uncensored()
    except Exception:  # noqa: BLE001
        uncensored = True
    if helper and not uncensored:
        from jarvis import gpu_scheduler
        from jarvis.conversation import estimate_tokens

        fits = estimate_tokens(system + user) + num_predict + 256 <= HELPER_CTX and num_predict <= gpu_scheduler.HELPER_MAX_PREDICT
        if fits and gpu_scheduler.helper_ready() and gpu_scheduler.model_size(helper) > 0:
            try:
                with gpu_scheduler.prefer_helper("image prompt preparation before an RTX image job"):
                    # explicit_model: the gateway's role policy would otherwise swap in the RTX chat
                    # model (it ran gemma4:12b on the RTX in the first live test, 2026-10-14).
                    return llm.ask_with_system(helper, system, user, options={**options, "num_ctx": HELPER_CTX},
                                               think=False, explicit_model=True)
            except Exception as exc:  # noqa: BLE001 — helper died mid-call: the RTX model still answers
                logger.warning("Helper prompt model failed, using %s: %s", _prompt_model(), exc)
    return llm.ask_with_system(_prompt_model(), system, user, options=options)


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
    if "flux" in ckpt or ckpt.startswith("z_image"):  # natural-language prompts, no negative
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
    from jarvis.image_request import requested_dimensions

    if (asked := requested_dimensions(user)) and _active_model_family() != "sd15":
        return asked  # "16:9 widescreen" → 1344×768 (was 1216×832 from the "wide" keyword)

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

    if family in ("flux", "qwen"):
        return {"positive": positive, "negative": ""}

    negative = ", ".join(dict.fromkeys([BASE_NEGATIVE, STYLE_NEGATIVE]))
    if _wants_photorealistic(user):
        negative = f"{negative}, painting, illustration, cartoon, stylized, CGI"
    return {"positive": positive, "negative": negative}


def _prompt_system(family: str) -> str:
    base = PROMPT_SYSTEM_FLUX if family in ("flux", "qwen") else PROMPT_SYSTEM_SDXL
    try:
        from jarvis.config import is_uncensored
        if is_uncensored():
            return base
    except Exception:
        pass
    return base.replace(PROMPT_UNCENSORED_NOTE, "")


def _merge_negative(family: str, llm_negative: str, fallback_negative: str) -> str:
    llm_negative = (llm_negative or "").strip()
    if family in ("flux", "qwen"):
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
    return "" if family in ("flux", "qwen") else BASE_NEGATIVE


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


DETAILED_WORDS = 40


def _no_retry_error(result: str) -> bool:
    """Failures the fast model would hit too (cancelled, thermal/RAM cutoff, GPU busy, refused)."""
    lower = result.lower()
    return any(k in lower for k in ("cancel", "interrupt", "stopped to protect", "not started", "refus", "not allowed"))


def _is_detailed(prompt: str) -> bool:
    """A description long enough to send verbatim to natural-language models."""
    return len(re.findall(r"[A-Za-z']+", prompt or "")) >= DETAILED_WORDS


def _rewrite_budget(prompt: str) -> int:
    """Output tokens for the prompt rewrite: room for every detail of a long request
    (the fixed 320 cut long rewrites short)."""
    words = len((prompt or "").split())
    return max(320, min(1536, int(words * 2.5) + 160))


def merge_followup_prompt(base: str, change: str) -> str:
    """Rebuild the previous image description with the requested change applied."""
    from jarvis.image_request import merge_followup_fallback

    base, change = (base or "").strip(), (change or "").strip()
    if not change or not base:
        return base or change
    try:
        raw = _rewrite_llm(FOLLOWUP_SYSTEM, f"Previous description:\n{base}\n\nRequested change:\n{change}",
                           num_predict=_rewrite_budget(base + " " + change), temperature=0.2)
        merged = (raw or "").strip().strip('"').strip()
        # A merge that lost most of the description is worse than the plain fallback.
        if merged and len(merged) >= 0.6 * len(base) and not merged.lower().startswith(("i ", "sorry", "here")):
            return merged
    except Exception as exc:  # noqa: BLE001
        logger.warning("Image follow-up merge failed: %s", exc)
    return merge_followup_fallback(base, change)


FOLLOWUP_SYSTEM = """You update an image description for a text-to-image model.

Apply the requested change to the previous description and output ONLY the complete updated
description as plain text. Keep every subject, count, position, relationship, style, lighting
and aspect-ratio detail that the change does not alter, worded as before. Replace details the
change contradicts (e.g. "seven witches instead of five" changes the count everywhere it
appears). Do not add commentary, quotes or markdown."""


class ImageEngine:
    def __init__(self):
        self.last_prompt: str = ""
        self.last_enhanced_prompt: str = ""
        self.last_negative_prompt: str = ""
        self.last_image: str = ""
        self.last_seed: int | None = None
        self.last_tier: dict = {}
        self.last_model_label: str = ""
        self.last_count_check: dict = {}

    def prepare_prompt(self, prompt: str, family: str | None = None) -> dict[str, str]:
        """Expand any casual request into model-appropriate prompts."""
        prompt = normalize_image_prompt(prompt)
        family = family or _active_model_family()
        if family in ("flux", "qwen") and _is_detailed(prompt):
            # A full description is already what the model needs; a rewrite could only drop
            # constraints ("exactly five", "behind the jet") from it.
            return {"positive": prompt, "negative": ""}
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
                raw = _rewrite_llm(_prompt_system(family), PROMPT_USER.format(prompt=prompt, family=family),
                                   num_predict=_rewrite_budget(prompt), temperature=0.35)
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

    def generate(
        self,
        prompt: str,
        output: str | None = None,
        *,
        enhance: bool | None = None,
        negative_prompt: str | None = None,
        enhanced_prompt: str | None = None,
        seed: int | None = None,
        steps: int | None = None,
        cfg: float | None = None,
        sampler: str | None = None,
        scheduler: str | None = None,
        width: int | None = None,
        height: int | None = None,
        checkpoint: str | None = None,
        workflow: str | None = None,
    ) -> str:
        """Generate image via ComfyUI (primary on Linux). Honors operator params end-to-end."""
        from jarvis.image_safety import refusal_for

        # Check what the user asked for, before prompt enhancement can reword it.
        refused = refusal_for(prompt, enhanced_prompt or "")
        if refused:
            return refused
        prompt = normalize_image_prompt(prompt)
        self.last_prompt = prompt
        self.last_enhanced_prompt = prompt
        self.last_negative_prompt = negative_prompt or BASE_NEGATIVE
        self.last_seed = seed
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        if output:
            dest = fs.resolve_path(output, base=IMAGE_DIR)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = IMAGE_DIR / f"image_{timestamp}.png"

        use_enhance = _auto_enhance_enabled() if enhance is None else enhance
        from jarvis import image_quality

        self.last_tier = image_quality.choose(prompt, checkpoint=checkpoint, workflow=workflow)
        self.last_count_check = {}
        use_quality = self.last_tier["tier"] == "quality"
        family = "qwen" if use_quality else _active_model_family()
        pos_prompt = prompt
        neg_prompt = negative_prompt if negative_prompt is not None else _default_negative(family)

        # Operator-edited enhanced prompt wins over silent re-enhance
        if enhanced_prompt and str(enhanced_prompt).strip():
            pos_prompt = str(enhanced_prompt).strip()
            self.last_enhanced_prompt = pos_prompt
            self.last_negative_prompt = neg_prompt
        elif use_enhance:
            from jarvis.media_jobs import report_progress

            report_progress(5, "Rewriting prompt…")
            prepared = self.prepare_prompt(prompt, family=family)
            pos_prompt = prepared["positive"]
            if not (negative_prompt or "").strip():
                neg_prompt = prepared.get("negative") or _default_negative(family)
            else:
                neg_prompt = negative_prompt
            self.last_enhanced_prompt = pos_prompt
            self.last_negative_prompt = neg_prompt
        else:
            self.last_enhanced_prompt = pos_prompt
            self.last_negative_prompt = neg_prompt

        from jarvis import comfyui

        if width and height:
            w, h = int(width), int(height)
        else:
            w, h = _scene_dimensions(prompt)
        from jarvis.cache_state import invalidate_gallery
        from jarvis.comfyui_settings import checkpoint_label

        result = ""
        if use_quality:
            from jarvis import qwen_image
            from jarvis.media_jobs import report_progress

            report_progress(6, f"High-quality model ({', '.join(self.last_tier['reasons'][:3]) or 'complex scene'})…")
            self.last_model_label = qwen_image.LABEL
            result = qwen_image.generate(pos_prompt, w, h, seed=seed, count_prompt=prompt)
            self.last_seed = getattr(qwen_image.generate, "last_seed", seed)
            self.last_count_check = dict(getattr(qwen_image.generate, "last_check", None) or {})
            qwen_image.release_memory()
            if result.startswith("ERROR:") and not _no_retry_error(result):
                # Say so rather than silently swapping models: the fast model is tried next.
                logger.warning("Qwen-Image failed, using the fast model: %s", result)
                self.last_tier = {**self.last_tier, "tier": "fast", "fallback": result[6:].strip()[:300]}
                report_progress(8, "High-quality model failed — using the fast model…")
                use_quality = False
            elif result.startswith("ERROR:"):
                return result
        if not use_quality:
            self.last_model_label = checkpoint_label() if not checkpoint else Path(str(checkpoint)).stem
            result = comfyui.generate(
                pos_prompt,
                width=w,
                height=h,
                negative_prompt=neg_prompt,
                checkpoint=checkpoint,
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler=sampler,
                scheduler=scheduler,
                workflow=workflow,
            )
            try:
                self.last_seed = getattr(comfyui.generate, "last_seed", seed)
            except Exception:
                self.last_seed = seed
        if not result.startswith("ERROR:") and Path(result).suffix.lower() in IMAGE_EXTENSIONS:
            src = Path(result)
            in_gallery = src.resolve().parent == IMAGE_DIR.resolve()
            # ComfyUI already saved into the gallery; copying it to image_<ts>.png showed every
            # image twice. Only an explicit output name relocates it (moved, not duplicated).
            if output and src.resolve() != dest.resolve():
                dest.parent.mkdir(parents=True, exist_ok=True)
                (shutil.move if in_gallery else shutil.copy2)(src, dest)
                result = str(dest)
            elif not in_gallery:
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
