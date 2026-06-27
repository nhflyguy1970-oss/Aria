"""Tests for P1 #34 voice-only demo mode."""

from __future__ import annotations

import os


def test_strip_for_speech():
    from jarvis.voice_only import strip_for_speech

    assert strip_for_speech("**Hello** `world`") == "Hello world"
    assert "code" in strip_for_speech("Before ```python\nx=1\n``` after").lower() or "Before" in strip_for_speech(
        "Before ```python\nx=1\n``` after"
    )


def test_prepare_voice_only_env():
    from jarvis.voice_only import prepare_voice_only_env

    prepare_voice_only_env()
    assert os.environ.get("JARVIS_VOICE_ONLY") == "1"
    assert os.environ.get("JARVIS_WAKEWORD_TO_CHAT") == "1"
    assert os.environ.get("JARVIS_WAKEWORD_SPEAK") == "0"


def test_voice_only_flag():
    from jarvis.p1_flags import voice_only_enabled

    assert isinstance(voice_only_enabled(), bool)


def test_run_once_mock(monkeypatch):
    from jarvis.voice_only import run_once

    class FakeAudio:
        def generate(self, text, auto_play=True):
            return "/tmp/test.wav"

    class FakeSession:
        pass

    class FakeAssistant:
        session = FakeSession()
        audio = FakeAudio()

        def process(self, message, voice=False):
            return {"ok": True, "message": f"Echo: {message}"}

    monkeypatch.setattr("jarvis.voice_only.speak_text", lambda text, assistant=None: "")
    result = run_once("set a timer", assistant=FakeAssistant())
    assert result["ok"] is True
    assert "Echo" in result["message"]
