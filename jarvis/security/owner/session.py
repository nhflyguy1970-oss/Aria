"""Owner session state machine — house-wide auth for Aria."""

from __future__ import annotations

import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any

from jarvis.security.owner import crypto as C


class OwnerState(str, Enum):
    OWNER_LOCKED = "OWNER_LOCKED"
    OWNER_UNLOCKED = "OWNER_UNLOCKED"
    OWNER_STEP_UP = "OWNER_STEP_UP"
    OWNER_REVOKED = "OWNER_REVOKED"


# Capability handles issued while unlocked; invalidated on lock/revoke.
class CapabilityHandleStore:
    def __init__(self) -> None:
        self._handles: dict[str, dict[str, Any]] = {}

    def issue(self, *, capability: str, session_id: str, ttl: float = 300.0) -> str:
        hid = C.random_token()
        self._handles[hid] = {
            "capability": capability,
            "session_id": session_id,
            "expires": time.time() + ttl,
        }
        return hid

    def valid(self, handle: str, *, capability: str | None = None) -> bool:
        row = self._handles.get(handle)
        if not row:
            return False
        if row["expires"] < time.time():
            self._handles.pop(handle, None)
            return False
        if capability and row["capability"] != capability:
            return False
        return True

    def clear(self) -> int:
        n = len(self._handles)
        self._handles.clear()
        return n


class OwnerSessionManager:
    """Hashed session verifiers on disk; soft vs hard lock semantics."""

    def __init__(self, path: Path, *, idle_seconds: int | None = None):
        self.path = Path(path)
        if idle_seconds is not None:
            self.idle_seconds = max(0, int(idle_seconds))
        else:
            from jarvis.p4_flags import lock_idle_seconds

            self.idle_seconds = lock_idle_seconds()
        self.handles = CapabilityHandleStore()
        self._state = OwnerState.OWNER_LOCKED
        self._session_id: str | None = None
        self._soft_locked = False  # UI/session locked but vault root may remain
        self._step_up_until = 0.0
        self._failed_attempts = 0
        self._lockout_until = 0.0
        self._generation = 0  # bumped on revoke — invalidates in-memory grants

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def state(self) -> OwnerState:
        if self._step_up_until > time.time() and self._state == OwnerState.OWNER_UNLOCKED:
            return OwnerState.OWNER_STEP_UP
        return self._state

    def auth_allowed(self) -> tuple[bool, str]:
        now = time.time()
        if now < self._lockout_until:
            wait = int(self._lockout_until - now)
            return False, f"Too many failed attempts. Try again in {wait}s."
        return True, ""

    def record_failure(self) -> None:
        self._failed_attempts += 1
        # Temporary backoff only — never permanent lockout.
        if self._failed_attempts >= 5:
            # 30s, 60s, 120s… capped at 5 minutes
            exp = min(5, self._failed_attempts - 4)
            self._lockout_until = time.time() + min(300, 30 * (2 ** (exp - 1)))

    def record_success(self) -> None:
        self._failed_attempts = 0
        self._lockout_until = 0.0

    def mark_unlocked(self) -> str:
        """Create house-wide owner session; return bearer token (shown once)."""
        token = C.random_token()
        sid = C.random_token()[:16]
        verifier = C.token_verifier(token)
        data = self._load()
        data.setdefault("sessions", {})[verifier] = {
            "session_id": sid,
            "created": time.time(),
            "last_active": time.time(),
        }
        self._save(data)
        self._state = OwnerState.OWNER_UNLOCKED
        self._session_id = sid
        self._soft_locked = False
        self.record_success()
        return token

    def _idle_expired(self, last_active: Any) -> bool:
        if self.idle_seconds <= 0:
            return False
        try:
            return time.time() - float(last_active or 0) > self.idle_seconds
        except (TypeError, ValueError):
            return False

    def touch(self, token: str | None) -> bool:
        if not token:
            return False
        data = self._load()
        row = data.get("sessions", {}).get(C.token_verifier(token))
        if not row:
            return False
        if self._idle_expired(row.get("last_active")):
            self.revoke_token(token)
            return False
        row["last_active"] = time.time()
        self._save(data)
        return True

    def session_valid(self, token: str | None) -> bool:
        if not token:
            return False
        if self._soft_locked or self._state in (OwnerState.OWNER_LOCKED, OwnerState.OWNER_REVOKED):
            # Soft lock: token may still exist but owner considered locked for capabilities
            if self._soft_locked:
                return False
        data = self._load()
        row = data.get("sessions", {}).get(C.token_verifier(token))
        if not row:
            return False
        if self._idle_expired(row.get("last_active")):
            self.revoke_token(token)
            return False
        return True

    def soft_lock(self) -> dict[str, Any]:
        """Lock UI/capabilities; vault root may remain for PIN soft unlock (not on disk)."""
        n = self.revoke_all()
        self._state = OwnerState.OWNER_LOCKED
        self._soft_locked = True
        self._step_up_until = 0.0
        self.handles.clear()
        self._generation += 1
        return {"ok": True, "mode": "soft", "revoked_sessions": n, "state": self.state.value}

    def hard_lock(self) -> dict[str, Any]:
        """Full lock — caller must also wipe vault root."""
        n = self.revoke_all()
        self._state = OwnerState.OWNER_REVOKED
        self._soft_locked = False
        self._session_id = None
        self._step_up_until = 0.0
        self.handles.clear()
        self._generation += 1
        # After revoke, settle to LOCKED for status UX
        self._state = OwnerState.OWNER_LOCKED
        return {"ok": True, "mode": "hard", "revoked_sessions": n, "state": self.state.value}

    def restore_after_soft_unlock(self) -> str:
        """PIN soft unlock: re-issue session without vault KDF."""
        if not self._soft_locked:
            raise RuntimeError("Not soft-locked")
        self._soft_locked = False
        self._state = OwnerState.OWNER_UNLOCKED
        return self.mark_unlocked()

    def grant_step_up(self, ttl: float = 180.0) -> dict[str, Any]:
        if self._state != OwnerState.OWNER_UNLOCKED and self.state != OwnerState.OWNER_STEP_UP:
            raise RuntimeError("Owner must be unlocked before step-up")
        self._step_up_until = time.time() + ttl
        self._state = OwnerState.OWNER_UNLOCKED
        return {"ok": True, "step_up_until": self._step_up_until, "ttl": ttl}

    def step_up_valid(self) -> bool:
        return self._step_up_until > time.time()

    def revoke_token(self, token: str | None) -> None:
        if not token:
            return
        data = self._load()
        data.get("sessions", {}).pop(C.token_verifier(token), None)
        self._save(data)

    def revoke_all(self) -> int:
        data = self._load()
        n = len(data.get("sessions") or {})
        data["sessions"] = {}
        self._save(data)
        return n

    def status(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "soft_locked": self._soft_locked,
            "step_up_valid": self.step_up_valid(),
            "idle_seconds": self.idle_seconds,
            "auto_idle_lock": self.idle_seconds > 0,
            "failed_attempts": self._failed_attempts,
            "lockout_active": time.time() < self._lockout_until,
            "generation": self._generation,
            "session_active": self._session_id is not None and self._state != OwnerState.OWNER_LOCKED,
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"sessions": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"sessions": {}}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass
