"""TTS playback queue tests."""

from __future__ import annotations

from unittest.mock import patch


def test_enqueue_and_wait_idle(tmp_path):
    from jarvis.tts_playback_queue import clear_tts_queue, enqueue_play, wait_tts_idle

    wav = tmp_path / "fake-a.wav"
    wav.write_bytes(b"RIFF")
    clear_tts_queue()
    with patch("jarvis.audio_device.play_file", return_value=str(wav)) as play:
        enqueue_play(str(wav))
        assert wait_tts_idle(timeout=2.0) is True
        play.assert_called_once_with(str(wav))


def test_clear_drops_pending(tmp_path):
    from jarvis.tts_playback_queue import clear_tts_queue, enqueue_play, tts_queue_busy

    a = tmp_path / "a.wav"
    b = tmp_path / "b.wav"
    a.write_bytes(b"RIFF")
    b.write_bytes(b"RIFF")
    clear_tts_queue()
    with patch("jarvis.audio_device.play_file", side_effect=lambda p: p):
        enqueue_play(str(a))
        enqueue_play(str(b))
    clear_tts_queue()
    assert tts_queue_busy() is False


def test_queue_status_shape():
    from jarvis.tts_playback_queue import get_queue_status

    st = get_queue_status()
    assert "pending" in st
    assert "busy" in st
    assert "idle" in st
