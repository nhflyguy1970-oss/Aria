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
        from jarvis.image_generation.params import normalize_params
        from jarvis.modules.image import normalize_image_prompt

        raw = dict(params or {})
        if message and not raw.get("prompt"):
            raw["prompt"] = message
        norm = normalize_params(raw, message=message)
        prompt = normalize_image_prompt(norm.get("prompt") or "")
        if not prompt:
            return err("Prompt required", module="image")

        # Device preference is configuration (Image Engine / Mission Control), not a fork.
        # Recovery "Retry on CPU" sets mode via services API before re-enqueue.

        enhance = norm.get("enhance")
        negative = norm.get("negative") or ""
        # Empty string means operator cleared negative; absent means use engine default
        if "negative" not in raw and "negative_prompt" not in raw:
            negative_arg = None
        else:
            negative_arg = negative

        enhanced_override = str(raw.get("enhanced_prompt") or raw.get("enhanced") or "").strip() or None
        n = int(norm.get("variations") or 1)
        paths: list[str] = []
        last_seed = norm.get("seed")
        strength = str(norm.get("variation_strength") or "minor").lower()

        for i in range(n):
            raise_if_cancelled()
            seed = norm.get("seed")
            if i > 0:
                # Variations: new seed unless reuse; minor/major tweak prompt lightly
                seed = None
                if strength == "major" and i == 1:
                    # Keep same params, random seed only
                    pass
            result = self.a.image.generate(
                prompt,
                enhance=enhance,
                negative_prompt=negative_arg,
                enhanced_prompt=enhanced_override,
                seed=seed,
                steps=norm.get("steps"),
                cfg=norm.get("cfg"),
                sampler=norm.get("sampler"),
                scheduler=norm.get("scheduler"),
                width=norm.get("width"),
                height=norm.get("height"),
                checkpoint=norm.get("checkpoint"),
                workflow=norm.get("workflow"),
            )
            if result.startswith("ERROR:"):
                from jarvis.image_generation.fallback import recovery_options

                rec = recovery_options(result)
                return err(result, module="image", **{k: v for k, v in rec.items() if k != "ok"})
            paths.append(result)
            last_seed = getattr(self.a.image, "last_seed", seed)

        result = paths[-1]
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
        negative_out = self.a.image.last_negative_prompt
        seed_str = "" if last_seed is None else str(last_seed)
        try:
            from jarvis.config import is_uncensored
            from jarvis.gallery_product.metadata import mark_generation

            project = ""
            try:
                from jarvis.active_project import get_active_slug

                project = get_active_slug() or ""
            except Exception:
                project = ""
            for p in paths:
                mark_generation(
                    Path(p).name,
                    prompt=prompt,
                    enhanced=enhanced or "",
                    negative=negative_out or "",
                    checkpoint=checkpoint_label(),
                    uncensored=is_uncensored(),
                    project=project,
                    seed=seed_str,
                )
        except Exception:
            pass

        try:
            from jarvis.image_generation.engine import save_last_settings

            save_last_settings(
                {
                    "prompt": prompt,
                    "enhanced": enhanced or "",
                    "negative": negative_out or "",
                    "seed": last_seed,
                    "steps": norm.get("steps"),
                    "cfg": norm.get("cfg"),
                    "sampler": norm.get("sampler"),
                    "scheduler": norm.get("scheduler"),
                    "width": norm.get("width"),
                    "height": norm.get("height"),
                    "checkpoint": norm.get("checkpoint") or checkpoint_label(),
                    "workflow": norm.get("workflow"),
                    "enhance": enhance,
                    "image": result,
                    "style_preset": norm.get("style_preset"),
                }
            )
        except Exception:
            pass

        self.a.session.note_image(result)

        msg = f"Here's your image — **{prompt[:80]}**"
        if len(paths) > 1:
            msg = f"Generated {len(paths)} images — **{prompt[:80]}**"
        if enhanced:
            msg += f"\n\n**Prompt sent to {checkpoint_label()}:**\n{enhanced}"
        if negative_out and negative_out != BASE_NEGATIVE:
            msg += f"\n\n**Avoiding:** {negative_out[:300]}"
        if seed_str:
            msg += f"\n\n**Seed:** `{seed_str}`"
        return ok(
            msg,
            module="image",
            type="image_result",
            output_path=result,
            image_path=result,
            image_name=name,
            image_paths=paths if len(paths) > 1 else None,
            enhanced_prompt=enhanced,
            negative_prompt=negative_out,
            seed=last_seed,
            recovery=None,
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
