"""Owner Security M2 — provider credential dual-read (isolated, disposable secrets)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

MASTER = "TestMaster-Passphrase-42!"

DISPOSABLE_OPENAI = "sk-isol-m2-disposable-key-not-live-aaaa"
DISPOSABLE_GEMINI = "AIzaIsolM2DisposableKeyNotLivebbbbcccc"


@pytest.fixture
def m2_svc(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.env_loader as el
    import jarvis.security.owner.service as owner_svc_mod

    env_file = tmp_path / "jarvis.env"
    env_file.write_text(
        f'export OPENAI_API_KEY="{DISPOSABLE_OPENAI}"\n'
        f'export GEMINI_API_KEY="{DISPOSABLE_GEMINI}"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(el, "ENV_FILE", env_file)
    monkeypatch.setenv("OPENAI_API_KEY", DISPOSABLE_OPENAI)
    monkeypatch.setenv("GEMINI_API_KEY", DISPOSABLE_GEMINI)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    from jarvis.security.owner import get_owner_security

    svc = get_owner_security(reset=True)
    assert Path(svc.paths["vault"]).is_relative_to(tmp_path)
    out = svc.setup(MASTER, confirm_password=MASTER)
    assert out.get("ok") is True
    svc.acknowledge_recovery(stored=True)
    return svc


def test_m2_migrate_openai_vault_first_lock_fail_closed(m2_svc, monkeypatch):
    from jarvis.integrations_product.secrets_bus import get_secret

    before = get_secret("openai_api_key")
    assert before == DISPOSABLE_OPENAI

    out = m2_svc.migrate_provider_credential("openai_api_key")
    assert out["ok"] is True
    assert out["migrated"] is True
    assert out["legacy_retained"] is True
    assert out["vault_id"] == "provider.openai.api_key"
    assert "value" not in out
    assert out["fingerprint"]["prefix_class"] == "sk"
    assert os.environ.get("OPENAI_API_KEY") == DISPOSABLE_OPENAI

    got = get_secret("openai_api_key")
    assert got == DISPOSABLE_OPENAI

    m2_svc.lock(hard=True)
    locked = get_secret("openai_api_key")
    assert locked == ""
    # Legacy env still present — not used for migrated fields
    assert os.environ.get("OPENAI_API_KEY") == DISPOSABLE_OPENAI

    unlocked = m2_svc.unlock(MASTER)
    assert unlocked["ok"] is True
    again = get_secret("openai_api_key")
    assert again == DISPOSABLE_OPENAI


def test_m2_unmigrated_falls_back_to_env(m2_svc):
    from jarvis.integrations_product.secrets_bus import get_secret

    # Gemini not migrated yet
    assert get_secret("gemini_api_key") == DISPOSABLE_GEMINI
    m2_svc.lock(hard=True)
    # Unmigrated still uses env even when locked (legacy path)
    assert get_secret("gemini_api_key") == DISPOSABLE_GEMINI


def test_m2_mismatch_does_not_overwrite(m2_svc, monkeypatch):
    first = m2_svc.migrate_provider_credential("openai_api_key")
    assert first["ok"] is True
    monkeypatch.setenv("OPENAI_API_KEY", "sk-different-isol-key-should-not-overwrite")
    second = m2_svc.migrate_provider_credential("openai_api_key")
    assert second["ok"] is False
    assert second.get("mismatch") is True
    from jarvis.integrations_product.secrets_bus import get_secret

    assert get_secret("openai_api_key") == DISPOSABLE_OPENAI


def test_m2_empty_field_not_migrated(m2_svc):
    out = m2_svc.migrate_provider_credential("anthropic_api_key")
    assert out["ok"] is False
    assert out.get("migrated") is False


def test_m2_http_migrate_never_returns_secret(m2_svc):
    st = m2_svc.provider_migration_status()
    assert st["ok"] is True
    blob = str(st)
    assert DISPOSABLE_OPENAI not in blob
    assert DISPOSABLE_GEMINI not in blob


def test_m2_subprocess_still_strips_provider_keys(m2_svc, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", DISPOSABLE_OPENAI)
    from jarvis.security.owner.env_boundary import build_subprocess_env

    env = build_subprocess_env()
    assert "OPENAI_API_KEY" not in env
    assert "GEMINI_API_KEY" not in env


def test_m2_acm_metadata_only(m2_svc):
    meta = m2_svc.acm_safe_metadata(provider="openai", configured=True, api_key=DISPOSABLE_OPENAI)
    assert "api_key" not in meta
    assert meta.get("configured") is True
    assert meta.get("provider") == "openai"


def test_m2_restart_new_instance_locked(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", DISPOSABLE_OPENAI)
    import jarvis.security.owner.service as owner_svc_mod

    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    from jarvis.security.owner import get_owner_security
    from jarvis.integrations_product.secrets_bus import get_secret

    svc1 = get_owner_security(reset=True)
    assert Path(svc1.paths["vault"]).is_relative_to(tmp_path)
    assert svc1.setup(MASTER, confirm_password=MASTER)["ok"] is True
    svc1.acknowledge_recovery(stored=True)
    assert svc1.migrate_provider_credential("openai_api_key")["ok"] is True

    owner_svc_mod._INSTANCE = None  # noqa: SLF001
    svc2 = get_owner_security(reset=True)
    assert svc2.vault.exists()
    assert svc2.vault.is_unlocked() is False
    assert get_secret("openai_api_key") == ""
    assert svc2.unlock(MASTER)["ok"] is True
    assert get_secret("openai_api_key") == DISPOSABLE_OPENAI
