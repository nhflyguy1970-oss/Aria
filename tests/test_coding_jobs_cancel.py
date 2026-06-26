"""Coding job cancel and workers."""

from jarvis import coding_jobs


def test_cancel_queued_job():
    coding_jobs._jobs.clear()
    coding_jobs._history.clear()
    coding_jobs._active_ids.clear()

    def slow():
        return {"ok": True, "message": "done"}

    job_id = coding_jobs.submit("test", slow)
    assert coding_jobs.cancel_job(job_id)
    job = coding_jobs.get_job(job_id)
    assert job["cancelled"] is True


def test_job_stats_workers():
    stats = coding_jobs.job_stats()
    assert stats["workers"] >= 1
