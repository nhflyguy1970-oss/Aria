"""Mission Control bridge for Voice health, latency, queue, recovery."""

from __future__ import annotations

import time
from typing import Any

_PANEL_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_PANEL_TTL_S = 45.0


def voice_mission_panel() -> dict[str, Any]:
    """MC panel without full product_status (avoids repeated duplex/cloud probes).

    diagnose()/whisper_backend import can take seconds cold — cache the panel so
    Mission Control enrich does not pay that cost on every poll (Tier 3A / SYS-P01).
    """
    now = time.monotonic()
    cached = _PANEL_CACHE.get("value")
    if isinstance(cached, dict) and now - float(_PANEL_CACHE.get("at") or 0) < _PANEL_TTL_S:
        out = dict(cached)
        out["cached"] = True
        return out

    from jarvis.voice_product.recovery import diagnose
    from jarvis.voice_product.status_bus import get_voice_state

    recovery = diagnose()
    state = get_voice_state()
    duplex: dict[str, Any] = {}
    cloud: dict[str, Any] = {}
    queue: dict[str, Any] = {}
    try:
        from jarvis.voice_duplex import duplex_status

        duplex = duplex_status() or {}
    except Exception:
        pass
    try:
        from jarvis.cloud_live_voice import cloud_live_status

        cloud = cloud_live_status() or {}
    except Exception:
        pass
    try:
        from jarvis.tts_playback_queue import get_queue_status

        queue = get_queue_status() or {}
    except Exception:
        pass

    whisper_ok = "whisper" in (recovery.get("healthy") or [])
    piper_ok = "piper" in (recovery.get("healthy") or [])

    panel = {
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
        "duplex": duplex.get("mode"),
        "recovery": recovery,
        "deep_links": {
            "voice_tab": "#voice",
            "settings": "#settings",
            "smoke": "/api/voice/smoke",
            "status": "/api/voice/product",
            "recovery": "/api/voice/recovery",
        },
        "errors": [i for i in (recovery.get("issues") or []) if i.get("severity") in ("error", "warning")],
        "cached": False,
    }
    _PANEL_CACHE["at"] = now
    _PANEL_CACHE["value"] = panel
    return dict(panel)
