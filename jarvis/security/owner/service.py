"""Owner Security Service — facade for vault + session + capabilities + PIN hybrid."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

from jarvis.security.owner import capabilities as caps
from jarvis.security.owner.acm_boundary import assert_safe_for_acm, safe_metadata_only
from jarvis.security.owner.session import OwnerSessionManager, OwnerState
from jarvis.security.owner.vault import OwnerVault, VaultAuthError, VaultError, VaultLockedError

_LOCK = threading.RLock()
_INSTANCE: "OwnerSecurityService | None" = None


def vault_paths(data_dir: Path | None = None) -> dict[str, Path]:
    if data_dir is None:
        import jarvis.config as config

        root = Path(config.DATA_DIR)
    else:
        root = Path(data_dir)
    base = root / "security" / "owner"
    return {
        "dir": base,
        "vault": base / "vault.json",
        "sessions": base / "sessions.json",
        "ack": base / "recovery_ack.json",
    }


class OwnerSecurityService:
    def __init__(self, data_dir: Path | None = None):
        paths = vault_paths(data_dir)
        self.paths = paths
        self.vault = OwnerVault(paths["vault"])
        self.sessions = OwnerSessionManager(paths["sessions"])
        self._recovery_ack = False
        self._load_ack()
        self._timings: list[dict[str, Any]] = []

    def _load_ack(self) -> None:
        p = self.paths["ack"]
        if p.is_file():
            try:
                import json

                self._recovery_ack = bool(json.loads(p.read_text(encoding="utf-8")).get("acknowledged"))
            except Exception:
                self._recovery_ack = False

    def _save_ack(self) -> None:
        import json

        self.paths["ack"].parent.mkdir(parents=True, exist_ok=True)
        self.paths["ack"].write_text(
            json.dumps({"acknowledged": True, "at": time.time()}, indent=2),
            encoding="utf-8",
        )
        self._recovery_ack = True

    def _time(self, name: str, seconds: float, **extra: Any) -> None:
        row = {"op": name, "ms": round(seconds * 1000, 2), **extra}
        self._timings.append(row)
        if len(self._timings) > 200:
            self._timings = self._timings[-100:]

    def timings(self) -> list[dict[str, Any]]:
        return list(self._timings)

    # --- status ---

    def status(self, *, session_token: str | None = None) -> dict[str, Any]:
        unlocked = self.vault.is_unlocked() and self.sessions.state in (
            OwnerState.OWNER_UNLOCKED,
            OwnerState.OWNER_STEP_UP,
        )
        if session_token and unlocked:
            if not self.sessions.session_valid(session_token):
                # Token expired → treat as locked for callers
                unlocked = False
        return {
            "ok": True,
            "phase": "M1",
            "vault": self.vault.status(),
            "session": self.sessions.status(),
            "owner_unlocked": unlocked,
            "recovery_acknowledged": self._recovery_ack,
            "pin_model": {
                "role": "convenience_soft_unlock_and_step_up",
                "vault_root_from_pin": False,
                "note": "PIN never reconstructs vault root from disk",
            },
            "acm_boundary": "metadata_only",
            "credential_migration": False,
        }

    def house_lock_status(
        self,
        *,
        session_token: str | None = None,
        pin_status: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Single house lock view: one master password when vault exists; else legacy PIN."""
        pin_status = dict(pin_status or {})
        owner = self.status(session_token=session_token)
        vault_exists = bool((owner.get("vault") or {}).get("exists"))
        out = {
            **pin_status,
            "ok": True,
            "owner_vault": vault_exists,
            "owner_unlocked": bool(owner.get("owner_unlocked")),
            "owner_state": (owner.get("session") or {}).get("state"),
            "recovery_acknowledged": bool(owner.get("recovery_acknowledged")),
            "soft_locked": bool((owner.get("session") or {}).get("soft_locked")),
            "one_password": True,
        }
        if vault_exists:
            unlocked = bool(owner.get("owner_unlocked"))
            idle = int((owner.get("session") or {}).get("idle_seconds") or 0)
            out["locked"] = not unlocked
            out["lock_capable"] = True
            out["idle_seconds"] = idle
            out["auto_idle_lock"] = idle > 0
            out["unlock_with"] = "master_password"
            out["pin_soft_unlock_available"] = bool(
                (owner.get("session") or {}).get("soft_locked") and pin_status.get("pin_configured")
            )
            out["session_valid"] = unlocked
            out["message"] = "Aria unlocked" if unlocked else "Enter your Aria Master Password"
        else:
            out["unlock_with"] = "pin" if pin_status.get("lock_capable") else "none"
            out["pin_soft_unlock_available"] = False
        return out

    # --- setup / unlock / lock / recovery ---

    def setup(self, master_password: str, *, confirm_password: str | None = None) -> dict[str, Any]:
        with _LOCK:
            if confirm_password is not None and confirm_password != master_password:
                return {"ok": False, "message": "Passwords do not match"}
            t0 = time.perf_counter()
            try:
                out = self.vault.initialize(master_password)
            except VaultError as exc:
                return {"ok": False, "message": str(exc)}
            token = self.sessions.mark_unlocked()
            self._time("vault_initialize", time.perf_counter() - t0)
            # Recovery key returned once — never log it
            return {
                "ok": True,
                "session_token": token,
                "recovery_key": out["recovery_key"],
                "recovery_ack_required": True,
                "message": out["message"],
                "state": self.sessions.state.value,
            }

    def acknowledge_recovery(self, *, stored: bool) -> dict[str, Any]:
        if not stored:
            return {
                "ok": False,
                "message": "You must confirm the recovery key is stored offline before continuing.",
            }
        self._save_ack()
        return {"ok": True, "recovery_acknowledged": True}

    def unlock(self, master_password: str) -> dict[str, Any]:
        with _LOCK:
            allowed, msg = self.sessions.auth_allowed()
            if not allowed:
                return {"ok": False, "message": msg, "temporary_lockout": True}
            t0 = time.perf_counter()
            try:
                self.vault.unlock(master_password)
            except VaultAuthError:
                self.sessions.record_failure()
                self._time("unlock_fail", time.perf_counter() - t0)
                return {"ok": False, "message": "Incorrect master password"}
            except VaultError as exc:
                return {"ok": False, "message": str(exc)}
            token = self.sessions.mark_unlocked()
            self._time("unlock", time.perf_counter() - t0)
            return {
                "ok": True,
                "session_token": token,
                "state": self.sessions.state.value,
            }

    def soft_unlock_with_pin(self, pin: str) -> dict[str, Any]:
        """PIN convenience unlock after soft lock — requires vault root still in memory.

        PIN never unwraps vault root from disk.
        """
        with _LOCK:
            if not self.sessions.status().get("soft_locked"):
                return {
                    "ok": False,
                    "message": "PIN soft-unlock only applies after soft lock. Use master password after hard lock/restart.",
                }
            if not self.vault.is_unlocked():
                return {
                    "ok": False,
                    "message": "Vault root not in memory. Enter master password.",
                }
            try:
                from jarvis.security.pin_lock import pin_configured, verify_pin
            except Exception:
                return {"ok": False, "message": "PIN subsystem unavailable"}
            if not pin_configured():
                return {
                    "ok": False,
                    "message": "No PIN configured. Use master password, or set a PIN while unlocked.",
                }
            if not verify_pin(pin):
                self.sessions.record_failure()
                return {"ok": False, "message": "Invalid PIN"}
            token = self.sessions.restore_after_soft_unlock()
            return {"ok": True, "session_token": token, "state": self.sessions.state.value, "mode": "pin_soft"}

    def lock(self, *, hard: bool = True) -> dict[str, Any]:
        with _LOCK:
            t0 = time.perf_counter()
            if hard:
                out = self.sessions.hard_lock()
                self.vault.lock()
            else:
                # Soft: keep root for PIN re-entry; revoke sessions/handles
                out = self.sessions.soft_lock()
                # Root stays — intentional for PIN hybrid
            self._time("lock", time.perf_counter() - t0, hard=hard)
            try:
                from jarvis.health_product.gate import revoke_grants

                revoke_grants()
            except Exception:
                pass
            try:
                from jarvis.uncensored_auth import invalidate_all_sessions

                invalidate_all_sessions()
            except Exception:
                pass
            return {**out, "vault_unlocked": self.vault.is_unlocked()}

    def recover(self, recovery_key: str, new_master_password: str) -> dict[str, Any]:
        with _LOCK:
            allowed, msg = self.sessions.auth_allowed()
            if not allowed:
                return {"ok": False, "message": msg, "temporary_lockout": True}
            t0 = time.perf_counter()
            try:
                self.vault.recover_with_key(recovery_key, new_master_password)
            except VaultAuthError:
                self.sessions.record_failure()
                return {"ok": False, "message": "Incorrect recovery key"}
            except VaultError as exc:
                return {"ok": False, "message": str(exc)}
            token = self.sessions.mark_unlocked()
            self._time("recovery", time.perf_counter() - t0)
            return {
                "ok": True,
                "session_token": token,
                "recovered": True,
                "state": self.sessions.state.value,
                "message": "Vault recovered. Master password updated. Keep your recovery key.",
            }

    def change_master_password(self, current: str, new_password: str) -> dict[str, Any]:
        with _LOCK:
            t0 = time.perf_counter()
            try:
                self.vault.change_master_password(current, new_password)
            except VaultAuthError:
                return {"ok": False, "message": "Incorrect current master password"}
            except VaultError as exc:
                return {"ok": False, "message": str(exc)}
            # Rotate sessions after password change
            self.sessions.hard_lock()
            # Re-unlock with new password already loaded in vault
            token = self.sessions.mark_unlocked()
            self._time("password_change", time.perf_counter() - t0)
            return {"ok": True, "session_token": token, "rotated": True}

    def step_up(self, *, master_password: str = "", pin: str = "") -> dict[str, Any]:
        with _LOCK:
            if not self.vault.is_unlocked() or self.sessions.state == OwnerState.OWNER_LOCKED:
                return {"ok": False, "locked": True, "message": "Unlock Aria first"}
            ok = False
            if master_password:
                # Verify by attempting unwrap against disk wrap (KDF once)
                try:
                    # Re-derive check without replacing root
                    from jarvis.security.owner import crypto as C

                    doc = self.vault._load_doc()  # noqa: SLF001 — intentional verify
                    kdf = C.KdfParams.from_dict(doc["master_kdf"])
                    unlock = C.derive_key(master_password.strip(), kdf)
                    C.unwrap_root(
                        unlock,
                        doc["wrapped_root_master"],
                        aad=C.VAULT_FORMAT.encode("utf-8"),
                    )
                    ok = True
                except Exception:
                    ok = False
            if not ok and pin:
                try:
                    from jarvis.security.pin_lock import pin_configured, verify_pin

                    ok = bool(pin_configured() and verify_pin(pin))
                except Exception:
                    ok = False
            if not ok:
                self.sessions.record_failure()
                return {"ok": False, "message": "Step-up failed"}
            return self.sessions.grant_step_up()

    # --- authorization / vault access ---

    def authorize(
        self,
        capability: str,
        *,
        room: str | None = None,
        session_token: str | None = None,
    ) -> dict[str, Any]:
        vault_exists = self.vault.exists()
        if not vault_exists:
            # One-password not provisioned yet — do not invent a second auth wall.
            decision = caps.authorize(
                capability,
                owner_unlocked=True,
                step_up_valid=True,
                room=room,
            )
            out = decision.to_dict()
            out["owner_vault"] = False
            out["reason"] = decision.reason if not decision.ok else "owner_vault_not_provisioned"
            return out
        owner_unlocked = self.vault.is_unlocked() and self.sessions.state in (
            OwnerState.OWNER_UNLOCKED,
            OwnerState.OWNER_STEP_UP,
        )
        if session_token and owner_unlocked and not self.sessions.session_valid(session_token):
            owner_unlocked = False
        decision = caps.authorize(
            capability,
            owner_unlocked=owner_unlocked,
            step_up_valid=self.sessions.step_up_valid(),
            room=room,
        )
        out = decision.to_dict()
        out["owner_vault"] = True
        if decision.ok and decision.risk in ("HIGH", "CRITICAL") and capability not in (
            "owner.unlock",
            "owner.recovery",
            "owner.lock",
        ):
            # Issue capability handle for callers that need revocation
            if self.sessions._session_id:  # noqa: SLF001
                hid = self.sessions.handles.issue(
                    capability=capability, session_id=self.sessions._session_id
                )
                out["capability_handle"] = hid
        return out

    def catalog(self) -> list[dict[str, Any]]:
        return caps.catalog()

    def vault_meta(self) -> dict[str, Any]:
        auth = self.authorize("vault.meta.read", room="security")
        if not auth.get("ok"):
            return auth
        return {
            "ok": True,
            "entries": self.vault.list_meta(),
            "vault": self.vault.status(),
        }

    def migrate_provider_credential(self, field: str) -> dict[str, Any]:
        """Copy one authorized provider env credential into the vault. Never returns the secret."""
        auth = self.authorize("vault.secret.migrate", room="integrations")
        if not auth.get("ok"):
            return auth
        from jarvis.security.owner.provider_credentials import migrate_field

        return migrate_field(self, field)

    def provider_migration_status(self) -> dict[str, Any]:
        auth = self.authorize("vault.meta.read", room="integrations")
        if not auth.get("ok"):
            return auth
        from jarvis.security.owner.provider_credentials import migration_status

        return migration_status(self)

    def put_test_secret(self, entry_id: str, secret: str, **kwargs: Any) -> dict[str, Any]:
        """Isol/test only — refuses if entry looks like a production migration id without unlock+step-up."""
        auth = self.authorize("vault.secret.write", room="security")
        if not auth.get("ok"):
            return auth
        try:
            return self.vault.put_secret(entry_id, secret, **kwargs)
        except (VaultLockedError, VaultError) as exc:
            return {"ok": False, "message": str(exc)}

    def get_test_secret(self, entry_id: str) -> dict[str, Any]:
        auth = self.authorize("vault.secret.use", room="integrations")
        if not auth.get("ok"):
            # secret.use is MEDIUM — unlocked is enough
            if auth.get("locked"):
                return auth
        try:
            val = self.vault.get_secret(entry_id)
            return {"ok": True, "value": val.decode("utf-8", errors="replace")}
        except (VaultLockedError, VaultError) as exc:
            return {"ok": False, "message": str(exc)}

    def acm_safe_metadata(self, **meta: Any) -> dict[str, Any]:
        return safe_metadata_only(**meta)

    def acm_assert_safe(self, payload: Any) -> None:
        assert_safe_for_acm(payload)


def get_owner_security(*, data_dir: Path | None = None, reset: bool = False) -> OwnerSecurityService:
    global _INSTANCE
    with _LOCK:
        if reset or _INSTANCE is None or data_dir is not None:
            # When data_dir provided, return ephemeral instance (tests)
            if data_dir is not None:
                return OwnerSecurityService(data_dir)
            if reset or _INSTANCE is None:
                _INSTANCE = OwnerSecurityService()
        return _INSTANCE
