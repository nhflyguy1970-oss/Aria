"""Single shared enqueue path for all Image Generation entry points."""

from __future__ import annotations

from typing import Any

from jarvis.image_generation.params import normalize_params
from jarvis.image_generation.presets import apply_preset_to_params


def submit_generation(
    assistant,
    raw_params: dict[str, Any] | None = None,
    *,
    message: str = "",
    source: str = "api",
) -> dict[str, Any]:
    """Enqueue generate_image through the one media queue — Gallery/Chat/MCP/Voice/Automation."""
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

    # Map to MediaHandler params (same for every source)
    job_params = {
        "prompt": params["prompt"],
        "negative": params.get("negative") or "",
        "negative_prompt": params.get("negative") or "",
        "enhance": params.get("enhance"),
        "enhanced_prompt": (raw_params or {}).get("enhanced_prompt")
        or (raw_params or {}).get("enhanced")
        or None,
        "seed": params.get("seed"),
        "steps": params.get("steps"),
        "cfg": params.get("cfg"),
        "sampler": params.get("sampler"),
        "scheduler": params.get("scheduler"),
        "width": params.get("width"),
        "height": params.get("height"),
        "checkpoint": params.get("checkpoint"),
        "workflow": params.get("workflow"),
        "device": params.get("device"),
        "variations": params.get("variations") or 1,
        "variation_strength": params.get("variation_strength"),
        "source": source,
    }
    # Drop Nones so handler defaults apply
    job_params = {k: v for k, v in job_params.items() if v is not None}

    result = assistant._enqueue_media(
        "generate_image",
        job_params,
        f"generate image: {params['prompt']}",
    )
    if not result.get("ok"):
        from jarvis.image_generation.fallback import recovery_options

        return {**result, **recovery_options(result.get("message") or "")}

    return {
        "ok": True,
        "pending": True,
        "job_id": result.get("job_id"),
        "message": result.get("message") or "Image generation queued",
        "action": "generate_image",
        "source": source,
        "params": {
            "prompt": params["prompt"],
            "negative": params.get("negative") or "",
            "enhance": params.get("enhance"),
            "seed": params.get("seed"),
            "width": params.get("width"),
            "height": params.get("height"),
            "style_preset": params.get("style_preset"),
        },
        "stay_in_gallery": source == "gallery",
        "status": "queued",
        "queue_position": result.get("queue_position"),
    }


def last_settings_snapshot(assistant=None) -> dict[str, Any]:
    """Last successful generation settings for reuse UI."""
    try:
        from jarvis.config import DATA_DIR
        import json

        path = DATA_DIR / "image_generation" / "last_settings.json"
        if path.is_file():
            return {"ok": True, **json.loads(path.read_text(encoding="utf-8"))}
    except Exception:
        pass
    out: dict[str, Any] = {"ok": True}
    if assistant and getattr(assistant, "image", None):
        out.update(
            {
                "prompt": getattr(assistant.image, "last_prompt", "") or "",
                "enhanced": getattr(assistant.image, "last_enhanced_prompt", "") or "",
                "negative": getattr(assistant.image, "last_negative_prompt", "") or "",
                "seed": getattr(assistant.image, "last_seed", None),
                "image": getattr(assistant.image, "last_image", "") or "",
            }
        )
    return out


def save_last_settings(fields: dict[str, Any]) -> None:
    try:
        import json

        from jarvis.config import DATA_DIR

        path = DATA_DIR / "image_generation" / "last_settings.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(fields, indent=2), encoding="utf-8")
    except Exception:
        pass
