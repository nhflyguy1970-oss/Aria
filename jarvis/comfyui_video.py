"""Video generation — AnimateDiff (when ready) or keyframe + Ken Burns fallback."""

from __future__ import annotations

import logging

from jarvis import comfyui
from jarvis.video_settings import (
    effective_duration,
    effective_engine,
    effective_fps,
    effective_size,
    should_try_animatediff,
)

log = logging.getLogger("jarvis")

_last_method = "ken_burns"
_last_fallback_reason = ""


def last_generation_method() -> str:
    return _last_method


def last_fallback_reason() -> str:
    return _last_fallback_reason


def generate_motion_clip(
    prompt: str,
    *,
    negative_prompt: str = "",
    width: int | None = None,
    height: int | None = None,
    duration: float | None = None,
    fps: int | None = None,
) -> tuple[str, str, str]:
    """
    Generate a motion clip.
    Returns (video_path, keyframe_path, method) or (ERROR:..., "", method).
    method is 'animatediff' or 'ken_burns'.
    """
    global _last_method, _last_fallback_reason

    from jarvis.services import ensure_comfyui_nvidia

    ensure_comfyui_nvidia(block=True, timeout=120)

    engine = effective_engine()
    dur = duration if duration is not None else effective_duration()
    frame_fps = fps if fps is not None else effective_fps()
    w, h = effective_size()
    if width:
        w = min(int(width), 1024)
    if height:
        h = min(int(height), 1024)

    try_animatediff = should_try_animatediff(engine)
    from jarvis.resource_router import should_prefer_ken_burns

    if should_prefer_ken_burns() and engine == "auto":
        try_animatediff = False
        _last_fallback_reason = "Ollama models still on GPU — using Ken Burns to avoid OOM"
    if try_animatediff:
        from jarvis.comfyui_animatediff import generate as generate_animatediff
        from jarvis.gpu import is_low_vram
        from jarvis.video_settings import effective_animatediff_frames, effective_animatediff_size

        ad_w, ad_h = effective_animatediff_size()
        if width:
            ad_w = min(int(width), ad_w)
        if height:
            ad_h = min(int(height), ad_h)
        frames = effective_animatediff_frames(dur, frame_fps)

        log.info(
            "AnimateDiff attempt: %dx%d, %d frames @ %d fps (engine=%s)",
            ad_w, ad_h, frames, frame_fps, engine,
        )
        result, _ = generate_animatediff(
            prompt,
            negative_prompt=negative_prompt,
            width=ad_w,
            height=ad_h,
            frames=frames,
            fps=frame_fps,
        )
        if not result.startswith("ERROR:"):
            _last_method = "animatediff"
            _last_fallback_reason = ""
            return result, "", "animatediff"

        reason = result[6:].strip() if result.startswith("ERROR:") else result
        log.warning("AnimateDiff failed: %s", reason)
        if (
            engine != "animatediff"
            and is_low_vram(10240)
            and _looks_like_vram_failure(result)
            and frames > 8
        ):
            log.info("Retrying AnimateDiff at 8 frames after VRAM failure")
            retry_frames = 8
            result, _ = generate_animatediff(
                prompt,
                negative_prompt=negative_prompt,
                width=ad_w,
                height=ad_h,
                frames=retry_frames,
                fps=frame_fps,
            )
            if not result.startswith("ERROR:"):
                _last_method = "animatediff"
                _last_fallback_reason = "retried at 8 frames"
                return result, "", "animatediff"

        if engine == "animatediff":
            _last_method = "animatediff"
            _last_fallback_reason = ""
            return result, "", "animatediff"

        _last_fallback_reason = reason
        if is_low_vram(10240) and _looks_like_vram_failure(result):
            log.warning("AnimateDiff likely hit VRAM limits — using Ken Burns")

    video, keyframe = generate_ken_burns_clip(
        prompt,
        negative_prompt=negative_prompt,
        width=w,
        height=h,
        duration=dur,
        fps=frame_fps,
    )
    _last_method = "ken_burns"
    if video.startswith("ERROR:"):
        return video, keyframe, "ken_burns"
    return video, keyframe, "ken_burns"


def _looks_like_vram_failure(message: str) -> bool:
    lower = message.lower()
    return any(
        token in lower
        for token in ("out of memory", "oom", "hip error", "cuda", "alloc", "vram", "gpu")
    )


def generate_ken_burns_clip(
    prompt: str,
    *,
    negative_prompt: str = "",
    width: int | None = None,
    height: int | None = None,
    duration: float | None = None,
    fps: int | None = None,
) -> tuple[str, str]:
    """Generate keyframe via ComfyUI then ffmpeg Ken Burns clip."""
    from jarvis.video_ops import image_to_motion_video
    from jarvis.video_settings import (
        effective_duration,
        effective_fps,
        effective_size,
        resolve_keyframe_checkpoint,
    )

    w, h = effective_size()
    if width:
        w = min(int(width), 1024)
    if height:
        h = min(int(height), 1024)
    dur = duration if duration is not None else effective_duration()
    frame_fps = fps if fps is not None else effective_fps()

    ckpt = resolve_keyframe_checkpoint()
    keyframe = comfyui.generate(
        prompt, width=w, height=h, negative_prompt=negative_prompt, checkpoint=ckpt,
    )
    if keyframe.startswith("ERROR:"):
        return keyframe, ""

    video = image_to_motion_video(
        keyframe, duration=dur, fps=frame_fps, width=w, height=h,
    )
    if video.startswith("ERROR:"):
        return video, keyframe
    return video, keyframe
