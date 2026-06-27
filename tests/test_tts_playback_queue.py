"""TTS playback queue tests."""

from __future__ import annotations

from unittest.mock import patch


def test_enqueue_and_wait_idle():
    from jarvis.tts_playback_queue import clear_tts_queue, enqueue_play, wait_tts_idle

    clear_tts_queue()
    with patch("jarvis.audio_device.play_file", return_value="ok.wav") as play:
        enqueue_play("/tmp/fake-a.wav")
        assert wait_tts_idle(timeout=2.0) is True
        play.assert_called_once_with("/tmp/fake-a.wav")


def test_clear_drops_pending():
    from jarvis.tts_playback_queue import clear_tts_queue, enqueue_play, tts_queue_busy

    clear_tts_queue()
    with patch("jarvis.audio_device.play_file", side_effect=lambda p: p):
        enqueue_play("/tmp/a.wav")
        enqueue_play("/tmp/b.wav")
    clear_tts_queue()
    assert tts_queue_busy() is False
