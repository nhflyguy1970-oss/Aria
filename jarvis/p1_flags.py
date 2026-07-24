"""P1 feature flags."""

from __future__ import annotations

import os


def _env(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "off")


def local_router_enabled() -> bool:
    return _env("JARVIS_LOCAL_ROUTER", "1")


def brain_routing_enabled() -> bool:
    return _env("JARVIS_BRAIN_ROUTING", "1")


def chat_sessions_enabled() -> bool:
    return _env("JARVIS_CHAT_SESSIONS", "1")


def voice_ws_enabled() -> bool:
    return _env("JARVIS_VOICE_WS", "1")


def realtime_stt_enabled() -> bool:
    return _env("JARVIS_REALTIMESTT", "0")


def duplex_voice_enabled() -> bool:
    return _env("JARVIS_VOICE_DUPLEX", "1")


def first_run_models_enabled() -> bool:
    return _env("JARVIS_FIRST_RUN_MODELS", "0")


def voice_only_enabled() -> bool:
    return _env("JARVIS_VOICE_ONLY", "0")


def p1_flags() -> dict:
    from jarvis.feature_flags import all_flags

    base = all_flags()
    base.update(
        {
            "local_router": local_router_enabled(),
            "brain_routing": brain_routing_enabled(),
            "chat_sessions": chat_sessions_enabled(),
            "voice_ws": voice_ws_enabled(),
            "realtimestt": realtime_stt_enabled(),
            "voice_duplex": duplex_voice_enabled(),
            "first_run_models": first_run_models_enabled(),
            "voice_only": voice_only_enabled(),
        }
    )
    return base
