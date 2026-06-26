"""Persisted GUI preferences."""

from jarvis import app_settings


def test_uncensored_pref_roundtrip(data_dir, monkeypatch):
    monkeypatch.setattr(app_settings, "SETTINGS_FILE", data_dir / "app_settings.json")
    assert app_settings.get_uncensored() is False
    app_settings.set_uncensored_pref(True)
    assert app_settings.get_uncensored() is True
    app_settings.set_uncensored_pref(False)
    assert app_settings.get_uncensored() is False
