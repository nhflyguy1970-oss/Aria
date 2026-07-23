"""Image, video, meme, and inpaint handlers (extracted from assistant)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from jarvis.modules.image import BASE_NEGATIVE
from jarvis.response import err, ok

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant


from jarvis.media_jobs import raise_if_cancelled


class MediaHandler:
    def __init__(self, assistant: JarvisAssistant) -> None:
        self.a = assistant

    def generate_image(self, params: dict, message: str) -> dict:
        raise_if_cancelled()
        from jarvis.modules.image import normalize_image_prompt

        prompt = normalize_image_prompt(params.get("prompt") or message or "")

        result = self.a.image.generate(prompt)
        if result.startswith("ERROR:"):
            return err(result, module="image")

        from jarvis.comfyui_settings import checkpoint_label
        from jarvis.prompt_history import add_entry

        add_entry(
            prompt,
            enhanced=self.a.image.last_enhanced_prompt or "",
            negative=self.a.image.last_negative_prompt or "",
            image_path=result,
            checkpoint=checkpoint_label(),
        )

        name = Path(result).name
        enhanced = self.a.image.last_enhanced_prompt
        negative = self.a.image.last_negative_prompt
        self.a.session.note_image(result)

        msg = f"Here's your image — **{prompt[:80]}**"
        if enhanced:
            msg += f"\n\n**Prompt sent to {checkpoint_label()}:**\n{enhanced}"
        if negative and negative != BASE_NEGATIVE:
            msg += f"\n\n**Avoiding:** {negative[:300]}"
        return ok(
            msg,
            module="image",
            type="image_result",
            output_path=result,
            image_path=result,
            image_name=name,
            enhanced_prompt=enhanced,
        )

    def generate_video(self, params: dict, message: str) -> dict:
        raise_if_cancelled()
        prompt = params.get("prompt") or message
        prompt = (
            re.sub(
                r"^(please\s+)?(create|generate|make)\s+(an?\s+)?(video|clip|animation|movie)\s+(of\s+)?",
                "",
                prompt,
                flags=re.I,
            ).strip()
            or prompt
        )

        result = self.a.video.generate(prompt)
        if result.startswith("ERROR:"):
            return err(result, module="video")

        name = Path(result).name
        enhanced = self.a.video.last_enhanced_prompt
        method = self.a.video.last_method
        plan = self.a.video.last_clip_plan or {}
        msg = f"Here's your video — **{prompt[:80]}**"
        if method == "animatediff":
            from jarvis.comfyui_animatediff import resolve_checkpoint

            ad_ckpt = resolve_checkpoint() or "SD 1.5"
            actual = plan.get("actual_duration_sec")
            target = plan.get("target_duration_sec")
            fps = plan.get("fps")
            frames = plan.get("frames")
            if actual and target and fps:
                msg += f"\n\n*AnimateDiff* — ~{actual}s ({frames} frames @ {fps} fps)"
                if plan.get("truncated"):
                    msg += f" (requested {target}s — VRAM cap; use **Ken Burns** engine for full length + your XL checkpoint)"
            else:
                msg += "\n\n*Generated with AnimateDiff (real motion)*"
            msg += f"\n*Model:* `{ad_ckpt}` (SD 1.5 — keyframe checkpoint below is Ken Burns only)"
        else:
            from jarvis.video_settings import keyframe_checkpoint_label

            ckpt_label = keyframe_checkpoint_label()
            msg += f"\n\n*Ken Burns clip* (keyframe: {ckpt_label})"
            if self.a.video.last_fallback_reason:
                msg += f"\nAnimateDiff unavailable — {self.a.video.last_fallback_reason[:120]}"
        if enhanced:
            label = "Prompt" if method == "animatediff" else "Keyframe prompt"
            msg += f"\n\n**{label}:**\n{enhanced}"
        ckpt_label = ""
        if method != "animatediff":
            from jarvis.video_settings import keyframe_checkpoint_label

            ckpt_label = keyframe_checkpoint_label()
        return ok(
            msg,
            module="video",
            type="video_result",
            output_path=result,
            video_path=result,
            video_name=name,
            keyframe_path=self.a.video.last_keyframe,
            enhanced_prompt=enhanced,
            checkpoint_label=ckpt_label,
            generation_method=method,
        )

    def generate_meme(self, params: dict, message: str) -> dict:
        raise_if_cancelled()
        idea = (params.get("idea") or params.get("prompt") or "").strip()
        top = (params.get("top") or "").strip()
        bottom = (params.get("bottom") or "").strip()
        if not idea and not top and not bottom:
            idea = (
                re.sub(
                    r"^(please\s+)?(make|create|generate)\s+(an?\s+)?meme\s+(about\s+)?",
                    "",
                    message,
                    flags=re.I,
                ).strip()
                or message
            )

        use_ai = params.get("use_ai_image", True)
        if isinstance(use_ai, str):
            use_ai = use_ai.lower() not in ("0", "false", "no")

        result = self.a.meme.generate(
            top=top,
            bottom=bottom,
            idea=idea,
            image_prompt=(params.get("image_prompt") or "").strip(),
            background_path=params.get("background_path"),
            use_ai_image=use_ai,
        )
        if result.startswith("ERROR:"):
            return err(result, module="meme")

        name = Path(result).name
        cap = " / ".join(x for x in (self.a.meme.last_top, self.a.meme.last_bottom) if x)
        msg = f"Here's your meme — **{cap[:100] or idea[:80]}**"
        if self.a.meme.last_image_prompt:
            msg += f"\n\n**Background scene:** {self.a.meme.last_image_prompt[:200]}"
        return ok(
            msg,
            module="meme",
            type="image_result",
            output_path=result,
            image_path=result,
            image_name=name,
        )

    def upscale_image(self, params: dict, message: str) -> dict:
        raise_if_cancelled()
        path = params.get("path") or self.a.session.last_image or self.a.image.last_image
        if not path:
            return err("Which image? Generate one first or give a path.", module="image")
        from jarvis.security.path_confine import resolve_image_library_path

        allowed = resolve_image_library_path(str(path))
        if allowed is None:
            return err("Image path not allowed or not found", module="image")
        path = str(allowed)
        try:
            scale = int(params.get("scale") or 2)
        except (TypeError, ValueError):
            scale = 2
        from jarvis.cache_state import invalidate_gallery
        from jarvis.image_post import upscale_local

        result = upscale_local(path, scale=scale)
        if result.startswith("ERROR:"):
            return err(result, module="image")
        invalidate_gallery()
        name = Path(result).name
        return ok(
            f"Upscaled **{scale}×** → `{name}` (Lanczos, local — no extra VRAM)",
            module="image",
            type="image_result",
            image_path=result,
            output_path=result,
            image_name=name,
        )

    def inpaint_image(self, params: dict, message: str) -> dict:
        raise_if_cancelled()
        path = params.get("path") or self.a.session.last_image or self.a.image.last_image
        prompt = (params.get("prompt") or "").strip()
        if not path:
            return err("Which image? Generate or attach one first.", module="image")
        if not prompt:
            return err("What should appear in the masked area? Give a prompt.", module="image")

        region = params.get("region") or params.get("crop")
        if isinstance(region, str) and region.strip():
            try:
                import json as _json

                region = _json.loads(region)
            except Exception:
                region = None
        if not region:
            from jarvis.vision_media import parse_region

            region = parse_region(message, None)

        denoise = params.get("denoise")
        try:
            denoise = float(denoise) if denoise is not None else None
        except (TypeError, ValueError):
            denoise = None

        from jarvis.cache_state import invalidate_gallery
        from jarvis.image_post import inpaint_region

        result = inpaint_region(
            path,
            params.get("mask_path"),
            prompt,
            region=region,
            negative_prompt=str(params.get("negative_prompt") or ""),
            denoise=denoise,
        )
        if result.startswith("ERROR:"):
            return err(result, module="image")
        invalidate_gallery()
        self.a.session.note_image(result)
        name = Path(result).name
        return ok(
            f"Inpainted → `{name}` (ComfyUI)",
            module="image",
            type="image_result",
            image_path=result,
            output_path=result,
            image_name=name,
        )

    def edit_image(self, params: dict, message: str) -> dict:
        raise_if_cancelled()
        path = params.get("path") or self.a.session.last_image or self.a.image.last_image
        prompt = (params.get("prompt") or message or "").strip()
        if not path:
            return err("Which image? Generate or pick one from Gallery first.", module="image")
        if not prompt:
            return err("What should change? Describe the edit.", module="image")

        denoise = params.get("denoise")
        try:
            denoise = float(denoise) if denoise is not None else None
        except (TypeError, ValueError):
            denoise = None

        from jarvis.image_post import edit_image as edit_fn

        result = edit_fn(path, prompt, denoise=denoise)
        if result.startswith("ERROR:"):
            return err(result, module="image")
        from jarvis.cache_state import invalidate_gallery

        invalidate_gallery()
        self.a.session.note_image(result)
        name = Path(result).name
        short = prompt[:80] + ("…" if len(prompt) > 80 else "")
        return ok(
            f"Edited image — **{short}** (img2img, keeps layout)\n\nSaved as `{name}`",
            module="image",
            type="image_result",
            image_path=result,
            output_path=result,
            image_name=name,
        )

    def enhance_prompt(self, params: dict, message: str) -> dict:
        prompt = params.get("prompt") or message
        prepared = self.a.image.prepare_prompt(prompt)
        return ok(
            f"**Positive prompt:**\n{prepared['positive']}\n\n**Negative prompt:**\n{prepared.get('negative') or '(default)'}",
            module="image",
            enhanced_prompt=prepared["positive"],
        )
