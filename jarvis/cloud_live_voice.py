"""Optional cloud live voice — OpenAI Realtime + Gemini Live (#84)."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any
from urllib import error, request

from jarvis.p4_flags import cloud_live_voice_enabled

log = logging.getLogger("jarvis.cloud_live")
_SESSIONS: dict[str, dict[str, Any]] = {}
OPENAI_REALTIME_MODEL = os.getenv("JARVIS_OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview-2024-12-17")
GEMINI_LIVE_MODEL = os.getenv("JARVIS_GEMINI_LIVE_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
OPENAI_WEBRTC_CLIENT_READY = False


def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or "").strip()


def _gemini_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()


def _openai_key_usable() -> bool:
    key = _openai_key()
    return bool(key) and key.startswith(("sk-", "sk_"))


def _gemini_key_usable() -> bool:
    key = _gemini_key()
    if not key or len(key) < 16:
        return False
    if key.startswith("AIza"):
        return True
    if key.startswith("AQ."):
        return True
    return len(key) >= 20


def _preferred_provider(*, openai: bool, gemini: bool) -> str:
    prefer = (os.getenv("JARVIS_CLOUD_LIVE_PROVIDER") or "auto").strip().lower()
    openai_ok = _openai_key_usable()
    gemini_ok = _gemini_key_usable()
    if prefer == "gemini_live" and gemini_ok:
        return "gemini_live"
    if prefer == "openai_realtime" and openai_ok:
        return "openai_realtime"
    if prefer == "auto":
        if gemini_ok and not openai_ok:
            return "gemini_live"
        if openai_ok:
            return "openai_realtime"
        if gemini_ok:
            return "gemini_live"
        return ""
    if openai_ok:
        return "openai_realtime"
    if gemini_ok:
        return "gemini_live"
    return ""


def cloud_live_status() -> dict[str, Any]:
    openai_raw = bool(_openai_key())
    gemini_raw = bool(_gemini_key())
    openai = _openai_key_usable()
    gemini = _gemini_key_usable()
    gemini_key = _gemini_key()
    gemini_key_warning = ""
    if gemini_raw and gemini_key.startswith("AQ."):
        gemini_key_warning = (
            " Gemini key format looks unusual — paste an AIza… key from Google AI Studio."
        )
    enabled = cloud_live_voice_enabled()
    provider = _preferred_provider(openai=openai_raw, gemini=gemini_raw) if enabled else ""
    if provider == "openai_realtime" and not OPENAI_WEBRTC_CLIENT_READY:
        if gemini:
            provider = "gemini_live"
        else:
            provider = ""
    key_hint = ""
    if enabled and not provider:
        if openai_raw and not openai:
            key_hint = " OpenAI key must start with sk- (Integrations → re-save)."
        elif gemini_raw and not gemini:
            key_hint = " Gemini key looks invalid — re-save from Google AI Studio."
        elif gemini_key_warning:
            key_hint = gemini_key_warning
        elif openai and OPENAI_WEBRTC_CLIENT_READY and gemini:
            key_hint = " OpenAI Realtime needs a WebRTC client — add a Gemini key."
        else:
            key_hint = " Add a Gemini or OpenAI API key in Integrations."
    available = bool(enabled and provider)
    if available:
        message = f"Cloud live ready ({provider.replace('_', ' ')})"
    elif not enabled:
        message = "Cloud live voice disabled — set JARVIS_CLOUD_LIVE_VOICE=1 and add API keys."
    else:
        message = f"Cloud live voice not configured.{key_hint}".strip()
    return {
        "available": available,
        "enabled": enabled,
        "provider": provider,
        "message": message,
        "openai_configured": openai_raw,
        "openai_usable": openai,
        "gemini_configured": gemini_raw,
        "gemini_usable": gemini,
        "webrtc_client": OPENAI_WEBRTC_CLIENT_READY,
        "active_sessions": len(_SESSIONS),
    }


def _create_openai_realtime_session() -> dict[str, Any]:
    key = _openai_key()
    if not key:
        return {"ok": False, "error": "OPENAI_API_KEY not set"}
    body = json.dumps(
        {
            "model": OPENAI_REALTIME_MODEL,
            "voice": os.getenv("JARVIS_OPENAI_REALTIME_VOICE", "verse"),
        }
    ).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/realtime/sessions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "ok": True,
            "provider": "openai_realtime",
            "model": OPENAI_REALTIME_MODEL,
            "client_secret": data.get("client_secret", {}).get("value"),
            "session": data,
        }
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        return {"ok": False, "error": detail or str(exc)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _create_gemini_live_session(session_id: str) -> dict[str, Any]:
    key = _gemini_key()
    if not key:
        return {"ok": False, "error": "GEMINI_API_KEY not set"}
    model = GEMINI_LIVE_MODEL
    if not model.startswith("models/"):
        model = f"models/{model}"
    return {
        "ok": True,
        "provider": "gemini_live",
        "session_id": session_id,
        "model": model,
        "bridge_ws": f"/ws/gemini-live/{session_id}",
        "sample_rate_in": 16000,
        "sample_rate_out": 24000,
    }


def start_live_session(*, provider: str = "") -> dict[str, Any]:
    st = cloud_live_status()
    if not st.get("available"):
        return {"ok": False, "message": st.get("message", "Cloud live voice not configured")}
    pick = (provider or st.get("provider") or "").strip().lower()
    if pick in ("openai_realtime", "openai") and not OPENAI_WEBRTC_CLIENT_READY:
        return {
            "ok": False,
            "message": "OpenAI Realtime WebRTC client is not available — use Gemini Live.",
        }
    session_id = uuid.uuid4().hex[:16]
    if pick in ("gemini_live", "gemini"):
        creds = _create_gemini_live_session(session_id)
    elif pick in ("openai_realtime", "openai"):
        creds = _create_openai_realtime_session()
        if creds.get("ok"):
            creds["session_id"] = session_id
    else:
        return {"ok": False, "message": "No cloud provider configured"}
    if not creds.get("ok"):
        return {"ok": False, "message": creds.get("error", "Cloud session failed")}
    _SESSIONS[session_id] = {**creds, "status": "pending"}
    return {
        "ok": True,
        "session_id": session_id,
        "provider": creds.get("provider"),
        "model": creds.get("model"),
        "bridge_ws": creds.get("bridge_ws"),
        "client_secret": creds.get("client_secret"),
        "message": f"Cloud live session started ({creds.get('provider')})",
    }


def get_live_session(session_id: str) -> dict[str, Any] | None:
    return _SESSIONS.get(session_id)


def mark_session_active(session_id: str) -> None:
    if session_id in _SESSIONS:
        _SESSIONS[session_id]["status"] = "active"


def end_live_session(session_id: str) -> dict[str, Any]:
    removed = _SESSIONS.pop(session_id, None)
    if not removed:
        return {"ok": False, "message": "Session not found"}
    try:
        from jarvis.events import emit_voice_state

        emit_voice_state("idle", detail="cloud-live-end")
    except Exception:
        pass
    return {"ok": True, "message": f"Ended cloud live session {session_id}"}


def list_live_sessions() -> list[dict[str, Any]]:
    return [{"session_id": sid, **row} for sid, row in _SESSIONS.items()]
