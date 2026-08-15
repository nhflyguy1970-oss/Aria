"""Unified secret bus — products consume this; storage is data/jarvis.env (plaintext today)."""

from __future__ import annotations

import json
import os
import re
import stat
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

AUDIT_FILE = DATA_DIR / "integrations_product" / "secret_audit.json"
POLICY_FILE = DATA_DIR / "integrations_product" / "secret_policy.json"
MAX_AUDIT = 200

# Canonical field → env var
SECRET_FIELDS: dict[str, str] = {
    "gemini_api_key": "GEMINI_API_KEY",
    "google_api_key": "GOOGLE_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openrouter_api_key": "OPENROUTER_API_KEY",
    "hf_token": "HF_TOKEN",
    "meshy_api_key": "JARVIS_MESHY_API_KEY",
}

FIELD_ALIASES: dict[str, str] = {
    "HUGGING_FACE_HUB_TOKEN": "hf_token",
    "MESHY_API_KEY": "meshy_api_key",
    "GOOGLE_API_KEY": "gemini_api_key",
}


def storage_info() -> dict[str, Any]:
    from jarvis.env_loader import ENV_FILE

    path = Path(ENV_FILE)
    mode = None
    exists = path.is_file()
    world_readable = False
    if exists:
        try:
            mode = stat.S_IMODE(path.stat().st_mode)
            world_readable = bool(mode & stat.S_IROTH)
        except OSError:
            pass
    vault_backed = False
    try:
        from jarvis.security.owner.provider_credentials import bound_owner_service, vault_has_entry
        from jarvis.security.owner.provider_credentials import AUTHORIZED_PROVIDER_FIELDS

        svc = bound_owner_service()
        if svc.vault.exists():
            vault_backed = any(
                vault_has_entry(svc, spec["vault_id"])
                for field, spec in AUTHORIZED_PROVIDER_FIELDS.items()
                if not spec.get("alias_of")
            )
    except Exception:
        vault_backed = False
    return {
        "backend": "owner_vault_then_jarvis_env" if vault_backed else "jarvis_env_file",
        "path": str(path),
        "encrypted": False,
        "vault_dual_read": True,
        "vault_backed": vault_backed,
        "os_keychain": False,
        "honest": True,
        "message": (
            "Provider credentials prefer the Owner Vault when migrated. "
            "data/jarvis.env remains as plaintext rollback during M2 and is not deleted. "
            "Keys are never synced to git and must not be stored in Memory or chat."
        ),
        "exists": exists,
        "mode_octal": oct(mode) if mode is not None else None,
        "world_readable": world_readable,
        "recommendation": (
            "chmod 600 data/jarvis.env"
            if world_readable or (mode is not None and mode != 0o600)
            else "File permissions look restrictive."
        ),
        "precedence": "VAULT FIRST; LEGACY FALLBACK ONLY IF NOT MIGRATED",
    }


def mask_preview(value: str, *, last4: bool = True) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if last4 and len(v) >= 8:
        return f"••••{v[-4:]}"
    return "••••••••"


def get_secret(field_or_env: str) -> str:
    """Read a secret by field id or env name. Never log the return value.

    Precedence: Owner Vault if that credential is migrated; else jarvis.env.
    Migrated + owner locked → empty (fail closed). No env fallback for migrated entries.
    """
    try:
        from jarvis.security.owner.provider_credentials import resolve_provider_secret

        resolved = resolve_provider_secret(field_or_env)
        if resolved is not None:
            if resolved.source in ("vault", "locked"):
                return resolved.value
            if resolved.source == "legacy":
                return resolved.value
    except Exception:
        pass

    field = field_or_env
    if field_or_env in SECRET_FIELDS:
        env_name = SECRET_FIELDS[field_or_env]
    elif field_or_env in FIELD_ALIASES:
        field = FIELD_ALIASES[field_or_env]
        env_name = SECRET_FIELDS[field]
    else:
        env_name = field_or_env
    val = (os.getenv(env_name) or "").strip()
    if not val and env_name == "GEMINI_API_KEY":
        val = (os.getenv("GOOGLE_API_KEY") or "").strip()
    if not val and env_name == "HF_TOKEN":
        val = (os.getenv("HUGGING_FACE_HUB_TOKEN") or "").strip()
    if not val and env_name == "JARVIS_MESHY_API_KEY":
        val = (os.getenv("MESHY_API_KEY") or "").strip()
    return val


def is_set(field: str) -> bool:
    return bool(get_secret(field))


def _audit(kind: str, field: str, *, detail: str = "") -> None:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, Any]] = []
    if AUDIT_FILE.is_file():
        try:
            raw = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                events = [e for e in raw if isinstance(e, dict)]
        except (json.JSONDecodeError, OSError):
            events = []
    events.append(
        {
            "ts": time.time(),
            "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "kind": kind,
            "field": field,
            "detail": detail[:200],
        }
    )
    AUDIT_FILE.write_text(json.dumps(events[-MAX_AUDIT:], indent=2), encoding="utf-8")


def _load_policy() -> dict[str, Any]:
    data: dict[str, Any] = {"enabled": {}, "rotated_at": {}, "notes": {}}
    if POLICY_FILE.is_file():
        try:
            raw = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update(raw)
        except (json.JSONDecodeError, OSError):
            pass
    data.setdefault("enabled", {})
    data.setdefault("rotated_at", {})
    data.setdefault("notes", {})
    return data


def _save_policy(data: dict[str, Any]) -> None:
    POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    POLICY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def is_provider_enabled(provider_id: str, default: bool = True) -> bool:
    pol = _load_policy()
    if provider_id in (pol.get("enabled") or {}):
        return bool(pol["enabled"][provider_id])
    return default


def set_provider_enabled(provider_id: str, enabled: bool) -> dict[str, Any]:
    pol = _load_policy()
    pol.setdefault("enabled", {})[provider_id] = bool(enabled)
    _save_policy(pol)
    _audit("enable" if enabled else "disable", provider_id)
    return {"ok": True, "provider_id": provider_id, "enabled": bool(enabled)}


def mark_rotated(field: str) -> None:
    pol = _load_policy()
    pol.setdefault("rotated_at", {})[field] = time.time()
    _save_policy(pol)


def secrets_status(*, last4: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in SECRET_FIELDS:
        val = get_secret(field)
        out[f"{field}_set"] = bool(val)
        out[f"{field}_preview"] = mask_preview(val, last4=last4) if val else ""
    # Compat aliases used by existing UI
    gemini = get_secret("gemini_api_key")
    out["gemini_api_key_set"] = bool(gemini)
    out["gemini_api_key_preview"] = mask_preview(gemini, last4=last4) if gemini else ""
    out["storage"] = "owner_vault_then_jarvis.env"
    out["storage_info"] = storage_info()
    out["hint"] = (
        "Keys are saved on this PC only (not synced to git). "
        "Migrated provider keys live in the Owner Vault; data/jarvis.env is retained for rollback."
    )
    out["fields"] = list(SECRET_FIELDS.keys())
    out["policy"] = {
        "enabled": _load_policy().get("enabled") or {},
        "rotated_at": _load_policy().get("rotated_at") or {},
    }
    return out


def save_secrets(patch: dict[str, Any]) -> dict[str, Any]:
    from jarvis.env_loader import load_jarvis_env, upsert_env_vars

    updates: dict[str, str] = {}
    for field, env_name in SECRET_FIELDS.items():
        if field not in patch:
            continue
        raw = patch.get(field)
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        # Ignore masked placeholders accidentally re-submitted
        if value.startswith("••••") or value == "********":
            continue
        if field == "hf_token" and not value.startswith("hf_"):
            value = f"hf_{value}" if not value.startswith("hf") else value
        updates[env_name] = value
        mark_rotated(field)
        _audit("write", field, detail=f"env={env_name}")

    if "gemini_api_key" in patch and str(patch.get("gemini_api_key") or "").strip():
        updates.pop("GOOGLE_API_KEY", None)

    changed = upsert_env_vars(updates) if updates else []
    load_jarvis_env(force=True)

    if updates.get("GEMINI_API_KEY") or updates.get("OPENAI_API_KEY"):
        explicit = os.getenv("JARVIS_CLOUD_LIVE_VOICE", "").strip().lower()
        if explicit not in ("0", "false", "no", "off"):
            upsert_env_vars({"JARVIS_CLOUD_LIVE_VOICE": "1"})
            load_jarvis_env(force=True)
            changed = list(set(list(changed) + ["JARVIS_CLOUD_LIVE_VOICE"]))

    # Tighten permissions when possible
    try:
        from jarvis.env_loader import ENV_FILE

        if Path(ENV_FILE).is_file():
            os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass

    out = secrets_status()
    out["ok"] = True
    out["changed"] = changed
    # Dual-write: if Owner Vault is unlocked, copy authorized fields into vault too.
    # Does not remove jarvis.env. Failures here must not roll back the env write.
    try:
        from jarvis.security.owner.provider_credentials import bound_owner_service, migrate_field, normalize_field

        svc = bound_owner_service()
        if svc.vault.exists() and svc.vault.is_unlocked():
            vault_writes = []
            for field in updates:
                canon = normalize_field(field)
                if not canon:
                    continue
                result = migrate_field(svc, canon, overwrite=True)
                vault_writes.append(
                    {
                        "field": canon,
                        "ok": bool(result.get("ok")),
                        "migrated": bool(result.get("migrated")),
                    }
                )
            out["vault_dual_write"] = vault_writes
    except Exception:
        out["vault_dual_write"] = []
    return out


def clear_secret(field: str) -> dict[str, Any]:
    env_name = SECRET_FIELDS.get(field)
    if not env_name:
        return {"ok": False, "message": f"Unknown field: {field}"}
    from jarvis.env_loader import ENV_FILE, load_jarvis_env

    if ENV_FILE.is_file():
        text = ENV_FILE.read_text(encoding="utf-8")
        pattern = re.compile(rf"^export\s+{re.escape(env_name)}=.*$\n?", re.MULTILINE)
        new_text = pattern.sub("", text)
        if new_text != text:
            ENV_FILE.write_text(new_text, encoding="utf-8")
            try:
                os.chmod(ENV_FILE, 0o600)
            except OSError:
                pass
    os.environ.pop(env_name, None)
    if field == "gemini_api_key":
        os.environ.pop("GOOGLE_API_KEY", None)
    load_jarvis_env(force=True)
    _audit("clear", field)
    return {"ok": True, **secrets_status()}


def rotate_secret(field: str, new_value: str) -> dict[str, Any]:
    """Write a new value (same as save) and mark rotated."""
    if not str(new_value or "").strip():
        return {"ok": False, "message": "new value required"}
    out = save_secrets({field: new_value})
    mark_rotated(field)
    _audit("rotate", field)
    out["rotated"] = True
    return out


def list_audit(limit: int = 50) -> list[dict[str, Any]]:
    if not AUDIT_FILE.is_file():
        return []
    try:
        events = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
        if isinstance(events, list):
            return list(reversed(events[-max(1, limit) :]))
    except (json.JSONDecodeError, OSError):
        pass
    return []


def hygiene_report() -> dict[str, Any]:
    from jarvis.integrations_product.settings import load_settings

    settings = load_settings()
    days = int(settings.get("rotation_reminder_days") or 90)
    pol = _load_policy()
    rotated = pol.get("rotated_at") or {}
    now = time.time()
    reminders = []
    unused = []
    for field in SECRET_FIELDS:
        if not is_set(field):
            continue
        ts = float(rotated.get(field) or 0)
        if ts and (now - ts) > days * 86400:
            reminders.append({"field": field, "age_days": int((now - ts) / 86400)})
        elif not ts:
            reminders.append({"field": field, "age_days": None, "note": "no rotation timestamp"})
    # Duplicate detection: gemini vs google both set differently
    g1 = (os.getenv("GEMINI_API_KEY") or "").strip()
    g2 = (os.getenv("GOOGLE_API_KEY") or "").strip()
    duplicates = []
    if g1 and g2 and g1 != g2:
        duplicates.append({"fields": ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "issue": "both set to different values"})
    storage = storage_info()
    return {
        "ok": True,
        "storage": storage,
        "rotation_reminders": reminders,
        "duplicates": duplicates,
        "unused_candidates": unused,
        "world_readable": storage.get("world_readable"),
        "recommendation": storage.get("recommendation"),
    }


def export_bundle(*, include_values: bool = False) -> dict[str, Any]:
    """Export metadata; values only if explicitly requested (still plaintext warning)."""
    fields = {}
    for field in SECRET_FIELDS:
        val = get_secret(field)
        fields[field] = {
            "set": bool(val),
            "preview": mask_preview(val) if val else "",
            "value": val if include_values and val else None,
        }
    return {
        "ok": True,
        "format": "aria_integrations_secrets_v1",
        "encrypted": False,
        "warning": "Bundle is NOT encrypted. Treat as secret material if values included.",
        "storage": storage_info(),
        "fields": fields,
        "policy": _load_policy(),
    }


def import_bundle(data: dict[str, Any], *, write_values: bool = False) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("format") != "aria_integrations_secrets_v1":
        return {"ok": False, "message": "unsupported bundle"}
    if write_values:
        patch = {}
        for field, meta in (data.get("fields") or {}).items():
            if isinstance(meta, dict) and meta.get("value"):
                patch[field] = meta["value"]
        if patch:
            save_secrets(patch)
    if isinstance(data.get("policy"), dict):
        _save_policy({**_load_policy(), **data["policy"]})
    return {"ok": True, "wrote_values": bool(write_values)}
