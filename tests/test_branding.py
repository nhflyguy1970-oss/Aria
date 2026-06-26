"""Assistant branding."""

import jarvis.branding as branding


def test_default_branding(monkeypatch):
    monkeypatch.delenv("JARVIS_ASSISTANT_NAME", raising=False)
    monkeypatch.delenv("JARVIS_ASSISTANT_FULL_NAME", raising=False)
    assert branding.assistant_name() == "ARIA"
    assert branding.assistant_full_name() == "Adaptive Reasoning Intelligence Assistant"
    assert "ARIA" in branding.assistant_intro()


def test_branding_env_override(monkeypatch):
    monkeypatch.setenv("JARVIS_ASSISTANT_NAME", "LARK")
    monkeypatch.setenv("JARVIS_ASSISTANT_FULL_NAME", "Local Autonomous Reasoning Kit")
    assert branding.assistant_name() == "LARK"
    assert branding.branding_dict()["assistant_full_name"] == "Local Autonomous Reasoning Kit"
