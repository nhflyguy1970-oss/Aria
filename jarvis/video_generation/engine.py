"""Single shared enqueue path for all Video Generation entry points."""

from __future__ import annotations

from typing import Any

from jarvis.video_generation.params import normalize_params
from jarvis.video_generation.presets import apply_preset_to_params


def submit_video(
    assistant,
    raw_params: dict[str, Any] | None = None,
    *,
    message: str = "",
    source: str = "api",
) -> dict[str, Any]:
    """Enqueue generate_video through the one media queue — Studio/Chat/MCP/Voice/Automation."""
    params = normalize_params(raw_params, message=message)
    if not params.get("prompt"):
        return {"ok": False, "message": "Prompt required", "recovery": "Enter a description"}

    preset_id = params.get("style_preset") or (raw_params or {}).get("preset_id") or ""
    project = ""
    try:
        from jarvis.active_project import get_active_slug

        project = get_active_slug() or ""
    except Exception:
        project = ""
    if preset_id:
        params = apply_preset_to_params(params, str(preset_id), project=project)

    if not assistant:
        return {"ok": False, "message": "Assistant unavailable", "recovery": "Restart Aria"}

    job_params = {
        "prompt": params["prompt"],
        "negative": params.get("negative") or "",
        "negative_prompt": params.get("negative") or "",
        "enhance": params.get("enhance"),
        "enhanced_prompt": (raw_params or {}).get("enhanced_prompt")
        or (raw_params or {}).get("enhanced")
        or None,
        "engine": params.get("engine"),
        "seed": params.get("seed"),
        "duration": params.get("duration"),
        "duration_sec": params.get("duration"),
        "fps": params.get("fps"),
        "width": params.get("width"),
        "height": params.get("height"),
        "frames": params.get("frames"),
        "animatediff_frames": params.get("frames"),
        "checkpoint": params.get("checkpoint"),
        "keyframe_preset": params.get("keyframe_preset"),
        "animatediff_checkpoint": params.get("animatediff_checkpoint"),
        "workflow": params.get("workflow"),
        "motion_strength": params.get("motion_strength"),
        "fallback": params.get("fallback"),
        "reference_path": params.get("reference_path"),
        "source": source,
    }
    job_params = {k: v for k, v in job_params.items() if v is not None}

    result = assistant._enqueue_media(
        "generate_video",
        job_params,
        f"generate video: {params['prompt']}",
    )
    if not result.get("ok"):
        from jarvis.video_generation.fallback import recovery_options

        return {**result, **recovery_options(result.get("message") or "")}

    return {
        "ok": True,
        "pending": True,
        "job_id": result.get("job_id"),
        "message": result.get("message") or "Video generation queued",
        "action": "generate_video",
        "source": source,
        "params": {
            "prompt": params["prompt"],
            "engine": params.get("engine"),
            "duration": params.get("duration"),
            "fps": params.get("fps"),
            "style_preset": params.get("style_preset"),
        },
        "stay_in_studio": source in ("studio", "video", "video_studio"),
        "status": "queued",
        "queue_position": result.get("queue_position"),
    }


def submit_storyboard(
    assistant,
    raw_params: dict[str, Any] | None = None,
    *,
    source: str = "studio",
) -> dict[str, Any]:
    """Enqueue storyboard_video on the shared media queue (never coding_jobs)."""
    params = normalize_params(raw_params)
    paths = params.get("paths") or []
    if not paths:
        return {"ok": False, "message": "Storyboard paths required"}
    if not assistant:
        return {"ok": False, "message": "Assistant unavailable", "recovery": "Restart Aria"}

    job_params = {
        "paths": paths,
        "sec_per_slide": params.get("sec_per_slide") or 3.5,
        "transition": params.get("transition") or "ken_burns",
        "width": params.get("width"),
        "height": params.get("height"),
        "source": source,
    }
    job_params = {k: v for k, v in job_params.items() if v is not None}

    result = assistant._enqueue_media(
        "storyboard_video",
        job_params,
        f"storyboard ({len(paths)} slides)",
    )
    if not result.get("ok"):
        from jarvis.video_generation.fallback import recovery_options

        return {**result, **recovery_options(result.get("message") or "")}

    return {
        "ok": True,
        "pending": True,
        "job_id": result.get("job_id"),
        "message": result.get("message") or "Storyboard queued",
        "action": "storyboard_video",
        "source": source,
        "stay_in_studio": True,
        "status": "queued",
        "paths": paths,
        "sec_per_slide": job_params.get("sec_per_slide"),
    }


def last_settings_snapshot(assistant=None) -> dict[str, Any]:
    try:
        import json

        from jarvis.config import DATA_DIR

        path = DATA_DIR / "video_generation" / "last_settings.json"
        if path.is_file():
            return {"ok": True, **json.loads(path.read_text(encoding="utf-8"))}
    except Exception:
        pass
    out: dict[str, Any] = {"ok": True}
    if assistant and getattr(assistant, "video", None):
        out.update(
            {
                "prompt": getattr(assistant.video, "last_prompt", "") or "",
                "enhanced": getattr(assistant.video, "last_enhanced_prompt", "") or "",
                "negative": getattr(assistant.video, "last_negative_prompt", "") or "",
                "seed": getattr(assistant.video, "last_seed", None),
                "video": getattr(assistant.video, "last_video", "") or "",
                "method": getattr(assistant.video, "last_method", "") or "",
                "clip_plan": getattr(assistant.video, "last_clip_plan", {}) or {},
            }
        )
    return out


def save_last_settings(fields: dict[str, Any]) -> None:
    try:
        import json

        from jarvis.config import DATA_DIR

        path = DATA_DIR / "video_generation" / "last_settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fields, indent=2), encoding="utf-8")
    except Exception:
        pass
