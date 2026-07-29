"""Integrations product — providers, secrets bus, tests, Mission Control."""

from __future__ import annotations

import pytest


@pytest.fixture()
def integ_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.env_loader as el
    import jarvis.integrations_product.secrets_bus as sb
    import jarvis.integrations_product.settings as settings
    import jarvis.integrations_product.usage as usage

    env_file = tmp_path / "jarvis.env"
    env_file.write_text("# test\n", encoding="utf-8")
    monkeypatch.setattr(el, "ENV_FILE", env_file)
    monkeypatch.setattr(sb, "AUDIT_FILE", tmp_path / "integrations_product" / "secret_audit.json")
    monkeypatch.setattr(sb, "POLICY_FILE", tmp_path / "integrations_product" / "secret_policy.json")
    monkeypatch.setattr(settings, "SETTINGS_FILE", tmp_path / "integrations_product" / "settings.json")
    monkeypatch.setattr(usage, "USAGE_FILE", tmp_path / "integrations_product" / "usage.json")
    (tmp_path / "integrations_product").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_terminology_boundaries():
    from jarvis.integrations_product.terminology import BOUNDARIES, TERMINOLOGY

    assert TERMINOLOGY["product"] == "Integrations"
    assert TERMINOLOGY["architecture_term"] == "External APIs"
    assert "secrets_lifecycle" in BOUNDARIES["owns"]
    assert "voice_cloud_live_behavior" in BOUNDARIES["does_not_own"]
    assert "public_api_marketplace" in BOUNDARIES["does_not_own"]


def test_secret_bus_save_clear_last4(integ_data, monkeypatch):
    from jarvis.integrations_product.secrets_bus import clear_secret, get_secret, save_secrets, secrets_status

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = save_secrets({"gemini_api_key": "AIza-test-key-1234"})
    assert out["ok"] is True
    assert get_secret("gemini_api_key") == "AIza-test-key-1234"
    st = secrets_status(last4=True)
    assert st["gemini_api_key_set"] is True
    assert st["gemini_api_key_preview"].endswith("1234")
    assert st["storage_info"]["encrypted"] is False
    cleared = clear_secret("gemini_api_key")
    assert cleared["ok"] is True
    assert get_secret("gemini_api_key") == ""


def test_compat_integration_secrets_facade(integ_data, monkeypatch):
    from jarvis.integration_secrets import get_secret, save_secrets, secrets_status

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    save_secrets({"openai_api_key": "sk-test-openai"})
    assert get_secret("openai_api_key").startswith("sk-")
    assert secrets_status()["openai_api_key_set"] is True


def test_provider_matrix_includes_meshy_and_ha():
    from jarvis.integrations_product.providers import provider_matrix

    ids = {p["id"] for p in provider_matrix()}
    assert "gemini" in ids
    assert "meshy" in ids
    assert "home_assistant" in ids
    assert "automation_webhook" in ids
    meshy = next(p for p in provider_matrix() if p["id"] == "meshy")
    assert meshy["owner_product"] == "Engineering"
    assert any("Meshy" in u or "3D" in u or "3d" in u.lower() for u in meshy["unlocks"])


def test_test_connection_key_missing(integ_data, monkeypatch):
    from jarvis.integrations_product.providers import test_connection

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    result = test_connection("gemini")
    assert result["ok"] is False
    assert result.get("error") == "key_missing"
    assert "recovery" in result


def test_test_connection_openai_presence_mocked(integ_data, monkeypatch):
    from jarvis.integrations_product import providers as prov

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    class _Resp:
        status = 200

        def read(self, n=None):
            return b'{"data":[]}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(prov.urllib.request, "urlopen", lambda *a, **k: _Resp())
    result = prov.test_connection("openai")
    assert result["ok"] is True
    assert result.get("latency_ms") is not None


def test_home_and_mission(integ_data):
    from jarvis.integrations_product.engine import home_payload, product_status
    from jarvis.integrations_product.mission_bridge import integrations_mission_panel

    home = home_payload()
    assert home["product"] == "Integrations"
    assert home["security"]["encrypted"] is False
    assert home["webhooks"]["inbound"] is not None
    st = product_status()
    assert st["architecture_term"] == "External APIs"
    panel = integrations_mission_panel()
    assert panel["product"] == "Integrations"
    assert "deep_links" in panel


def test_hygiene_and_usage(integ_data, monkeypatch):
    from jarvis.integrations_product.secrets_bus import hygiene_report, save_secrets
    from jarvis.integrations_product.usage import list_usage, record_usage

    save_secrets({"hf_token": "hf_abcdefghij"})
    report = hygiene_report()
    assert report["storage"]["encrypted"] is False
    record_usage("gemini", action="test_connection", ok=False, message="sk-should-redact-this")
    events = list_usage(5)
    assert events
    assert "sk-" not in (events[0].get("message") or "")


def test_connectors_bootstrap_registers_ollama():
    from jarvis.intelligence.connectors import bootstrap_default_connectors, list_connectors

    names = bootstrap_default_connectors()
    assert "aria_local" in names
    assert "ollama" in names
    listed = {c["name"] for c in list_connectors()}
    assert "aria_local" in listed


def test_experimental_nl_setup():
    from jarvis.integrations_product.experimental import experimental_status, nl_setup_suggest

    status = experimental_status()
    assert any(i["id"] == "os_keychain" and not i["available"] for i in status["items"])
    sug = nl_setup_suggest("I want cloud live gemini voice")
    assert sug["ok"]
    assert any(s["provider_id"] == "gemini" for s in sug["suggestions"])


def test_enrich_snapshot_integrations(integ_data):
    from jarvis.mission_control_ops.enrich import enrich_snapshot

    snap = enrich_snapshot({})
    assert snap["integrations"]["product"] == "Integrations"


def test_integrations_product_api(chat_app, integ_data):
    res = chat_app.get("/api/integrations/product")
    assert res.status_code == 200
    assert res.json()["product"] == "Integrations"
    home = chat_app.get("/api/integrations/product/home")
    assert home.status_code == 200
    assert home.json()["ok"] is True
    secrets = chat_app.get("/api/integrations/secrets")
    assert secrets.status_code == 200
    assert secrets.json().get("ok") is True
    providers = chat_app.get("/api/integrations/product/providers")
    assert any(p["id"] == "meshy" for p in providers.json()["providers"])


def test_enable_disable_provider(integ_data):
    from jarvis.integrations_product.providers import enrich_provider, get_provider_def
    from jarvis.integrations_product.secrets_bus import set_provider_enabled

    set_provider_enabled("meshy", False)
    item = enrich_provider(get_provider_def("meshy"))
    assert item["enabled"] is False
    set_provider_enabled("meshy", True)
