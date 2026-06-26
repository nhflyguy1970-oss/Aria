"""Tests for AE-5 VST bridge (software EQ + live filter config generation)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis.audio_vst import SOFTWARE_CHAINS, list_chains, process_file, status
from jarvis.audio_vst_live import (
    LIVE_SINK_NODE,
    activate_live,
    deactivate_live,
    generate_filter_conf,
    install_filter_configs,
)


def test_list_chains_includes_builtins():
    ids = {c["id"] for c in list_chains()}
    assert "voice" in ids
    assert "scout" in ids


def test_process_file_flat_passthrough(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"RIFF" + b"\0" * 40)
    assert process_file(wav, "flat") == str(wav.resolve())


def test_process_file_unknown_chain(tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"x")
    out = process_file(wav, "not_a_chain")
    assert out.startswith("ERROR:")


@patch("jarvis.audio_vst._process_ffmpeg", return_value="/tmp/out.wav")
def test_process_file_voice(mock_ff, tmp_path):
    wav = tmp_path / "a.wav"
    wav.write_bytes(b"x")
    result = process_file(wav, "voice")
    assert result == "/tmp/out.wav"
    mock_ff.assert_called_once()


def test_generate_filter_conf_voice():
    conf = generate_filter_conf("voice")
    assert "jarvis_ae5_voice" in conf
    assert "bq_peaking" in conf
    assert "libpipewire-module-filter-chain" in conf


def test_install_filter_configs_writes_files(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.audio_vst_live.FILTER_DIR", tmp_path)
    monkeypatch.setattr("jarvis.audio_vst_live.shutil.which", lambda _: "/usr/bin/pactl")
    ok, msg = install_filter_configs()
    assert ok
    assert (tmp_path / "jarvis-ae5-voice.conf").is_file()
    assert "voice" in msg.lower() or "Installed" in msg


@patch("jarvis.audio_vst_live._run", return_value=(0, "alsa_output.pci-0000_04_00.0.analog-stereo"))
@patch("jarvis.audio_vst_live._detect_pipewire_sink", return_value="alsa_output.pci-0000_04_00.0.analog-stereo")
def test_deactivate_live_restores_creative(mock_sink, mock_run):
    ok, msg = deactivate_live()
    assert ok
    assert "Creative" in msg or "alsa_output" in msg
    mock_run.assert_called()


@patch("jarvis.audio_vst_live.live_sink_available", return_value=False)
@patch("jarvis.audio_vst_live.install_filter_configs", return_value=(True, "restart pipewire"))
def test_activate_live_not_loaded(_install, _avail):
    ok, msg = activate_live("voice")
    assert not ok
    assert "not loaded" in msg.lower() or "restart" in msg.lower()


def test_status_structure():
    s = status()
    assert "chains" in s
    assert "ffmpeg" in s
    assert isinstance(s["chains"], list)


def test_all_live_presets_have_sink_nodes():
    for preset in ("voice", "music", "scout", "gaming", "flat"):
        assert preset in LIVE_SINK_NODE
        assert preset in SOFTWARE_CHAINS or preset == "flat"
