"""Owner Security M3 — HA token + LAN API key dual-read (isolated, disposable secrets)."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

MASTER = "TestMaster-Passphrase-42!"
DISPOSABLE_HA = "eyJisolM3DisposableHomeAssistantTokenNotLivexxxx." + ("a" * 80)
DISPOSABLE_LAN = "isol-m3-lan-key-not-live"


@pytest.fixture
def m3_svc(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.env_loader as el
    import jarvis.security.owner.service as owner_svc_mod

    env_file = tmp_path / "jarvis.env"
    env_file.write_text(
        f'export JARVIS_HA_TOKEN="{DISPOSABLE_HA}"\n'
        f'export JARVIS_API_KEY="{DISPOSABLE_LAN}"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(el, "ENV_FILE", env_file)
    monkeypatch.setenv("JARVIS_HA_TOKEN", DISPOSABLE_HA)
    monkeypatch.setenv("JARVIS_HA_URL", "http://127.0.0.1:8123")
    monkeypatch.setenv("JARVIS_API_KEY", DISPOSABLE_LAN)
    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    from jarvis.security.owner import get_owner_security

    svc = get_owner_security(reset=True)
    assert Path(svc.paths["vault"]).is_relative_to(tmp_path)
    out = svc.setup(MASTER, confirm_password=MASTER)
    assert out.get("ok") is True
    svc.acknowledge_recovery(stored=True)
    return svc


def test_m3_ha_migrate_vault_first_lock_fail_closed(m3_svc):
    from jarvis.home_assistant import ha_token

    assert ha_token() == DISPOSABLE_HA
    out = m3_svc.migrate_provider_credential("ha_token")
    assert out["ok"] is True
    assert out["migrated"] is True
    assert out["legacy_retained"] is True
    assert out["vault_id"] == "ha.token"
    assert "value" not in out
    assert os.environ.get("JARVIS_HA_TOKEN") == DISPOSABLE_HA
    assert ha_token() == DISPOSABLE_HA

    m3_svc.lock(hard=True)
    assert ha_token() == ""
    assert os.environ.get("JARVIS_HA_TOKEN") == DISPOSABLE_HA
    from jarvis.home_assistant import check_connection, ha_credential_locked

    assert ha_credential_locked() is True
    locked_conn = check_connection()
    assert locked_conn.get("ok") is False
    assert locked_conn.get("locked") is True
    assert "Master Password" in (locked_conn.get("message") or "")
    assert "paste" not in (locked_conn.get("message") or "").lower()

    unlocked = m3_svc.unlock(MASTER)
    assert unlocked["ok"] is True
    assert ha_token() == DISPOSABLE_HA


def test_m3_lan_migrate_vault_first_lock_fail_closed(m3_svc):
    from jarvis.auth import api_key_enabled, check_key, get_api_key

    assert get_api_key() == DISPOSABLE_LAN
    out = m3_svc.migrate_provider_credential("lan_api_key")
    assert out["ok"] is True
    assert out["vault_id"] == "lan.api_key"
    assert "value" not in out
    assert get_api_key() == DISPOSABLE_LAN
    assert api_key_enabled() is True

    m3_svc.lock(hard=True)
    assert get_api_key() == ""
    assert api_key_enabled() is True
    assert os.environ.get("JARVIS_API_KEY") == DISPOSABLE_LAN

    req_ok = MagicMock()
    req_ok.headers = {"X-API-Key": DISPOSABLE_LAN}
    req_ok.query_params = {}
    assert check_key(req_ok) is False

    unlocked = m3_svc.unlock(MASTER)
    assert unlocked["ok"] is True
    assert get_api_key() == DISPOSABLE_LAN
    assert check_key(req_ok) is True


def test_m3_lan_key_does_not_unlock_owner(m3_svc):
    m3_svc.lock(hard=True)
    bad = m3_svc.unlock(DISPOSABLE_LAN)
    assert bad.get("ok") is not True
    assert m3_svc.vault.is_unlocked() is False
    good = m3_svc.unlock(MASTER)
    assert good["ok"] is True


def test_m3_health_step_up_rejects_lan_api_key(m3_svc, monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_PIN_LOCK", "1")
    monkeypatch.setattr("jarvis.security.pin_lock.PIN_FILE", tmp_path / "pin.json")
    from jarvis.health_product.gate import _verify_credentials
    from jarvis.security.pin_lock import set_pin

    set_pin("1357")
    assert m3_svc.migrate_provider_credential("lan_api_key")["ok"] is True
    assert _verify_credentials(DISPOSABLE_LAN, None) is False
    assert _verify_credentials("1357", None) is True
    assert _verify_credentials(MASTER, None) is True


def test_m3_unmigrated_ha_falls_back_to_env(m3_svc):
    from jarvis.home_assistant import ha_token

    assert ha_token() == DISPOSABLE_HA
    m3_svc.lock(hard=True)
    assert ha_token() == DISPOSABLE_HA


def test_m3_subprocess_strips_ha_and_lan(m3_svc, monkeypatch):
    monkeypatch.setenv("JARVIS_HA_TOKEN", DISPOSABLE_HA)
    monkeypatch.setenv("HOME_ASSISTANT_TOKEN", DISPOSABLE_HA)
    monkeypatch.setenv("JARVIS_API_KEY", DISPOSABLE_LAN)
    from jarvis.security.owner.env_boundary import build_subprocess_env, copy_process_env

    sandbox = build_subprocess_env()
    hostish = copy_process_env()
    for env in (sandbox, hostish):
        assert "JARVIS_HA_TOKEN" not in env
        assert "HOME_ASSISTANT_TOKEN" not in env
        assert "JARVIS_API_KEY" not in env


def test_m3_acm_metadata_only(m3_svc):
    meta = m3_svc.acm_safe_metadata(
        configured=True,
        ha_token=DISPOSABLE_HA,
        lan_api_key=DISPOSABLE_LAN,
        api_key=DISPOSABLE_LAN,
    )
    assert "ha_token" not in meta
    assert "lan_api_key" not in meta
    assert "api_key" not in meta
    assert meta.get("configured") is True


def test_m3_restart_new_instance_locked(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setenv("JARVIS_HA_TOKEN", DISPOSABLE_HA)
    monkeypatch.setenv("JARVIS_API_KEY", DISPOSABLE_LAN)
    import jarvis.security.owner.service as owner_svc_mod

    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    from jarvis.auth import get_api_key
    from jarvis.home_assistant import ha_token
    from jarvis.security.owner import get_owner_security

    svc1 = get_owner_security(reset=True)
    assert Path(svc1.paths["vault"]).is_relative_to(tmp_path)
    assert svc1.setup(MASTER, confirm_password=MASTER)["ok"] is True
    svc1.acknowledge_recovery(stored=True)
    assert svc1.migrate_provider_credential("ha_token")["ok"] is True
    assert svc1.migrate_provider_credential("lan_api_key")["ok"] is True

    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    svc2 = get_owner_security(reset=True)
    assert svc2.vault.exists()
    assert svc2.vault.is_unlocked() is False
    assert ha_token() == ""
    assert get_api_key() == ""
    assert os.environ.get("JARVIS_HA_TOKEN") == DISPOSABLE_HA
    assert os.environ.get("JARVIS_API_KEY") == DISPOSABLE_LAN
