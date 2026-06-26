"""Tests for coding job queue."""

import time

from jarvis.coding_jobs import get_job, job_stats, submit


def test_coding_job_completes():
    done = []

    def work():
        done.append(True)
        return {"ok": True, "message": "proposal ready", "type": "proposal"}

    job_id = submit("Test task", work)
    for _ in range(50):
        job = get_job(job_id)
        assert job is not None
        if job["done"]:
            assert job["result"]["ok"] is True
            assert done
            break
        time.sleep(0.05)
    else:
        raise AssertionError("coding job did not finish")


def test_coding_job_stats():
    stats = job_stats()
    assert "busy" in stats
    assert "completed" in stats
