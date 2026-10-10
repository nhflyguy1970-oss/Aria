"""Disabled optional execution must stop before exports, secrets or models."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from jarvis import audio_diarize, router_training


@pytest.fixture(autouse=True)
def guarded_environment(monkeypatch):
    monkeypatch.setenv("JARVIS_SAFE_MODE", "0")
    monkeypatch.setenv("JARVIS_AUTONOMY", "bounded")
    monkeypatch.delenv("JARVIS_TRAINING_ENABLED", raising=False)
    monkeypatch.delenv("JARVIS_DIARIZATION_ENABLED", raising=False)


DISABLED = [("0", None), ("0", "0"), ("0", "false"), ("0", "invalid"), ("1", "1")]


def flag(monkeypatch, key, value):
    if value is None:
        monkeypatch.delenv(key, raising=False)
    else:
        monkeypatch.setenv(key, value)


@pytest.mark.parametrize("safe,enabled", DISABLED)
@pytest.mark.parametrize("entry", ["train_router_model", "train_functiongemma_router"])
def test_disabled_training_has_no_side_effects(monkeypatch, tmp_path, safe, enabled, entry):
    monkeypatch.setenv("JARVIS_SAFE_MODE", safe)
    flag(monkeypatch, "JARVIS_TRAINING_ENABLED", enabled)
    exporter = Mock(side_effect=AssertionError("training export must not run"))
    runner = Mock(side_effect=AssertionError("model subprocess must not run"))
    monkeypatch.setattr(router_training, "export_training_jsonl", exporter)
    monkeypatch.setattr(router_training, "export_functiongemma_jsonl", exporter)
    monkeypatch.setattr(router_training.subprocess, "run", runner)
    kwargs = {"output_dir": str(tmp_path / "must-not-exist")} if entry == "train_functiongemma_router" else {}
    result = getattr(router_training, entry)(**kwargs)
    assert result["ok"] is False and result["blocked"] is True and result["error"]
    exporter.assert_not_called()
    runner.assert_not_called()
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("safe,enabled", DISABLED)
def test_disabled_diarization_and_status_do_not_probe_or_execute(monkeypatch, tmp_path, safe, enabled):
    monkeypatch.setenv("JARVIS_SAFE_MODE", safe)
    flag(monkeypatch, "JARVIS_DIARIZATION_ENABLED", enabled)
    forbidden = Mock(side_effect=AssertionError("disabled dependency/credential/backend reached"))
    for name in ("hf_token", "hf_token_configured", "pyannote_available", "_diarize_pyannote", "_diarize_whisper_segments"):
        monkeypatch.setattr(audio_diarize, name, forbidden)
    # A nonexistent path still reports disabled, proving the guard precedes file access.
    result = audio_diarize.diarize(tmp_path / "never-read.wav")
    assert result["ok"] is False and result["blocked"] is True
    status = audio_diarize.diarize_status()
    assert status["enabled"] is False and status["engine"] == "disabled"
    forbidden.assert_not_called()
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("safe,enabled", [("0", "0"), ("1", "1")])
def test_real_http_training_and_diarization_paths_are_blocked(monkeypatch, tmp_path, safe, enabled):
    from fastapi.testclient import TestClient
    from jarvis.gui import server

    monkeypatch.setenv("JARVIS_SAFE_MODE", safe)
    monkeypatch.setenv("JARVIS_TRAINING_ENABLED", enabled)
    monkeypatch.setenv("JARVIS_DIARIZATION_ENABLED", enabled)
    forbidden = Mock(side_effect=AssertionError("HTTP must not reach implementation side effects"))
    for name in ("export_training_jsonl", "export_functiongemma_jsonl"):
        monkeypatch.setattr(router_training, name, forbidden)
    for name in ("hf_token", "pyannote_available", "_diarize_pyannote", "_diarize_whisper_segments"):
        monkeypatch.setattr(audio_diarize, name, forbidden)
    fixture = tmp_path / "audio.wav"
    fixture.write_bytes(b"private fixture")
    monkeypatch.setattr(server.assistant.audio, "_resolve_audio", lambda path: fixture)
    # No lifespan context: do not start background workers/services.
    client = TestClient(server.app)
    for endpoint in ("/api/router/training/train", "/api/router/training/train-functiongemma"):
        response = client.post(endpoint)
        assert response.status_code == 200
        assert response.json()["blocked"] is True and response.json()["ok"] is False
    response = client.post("/api/audio/diarize", data={"path": str(fixture)})
    assert response.status_code == 400 and response.json()["ok"] is False
    assert "disabled" in response.json()["message"] or "safe mode" in response.json()["message"]
    forbidden.assert_not_called()


def test_behavior_diarization_uses_the_same_guard(monkeypatch, tmp_path):
    from jarvis.behaviors.audio.engine import AudioActionEngine
    from jarvis.modules.audio import AudioEngine

    module = AudioEngine.__new__(AudioEngine)
    module._resolve_audio = lambda path: tmp_path / "fixture.wav"
    forbidden = Mock(side_effect=AssertionError("behavior must not execute backend"))
    monkeypatch.setattr(audio_diarize, "hf_token", forbidden)
    ctx = SimpleNamespace(audio=module, session=SimpleNamespace(resolve_audio=lambda path: "fixture.wav"))
    result = AudioActionEngine.diarize_audio(ctx, {}, "diarize it")
    assert result["ok"] is False and "disabled" in result["message"]
    forbidden.assert_not_called()


def test_explicitly_enabled_router_still_creates_model_using_mock_runner(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_TRAINING_ENABLED", "1")
    exported = tmp_path / "training.jsonl"
    exported.write_text('{"messages":[{"content":"hi"},{"content":"chat"}]}\n')
    monkeypatch.setattr(router_training, "export_training_jsonl", lambda: exported)
    monkeypatch.setattr(router_training, "MODELFILE", tmp_path / "router.Modelfile")
    monkeypatch.setattr("jarvis.local_router.router_model", lambda: "fixture-base")
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(router_training.subprocess, "run", runner)
    assert router_training.train_router_model(name="fixture-router")["ok"] is True
    assert runner.call_args.args[0][:3] == ["ollama", "create", "fixture-router"]
    monkeypatch.setenv("JARVIS_TRAINING_ENABLED", "0")
    assert router_training.train_router_model()["blocked"] is True
    assert runner.call_count == 1


def test_enabled_functiongemma_reaches_export_without_loading_models(monkeypatch, tmp_path):
    monkeypatch.setenv("JARVIS_TRAINING_ENABLED", "1")
    exporter = Mock(return_value=tmp_path / "missing.jsonl")
    monkeypatch.setattr(router_training, "export_functiongemma_jsonl", exporter)
    result = router_training.train_functiongemma_router()
    assert "No FunctionGemma training rows" in result["error"]
    exporter.assert_called_once()


@pytest.mark.parametrize("engine", ["pyannote", "whisper", "pyannote_failure"])
def test_enabled_diarization_retains_backends_and_fallback(monkeypatch, tmp_path, engine):
    monkeypatch.setenv("JARVIS_DIARIZATION_ENABLED", "1")
    path = tmp_path / "fixture.wav"
    path.write_bytes(b"fixture")
    monkeypatch.setattr(audio_diarize, "hf_token", lambda: "fixture-token")
    monkeypatch.setattr(audio_diarize, "pyannote_available", lambda: engine != "whisper")
    pyannote = Mock(return_value={"ok": True, "engine": "pyannote"})
    if engine == "pyannote_failure":
        pyannote.side_effect = RuntimeError("fixture backend failure")
    whisper = Mock(return_value={"ok": True, "engine": "whisper"})
    monkeypatch.setattr(audio_diarize, "_diarize_pyannote", pyannote)
    monkeypatch.setattr(audio_diarize, "_diarize_whisper_segments", whisper)
    result = audio_diarize.diarize(path, num_speakers=2)
    assert result["engine"] == ("pyannote" if engine == "pyannote" else "whisper")
    monkeypatch.setenv("JARVIS_DIARIZATION_ENABLED", "0")
    calls = pyannote.call_count + whisper.call_count
    assert audio_diarize.diarize(path)["blocked"] is True
    assert pyannote.call_count + whisper.call_count == calls
