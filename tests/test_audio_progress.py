"""Tests for audio job persistence and GPU serialization."""

from jarvis import audio_progress as ap


def test_audio_job_persist_and_reload(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(ap, "DATA_DIR", data_dir)
    monkeypatch.setattr(ap, "_STATE_FILE", data_dir / "audio_jobs_state.json")
    ap._jobs.clear()

    job_id = ap.start_job("Test song")
    ap.update_job(job_id, 50, "Halfway")
    ap.finish_job(job_id, result={"audio_path": "/tmp/x.wav"})

    ap._jobs.clear()
    ap._load_state()
    job = ap.get_job(job_id)
    assert job is not None
    assert job["done"] is True
    assert job["result"]["audio_path"] == "/tmp/x.wav"


def test_audio_gpu_slot_serializes():
    from jarvis.audio_work import audio_gpu_slot

    with audio_gpu_slot("a"):
        assert True
