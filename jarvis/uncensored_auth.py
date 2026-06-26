"""Password gate for uncensored mode."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
from pathlib import Path

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis")

AUTH_FILE = DATA_DIR / "uncensored_auth.json"
SESSIONS_FILE = DATA_DIR / "uncensored_sessions.json"
SESSION_TTL = int(os.getenv("JARVIS_UNCENSORED_SESSION_HOURS", "12")) * 3600
_PBKDF2_ITERS = 120_000
_MAX_FAILURES = int(os.getenv("JARVIS_UNCENSORED_MAX_ATTEMPTS", "5"))
_LOCKOUT_SECONDS = int(os.getenv("JARVIS_UNCENSORED_LOCKOUT_SEC", "300"))

_sessions: dict[str, float] = {}
_failed_attempts: dict[str, list[float]] = {}


def _load_auth() -> dict | None:
    if not AUTH_FILE.exists():
        return None
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERS).hex()


def clear_password() -> None:
    """Remove stored password (standard mode only — caller must verify)."""
    try:
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()
    except OSError as exc:
        log.warning("Could not remove uncensored auth file: %s", exc)
    invalidate_all_sessions()
    _failed_attempts.clear()


def is_configured() -> bool:
    data = _load_auth()
    return bool(data and data.get("salt") and data.get("hash"))


def set_password(password: str) -> None:
    password = (password or "").strip()
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters")
    salt = os.urandom(16)
    payload = {"salt": salt.hex(), "hash": _hash_password(password, salt)}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    AUTH_FILE.chmod(0o600)


def verify_password(password: str) -> bool:
    data = _load_auth()
    if not data:
        return False
    try:
        salt = bytes.fromhex(data["salt"])
        expected = data["hash"]
    except (KeyError, ValueError, TypeError):
        return False
    got = _hash_password(password or "", salt)
    return secrets.compare_digest(got, expected)


def _prune_sessions() -> None:
    now = time.time()
    expired = [token for token, expiry in _sessions.items() if expiry <= now]
    for token in expired:
        _sessions.pop(token, None)


def _save_sessions() -> None:
    _prune_sessions()
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SESSIONS_FILE.write_text(json.dumps(_sessions), encoding="utf-8")
        SESSIONS_FILE.chmod(0o600)
    except OSError as exc:
        log.warning("Could not persist uncensored sessions: %s", exc)


def _load_sessions() -> None:
    global _sessions
    if not SESSIONS_FILE.exists():
        return
    try:
        raw = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            _sessions = {str(k): float(v) for k, v in raw.items()}
            _prune_sessions()
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        log.warning("Could not load uncensored sessions: %s", exc)


_load_sessions()


def _prune_failures(client_id: str) -> None:
    now = time.time()
    attempts = _failed_attempts.get(client_id, [])
    attempts = [t for t in attempts if now - t < _LOCKOUT_SECONDS]
    if attempts:
        _failed_attempts[client_id] = attempts
    else:
        _failed_attempts.pop(client_id, None)


def lockout_remaining(client_id: str = "local") -> int:
    _prune_failures(client_id)
    attempts = _failed_attempts.get(client_id, [])
    if len(attempts) < _MAX_FAILURES:
        return 0
    oldest = min(attempts)
    return max(0, int(_LOCKOUT_SECONDS - (time.time() - oldest)))


def _record_failure(client_id: str) -> None:
    now = time.time()
    attempts = _failed_attempts.setdefault(client_id, [])
    attempts.append(now)
    _prune_failures(client_id)


def _clear_failures(client_id: str) -> None:
    _failed_attempts.pop(client_id, None)


def create_session() -> str:
    _prune_sessions()
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time() + SESSION_TTL
    _save_sessions()
    return token


def validate_session(token: str) -> bool:
    if not token:
        return False
    _prune_sessions()
    expiry = _sessions.get(token)
    if not expiry or expiry <= time.time():
        _sessions.pop(token, None)
        _save_sessions()
        return False
    return True


def invalidate_session(token: str) -> None:
    if token and _sessions.pop(token, None) is not None:
        _save_sessions()


def invalidate_all_sessions() -> None:
    global _sessions
    if _sessions:
        _sessions = {}
        _save_sessions()


def try_enable(
    password: str = "",
    session_token: str = "",
    confirm: str = "",
    *,
    client_id: str = "local",
) -> tuple[str | None, str | None]:
    """Validate unlock for enabling uncensored mode. Returns (session_token, error)."""
    remaining = lockout_remaining(client_id)
    if remaining > 0:
        return None, f"Too many attempts — try again in {remaining // 60 + 1} min"

    if validate_session(session_token):
        return session_token or create_session(), None

    password = (password or "").strip()
    confirm = (confirm or "").strip()

    if not is_configured():
        if len(password) < 4:
            return None, "Choose a password (at least 4 characters)"
        if not confirm:
            return None, "Confirm password required"
        if password != confirm:
            return None, "Passwords do not match — check both fields (no extra spaces)"
        set_password(password)
        _clear_failures(client_id)
        return create_session(), None

    if verify_password(password):
        _clear_failures(client_id)
        return create_session(), None

    _record_failure(client_id)
    return None, "Wrong password"


def auth_status(session_token: str = "", *, client_id: str = "local") -> dict:
    return {
        "configured": is_configured(),
        "session_valid": validate_session(session_token),
        "session_hours": SESSION_TTL // 3600,
        "lockout_seconds": lockout_remaining(client_id),
    }


def enforce_env_unlock() -> bool:
    """CLI / launch script: allow env uncensored only when password matches (if configured)."""
    if not is_configured():
        env_pw = os.getenv("JARVIS_UNCENSORED_PASSWORD", "").strip()
        if env_pw:
            set_password(env_pw)
        return True
    env_pw = os.getenv("JARVIS_UNCENSORED_PASSWORD", "").strip()
    return bool(env_pw and verify_password(env_pw))
