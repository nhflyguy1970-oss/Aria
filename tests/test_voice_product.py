"""Voice product — unified pipeline, status, profiles, recovery, Cloud Live honesty."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_emit_voice_state_exists_and_publishes():
    from jarvis.events import emit_voice_state
    from jarvis.voice_product.status_bus import get_voice_state, set_voice_state

    set_voice_state("idle", publish=False)
    with patch("jarvis.ws_hub.publish") as pub:
        emit_voice_state("listening", detail="test")
        assert get_voice_state()["state"] == "listening"
        pub.assert_called()
        assert pub.call_args[0][0] == "voice_state"


def test_unified_settings_roundtrip(tmp_path, monkeypatch):
    from jarvis.voice_product import settings as vs

    monkeypatch.setattr(vs, "VOICE_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(vs, "LEGACY_VOICE_FILE", tmp_path / "legacy.json")
    saved = vs.save_unified_settings(
        {"speak_replies": True, "server_whisper": True, "duplex_mode": "half"}
    )
    assert saved["speak_replies"] is True
    loaded = vs.load_unified_settings()
    assert loaded["speak_replies"] is True
    assert loaded["duplex_mode"] == "half"
    assert not (tmp_path / "legacy.json").exists()


def test_voice_settings_adapter_uses_unified(tmp_path, monkeypatch):
    from jarvis.voice_product import settings as vs
    import jarvis.voice_settings as legacy

    monkeypatch.setattr(vs, "VOICE_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(vs, "LEGACY_VOICE_FILE", tmp_path / "legacy.json")
    vs.save_unified_settings({"duplex_mode": "full", "stt_backend": "whisper"})
    data = legacy.load_voice_settings()
    assert data["duplex_mode"] == "full"
    assert legacy.stt_backend() == "whisper"


def test_legacy_voice_settings_migrate_once(tmp_path, monkeypatch):
    from jarvis.voice_product import settings as vs

    voice_file = tmp_path / "settings.json"
    legacy_file = tmp_path / "voice_settings.json"
    legacy_file.write_text('{"duplex_mode": "full", "stt_backend": "vosk"}', encoding="utf-8")
    monkeypatch.setattr(vs, "VOICE_FILE", voice_file)
    monkeypatch.setattr(vs, "LEGACY_VOICE_FILE", legacy_file)

    data = vs.load_unified_settings()

    assert data["duplex_mode"] == "full"
    assert data["stt_backend"] == "vosk"
    assert voice_file.is_file()
    assert not legacy_file.exists()


def test_voice_save_does_not_mirror_audio_settings(tmp_path, monkeypatch):
    from jarvis import audio_settings
    from jarvis.voice_product import settings as vs

    monkeypatch.setattr(vs, "VOICE_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(vs, "LEGACY_VOICE_FILE", tmp_path / "legacy.json")
    monkeypatch.setattr(audio_settings, "SETTINGS_FILE", tmp_path / "audio_settings.json")

    vs.save_unified_settings({"duplex_mode": "full"})

    assert not audio_settings.SETTINGS_FILE.exists()


def test_intent_router_gallery_and_chat_fallback():
    from jarvis.voice_product.intent_router import apply_route, route_utterance

    route = route_utterance("please open the gallery")
    assert route["product"] == "gallery"
    out = apply_route(route)
    assert out["handled"] is True
    assert out["navigate"] == "gallery"
    assert route_utterance("what is the weather in toronto") is None


def test_profiles_builtin_and_activate(tmp_path, monkeypatch):
    from jarvis.voice_product import profiles as vp
    from jarvis.voice_product import settings as vs

    monkeypatch.setattr(vp, "PROFILES_FILE", tmp_path / "profiles.json")
    monkeypatch.setattr(vs, "VOICE_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(vs, "LEGACY_VOICE_FILE", tmp_path / "legacy.json")
    profiles = vp.list_profiles()
    assert any(p["id"] == "quiet_office" for p in profiles)
    activated = vp.activate_profile("coding")
    assert activated["id"] == "coding"
    assert vs.load_unified_settings().get("active_profile") == "coding"
    assert vs.load_unified_settings().get("speak_replies") is False


def test_duplex_before_listen_stops_when_half():
    from jarvis.voice_duplex import before_listen

    with patch("jarvis.voice_duplex.duplex_mode", return_value="half"):
        with patch("jarvis.tts_playback_queue.clear_tts_queue") as clear:
            with patch("jarvis.audio_device.stop_playback") as stop:
                before_listen()
                clear.assert_called_once()
                stop.assert_called_once()


def test_duplex_full_skips_before_listen_stop():
    from jarvis.voice_duplex import before_listen

    with patch("jarvis.voice_duplex.duplex_mode", return_value="full"):
        with patch("jarvis.tts_playback_queue.clear_tts_queue") as clear:
            before_listen()
            clear.assert_not_called()


def test_barge_in_full_duplex():
    from jarvis.voice_duplex import maybe_barge_in

    with patch("jarvis.voice_duplex.duplex_mode", return_value="full"):
        with patch("jarvis.voice_duplex.load_voice_settings", return_value={"interrupt_on_speak": True}):
            with patch("jarvis.audio_device.playback_active", return_value=True):
                with patch("jarvis.tts_playback_queue.clear_tts_queue") as clear:
                    with patch("jarvis.audio_device.stop_playback"):
                        with patch("jarvis.events.emit_voice_state"):
                            assert maybe_barge_in() is True
                            clear.assert_called()


def test_cloud_live_hides_openai_without_webrtc():
    from jarvis import cloud_live_voice as cl

    with patch.object(cl, "OPENAI_WEBRTC_CLIENT_READY", False):
        with patch.object(cl, "_openai_key_usable", return_value=True):
            with patch.object(cl, "_gemini_key_usable", return_value=False):
                with patch.object(cl, "_openai_key", return_value="sk-test"):
                    with patch.object(cl, "_gemini_key", return_value=""):
                        with patch("jarvis.cloud_live_voice.cloud_live_voice_enabled", return_value=True):
                            st = cl.cloud_live_status()
    assert st.get("openai_hidden") is True
    assert "openai_realtime" not in (st.get("providers_shown") or [])
    assert st.get("provider") in ("", None)


def test_cloud_live_rejects_openai_start_without_webrtc():
    from jarvis.cloud_live_voice import start_live_session

    with patch(
        "jarvis.cloud_live_voice.cloud_live_status",
        return_value={"available": True, "provider": "openai_realtime"},
    ):
        out = start_live_session(provider="openai_realtime")
    assert out.get("ok") is False
    assert "WebRTC" in (out.get("message") or "")


def test_speak_text_uses_queue():
    from jarvis.voice_product.engine import speak_text

    audio = MagicMock()
    audio.generate.return_value = "/tmp/fake.wav"
    assistant = MagicMock()
    assistant.audio = audio

    with patch("jarvis.voice_product.speech_policy.should_speak_reply", return_value=True):
        with patch("jarvis.voice_product.settings.load_unified_settings", return_value={
            "interrupt_on_speak": False,
            "speak_chunk_sentences": False,
        }):
            with patch("jarvis.tts_stream.sanitize_for_speech", return_value="Hello there"):
                with patch("pathlib.Path.is_file", return_value=True):
                    with patch("jarvis.tts_playback_queue.enqueue_play") as enq:
                        with patch("jarvis.voice_product.status_bus.set_voice_state"):
                            out = speak_text("Hello", assistant=assistant, force=True, source="test")
    assert out.get("ok") is True
    enq.assert_called()
    audio.generate.assert_called()


def test_process_utterance_routes_intent():
    from jarvis.voice_product.engine import process_utterance

    with patch("jarvis.voice_product.engine.speak_text", return_value={"ok": True}):
        with patch("jarvis.voice_product.status_bus.set_voice_state"):
            out = process_utterance("open mission control", source="api")
    assert out.get("handled") is True
    assert out.get("product") == "mission_control"
    assert out.get("pipeline") == "voice_engine"


def test_recovery_diagnose_shape():
    from jarvis.voice_product.recovery import diagnose

    d = diagnose()
    assert "severity" in d
    assert "issues" in d
    assert "healthy" in d
    assert "mic_note" in d


def test_speech_policy_redaction():
    from jarvis.voice_product.speech_policy import presentation_for_profile

    open_view = presentation_for_profile(transcript="secret", audio_url="/a.wav", censored=False)
    assert open_view["redacted"] is False
    closed = presentation_for_profile(transcript="secret", audio_url="/a.wav", censored=True)
    assert closed["redacted"] is True
    assert closed["has_original"] is True
    assert "secret" not in closed["transcript"]


def test_mission_bridge_panel():
    from jarvis.voice_product.mission_bridge import voice_mission_panel

    panel = voice_mission_panel()
    assert panel["product"] == "Voice"
    assert "deep_links" in panel
    assert "recovery" in panel


def test_tts_queue_status():
    from jarvis.tts_playback_queue import get_queue_status

    st = get_queue_status()
    assert "pending" in st
    assert "busy" in st


def test_experimental_status():
    from jarvis.voice_product.experimental import experimental_status

    st = experimental_status()
    assert st["experimental"] is True
    assert "flags" in st


@pytest.mark.parametrize(
    "utterance,product",
    [
        ("open browser", "browser"),
        ("generate an image of a cat", "image_generation"),
        ("show coding", "coding"),
        ("stop speaking", "voice"),
    ],
)
def test_intent_routes_param(utterance, product):
    from jarvis.voice_product.intent_router import route_utterance

    r = route_utterance(utterance)
    assert r is not None
    assert r["product"] == product
