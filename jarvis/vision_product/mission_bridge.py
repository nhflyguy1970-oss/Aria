"""Mission Control bridge for Vision."""

from __future__ import annotations

from typing import Any


def vision_mission_panel() -> dict[str, Any]:
    from jarvis.vision_product.batch import list_jobs
    from jarvis.vision_product.settings import load_settings
    from jarvis.vision_product.status_bus import get_vision_state

    state = get_vision_state()
    settings = {}
    try:
        settings = load_settings() or {}
    except Exception:
        settings = {}
    model = ""
    try:
        from jarvis import llm

        model = llm.vision_model_for_task("describe") or ""
    except Exception:
        pass
    jobs = list_jobs()[:8]
    failures = [j for j in jobs if int(j.get("failed") or 0) > 0 or j.get("status") == "error"]

    return {
        "product": "Vision",
        "state": state.get("state") or "idle",
        "detail": state.get("detail") or "",
        "model": model,
        "quality_mode": settings.get("quality_mode"),
        "estimated_vram_mb": None,
        "free_vram_mb": None,
        "low_vram": None,
        "warnings": [],
        "queue": {"batch_jobs": len(jobs), "active": sum(1 for j in jobs if j.get("status") == "running")},
        "jobs": jobs,
        "failures": failures[:5],
        "profiles": {"active": settings.get("active_profile"), "count": len(settings.get("profiles") or [])},
        "deep_links": {
            "vision_home": "#vision",
            "settings": "#vision",
            "status": "/api/vision/product",
            "honesty": "/api/vision/honesty",
            "history": "/api/vision/history",
        },
    }
