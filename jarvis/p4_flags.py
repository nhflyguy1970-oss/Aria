"""P4 feature flags — security, presence, desktop shell."""

from __future__ import annotations

import os


def _env(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "off")


def pin_lock_enabled() -> bool:
    return _env("JARVIS_PIN_LOCK", "0")


def health_step_up_enabled() -> bool:
    """Sensitive Health ops: Owner Security step-up when the vault exists."""
    explicit = os.getenv("JARVIS_HEALTH_STEP_UP", "").strip().lower()
    if explicit in ("0", "false", "no", "off"):
        return False
    if explicit in ("1", "true", "yes", "on"):
        return True
    try:
        from pathlib import Path

        from jarvis.config import DATA_DIR
        from jarvis.security.owner.service import vault_paths

        if vault_paths(Path(DATA_DIR))["vault"].is_file():
            if os.getenv("PYTEST_CURRENT_TEST"):
                from jarvis.env_loader import PROJECT_ROOT

                live = (PROJECT_ROOT / "data" / "security" / "owner" / "vault.json").resolve()
                if vault_paths(Path(DATA_DIR))["vault"].resolve() == live:
                    return pin_lock_enabled()
            return True
    except Exception:
        pass
    return pin_lock_enabled()


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
    """Owner idle re-lock in seconds. 0 = no automatic idle lock (daily-use default).

    Opt-in only via JARVIS_OWNER_IDLE_SECONDS. PIN-era JARVIS_LOCK_IDLE / JARVIS_LOCK_IDLE_SEC
    are ignored so a leftover 900s PIN idle in jarvis.env cannot lock the house.
    Restart and explicit Lock Aria still lock the house.
    """
    raw = os.getenv("JARVIS_OWNER_IDLE_SECONDS") or "0"
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def p4_flags() -> dict:
    from jarvis.p3_flags import p3_flags as _p3

    base = _p3()
    base.update(
        {
            "pin_lock": pin_lock_enabled(),
            "health_step_up": health_step_up_enabled(),
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
