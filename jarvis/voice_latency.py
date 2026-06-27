"""Voice latency metrics and round-trip measurement (#26)."""

from __future__ import annotations

import time
from typing import Any

from jarvis.voice_settings import load_voice_settings


def voice_latency_profile() -> dict[str, Any]:
    vs = load_voice_settings()
    from jarvis.audio_settings import load_settings

    audio = load_settings()
    return {
        "speak_chunk_sentences": bool(vs.get("speak_chunk_sentences", True)),
        "tts_chunk_max_chars": int(vs.get("tts_chunk_max_chars") or 120),
        "tts_latency_target_ms": int(vs.get("tts_latency_target_ms") or 800),
        "piper_speed": float(audio.get("piper_speed") or 1.0),
        "stt_backend": vs.get("stt_backend") or "whisper",
        "duplex_mode": vs.get("duplex_mode") or "half",
    }


def measure_voice_round_trip(*, assistant=None) -> dict[str, Any]:
    """STT placeholder + LLM ping + TTS generate timing."""
    from jarvis.voice_smoke import run_voice_smoke

    smoke = run_voice_smoke(assistant=assistant)
    tts_ms = next((c.get("ms") for c in smoke.get("checks") or [] if c.get("name") == "TTS generate"), None)
    llm_ms = next((c.get("ms") for c in smoke.get("checks") or [] if c.get("name") == "LLM round-trip"), None)
    total = (tts_ms or 0) + (llm_ms or 0)
    target = int(load_voice_settings().get("tts_latency_target_ms") or 800)
    return {
        "ok": smoke.get("ok", False),
        "llm_ms": llm_ms,
        "tts_ms": tts_ms,
        "estimated_round_trip_ms": total,
        "target_ms": target,
        "within_target": total <= target if total else None,
        "checks": smoke.get("checks") or [],
    }
