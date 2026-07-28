"""Recovery advisor after generation failures."""

from __future__ import annotations

from typing import Any


def recovery_options(error: str = "", *, gpu_failure: bool = False) -> dict[str, Any]:
    msg = (error or "").lower()
    gpu = gpu_failure or any(t in msg for t in ("cuda", "gpu", "vram", "out of memory", "oom"))
    offline = "not running" in msg or "comfyui" in msg and "not" in msg
    actions = [
        {"id": "retry_gpu", "label": "Retry on GPU", "action": "retry", "device": "gpu"},
        {"id": "retry_cpu", "label": "Retry on CPU", "action": "retry", "device": "cpu"},
        {
            "id": "open_mc",
            "label": "Open Mission Control",
            "action": "open_view",
            "view": "mission-control",
        },
        {"id": "open_jobs", "label": "Open Job Center", "action": "open_view", "view": "jobs"},
    ]
    if offline:
        actions.insert(
            0,
            {
                "id": "restart_comfy",
                "label": "Restart ComfyUI",
                "action": "restart_comfyui",
            },
        )
    return {
        "ok": True,
        "gpu_failure": gpu,
        "offline": offline,
        "message": error or "Generation failed",
        "actions": actions,
        "hint": (
            "GPU may be out of memory — try CPU or free VRAM in Mission Control."
            if gpu
            else "Check ComfyUI status in Mission Control or the Image Engine panel."
        ),
    }
