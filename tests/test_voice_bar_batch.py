"""Tests for voice bar batch #26 #27 #30 #84."""

from __future__ import annotations

from unittest.mock import patch


def test_duplex_status_modes():
    from jarvis.voice_duplex import duplex_status

    with patch("jarvis.voice_duplex.duplex_mode", return_value="half"):
        st = duplex_status()
    assert st["mode"] == "half"
    assert st["barge_in"] is False
    assert st["stop_before_listen"] is True

    with patch("jarvis.voice_duplex.duplex_mode", return_value="full"):
        st = duplex_status()
    assert st["barge_in"] is True


def test_tts_stream_chunks():
    from jarvis.tts_stream import split_speak_chunks

    text = "Hello world. This is ARIA. " + ("More text here. " * 5)
    chunks = split_speak_chunks(text, max_chars=40)
    assert chunks
    assert all(len(c) <= 40 for c in chunks)


def test_cloud_live_openai_rejected_without_webrtc():
    from jarvis.cloud_live_voice import start_live_session

    with patch(
        "jarvis.cloud_live_voice.cloud_live_status",
        return_value={"available": True, "provider": "openai_realtime", "openai_key": True},
    ):
        out = start_live_session(provider="openai_realtime")
    assert out.get("ok") is False
    assert "WebRTC" in (out.get("message") or "")


def test_cloud_live_gemini_session_mock():
    from jarvis.cloud_live_voice import start_live_session

    fake = {
        "ok": True,
        "provider": "gemini_live",
        "model": "models/gemini-test",
        "bridge_ws": "/ws/gemini-live/abc",
    }
    with patch(
        "jarvis.cloud_live_voice.cloud_live_status",
        return_value={"available": True, "provider": "gemini_live"},
    ):
        with patch("jarvis.cloud_live_voice._create_gemini_live_session", return_value=fake):
            out = start_live_session(provider="gemini_live")
    assert out.get("ok") is True
    assert out.get("provider") == "gemini_live"
    assert out.get("session_id")
    assert out.get("bridge_ws")
