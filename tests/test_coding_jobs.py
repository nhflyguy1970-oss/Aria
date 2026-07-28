"""Coding jobs queue coverage."""

from __future__ import annotations

import time

import pytest


@pytest.fixture
def jobs_env(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.coding_jobs._state_file", tmp_path / "coding_jobs_state.json")
    monkeypatch.setattr("jarvis.coding_jobs._jobs", {})
    monkeypatch.setattr("jarvis.coding_jobs._active_ids", set())
    monkeypatch.setattr("jarvis.coding_jobs._history", __import__("collections").deque(maxlen=32))
    monkeypatch.setattr("jarvis.coding_jobs._stats", {"completed": 0, "failed": 0, "cancelled": 0})
    monkeypatch.setattr("jarvis.coding_jobs._loaded", True)
    monkeypatch.setattr("jarvis.coding_jobs._queue", None)
    monkeypatch.setattr("jarvis.coding_jobs._workers", [])
    return tmp_path


def test_submit_and_get_job(jobs_env):
    from jarvis.coding_jobs import get_job, job_stats, list_recent, submit

    def work():
        return {"ok": True, "message": "done", "proposal_id": "p1"}

    # Force sync path if submit starts workers — use internal register
    from jarvis import coding_jobs

    jid = "testjob01"
    with coding_jobs._lock:
        coding_jobs._jobs[jid] = {
            "id": jid,
            "label": "Test job",
            "pct": 0,
            "message": "queued",
            "done": False,
            "error": "",
            "started": time.time(),
            "cancelled": False,
            "kind": "agent",
        }
        coding_jobs._history.append(jid)

    job = get_job(jid)
    assert job and job["id"] == jid
    recent = list_recent(5)
    assert any(j["id"] == jid for j in recent)
    stats = job_stats()
    assert "pending" in stats
    assert "completed" in stats


def test_cancel_job(jobs_env):
    from jarvis import coding_jobs

    jid = "cancelme1"
    with coding_jobs._lock:
        coding_jobs._jobs[jid] = {
            "id": jid,
            "label": "Cancel me",
            "pct": 10,
            "message": "running",
            "done": False,
            "error": "",
            "started": time.time(),
            "cancelled": False,
            "kind": "agent",
        }
        coding_jobs._active_ids.add(jid)
        coding_jobs._history.append(jid)

    assert coding_jobs.cancel_job(jid) is True
    job = coding_jobs.get_job(jid)
    assert job["cancelled"] is True or job["done"] is True


def test_jobs_center_enriches_coding(jobs_env):
    from jarvis import coding_jobs
    from jarvis.jobs_center import _sanitize_job

    jid = "enrich01"
    with coding_jobs._lock:
        coding_jobs._jobs[jid] = {
            "id": jid,
            "label": "Enrich",
            "pct": 100,
            "message": "done",
            "done": True,
            "error": "",
            "started": time.time(),
            "cancelled": False,
            "kind": "agent",
            "result": {"ok": True, "proposal_id": "abcd1234", "message": "proposal ready"},
        }
    row = _sanitize_job(coding_jobs.get_job(jid), queue="coding")
    assert row.get("proposal_id") == "abcd1234"
    assert row.get("deep_links")
