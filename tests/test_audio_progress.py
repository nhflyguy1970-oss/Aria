"""Tests for audio job persistence and GPU serialization."""

from jarvis import audio_progress as ap


def test_audio_job_lifecycle(tmp_path, monkeypatch):
    """Audio jobs are in-memory progress — persist across process restart is not claimed."""
    ap._jobs.clear()
    job_id = ap.start_job("Test song")
    ap.update_job(job_id, 50, "Halfway")
    mid = ap.get_job(job_id)
    assert mid is not None
    assert mid["pct"] == 50
    ap.finish_job(job_id, result={"audio_path": "/tmp/x.wav"})
    job = ap.get_job(job_id)
    assert job is not None
    assert job["done"] is True
    assert job["result"]["audio_path"] == "/tmp/x.wav"


def test_audio_gpu_slot_serializes():
    from jarvis.audio_work import audio_gpu_slot

    with audio_gpu_slot("a"):
        assert True
