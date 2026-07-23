"""GUI security — PIN lock, sessions, idle re-lock."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p4_flags import face_auth_enabled, lock_idle_seconds, pin_lock_enabled

PIN_FILE = DATA_DIR / "security" / "pin.json"
SESSIONS_FILE = DATA_DIR / "security" / "sessions.json"


def _ensure_dir() -> None:
    PIN_FILE.parent.mkdir(parents=True, exist_ok=True)


def pin_configured() -> bool:
    return PIN_FILE.is_file()


def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 120_000).hex()


def set_pin(pin: str) -> dict[str, Any]:
    pin = (pin or "").strip()
    if not pin.isdigit() or not (4 <= len(pin) <= 6):
        raise ValueError("PIN must be 4–6 digits")
    _ensure_dir()
    salt = secrets.token_hex(16)
    PIN_FILE.write_text(
        json.dumps({"salt": salt, "hash": _hash_pin(pin, salt)}, indent=2),
        encoding="utf-8",
    )
    return {"ok": True, "configured": True}


def verify_pin(pin: str) -> bool:
    import hmac

    if not PIN_FILE.is_file():
        return False
    try:
        data = json.loads(PIN_FILE.read_text(encoding="utf-8"))
        got = _hash_pin((pin or "").strip(), data["salt"])
        expected = data["hash"]
        return hmac.compare_digest(got, expected)
    except (json.JSONDecodeError, OSError, KeyError, TypeError):
        return False


def _load_sessions() -> dict[str, Any]:
    if not SESSIONS_FILE.is_file():
        return {"sessions": {}}
    try:
        return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"sessions": {}}


def _save_sessions(data: dict[str, Any]) -> None:
    _ensure_dir()
    SESSIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_session(*, device_id: str | None = None) -> str:
    token = secrets.token_urlsafe(32)
    data = _load_sessions()
    data.setdefault("sessions", {})[token] = {
        "created": time.time(),
        "last_active": time.time(),
        "device_id": device_id or "",
    }
    _save_sessions(data)
    return token


def touch_session(token: str | None) -> bool:
    if not token:
        return False
    data = _load_sessions()
    row = data.get("sessions", {}).get(token)
    if not row:
        return False
    row["last_active"] = time.time()
    _save_sessions(data)
    return True


def session_valid(token: str | None) -> bool:
    if not token:
        return False
    if not pin_lock_enabled():
        return True
    if not pin_configured():
        return True
    data = _load_sessions()
    row = data.get("sessions", {}).get(token)
    if not row:
        return False
    idle = lock_idle_seconds()
    if time.time() - float(row.get("last_active", 0)) > idle:
        revoke_session(token)
        return False
    return True


def revoke_session(token: str | None) -> None:
    if not token:
        return
    data = _load_sessions()
    data.get("sessions", {}).pop(token, None)
    _save_sessions(data)


def revoke_all_sessions() -> int:
    data = _load_sessions()
    count = len(data.get("sessions") or {})
    data["sessions"] = {}
    _save_sessions(data)
    return count


def lock_status(*, session_token: str | None = None) -> dict[str, Any]:
    valid = session_valid(session_token) if session_token else not pin_configured()
    locked = pin_lock_enabled() and pin_configured() and not valid
    return {
        "ok": True,
        "locked": locked,
        "pin_lock_enabled": pin_lock_enabled(),
        "pin_configured": pin_configured(),
        "face_auth_enabled": face_auth_enabled(),
        "idle_seconds": lock_idle_seconds(),
        "lock_capable": pin_configured(),
        "session_valid": valid,
    }
