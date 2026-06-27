"""P4 feature flags — security, presence, desktop shell."""

from __future__ import annotations

import os


def _env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "off")


def pin_lock_enabled() -> bool:
    return _env("JARVIS_PIN_LOCK", "0")


def face_auth_enabled() -> bool:
    return _env("JARVIS_FACE_AUTH", "0")


def trusted_lan_enabled() -> bool:
    return _env("JARVIS_TRUSTED_LAN", "1")


def gestures_enabled() -> bool:
    return _env("JARVIS_GESTURES", "0")


def cloud_live_voice_enabled() -> bool:
    explicit = os.getenv("JARVIS_CLOUD_LIVE_VOICE", "").strip().lower()
    if explicit in ("0", "false", "no", "off"):
        return False
    if explicit in ("1", "true", "yes", "on"):
        return True
    gemini = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    openai = (os.getenv("OPENAI_API_KEY") or "").strip()
    return bool(gemini or openai)


def floating_panels_enabled() -> bool:
    return _env("JARVIS_FLOATING_PANELS", "1")


def socketio_enabled() -> bool:
    return _env("JARVIS_SOCKETIO", "0")


def electron_shell_enabled() -> bool:
    return _env("JARVIS_ELECTRON_SHELL", "1")


def pyside_shell_enabled() -> bool:
    return _env("JARVIS_PYSIDE_SHELL", "1")


def lock_idle_seconds() -> int:
    try:
        return max(60, int(os.getenv("JARVIS_LOCK_IDLE_SEC", "900")))
    except ValueError:
        return 900


def p4_flags() -> dict:
    from jarvis.p3_flags import p3_flags as _p3

    base = _p3()
    base.update(
        {
            "pin_lock": pin_lock_enabled(),
            "face_auth": face_auth_enabled(),
            "trusted_lan": trusted_lan_enabled(),
            "gestures": gestures_enabled(),
            "cloud_live_voice": cloud_live_voice_enabled(),
            "floating_panels": floating_panels_enabled(),
            "socketio": socketio_enabled(),
            "electron_shell": electron_shell_enabled(),
            "pyside_shell": pyside_shell_enabled(),
        }
    )
    return base
