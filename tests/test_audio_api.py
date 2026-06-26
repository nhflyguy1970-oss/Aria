"""API tests for /api/audio/* routes."""

from __future__ import annotations

import pytest


@pytest.fixture
def audio_client(assistant, data_dir, monkeypatch):
    import jarvis.gui.server as gui_server
    import jarvis.modules.audio as audio_mod
    from fastapi.testclient import TestClient

    rec = data_dir / "audio" / "recordings"
    gen = data_dir / "audio" / "generated"
    edited = data_dir / "audio" / "edited"
    for d in (rec, gen, edited):
        d.mkdir(parents=True, exist_ok=True)
    lib = {"recordings": rec, "generated": gen, "edited": edited}
    monkeypatch.setattr(audio_mod, "AUDIO_DIR", data_dir / "audio")
    monkeypatch.setattr(audio_mod, "RECORDINGS_DIR", rec)
    monkeypatch.setattr(audio_mod, "GENERATED_DIR", gen)
    monkeypatch.setattr(audio_mod, "EDITED_DIR", edited)
    monkeypatch.setattr(audio_mod, "AUDIO_LIBRARY_DIRS", lib)
    monkeypatch.setattr(audio_mod, "DATA_DIR", data_dir)
    monkeypatch.setattr("jarvis.config.DATA_DIR", data_dir)
    monkeypatch.setattr(gui_server, "assistant", assistant)
    monkeypatch.setattr(gui_server, "DATA_DIR", data_dir)
    monkeypatch.setattr("jarvis.gui.extra_routes.DATA_DIR", data_dir)
    return TestClient(gui_server.app)


def test_audio_status(audio_client):
    res = audio_client.get("/api/audio/status")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "whisper_model" in body


def test_audio_torch_device(audio_client):
    res = audio_client.get("/api/audio/torch-device")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "device" in res.json()


def test_audio_session_roundtrip(audio_client):
    res = audio_client.post("/api/audio/session", data={"transcript": "hello", "audio_path": "/tmp/x.wav"})
    assert res.status_code == 200
    sess = audio_client.get("/api/audio/session").json()
    assert sess["session"]["transcript"] == "hello"


def test_audio_search_empty(audio_client):
    res = audio_client.get("/api/audio/search?q=nonexistent_xyz")
    assert res.status_code == 200
    assert res.json()["results"] == []


def test_audio_wakeword_status(audio_client):
    res = audio_client.get("/api/audio/wakeword/status")
    assert res.status_code == 200
    assert "available" in res.json()


def test_audio_vocals_status(audio_client):
    res = audio_client.get("/api/audio/vocals/status")
    assert res.status_code == 200
    assert "bark" in res.json()


def test_audio_music_status(audio_client):
    res = audio_client.get("/api/audio/music/status")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_audio_recent(audio_client):
    res = audio_client.get("/api/audio/recent")
    assert res.status_code == 200
    assert "recordings" in res.json()
    assert "songs" in res.json()


def test_audio_delete_file(audio_client, data_dir):
    rec_dir = data_dir / "audio" / "recordings"
    rec_dir.mkdir(parents=True, exist_ok=True)
    wav = rec_dir / "test_delete.wav"
    wav.write_bytes(b"RIFF")
    res = audio_client.post("/api/audio/delete", data={"path": str(wav), "category": "recordings"})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert not wav.exists()


def test_audio_delete_rejects_outside_data(audio_client):
    res = audio_client.post("/api/audio/delete", data={"path": "/etc/passwd", "category": "recordings"})
    assert res.status_code == 400


def test_audio_file_rejects_outside_library(audio_client, data_dir):
    secret = data_dir / "secret.wav"
    secret.write_bytes(b"x")
    res = audio_client.get("/api/audio/file", params={"path": str(secret)})
    assert res.status_code == 404


def test_audio_file_serves_library_file(audio_client, data_dir):
    rec = data_dir / "audio" / "recordings" / "playme.wav"
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_bytes(b"RIFF")
    res = audio_client.get("/api/audio/file", params={"path": str(rec)})
    assert res.status_code == 200


def test_audio_whisper_language(audio_client):
    res = audio_client.post("/api/audio/whisper-language", data={"language": "en"})
    assert res.status_code == 200
    assert res.json()["whisper_language"] == "en"


def test_audio_diarize_mock(audio_client, assistant, monkeypatch, data_dir):
    wav = data_dir / "test.wav"
    wav.write_bytes(b"x")
    monkeypatch.setattr(
        assistant.audio,
        "diarize",
        lambda path, num_speakers=None: {
            "ok": True,
            "engine": "test",
            "segments": [{"speaker": "A", "start": 0, "end": 1, "text": "hi"}],
            "transcript": "**A:** hi",
        },
    )
    res = audio_client.post("/api/audio/diarize", data={"path": str(wav)})
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_audio_job_not_found(audio_client):
    res = audio_client.get("/api/audio/job/doesnotexist")
    assert res.status_code == 404


def test_audio_devices(audio_client):
    res = audio_client.get("/api/audio/devices")
    assert res.status_code == 200


def test_audio_piper_speed(audio_client):
    res = audio_client.post("/api/audio/piper-speed", data={"speed": "1.1"})
    assert res.status_code == 200
    assert res.json()["piper_speed"] == 1.1
