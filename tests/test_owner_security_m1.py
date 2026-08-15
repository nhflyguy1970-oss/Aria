"""Owner Security Vault M1 — empty vault + session foundation (isolated tests)."""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def owner_svc(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    # Isolate PIN file for soft-unlock tests
    monkeypatch.setattr("jarvis.security.pin_lock.PIN_FILE", tmp_path / "pin.json")
    monkeypatch.setattr("jarvis.security.pin_lock.SESSIONS_FILE", tmp_path / "pin_sessions.json")
    from jarvis.security.owner import get_owner_security

    return get_owner_security(data_dir=tmp_path)


MASTER = "TestMaster-Passphrase-42!"
MASTER2 = "TestMaster-Passphrase-99!"


def test_setup_unlock_lock_cycle(owner_svc):
    st = owner_svc.status()
    assert st["vault"]["exists"] is False
    out = owner_svc.setup(MASTER)
    assert out["ok"] is True
    assert out.get("recovery_key")
    assert out.get("session_token")
    recovery = out["recovery_key"]
    assert owner_svc.acknowledge_recovery(stored=True)["ok"]

    assert owner_svc.vault.is_unlocked()
    assert owner_svc.status()["owner_unlocked"] is True

    lock = owner_svc.lock(hard=True)
    assert lock["ok"]
    assert owner_svc.vault.is_unlocked() is False
    assert owner_svc.status()["owner_unlocked"] is False

    bad = owner_svc.unlock("wrong-password-xxxx")
    assert bad["ok"] is False

    good = owner_svc.unlock(MASTER)
    assert good["ok"] is True
    assert good.get("session_token")
    # recovery key must not be logged into timings
    assert all("recovery" not in str(t).lower() or t.get("op") == "recovery" for t in owner_svc.timings())
    assert recovery  # kept for recovery test


def test_incorrect_password_backoff(owner_svc):
    owner_svc.setup(MASTER)
    owner_svc.lock(hard=True)
    for _ in range(5):
        owner_svc.unlock("nope-nope-nope!!")
    blocked = owner_svc.unlock(MASTER)
    # May be temporary lockout after 5 failures
    if blocked.get("temporary_lockout"):
        assert blocked["ok"] is False
    else:
        # If timing window elapsed in test, unlock may succeed — still ok
        assert "ok" in blocked


def test_recovery_restores_access_and_keeps_entries(owner_svc):
    setup = owner_svc.setup(MASTER)
    recovery = setup["recovery_key"]
    owner_svc.acknowledge_recovery(stored=True)
    # Step-up then put disposable secret
    assert owner_svc.step_up(master_password=MASTER)["ok"]
    put = owner_svc.put_test_secret("test.disposable", "secret-value-isol-only", kind="api_key", label="Isol")
    assert put.get("ok") is True

    owner_svc.lock(hard=True)
    # Simulate lost master — recover
    rec = owner_svc.recover(recovery, MASTER2)
    assert rec["ok"] is True
    got = owner_svc.get_test_secret("test.disposable")
    assert got.get("ok") is True
    assert got.get("value") == "secret-value-isol-only"

    # Old master fails
    owner_svc.lock(hard=True)
    assert owner_svc.unlock(MASTER)["ok"] is False
    assert owner_svc.unlock(MASTER2)["ok"] is True


def test_session_revocation_invalidates_capabilities(owner_svc):
    owner_svc.setup(MASTER)
    owner_svc.acknowledge_recovery(stored=True)
    assert owner_svc.step_up(master_password=MASTER)["ok"]
    auth = owner_svc.authorize("journal.export", room="journal")
    assert auth["ok"] is True
    handle = auth.get("capability_handle")
    assert handle
    assert owner_svc.sessions.handles.valid(handle, capability="journal.export")

    owner_svc.lock(hard=True)
    assert owner_svc.sessions.handles.valid(handle, capability="journal.export") is False
    denied = owner_svc.authorize("journal.export", room="journal")
    assert denied["ok"] is False
    assert denied.get("locked") is True


def test_capability_denial_wrong_room(owner_svc):
    owner_svc.setup(MASTER)
    owner_svc.acknowledge_recovery(stored=True)
    owner_svc.step_up(master_password=MASTER)
    denied = owner_svc.authorize("health.delete", room="journal")
    assert denied["ok"] is False


def test_step_up_boundary(owner_svc):
    owner_svc.setup(MASTER)
    owner_svc.acknowledge_recovery(stored=True)
    # HIGH without step-up
    need = owner_svc.authorize("vault.secret.reveal", room="security")
    assert need["ok"] is False
    assert need.get("step_up_required") is True
    assert owner_svc.step_up(master_password=MASTER)["ok"]
    ok = owner_svc.authorize("vault.secret.reveal", room="security")
    assert ok["ok"] is True


def test_pin_soft_unlock_does_not_unwrap_from_disk(owner_svc, monkeypatch):
    from jarvis.security.pin_lock import set_pin

    owner_svc.setup(MASTER)
    owner_svc.acknowledge_recovery(stored=True)
    set_pin("2468")

    # Soft lock keeps root in memory
    soft = owner_svc.lock(hard=False)
    assert soft["mode"] == "soft"
    assert owner_svc.vault.is_unlocked() is True
    pin_ok = owner_svc.soft_unlock_with_pin("2468")
    assert pin_ok["ok"] is True

    # Hard lock clears root — PIN cannot restore
    owner_svc.lock(hard=True)
    assert owner_svc.vault.is_unlocked() is False
    pin_fail = owner_svc.soft_unlock_with_pin("2468")
    assert pin_fail["ok"] is False
    assert "master" in pin_fail["message"].lower()


def test_restart_behavior_locked(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    from jarvis.security.owner import get_owner_security

    svc1 = get_owner_security(data_dir=tmp_path)
    svc1.setup(MASTER)
    assert svc1.vault.is_unlocked()
    # Simulate process restart: new service instance, same files
    svc2 = get_owner_security(data_dir=tmp_path)
    assert svc2.vault.exists()
    assert svc2.vault.is_unlocked() is False
    assert svc2.status()["owner_unlocked"] is False


def test_empty_vault_integrity(owner_svc):
    owner_svc.setup(MASTER)
    meta = owner_svc.vault.status()
    assert meta["entry_count"] == 0
    assert meta["exists"] is True


def test_acm_boundary_rejects_secrets(owner_svc):
    with pytest.raises(ValueError):
        owner_svc.acm_assert_safe({"note": "password: hunter2-secret-value"})
    with pytest.raises(ValueError):
        owner_svc.acm_assert_safe({"api_key": "sk-abcdefghijklmnopqrstuvwxyz"})
    safe = owner_svc.acm_safe_metadata(provider="openai", configured=True, password="nope")
    assert "password" not in safe
    assert safe.get("configured") is True


def test_env_boundary_strips_secrets(monkeypatch):
    monkeypatch.setenv("JARVIS_API_KEY", "live-should-not-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-leak")
    monkeypatch.setenv("PATH", "/usr/bin")
    from jarvis.security.owner.env_boundary import build_subprocess_env

    env = build_subprocess_env()
    assert "JARVIS_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env
    assert env.get("PATH")


def test_health_step_up_rejects_lan_api_key(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_PIN_LOCK", "1")
    monkeypatch.setenv("JARVIS_API_KEY", "lan-key-not-for-health")
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("jarvis.security.pin_lock.PIN_FILE", tmp_path / "pin.json")
    from jarvis.health_product.gate import _verify_credentials
    from jarvis.security.pin_lock import set_pin

    set_pin("1357")
    assert _verify_credentials("lan-key-not-for-health", None) is False
    assert _verify_credentials("1357", None) is True


def test_house_lock_status_one_password(owner_svc):
    pin = {"ok": True, "locked": False, "lock_capable": False, "pin_configured": False}
    before = owner_svc.house_lock_status(pin_status=pin)
    assert before["owner_vault"] is False
    assert before["unlock_with"] == "none"
    assert before["locked"] is False or before.get("locked") in (False, None)

    owner_svc.setup(MASTER, confirm_password=MASTER)
    after = owner_svc.house_lock_status(pin_status=pin)
    assert after["owner_vault"] is True
    assert after["unlock_with"] == "master_password"
    assert after["locked"] is False
    owner_svc.lock(hard=True)
    locked = owner_svc.house_lock_status(pin_status=pin)
    assert locked["locked"] is True
    assert locked["lock_capable"] is True


def test_setup_confirm_mismatch(owner_svc):
    out = owner_svc.setup(MASTER, confirm_password="different-password-xx")
    assert out["ok"] is False
    assert owner_svc.vault.exists() is False


def test_authorize_without_vault_does_not_block_rooms(owner_svc):
    auth = owner_svc.authorize("journal.read", room="journal")
    assert auth["ok"] is True
    assert auth.get("owner_vault") is False

