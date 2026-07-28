"""Mission Control bridge — video engine health deep links."""

from __future__ import annotations

from typing import Any


def engine_health() -> dict[str, Any]:
    running = False
    try:
        from jarvis import comfyui

        running = bool(comfyui.is_available())
    except Exception:
        pass

    ad: dict[str, Any] = {}
    try:
        from jarvis.comfyui_animatediff import readiness

        ad = readiness()
    except Exception:
        ad = {"ready": False}

    settings: dict[str, Any] = {}
    try:
        from jarvis.video_settings import get_settings_dict

        settings = get_settings_dict()
    except Exception:
        pass

    vram: dict[str, Any] = {}
    try:
        from jarvis.gpu import detect_gpu

        snap = detect_gpu()
        vram = {
            "free_mb": snap.get("free_vram_mb"),
            "total_mb": snap.get("vram_mb"),
            "used_mb": snap.get("vram_used_mb"),
            "name": snap.get("name") or "",
        }
    except Exception:
        pass

    queue: dict[str, Any] = {}
    try:
        from jarvis.media_jobs import busy_state

        queue = busy_state()
    except Exception:
        pass

    return {
        "running": running,
        "animatediff": ad,
        "settings": {
            "engine": settings.get("engine"),
            "duration_sec": settings.get("duration_sec"),
            "fps": settings.get("fps"),
            "clip_plan": settings.get("clip_plan"),
        },
        "vram": vram,
        "queue": queue,
        "deep_links": {
            "mission_control": "mission-control",
            "job_center": "jobs",
            "video_studio": "video",
            "generate": "video#videoGenerateSection",
        },
    }
