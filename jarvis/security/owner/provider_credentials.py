"""Credential map — vault-first dual-read, metadata only.

M2: Integration / Provider API keys.
M3: Home Assistant token (`ha.token`) and LAN API key (`lan.api_key`).
Never log or return secret values from HTTP. KDF is not used per get.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

# Canonical Integrations secret_field → vault entry.
# Aliases are additional env names read only when the primary is empty.
AUTHORIZED_PROVIDER_FIELDS: dict[str, dict[str, Any]] = {
    "openai_api_key": {
        "env": "OPENAI_API_KEY",
        "aliases": (),
        "vault_id": "provider.openai.api_key",
        "label": "OpenAI API key",
        "provider_id": "openai",
        "validate": "openai",
        "migration": "AUTHORIZED NOW",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "gemini_api_key": {
        "env": "GEMINI_API_KEY",
        "aliases": ("GOOGLE_API_KEY",),
        "vault_id": "provider.gemini.api_key",
        "label": "Gemini API key",
        "provider_id": "gemini",
        "validate": "gemini",
        "migration": "AUTHORIZED NOW",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "google_api_key": {
        "env": "GOOGLE_API_KEY",
        "aliases": ("GEMINI_API_KEY",),
        "vault_id": "provider.gemini.api_key",
        "label": "Gemini API key (GOOGLE_API_KEY alias)",
        "provider_id": "gemini",
        "validate": "gemini",
        "migration": "AUTHORIZED NOW",
        "alias_of": "gemini_api_key",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "anthropic_api_key": {
        "env": "ANTHROPIC_API_KEY",
        "aliases": (),
        "vault_id": "provider.anthropic.api_key",
        "label": "Anthropic API key",
        "provider_id": "anthropic",
        "validate": "anthropic",
        "migration": "AUTHORIZED NOW",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "openrouter_api_key": {
        "env": "OPENROUTER_API_KEY",
        "aliases": (),
        "vault_id": "provider.openrouter.api_key",
        "label": "OpenRouter API key",
        "provider_id": "openrouter",
        "validate": "openrouter",
        "migration": "AUTHORIZED NOW",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "hf_token": {
        "env": "HF_TOKEN",
        "aliases": ("HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"),
        "vault_id": "provider.huggingface.token",
        "label": "Hugging Face token",
        "provider_id": "huggingface",
        "validate": "huggingface",
        "migration": "AUTHORIZED NOW",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "meshy_api_key": {
        "env": "JARVIS_MESHY_API_KEY",
        "aliases": ("MESHY_API_KEY",),
        "vault_id": "provider.meshy.api_key",
        "label": "Meshy API key",
        "provider_id": "meshy",
        "validate": "meshy",
        "migration": "AUTHORIZED NOW",
        "phase": "M2",
        "room": "integrations",
        "category": "provider",
    },
    "ha_token": {
        "env": "JARVIS_HA_TOKEN",
        "aliases": ("HOME_ASSISTANT_TOKEN",),
        "vault_id": "ha.token",
        "label": "Home Assistant token",
        "provider_id": "home_assistant",
        "validate": "ha",
        "migration": "AUTHORIZED NOW",
        "phase": "M3",
        "room": "ha",
        "category": "ha",
    },
    "lan_api_key": {
        "env": "JARVIS_API_KEY",
        "aliases": (),
        "vault_id": "lan.api_key",
        "label": "LAN API key",
        "provider_id": "lan",
        "validate": "lan",
        "migration": "AUTHORIZED NOW",
        "phase": "M3",
        "room": "lan",
        "category": "lan",
    },
}

ENV_TO_FIELD: dict[str, str] = {}
for _field, _spec in AUTHORIZED_PROVIDER_FIELDS.items():
    ENV_TO_FIELD[_spec["env"]] = _field
    for _alias in _spec.get("aliases") or ():
        ENV_TO_FIELD.setdefault(_alias, _field)


def normalize_field(field_or_env: str) -> str | None:
    raw = (field_or_env or "").strip()
    if not raw:
        return None
    if raw in AUTHORIZED_PROVIDER_FIELDS:
        spec = AUTHORIZED_PROVIDER_FIELDS[raw]
        return spec.get("alias_of") or raw
    if raw in ENV_TO_FIELD:
        field = ENV_TO_FIELD[raw]
        spec = AUTHORIZED_PROVIDER_FIELDS[field]
        return spec.get("alias_of") or field
    return None


def fingerprint(secret: str) -> dict[str, Any]:
    """Non-reversible metadata. Never include the secret or last-4."""
    v = (secret or "").strip()
    if not v:
        return {"configured": False, "length": 0, "sha256_8": "", "prefix_class": "empty"}
    prefix_class = "other"
    if v.startswith("sk-ant-"):
        prefix_class = "sk-ant"
    elif v.startswith("sk-"):
        prefix_class = "sk"
    elif v.startswith("AIza"):
        prefix_class = "AIza"
    elif v.startswith("hf_"):
        prefix_class = "hf"
    elif v.startswith("eyJ"):
        prefix_class = "jwt"
    return {
        "configured": True,
        "length": len(v),
        "sha256_8": hashlib.sha256(v.encode("utf-8")).hexdigest()[:8],
        "prefix_class": prefix_class,
    }


def validate_shape(kind: str, secret: str) -> dict[str, Any]:
    v = (secret or "").strip()
    if not v:
        return {"ok": False, "reason": "empty"}
    if kind == "openai":
        if not v.startswith("sk-") or len(v) < 20:
            return {"ok": False, "reason": "unexpected_openai_shape"}
    elif kind == "gemini":
        if len(v) < 20:
            return {"ok": False, "reason": "unexpected_gemini_shape"}
    elif kind == "huggingface":
        if not v.startswith("hf_") or len(v) < 20:
            return {"ok": False, "reason": "unexpected_hf_shape"}
    elif kind in ("anthropic", "openrouter", "meshy"):
        if len(v) < 12:
            return {"ok": False, "reason": "too_short"}
    elif kind == "ha":
        if len(v) < 40:
            return {"ok": False, "reason": "unexpected_ha_token_shape"}
    elif kind == "lan":
        if len(v) < 8:
            return {"ok": False, "reason": "unexpected_lan_key_shape"}
    return {"ok": True, "reason": "shape_ok"}


def read_legacy_env(field: str) -> str:
    spec = AUTHORIZED_PROVIDER_FIELDS.get(field)
    if not spec:
        return ""
    val = (os.getenv(spec["env"]) or "").strip()
    if val:
        return val
    for alias in spec.get("aliases") or ():
        val = (os.getenv(alias) or "").strip()
        if val:
            return val
    return ""


def bound_owner_service():
    """Return the Owner Security service bound to current DATA_DIR.

    Live Aria: the unlocked process singleton.
    Tests with a different DATA_DIR: ephemeral instance (do not touch live vault).
    """
    from jarvis.config import DATA_DIR
    from jarvis.security.owner.service import get_owner_security, vault_paths

    expected = vault_paths(Path(DATA_DIR))["vault"]
    svc = get_owner_security()
    try:
        if Path(svc.paths["vault"]) == Path(expected):
            return svc
    except Exception:
        pass
    return get_owner_security(data_dir=Path(DATA_DIR))


def vault_has_entry(svc, vault_id: str) -> bool:
    try:
        for row in svc.vault.list_meta():
            if row.get("id") == vault_id:
                return True
    except Exception:
        return False
    return False


@dataclass
class ResolveResult:
    source: Literal["vault", "legacy", "locked", "missing"]
    value: str
    vault_id: str = ""
    field: str = ""


def resolve_provider_secret(field_or_env: str) -> ResolveResult | None:
    """Vault-first for migrated provider credentials.

    Returns None if this is not an authorized provider field (caller may use other stores).
    Migrated + locked → source=locked, value="" (no env fallback).
    Not migrated → source=legacy, value from env.
    """
    field = normalize_field(field_or_env)
    if not field:
        return None
    spec = AUTHORIZED_PROVIDER_FIELDS[field]
    vault_id = spec["vault_id"]
    try:
        svc = bound_owner_service()
    except Exception:
        return ResolveResult(source="legacy", value=read_legacy_env(field), vault_id=vault_id, field=field)

    if not svc.vault.exists():
        return ResolveResult(source="legacy", value=read_legacy_env(field), vault_id=vault_id, field=field)

    # Pytest must never decrypt the live Owner Vault.
    if os.getenv("PYTEST_CURRENT_TEST"):
        from jarvis.env_loader import PROJECT_ROOT

        live = (PROJECT_ROOT / "data" / "security" / "owner").resolve()
        try:
            if Path(svc.paths["vault"]).resolve().is_relative_to(live):
                return ResolveResult(source="legacy", value=read_legacy_env(field), vault_id=vault_id, field=field)
        except Exception:
            pass

    migrated = vault_has_entry(svc, vault_id)
    if not migrated:
        return ResolveResult(source="legacy", value=read_legacy_env(field), vault_id=vault_id, field=field)

    room = spec.get("room") or "integrations"
    auth = svc.authorize("vault.secret.use", room=room)
    if not auth.get("ok"):
        return ResolveResult(source="locked", value="", vault_id=vault_id, field=field)

    t0 = time.perf_counter()
    try:
        raw = svc.vault.get_secret(vault_id)
        val = raw.decode("utf-8", errors="replace").strip()
    except Exception:
        svc._time("credential_get_fail", time.perf_counter() - t0, vault_id=vault_id)  # noqa: SLF001
        return ResolveResult(source="locked", value="", vault_id=vault_id, field=field)
    svc._time("credential_get", time.perf_counter() - t0, vault_id=vault_id)  # noqa: SLF001
    return ResolveResult(source="vault", value=val, vault_id=vault_id, field=field)


def migrate_field(svc, field_or_env: str, *, overwrite: bool = False) -> dict[str, Any]:
    """Copy one env credential into the vault. Does not modify jarvis.env."""
    import os

    from jarvis.env_loader import PROJECT_ROOT

    if os.getenv("PYTEST_CURRENT_TEST") and Path(svc.paths["vault"]).resolve().is_relative_to(
        (PROJECT_ROOT / "data" / "security" / "owner").resolve()
    ):
        return {
            "ok": False,
            "message": "Refusing to mutate the live Owner Vault under pytest",
            "migrated": False,
        }
    field = normalize_field(field_or_env)
    if not field:
        return {"ok": False, "message": "Not an authorized provider field", "field": field_or_env}
    spec = AUTHORIZED_PROVIDER_FIELDS[field]
    vault_id = spec["vault_id"]
    env_name = spec["env"]
    legacy = read_legacy_env(field)
    if not legacy:
        return {
            "ok": False,
            "field": field,
            "vault_id": vault_id,
            "env": env_name,
            "message": "Legacy env credential not configured — nothing to migrate",
            "migrated": False,
        }
    shape = validate_shape(spec["validate"], legacy)
    if not shape["ok"]:
        return {
            "ok": False,
            "field": field,
            "vault_id": vault_id,
            "env": env_name,
            "message": f"Validation failed: {shape['reason']}",
            "migrated": False,
            "fingerprint": fingerprint(legacy),
        }

    fp = fingerprint(legacy)
    if vault_has_entry(svc, vault_id):
        try:
            existing = svc.vault.get_secret(vault_id).decode("utf-8", errors="replace").strip()
        except Exception as exc:
            return {"ok": False, "field": field, "vault_id": vault_id, "message": str(exc), "migrated": False}
        if existing == legacy:
            return {
                "ok": True,
                "field": field,
                "vault_id": vault_id,
                "env": env_name,
                "migrated": True,
                "already_migrated": True,
                "legacy_retained": True,
                "fingerprint": fp,
            }
        if not overwrite:
            return {
                "ok": False,
                "field": field,
                "vault_id": vault_id,
                "env": env_name,
                "message": "Vault and legacy env differ — not overwriting. Rollback: keep using env.",
                "migrated": False,
                "mismatch": True,
            }

    t0 = time.perf_counter()
    try:
        svc.vault.put_secret(
            vault_id,
            legacy,
            kind="api_key",
            label=spec["label"],
            meta={
                "source_env": env_name,
                "phase": spec.get("phase") or "M2",
                "provider_id": spec["provider_id"],
            },
        )
    except Exception as exc:
        return {"ok": False, "field": field, "vault_id": vault_id, "message": str(exc), "migrated": False}
    svc._time("credential_put", time.perf_counter() - t0, vault_id=vault_id)  # noqa: SLF001

    # Verify round-trip without returning the secret
    got = svc.vault.get_secret(vault_id).decode("utf-8", errors="replace").strip()
    if got != legacy:
        return {
            "ok": False,
            "field": field,
            "vault_id": vault_id,
            "message": "Vault round-trip mismatch — legacy env retained",
            "migrated": False,
        }
    return {
        "ok": True,
        "field": field,
        "vault_id": vault_id,
        "env": env_name,
        "migrated": True,
        "already_migrated": False,
        "legacy_retained": True,
        "fingerprint": fp,
        "provider_id": spec["provider_id"],
    }


def migration_status(svc) -> dict[str, Any]:
    entries = []
    try:
        meta_rows = {row.get("id"): row for row in svc.vault.list_meta()}
    except Exception:
        meta_rows = {}
    seen_vault: set[str] = set()
    for field, spec in AUTHORIZED_PROVIDER_FIELDS.items():
        if spec.get("alias_of"):
            continue
        vault_id = spec["vault_id"]
        if vault_id in seen_vault:
            continue
        seen_vault.add(vault_id)
        legacy = read_legacy_env(field)
        migrated = vault_id in meta_rows
        source = "vault" if migrated and svc.vault.is_unlocked() else (
            "locked" if migrated else ("legacy" if legacy else "missing")
        )
        row = {
            "field": field,
            "env": spec["env"],
            "vault_id": vault_id,
            "provider_id": spec["provider_id"],
            "category": spec.get("category") or "provider",
            "phase": spec.get("phase") or "M2",
            "legacy_configured": bool(legacy),
            "vault_entry": migrated,
            "source": source,
            "migration": spec["migration"],
        }
        if legacy:
            row["legacy_fingerprint"] = fingerprint(legacy)
        entries.append(row)
    return {
        "ok": True,
        "phase": "M2+M3",
        "precedence": "VAULT FIRST; LEGACY FALLBACK ONLY IF NOT MIGRATED",
        "owner_unlocked": bool(svc.vault.is_unlocked()),
        "entries": entries,
    }


def sync_vault_secret_if_migrated(field_or_env: str, secret: str) -> dict[str, Any]:
    """If this field is already in the vault and unlocked, keep vault in sync.

    Used when a Room writes a new token to jarvis.env after migration.
    Does not create a new vault entry (that is migrate_field).
    """
    field = normalize_field(field_or_env)
    if not field:
        return {"ok": False, "synced": False, "reason": "unknown_field"}
    spec = AUTHORIZED_PROVIDER_FIELDS[field]
    vault_id = spec["vault_id"]
    cleaned = (secret or "").strip()
    if not cleaned:
        return {"ok": False, "synced": False, "reason": "empty"}
    try:
        svc = bound_owner_service()
    except Exception as exc:
        return {"ok": False, "synced": False, "reason": str(exc)}
    if not vault_has_entry(svc, vault_id):
        return {"ok": True, "synced": False, "reason": "not_migrated"}
    if not svc.vault.is_unlocked():
        return {"ok": False, "synced": False, "reason": "locked"}
    try:
        svc.vault.put_secret(
            vault_id,
            cleaned,
            kind="api_key",
            label=spec["label"],
            meta={
                "source_env": spec["env"],
                "phase": spec.get("phase") or "M2",
                "provider_id": spec["provider_id"],
            },
        )
    except Exception as exc:
        return {"ok": False, "synced": False, "reason": str(exc)}
    return {"ok": True, "synced": True, "vault_id": vault_id}
