"""Mission Control bridge for Vision."""

from __future__ import annotations

from typing import Any


def vision_mission_panel() -> dict[str, Any]:
    from jarvis.vision_product.batch import list_jobs
    from jarvis.vision_product.engine import product_status
    from jarvis.vision_product.honesty import honesty_report
    from jarvis.vision_product.status_bus import get_vision_state

    status = product_status()
    honesty = honesty_report(task="describe")
    state = get_vision_state()
    jobs = list_jobs()[:8]
    failures = [j for j in jobs if int(j.get("failed") or 0) > 0 or j.get("status") == "error"]

    return {
        "product": "Vision",
        "state": state.get("state") or "idle",
        "detail": state.get("detail") or "",
        "model": honesty.get("model") or "",
        "quality_mode": honesty.get("quality_mode"),
        "estimated_vram_mb": honesty.get("estimated_vram_mb"),
        "free_vram_mb": honesty.get("free_vram_mb"),
        "low_vram": honesty.get("low_vram"),
        "warnings": honesty.get("warnings") or [],
        "queue": {"batch_jobs": len(jobs), "active": sum(1 for j in jobs if j.get("status") == "running")},
        "jobs": jobs,
        "failures": failures[:5],
        "profiles": status.get("profiles"),
        "deep_links": {
            "vision_home": "#vision",
            "settings": "#vision",
            "status": "/api/vision/product",
            "honesty": "/api/vision/honesty",
            "history": "/api/vision/history",
        },
    }
