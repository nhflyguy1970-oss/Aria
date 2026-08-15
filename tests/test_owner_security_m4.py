"""Owner Security M4 — Health/Uncensored session unification (isolated)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

MASTER = "TestMaster-Passphrase-42!"
DISPOSABLE_LAN = "isol-m4-lan-key-not-for-health"
DISPOSABLE_BACKUP = "portable-health-backup-password-xx"


@pytest.fixture
def m4_svc(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.security.owner.service as owner_svc_mod

    monkeypatch.setenv("JARVIS_API_KEY", DISPOSABLE_LAN)
    monkeypatch.delenv("JARVIS_HEALTH_STEP_UP", raising=False)
    monkeypatch.delenv("JARVIS_PIN_LOCK", raising=False)
    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    from jarvis.security.owner import get_owner_security

    svc = get_owner_security(reset=True)
    assert Path(svc.paths["vault"]).is_relative_to(tmp_path)
    assert svc.setup(MASTER, confirm_password=MASTER)["ok"] is True
    svc.acknowledge_recovery(stored=True)
    return svc


def test_m4_health_home_unlocked_no_password(m4_svc):
    from jarvis.health_product.gate import require, require_owner

    assert require_owner(None) is None
    assert require(None, "checkin") is None


def test_m4_health_locked_fail_closed(m4_svc):
    from jarvis.health_product.gate import require, require_owner, revoke_grants

    m4_svc.lock(hard=True)
    err = require_owner(None)
    assert err and err.get("locked") is True
    assert "Master Password" in err["message"]
    assert require(None, "export_record")["locked"] is True
    assert require(None, "backup_create")["locked"] is True
    revoke_grants()
    m4_svc.unlock(MASTER)
    assert require_owner(None) is None


def test_m4_sensitive_needs_owner_step_up_not_lan_or_backup_password(m4_svc):
    from jarvis.health_product.gate import require

    denied = require(None, "export_record")
    assert denied and denied.get("step_up_required") is True
    assert denied.get("prompt_class") == "A"

    assert require(None, "backup_create", body={"password": DISPOSABLE_BACKUP})["step_up_required"] is True
    assert require(None, "backup_create", body={"password": DISPOSABLE_LAN})["step_up_required"] is True
    assert require(None, "export_record", body={"password": DISPOSABLE_LAN})["ok"] is False

    ok = require(None, "export_record", body={"master_password": MASTER})
    assert ok is None


def test_m4_lan_key_never_health_or_owner(m4_svc):
    from jarvis.health_product.gate import _verify_credentials, step_up

    assert _verify_credentials(DISPOSABLE_LAN, None) is False
    bad = step_up(None, pin=DISPOSABLE_LAN, op="export_record")
    assert bad.get("ok") is False
    m4_svc.lock(hard=True)
    assert m4_svc.unlock(DISPOSABLE_LAN).get("ok") is not True
    assert m4_svc.unlock(MASTER)["ok"] is True


def test_m4_lock_revokes_health_grants(m4_svc):
    from jarvis.health_product.gate import _has_grant, grant, require

    grant("local", "export_record", ttl=300)
    assert _has_grant("local", "export_record") is True
    m4_svc.lock(hard=True)
    assert _has_grant("local", "export_record") is False
    assert require(None, "export_record")["locked"] is True


def test_m4_uncensored_uses_owner_not_second_password(m4_svc, tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.uncensored_auth.AUTH_FILE", tmp_path / "uncensored_auth.json")
    monkeypatch.setattr("jarvis.uncensored_auth.SESSIONS_FILE", tmp_path / "uncensored_sessions.json")
    from jarvis.uncensored_auth import auth_status, is_configured, try_enable

    st = auth_status()
    assert st["owner_vault"] is True
    assert st["auth_mode"] == "owner_security"
    token, err = try_enable("", client_id="isol")
    assert token is None
    assert "Master Password" in (err or "")
    token, err = try_enable(DISPOSABLE_LAN, client_id="isol")
    assert token is None
    token, err = try_enable(MASTER, client_id="isol")
    assert err is None
    assert token
    assert is_configured() is False  # did not write a second password file


def test_m4_uncensored_denied_when_locked(m4_svc, tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.uncensored_auth.AUTH_FILE", tmp_path / "uncensored_auth.json")
    monkeypatch.setattr("jarvis.uncensored_auth.SESSIONS_FILE", tmp_path / "uncensored_sessions.json")
    from jarvis.uncensored_auth import try_enable

    assert try_enable(MASTER, client_id="isol")[0]
    m4_svc.lock(hard=True)
    token, err = try_enable(MASTER, client_id="isol")
    assert token is None
    assert "Unlock Aria" in (err or "")


def test_m4_capability_rooms_not_superuser(m4_svc):
    health = m4_svc.authorize("health.read", room="health")
    assert health.get("ok") is True
    wrong = m4_svc.authorize("health.delete", room="flytying")
    assert wrong.get("ok") is False
    export = m4_svc.authorize("health.export", room="health")
    assert export.get("step_up_required") is True or export.get("ok") is True
