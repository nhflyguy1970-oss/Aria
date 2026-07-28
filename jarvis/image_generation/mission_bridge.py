"""Mission Control bridge — engine health deep links (MC owns health UI)."""

from __future__ import annotations

from typing import Any


def engine_health() -> dict[str, Any]:
    running = False
    device = ""
    try:
        from jarvis import comfyui

        running = bool(comfyui.is_available())
        device = comfyui.comfyui_device_name() or ""
    except Exception:
        pass

    mode = "auto"
    cpu = False
    checkpoint = ""
    try:
        from jarvis.comfyui_settings import checkpoint_label, effective_cpu_mode, get_settings_dict

        settings = get_settings_dict()
        mode = settings.get("mode") or "auto"
        cpu = effective_cpu_mode()
        checkpoint = checkpoint_label()
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
        "device_name": device,
        "mode": mode,
        "cpu_mode": cpu,
        "checkpoint": checkpoint,
        "vram": vram,
        "queue": queue,
        "deep_links": {
            "mission_control": "mission-control",
            "job_center": "jobs",
            "image_engine": "gallery#imageEnginePanel",
            "gallery_generate": "gallery#galleryGenerateSection",
        },
    }
