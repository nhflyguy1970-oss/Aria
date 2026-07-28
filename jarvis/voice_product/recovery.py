"""Recovery advisor — detect voice failures and suggest actions."""

from __future__ import annotations

import shutil
from typing import Any


def diagnose() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    healthy: list[str] = []

    try:
        from jarvis.audio_whisper import whisper_backend

        backend = whisper_backend()
        if backend and backend != "none":
            healthy.append("whisper")
        else:
            issues.append(
                {
                    "code": "missing_whisper",
                    "severity": "warning",
                    "message": "Server Whisper unavailable",
                    "actions": [
                        {"id": "install_whisper", "label": "Install faster-whisper"},
                        {"id": "use_browser_stt", "label": "Use browser speech recognition"},
                    ],
                }
            )
    except Exception:
        issues.append(
            {
                "code": "missing_whisper",
                "severity": "warning",
                "message": "Whisper module error",
                "actions": [{"id": "check_logs", "label": "Check logs"}],
            }
        )

    piper = shutil.which("piper")
    if piper:
        healthy.append("piper")
    else:
        issues.append(
            {
                "code": "missing_piper",
                "severity": "warning",
                "message": "Piper TTS binary not found on PATH",
                "actions": [
                    {"id": "install_piper", "label": "Install Piper"},
                    {"id": "use_browser_tts", "label": "Use browser TTS"},
                ],
            }
        )

    try:
        import os

        has_gemini = bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))
        if has_gemini:
            healthy.append("gemini_live_key")
        else:
            issues.append(
                {
                    "code": "cloud_key_missing",
                    "severity": "info",
                    "message": "Gemini Live API key not configured",
                    "actions": [{"id": "set_gemini_key", "label": "Set GOOGLE_API_KEY"}],
                }
            )
    except Exception:
        pass

    try:
        from jarvis.tts_playback_queue import get_queue_status

        q = get_queue_status()
        depth = int(q.get("pending") or 0)
        if depth > 8:
            issues.append(
                {
                    "code": "high_latency",
                    "severity": "warning",
                    "message": f"TTS queue depth high ({depth})",
                    "actions": [
                        {"id": "clear_queue", "label": "Clear TTS queue"},
                        {"id": "stop_speaking", "label": "Stop speaking"},
                    ],
                }
            )
        else:
            healthy.append("tts_queue")
    except Exception:
        healthy.append("tts_queue_unknown")

    try:
        from jarvis.voice_product.settings import load_unified_settings

        settings = load_unified_settings()
        if settings.get("duplex_mode") == "full" and not settings.get("full_duplex_enabled", True):
            issues.append(
                {
                    "code": "duplex_unavailable",
                    "severity": "info",
                    "message": "Full duplex requested but not enabled",
                    "actions": [{"id": "use_half_duplex", "label": "Switch to half duplex"}],
                }
            )
    except Exception:
        pass

    severity = "ok"
    if any(i.get("severity") == "error" for i in issues):
        severity = "error"
    elif any(i.get("severity") == "warning" for i in issues):
        severity = "warning"
    elif issues:
        severity = "info"

    return {
        "ok": severity in ("ok", "info"),
        "severity": severity,
        "healthy": healthy,
        "issues": issues,
        "mic_note": (
            "Browser mic permission is checked in the client; "
            "server Whisper enables voice without browser STT."
        ),
    }


def apply_recovery_action(action_id: str) -> dict[str, Any]:
    aid = (action_id or "").strip()
    if aid == "stop_speaking":
        from jarvis.voice_product.engine import stop_speaking

        stop_speaking()
        return {"ok": True, "action": aid}
    if aid == "clear_queue":
        try:
            from jarvis.tts_playback_queue import clear_tts_queue

            clear_tts_queue()
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "action": aid}
    if aid == "use_half_duplex":
        from jarvis.voice_product.settings import save_unified_settings

        save_unified_settings({"duplex_mode": "half"})
        return {"ok": True, "action": aid}
    return {"ok": False, "error": "unknown_action", "action": aid}
