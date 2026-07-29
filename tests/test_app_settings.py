"""App settings — uncensored preference persistence."""

from __future__ import annotations


def test_app_settings_uncensored_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.app_settings as app_settings
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(app_settings, "SETTINGS_FILE", tmp_path / "app_settings.json")

    assert app_settings.get_uncensored() is False
    app_settings.set_uncensored_pref(True)
    assert app_settings.get_uncensored() is True
    app_settings.set_uncensored_pref(False)
    assert app_settings.get_uncensored() is False
    raw = app_settings.load()
    assert "uncensored" in raw
