"""Experimental Voice features — gated, never advertised as production-ready."""

from __future__ import annotations

import os
from typing import Any


def experimental_flags() -> dict[str, bool]:
    return {
        "continuous_local_duplex": os.getenv("JARVIS_VOICE_EXP_CONTINUOUS_DUPLEX", "0") == "1",
        "voice_agent_router": os.getenv("JARVIS_VOICE_EXP_AGENT_ROUTER", "0") == "1",
        "latency_auto_tuning": os.getenv("JARVIS_VOICE_EXP_LATENCY_AUTO", "0") == "1",
        "hybrid_local_cloud": os.getenv("JARVIS_VOICE_EXP_HYBRID", "0") == "1",
        "wake_scene_automation": os.getenv("JARVIS_VOICE_EXP_WAKE_SCENE", "0") == "1",
        "context_aware_voices": os.getenv("JARVIS_VOICE_EXP_CONTEXT_VOICE", "0") == "1",
        "adaptive_tts_quality": os.getenv("JARVIS_VOICE_EXP_ADAPTIVE_TTS", "0") == "1",
    }


def experimental_status() -> dict[str, Any]:
    flags = experimental_flags()
    return {
        "ok": True,
        "experimental": True,
        "message": "Experimental features are opt-in via env flags and share the same Voice engine.",
        "flags": flags,
        "enabled": [k for k, v in flags.items() if v],
    }


def maybe_auto_tune_latency() -> dict[str, Any]:
    """If latency auto-tuning is on, nudge chunk size toward target."""
    if not experimental_flags().get("latency_auto_tuning"):
        return {"ok": True, "applied": False}
    try:
        from jarvis.voice_latency import measure_voice_round_trip, voice_latency_profile
        from jarvis.voice_product.settings import load_unified_settings, save_unified_settings

        profile = voice_latency_profile()
        target = int(load_unified_settings().get("tts_latency_target_ms") or 800)
        measured = int((profile or {}).get("last_ms") or 0)
        if not measured:
            trip = measure_voice_round_trip()
            measured = int(trip.get("total_ms") or 0)
        if not measured:
            return {"ok": True, "applied": False, "reason": "no_measurement"}
        chunk = int(load_unified_settings().get("tts_chunk_max_chars") or 220)
        if measured > target * 1.4 and chunk > 80:
            chunk = max(80, chunk - 40)
            save_unified_settings({"tts_chunk_max_chars": chunk})
            return {"ok": True, "applied": True, "tts_chunk_max_chars": chunk, "measured_ms": measured}
        if measured < target * 0.6 and chunk < 320:
            chunk = min(320, chunk + 20)
            save_unified_settings({"tts_chunk_max_chars": chunk})
            return {"ok": True, "applied": True, "tts_chunk_max_chars": chunk, "measured_ms": measured}
        return {"ok": True, "applied": False, "measured_ms": measured, "tts_chunk_max_chars": chunk}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
