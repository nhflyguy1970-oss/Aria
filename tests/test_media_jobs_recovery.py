"""Media job persistence across server restarts."""

import json

from jarvis.media_jobs import _jobs, _history, _state_file, recover_stale_jobs


def test_recover_stale_jobs_marks_interrupted(monkeypatch, tmp_path):
    state = {
        "jobs": [
            {
                "id": "abc123",
                "kind": "edit_image",
                "label": "Image edit",
                "done": False,
                "message": "Running…",
                "pct": 5,
                "started": 1.0,
            }
        ],
        "stats": {"completed": 0, "failed": 0, "cancelled": 0, "timed_out": 0},
    }
    path = tmp_path / "media_jobs_state.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr("jarvis.media_jobs._state_file", path)
    monkeypatch.setattr("jarvis.media_jobs._recovered", False)
    _jobs.clear()
    _history.clear()

    count = recover_stale_jobs()
    assert count == 1
    job = _jobs["abc123"]
    assert job["done"] is True
    assert "restart" in job["error"].lower()
    assert job["result"]["ok"] is False
