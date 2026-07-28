"""Recovery advisor after video generation failures."""

from __future__ import annotations

from typing import Any


def recovery_options(error: str = "", *, gpu_failure: bool = False) -> dict[str, Any]:
    msg = (error or "").lower()
    gpu = gpu_failure or any(
        t in msg for t in ("cuda", "gpu", "vram", "out of memory", "oom", "hip error")
    )
    offline = "not running" in msg or ("comfyui" in msg and "not" in msg)
    ad_missing = "animatediff" in msg and any(t in msg for t in ("missing", "not ready", "install"))
    actions = [
        {"id": "retry", "label": "Retry", "action": "retry"},
        {"id": "retry_low_vram", "label": "Retry lower VRAM (8 frames)", "action": "retry", "frames": 8},
        {"id": "retry_kb", "label": "Retry Ken Burns", "action": "retry", "engine": "ken_burns"},
        {"id": "retry_ad", "label": "Retry AnimateDiff", "action": "retry", "engine": "animatediff"},
        {"id": "reduce_duration", "label": "Retry shorter clip", "action": "retry", "duration": 3},
        {
            "id": "open_mc",
            "label": "Open Mission Control",
            "action": "open_view",
            "view": "mission-control",
        },
        {"id": "open_jobs", "label": "Open Job Center", "action": "open_view", "view": "jobs"},
        {"id": "free_vram", "label": "Free VRAM", "action": "free_vram"},
    ]
    if offline or ad_missing:
        actions.insert(
            0,
            {
                "id": "install_ad" if ad_missing else "restart_comfy",
                "label": "Install AnimateDiff" if ad_missing else "Check ComfyUI",
                "action": "install_animatediff" if ad_missing else "open_view",
                "view": "mission-control",
            },
        )
    return {
        "ok": True,
        "gpu_failure": gpu,
        "offline": offline,
        "animatediff_missing": ad_missing,
        "message": error or "Video generation failed",
        "actions": actions,
        "hint": (
            "GPU may be out of memory — retry Ken Burns, reduce frames, or free VRAM in Mission Control."
            if gpu
            else "Check AnimateDiff install status and ComfyUI in Mission Control / Video Studio."
        ),
    }
