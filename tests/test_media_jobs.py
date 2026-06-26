"""Tests for media job queue."""

from jarvis.media_jobs import (
    ACTION_LABELS,
    QUEUED_ACTIONS,
    busy_state,
    cancel_job,
    get_job,
    is_busy,
    submit,
)


def test_submit_and_complete():
    done = []

    def work():
        done.append(True)
        return {"ok": True, "message": "done"}

    job_id = submit("generate_image", "Test image", work)
    assert job_id
    import time

    for _ in range(50):
        job = get_job(job_id)
        assert job is not None
        if job["done"]:
            assert job["result"]["ok"] is True
            assert done
            break
        time.sleep(0.05)
    else:
        raise AssertionError("job did not finish")


def test_busy_state_tracks_queue():
    state = busy_state()
    assert "busy" in state
    assert "pending" in state


def test_queued_actions_cover_media():
    assert "generate_image" in QUEUED_ACTIONS
    assert "generate_video" in QUEUED_ACTIONS
    assert ACTION_LABELS["generate_video"] == "Video render"


def test_cancel_before_start():
    import threading

    gate = threading.Event()

    def blocked():
        gate.wait(timeout=5)
        return {"ok": True}

    job_id = submit("generate_meme", "Meme", blocked)
    assert cancel_job(job_id) is True
    gate.set()


def test_cancel_active_job_interrupts():
    import threading
    import time

    from jarvis.media_jobs import MediaJobCancelled, job_cancelled, raise_if_cancelled

    started = threading.Event()

    def work():
        started.set()
        while not job_cancelled():
            time.sleep(0.02)
        raise_if_cancelled()
        return {"ok": True}

    job_id = submit("generate_image", "Test", work)
    for _ in range(100):
        if started.wait(timeout=0.05):
            break
    assert cancel_job(job_id)
    for _ in range(100):
        job = get_job(job_id)
        if job and job["done"]:
            assert job["result"]["ok"] is False
            assert "cancel" in job["message"].lower()
            break
        time.sleep(0.05)
    else:
        raise AssertionError("cancelled job did not finish")
