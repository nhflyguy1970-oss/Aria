"""Tests for Jarvis audio module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jarvis.modules.audio import AudioEngine


@pytest.fixture
def audio_engine(monkeypatch):
    monkeypatch.setenv("JARVIS_AUTO_PLAY", "0")
    monkeypatch.setenv("JARVIS_SET_DEFAULT_SINK", "0")
    with patch.object(AudioEngine, "__init__", lambda self: None):
        engine = AudioEngine()
    engine.last_transcript = ""
    engine.last_output = ""
    engine.devices = {"auto_play": False, "name": "Test Audio"}
    engine.conversation = MagicMock()
    return engine


def test_default_whisper_model(monkeypatch):
    monkeypatch.setenv("JARVIS_WHISPER_MODEL", "small")
    with patch.object(AudioEngine, "__init__", lambda self: None):
        engine = AudioEngine()
    assert engine.default_whisper_model() == "small"


def test_build_fade_out_uses_duration(audio_engine):
    cmd = audio_engine._build_ffmpeg_edit_cmd(
        Path("/tmp/in.wav"),
        Path("/tmp/out.wav"),
        fade_out_sec=2.0,
        src_duration=10.0,
    )
    joined = " ".join(cmd)
    assert "afade=t=out:st=8.0:d=2.0" in joined


def test_transcribe_uses_env_model(audio_engine, monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_WHISPER_MODEL", "tiny")
    wav = tmp_path / "clip.wav"
    wav.write_bytes(b"RIFF")
    tmp_path / "clip.txt"
    with patch.object(audio_engine, "_resolve_audio", return_value=wav), patch(
        "jarvis.audio_whisper.transcribe", return_value="hello world"
    ) as fw, patch("jarvis.audio_search.index_transcript"):
        result = audio_engine.transcribe(str(wav), model="tiny")
    assert result == "hello world"
    fw.assert_called_once()


def test_record_delegates(audio_engine, tmp_path):
    out = tmp_path / "rec.wav"
    with patch("jarvis.modules.audio.record_to_file", return_value=str(out)) as rec:
        result = audio_engine.record(3.0, source="alsa_input.usb-mic")
    rec.assert_called_once()
    assert rec.call_args.kwargs.get("source") == "alsa_input.usb-mic"
    assert result == str(out)
    assert audio_engine.last_output == str(out)


def test_effective_input_source_prefers_creative_over_usb(monkeypatch):
    from jarvis import audio_device

    monkeypatch.delenv("JARVIS_AUDIO_SOURCE", raising=False)
    usb = "alsa_input.usb-BlueTrm_USB_MIC_20170726905923-00.mono-fallback"
    creative = "alsa_input.pci-0000_04_00.0.analog-stereo"
    with patch("jarvis.audio_settings.saved_input_source", return_value=""), patch.object(
        audio_device,
        "list_input_sources",
        return_value=[
            {"name": usb, "is_usb_mic": True},
            {"name": creative, "is_usb_mic": False},
        ],
    ):
        assert audio_device.effective_input_source() == creative


def test_effective_input_source_uses_saved_usb_when_set(monkeypatch):
    from jarvis import audio_device

    usb = "alsa_input.usb-BlueTrm_USB_MIC_20170726905923-00.mono-fallback"
    with patch("jarvis.audio_settings.saved_input_source", return_value=usb):
        assert audio_device.effective_input_source() == usb


def test_capture_volume_for_creative_defaults_100(monkeypatch):
    from jarvis import audio_device

    monkeypatch.delenv("JARVIS_CREATIVE_CAPTURE_VOLUME", raising=False)
    monkeypatch.delenv("JARVIS_CAPTURE_VOLUME", raising=False)
    with patch("jarvis.audio_settings.saved_creative_capture_volume", return_value=""):
        assert audio_device.capture_volume_for("alsa_input.pci-0000_04_00.0.analog-stereo") == "100%"


def test_capture_volume_for_creative(monkeypatch):
    from jarvis import audio_device

    monkeypatch.setenv("JARVIS_CREATIVE_CAPTURE_VOLUME", "200%")
    with patch("jarvis.audio_settings.saved_creative_capture_volume", return_value=""):
        assert audio_device.capture_volume_for("alsa_input.pci-0000_04_00.0.analog-stereo") == "200%"


def test_prepare_input_source_uses_pactl_only(monkeypatch):
    from jarvis import audio_device

    with patch("jarvis.audio_settings.saved_creative_capture_volume", return_value="200%"), patch.object(
        audio_device, "_run"
    ) as run:
        audio_device.prepare_input_source("alsa_input.pci-0000_04_00.0.analog-stereo")
    assert run.call_count == 2
    assert run.call_args_list[1].args[0] == ["pactl", "set-source-volume", "alsa_input.pci-0000_04_00.0.analog-stereo", "200%"]


def test_mic_routing_status_mismatch():
    from jarvis import audio_device

    with patch.object(audio_device, "creative_mixer_snapshot", return_value={"input_source": "Microphone"}), patch(
        "jarvis.audio_settings.saved_mic_profile", return_value="front"
    ):
        st = audio_device.mic_routing_status()
    assert st["routing_ok"] is False
    assert "Front Microphone" in st["routing_hint"]


def test_speech_enhance_af_creative():
    from jarvis import audio_device

    af = audio_device._speech_enhance_af("alsa_input.pci-0000_04_00.0.analog-stereo")
    assert "afftdn" in af
    assert "loudnorm" in af
    assert "agate" in af


def test_record_rejects_silent(tmp_path):
    from jarvis import audio_device

    dest = tmp_path / "silent.wav"
    dest.write_bytes(b"RIFF")
    with patch.object(audio_device, "measure_levels_db", return_value={"peak_db": -58.5, "mean_db": -70.0}), patch.object(
        audio_device, "normalize_recording", return_value=True,
    ), patch.object(
        audio_device, "_record_with_pw_record", return_value=(True, str(dest)),
    ), patch.object(audio_device, "prepare_input_source"):
        result = audio_device.record_to_file(dest, 1.0, source="alsa_input.pci-0000_04_00.0.analog-stereo")
    assert result.startswith("ERROR:")
    assert "too low" in result
    assert not dest.exists()


def test_status_shape(audio_engine):
    with patch.object(audio_engine, "_whisper_path", return_value="/bin/whisper"), patch.object(
        audio_engine, "_ffmpeg_path", return_value="/bin/ffmpeg"
    ), patch.object(audio_engine, "_espeak_path", return_value="/bin/espeak"), patch.object(
        audio_engine, "get_devices", return_value={"name": "Test"}
    ), patch("jarvis.config.piper_ready", return_value=False):
        st = audio_engine.status()
    assert st["whisper_cli"] is True
    assert "whisper_model" in st
    assert st["devices"]["name"] == "Test"


def test_music_gen_missing_backends(tmp_path, monkeypatch):
    from jarvis import music_gen

    monkeypatch.setattr(music_gen, "MUSIC_DIR", tmp_path)
    monkeypatch.setattr(music_gen, "_transformers_available", lambda: False)
    monkeypatch.setattr(music_gen, "_audiocraft_available", lambda: False)
    result = music_gen.generate_music("calm piano", duration=5)
    assert result.startswith("ERROR:")


def test_musicgen_backend_detects_transformers():
    from jarvis.music_gen import musicgen_available, musicgen_backend

    assert isinstance(musicgen_available(), bool)
    if musicgen_available():
        assert musicgen_backend() in ("transformers", "audiocraft")


def test_saved_whisper_model():
    from jarvis.audio_settings import WHISPER_MODELS, saved_whisper_model

    assert "base" in WHISPER_MODELS
    assert saved_whisper_model() == "" or saved_whisper_model() in WHISPER_MODELS


def test_default_whisper_model_uses_saved(monkeypatch):
    with patch.object(AudioEngine, "__init__", lambda self: None):
        engine = AudioEngine()
    with patch("jarvis.modules.audio.saved_whisper_model", return_value="small"):
        assert engine.default_whisper_model() == "small"


def test_analyze_audio(audio_engine, monkeypatch, tmp_path):
    wav = tmp_path / "clip.wav"
    wav.write_bytes(b"RIFF")
    with patch.object(audio_engine, "transcribe", return_value="hello there"), patch(
        "jarvis.modules.audio.llm.ask", return_value="Summary line"
    ):
        result = audio_engine.analyze(str(wav))
    assert result["ok"] is True
    assert result["transcript"] == "hello there"
    assert "Summary" in result["summary"]


def test_waveform_peaks(audio_engine, tmp_path):
    import struct
    import wave

    wav = tmp_path / "tone.wav"
    with wave.open(str(wav), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        frames = struct.pack("<h", 16000) * 800
        wf.writeframes(frames)
    with patch.object(audio_engine, "_resolve_audio", return_value=wav), patch.object(
        audio_engine, "_probe_duration", return_value=0.1
    ):
        result = audio_engine.waveform(str(wav), samples=50)
    assert result["ok"] is True
    assert len(result["peaks"]) <= 50
    assert max(result["peaks"]) > 0


def test_ptt_cancels_stale_sessions():
    from jarvis import audio_device

    with patch("jarvis.audio_device.shutil.which", return_value="/usr/bin/pw-record"), patch.object(
        audio_device, "effective_input_source", return_value="alsa_input.test"
    ), patch.object(audio_device, "prepare_input_source"), patch.object(
        audio_device, "_is_creative_input", return_value=False
    ), patch("jarvis.audio_device.subprocess.Popen") as popen:
        proc = MagicMock()
        proc.poll.return_value = None
        popen.return_value = proc
        sid1, _ = audio_device.start_ptt_record(Path("/tmp/a.wav"))
        sid2, _ = audio_device.start_ptt_record(Path("/tmp/b.wav"))
    assert sid1 != sid2
    proc.kill.assert_called()


def test_record_ptt_flow(audio_engine, tmp_path, monkeypatch):
    out = tmp_path / "ptt.wav"
    with patch("jarvis.modules.audio.start_ptt_record", return_value=("abc123", "")), patch(
        "jarvis.modules.audio.RECORDINGS_DIR", tmp_path
    ):
        sid, path = audio_engine.record_ptt_start()
    assert sid == "abc123"
    with patch("jarvis.modules.audio.stop_ptt_record", return_value=str(out)):
        assert audio_engine.record_ptt_stop("abc123") == str(out)


def test_audio_search_index():
    from jarvis.audio_search import index_transcript, search

    index_transcript("/tmp/test.wav", "hello jarvis audio search", title="test.wav")
    hits = search("jarvis audio")
    assert any("jarvis" in h.get("snippet", "").lower() for h in hits)


def test_whisper_backend():
    from jarvis.audio_whisper import whisper_backend
    assert whisper_backend() in ("faster-whisper", "cli", "none")


def test_torch_device():
    from jarvis.torch_device import device_info, torch_device, whisper_device

    assert torch_device() in ("cuda", "cpu", "mps")
    assert whisper_device() in ("cuda", "cpu", "auto")
    info = device_info()
    assert "device" in info
    assert "whisper_device" in info


def test_hf_token_configured(monkeypatch):
    from jarvis.audio_diarize import diarize_status, hf_token_configured

    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACE_TOKEN", raising=False)
    assert hf_token_configured() is False
    st = diarize_status()
    assert "pyannote" in st
    assert st["hf_token"] is False


def test_diarize_fallback(tmp_path):
    from jarvis.audio_diarize import _format_diarized

    segs = [
        {"speaker": "Speaker A", "start": 0, "end": 1, "text": "hello"},
        {"speaker": "Speaker B", "start": 2, "end": 3, "text": "world"},
    ]
    text = _format_diarized(segs)
    assert "Speaker A" in text
    assert "hello" in text


def test_clean_wakeword_transcript():
    from jarvis.audio_wakeword import _clean_wakeword_transcript

    assert _clean_wakeword_transcript("Hey Jarvis, what's the weather?") == "what's the weather?"
    assert _clean_wakeword_transcript("hey jarvis") == "hey jarvis"


def test_wakeword_status():
    from jarvis.audio_wakeword import status, wakeword_available
    assert isinstance(wakeword_available(), bool)
    st = status()
    assert "available" in st
    assert "record_on_detect" in st
    assert "phrase" in st


def test_load_wakeword_model():
    from jarvis.audio_wakeword import OWW_FRAME_SAMPLES, load_wakeword_model
    import numpy as np

    model = load_wakeword_model("hey_jarvis")
    assert model.models
    frame = np.zeros(OWW_FRAME_SAMPLES, dtype=np.int16)
    pred = model.predict(frame)
    assert pred


def test_resolve_audio_rejects_unknown(audio_engine):
    with pytest.raises(ValueError, match="Unsupported"):
        audio_engine._resolve_audio("file.xyz")
