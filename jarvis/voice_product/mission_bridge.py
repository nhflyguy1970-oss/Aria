"""Mission Control bridge for Voice health, latency, queue, recovery."""

from __future__ import annotations

from typing import Any


def voice_mission_panel() -> dict[str, Any]:
    from jarvis.voice_product.engine import product_status
    from jarvis.voice_product.recovery import diagnose
    from jarvis.voice_product.status_bus import get_voice_state

    status = product_status()
    recovery = diagnose()
    state = get_voice_state()

    whisper_ok = "whisper" in (recovery.get("healthy") or [])
    piper_ok = "piper" in (recovery.get("healthy") or [])
    cloud = status.get("cloud_live") or {}
    queue = status.get("queue") or {}

    return {
        "product": "Voice",
        "state": state.get("state") or "idle",
        "detail": state.get("detail") or "",
        "whisper": whisper_ok,
        "piper": piper_ok,
        "cloud_live": {
            "available": bool(cloud.get("available")),
            "provider": cloud.get("provider") or "",
            "active_sessions": cloud.get("active_sessions") or 0,
            "openai_advertised": False,  # hidden until WebRTC
            "webrtc_client": bool(cloud.get("webrtc_client")),
        },
        "queue": queue,
        "duplex": (status.get("duplex") or {}).get("mode"),
        "recovery": recovery,
        "deep_links": {
            "voice_tab": "#voice",
            "settings": "#settings",
            "smoke": "/api/voice/smoke",
            "status": "/api/voice/product",
            "recovery": "/api/voice/recovery",
        },
        "errors": [i for i in (recovery.get("issues") or []) if i.get("severity") in ("error", "warning")],
    }
