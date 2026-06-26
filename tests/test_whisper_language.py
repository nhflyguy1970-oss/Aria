"""Whisper language auto-detect."""

from jarvis.audio_whisper import _effective_language


def test_effective_language_auto(monkeypatch):
    monkeypatch.setenv("JARVIS_WHISPER_LANGUAGE", "auto")
    monkeypatch.setattr("jarvis.audio_whisper.saved_whisper_language", lambda: "auto")
    assert _effective_language(None) is None
    assert _effective_language("auto") is None


def test_effective_language_explicit():
    assert _effective_language("es") == "es"
