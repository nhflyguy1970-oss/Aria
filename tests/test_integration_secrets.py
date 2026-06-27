"""Integration secrets GUI persistence."""

from jarvis.integration_secrets import save_secrets, secrets_status
from jarvis.p4_flags import cloud_live_voice_enabled


def test_cloud_live_auto_enabled_with_gemini_key(monkeypatch):
    monkeypatch.delenv("JARVIS_CLOUD_LIVE_VOICE", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-test-key")
    assert cloud_live_voice_enabled() is True


def test_cloud_live_explicit_off(monkeypatch):
    monkeypatch.setenv("JARVIS_CLOUD_LIVE_VOICE", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "AIza-test-key")
    assert cloud_live_voice_enabled() is False


def test_save_gemini_key_via_api(monkeypatch, tmp_path):
    import jarvis.env_loader as el
    import jarvis.integration_secrets as sec

    env_file = tmp_path / "jarvis.env"
    env_file.write_text("# test\n", encoding="utf-8")
    monkeypatch.setattr(el, "ENV_FILE", env_file)
    monkeypatch.chdir(tmp_path)

    out = save_secrets({"gemini_api_key": "AIza-secret"})
    assert out.get("ok") is True
    assert "GEMINI_API_KEY" in env_file.read_text(encoding="utf-8")
    st = secrets_status()
    assert st["gemini_api_key_set"] is True
