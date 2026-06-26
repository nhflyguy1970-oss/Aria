"""Audio job cancellation."""

import pytest

from jarvis.audio_progress import JobCancelled, cancel_job, finish_job, start_job, update_job


def test_cancel_job_stops_updates():
    job_id = start_job("test")
    assert cancel_job(job_id)
    with pytest.raises(JobCancelled):
        update_job(job_id, 50, "mid")
    finish_job(job_id, error="Cancelled by user")
