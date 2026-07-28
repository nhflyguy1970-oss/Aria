"""Coding job cancel edge cases."""

from __future__ import annotations

import time


def test_cancel_missing_job(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.coding_jobs._state_file", tmp_path / "coding_jobs_state.json")
    monkeypatch.setattr("jarvis.coding_jobs._jobs", {})
    monkeypatch.setattr("jarvis.coding_jobs._active_ids", set())
    monkeypatch.setattr("jarvis.coding_jobs._history", __import__("collections").deque(maxlen=32))
    monkeypatch.setattr("jarvis.coding_jobs._loaded", True)
    from jarvis.coding_jobs import cancel_job

    assert cancel_job("missing") is False


def test_cancel_already_done(tmp_path, monkeypatch):
    from jarvis import coding_jobs

    monkeypatch.setattr("jarvis.coding_jobs._state_file", tmp_path / "coding_jobs_state.json")
    monkeypatch.setattr("jarvis.coding_jobs._loaded", True)
    jid = "donejob01"
    with coding_jobs._lock:
        coding_jobs._jobs[jid] = {
            "id": jid,
            "label": "Done",
            "pct": 100,
            "message": "done",
            "done": True,
            "error": "",
            "started": time.time(),
            "cancelled": False,
            "kind": "agent",
        }
    assert coding_jobs.cancel_job(jid) is False
