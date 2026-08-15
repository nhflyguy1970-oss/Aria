"""Health access gate — Owner session first; step-up only for sensitive ops.

LAN API key and HA token are not Health authenticators.
Portable backup passwords are not Owner credentials.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

# Ordinary Health Room use (timeline, check-in, viewing) is NOT in this set.
# These are the ops actually wired through _gate_or_response.
SENSITIVE_OPS = frozenset(
    {
        "export_record",
        "edit_medications",
        "edit_allergies",
        "edit_conditions",
        "edit_family_history",
        "edit_emergency",
        "delete_record",
        "cloud_consult",
        "backup_create",
        "backup_restore",
        "view_full_record",
        "emergency_info",
    }
)

# Ops whose JSON body.password is a portable-file secret, never Owner auth.
PORTABLE_PASSWORD_OPS = frozenset({"backup_create", "backup_restore"})

_GRANTS: dict[str, dict[str, float]] = {}  # token -> {op: expires}
_GRANT_GENERATION = 0


def revoke_grants() -> None:
    """Owner lock / restart — drop in-memory Health step-up grants."""
    global _GRANT_GENERATION
    _GRANTS.clear()
    _GRANT_GENERATION += 1


def _owner_service():
    try:
        from jarvis.config import DATA_DIR
        from jarvis.env_loader import PROJECT_ROOT
        from jarvis.security.owner.service import get_owner_security, vault_paths

        data_dir = Path(DATA_DIR)
        expected = vault_paths(data_dir)["vault"]
        if os.getenv("PYTEST_CURRENT_TEST"):
            live = (PROJECT_ROOT / "data" / "security" / "owner").resolve()
            try:
                if expected.resolve().is_relative_to(live):
                    return None
            except Exception:
                return None
        svc = get_owner_security()
        try:
            if Path(svc.paths["vault"]) != Path(expected):
                svc = get_owner_security(data_dir=data_dir)
        except Exception:
            svc = get_owner_security(data_dir=data_dir)
        if not svc.vault.exists():
            return None
        return svc
    except Exception:
        return None


def owner_vault_configured() -> bool:
    svc = _owner_service()
    try:
        return bool(svc and svc.vault.exists())
    except Exception:
        return False


def owner_unlocked() -> bool:
    svc = _owner_service()
    if not svc:
        return True
    try:
        if not svc.vault.exists():
            return True
        return bool(svc.vault.is_unlocked() and svc.sessions.state.value != "OWNER_LOCKED")
    except Exception:
        return False


def owner_step_up_valid() -> bool:
    svc = _owner_service()
    if not svc:
        return False
    try:
        return bool(svc.sessions.step_up_valid())
    except Exception:
        return False


def health_step_up_enabled() -> bool:
    from jarvis import p4_flags

    explicit = os.getenv("JARVIS_HEALTH_STEP_UP", "").strip().lower()
    if explicit in ("0", "false", "no", "off"):
        return False
    if explicit in ("1", "true", "yes", "on"):
        return True
    if owner_vault_configured():
        return True
    return bool(p4_flags.pin_lock_enabled())


def step_up_ttl() -> int:
    try:
        return max(60, int(os.getenv("JARVIS_HEALTH_STEPUP_TTL", "300")))
    except ValueError:
        return 300


def _token_from_request(request) -> str:
    """Grant cache key — never treat LAN/HA secrets as authenticators.

    Prefer owner session header; fall back to a non-secret local bucket.
    Do not key grants on X-API-Key (LAN credential).
    """
    if request is None:
        return "local"
    headers = getattr(request, "headers", {}) or {}
    return (
        headers.get("x-jarvis-session")
        or headers.get("X-Jarvis-Session")
        or "local"
    )


def _has_grant(token: str, op: str) -> bool:
    bucket = _GRANTS.get(token) or {}
    exp = bucket.get(op) or bucket.get("*")
    return bool(exp and exp > time.time())


def grant(token: str, op: str, *, ttl: int | None = None) -> dict[str, Any]:
    ttl = ttl if ttl is not None else step_up_ttl()
    bucket = _GRANTS.setdefault(token, {})
    bucket[op] = time.time() + ttl
    bucket["*"] = time.time() + min(ttl, 120)
    return {"ok": True, "op": op, "expires_in": ttl}


def _owner_secret_from_body(op: str, body: dict | None) -> str:
    body = body or {}
    pin = str(body.get("pin") or "").strip()
    master = str(body.get("master_password") or "").strip()
    if pin:
        return pin
    if master:
        return master
    if op in PORTABLE_PASSWORD_OPS:
        return ""
    # Generic password field only when it is not a portable-file password
    return str(body.get("password") or "").strip()


def require_owner(request=None) -> dict[str, Any] | None:
    """Fail closed when the Owner Vault exists and the house is locked."""
    if not owner_vault_configured():
        return None
    if owner_unlocked():
        return None
    try:
        store.log_event("health_access", "owner_locked")
    except Exception:
        pass
    return {
        "ok": False,
        "locked": True,
        "step_up_required": False,
        "message": "Unlock Aria with your Master Password to use Health.",
        "disclaimer": DISCLAIMER,
        "status_code": 423,
        "prompt_class": "A",
    }


def require(request, op: str, *, body: dict | None = None) -> dict[str, Any] | None:
    """Return None if allowed, or an error dict if locked / step-up required / failed."""
    locked = require_owner(request)
    if locked:
        return locked
    if op not in SENSITIVE_OPS:
        return None
    if not health_step_up_enabled():
        return None
    if op == "emergency_info" and os.getenv("JARVIS_HEALTH_EMERGENCY_OPEN", "").lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        try:
            store.log_event("health_access", f"emergency_open:{op}")
        except Exception:
            pass
        return None
    if owner_step_up_valid():
        return None
    token = _token_from_request(request)
    if _has_grant(token, op):
        try:
            store.log_event("health_access", f"granted_cache:{op}")
        except Exception:
            pass
        return None

    secret = _owner_secret_from_body(op, body)
    if secret:
        ok = _verify_credentials(secret, request)
        if ok:
            grant(token, op)
            try:
                store.log_event("health_access", f"step_up_ok:{op}")
            except Exception:
                pass
            return None
        try:
            store.log_event("health_access", "step_up_fail")
        except Exception:
            pass
        return {
            "ok": False,
            "step_up_required": True,
            "op": op,
            "message": "Incorrect Master Password or PIN for Health step-up.\n\n_" + DISCLAIMER + "_",
            "disclaimer": DISCLAIMER,
            "status_code": 403,
            "prompt_class": "A",
        }

    try:
        store.log_event("health_access", f"step_up_required:{op}")
    except Exception:
        pass
    return {
        "ok": False,
        "step_up_required": True,
        "op": op,
        "message": (
            f"Health needs a quick Owner confirmation before **{op.replace('_', ' ')}**. "
            "Enter your Aria Master Password"
            + (" or PIN" if _pin_configured() else "")
            + " — not a backup or LAN key.\n\n_"
            + DISCLAIMER
            + "_"
        ),
        "disclaimer": DISCLAIMER,
        "status_code": 423,
        "prompt_class": "A",
    }


def _pin_configured() -> bool:
    try:
        from jarvis.security.pin_lock import pin_configured

        return bool(pin_configured())
    except Exception:
        return False


def _verify_credentials(secret: str, request) -> bool:
    """Owner presence — PIN convenience or Master Password via Owner Security.

    LAN API key and HA token are not authenticators.
    """
    secret = (secret or "").strip()
    if not secret:
        return False
    svc = _owner_service()
    if svc and svc.vault.exists():
        try:
            out = svc.step_up(master_password=secret, pin=secret)
            return bool(out.get("ok"))
        except Exception:
            return False
    # No owner vault: PIN convenience only (legacy)
    try:
        from jarvis.security import pin_lock

        if hasattr(pin_lock, "verify_pin") and pin_lock.verify_pin(secret):
            return True
        if hasattr(pin_lock, "check_pin") and pin_lock.check_pin(secret):
            return True
    except Exception:
        pass
    return False


def status(request=None) -> dict[str, Any]:
    token = _token_from_request(request)
    bucket = _GRANTS.get(token) or {}
    active = {k: int(v - time.time()) for k, v in bucket.items() if v > time.time()}
    return {
        "ok": True,
        "enabled": health_step_up_enabled(),
        "ttl": step_up_ttl(),
        "active_grants": active,
        "ops": sorted(SENSITIVE_OPS),
        "owner_vault": owner_vault_configured(),
        "owner_unlocked": owner_unlocked(),
        "owner_step_up_valid": owner_step_up_valid(),
        "pin_convenience": _pin_configured(),
        "portable_backup_distinct": True,
        "disclaimer": DISCLAIMER,
    }


def step_up(request, *, pin: str = "", op: str = "*") -> dict[str, Any]:
    token = _token_from_request(request)
    locked = require_owner(request)
    if locked:
        locked.pop("status_code", None)
        return locked
    if not health_step_up_enabled():
        return {
            "ok": True,
            "enabled": False,
            "message": "Health step-up is not required right now.",
            "disclaimer": DISCLAIMER,
        }
    if not pin:
        return {
            "ok": False,
            "step_up_required": True,
            "message": "Aria Master Password (or PIN) required.",
            "prompt_class": "A",
            "disclaimer": DISCLAIMER,
        }
    if not _verify_credentials(pin, request):
        try:
            store.log_event("health_access", "step_up_fail:explicit")
        except Exception:
            pass
        return {"ok": False, "message": "Incorrect Master Password or PIN.", "disclaimer": DISCLAIMER}
    g = grant(token, op if op in SENSITIVE_OPS or op == "*" else "*")
    try:
        store.log_event("health_access", f"step_up_ok:{op}")
    except Exception:
        pass
    return {**g, "message": "Health step-up confirmed.", "disclaimer": DISCLAIMER, "prompt_class": "A"}
