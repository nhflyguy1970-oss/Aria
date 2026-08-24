"""Phase 8 — restart/recovery certification for the job registries.

A job that was running when the process died must not come back reporting
itself as still running. It either resumes (media, which carries a resume
payload) or it is closed out with an accurate interrupted message (coding and
background, which cannot resume). Silently reloading done=False leaves the UI
polling "Working…" against a job nothing will ever finish.
"""

from __future__ import annotations

import json
from collections import deque

import pytest


def _fresh_coding(monkeypatch, tmp_path, jobs: list[dict]):
    """Point coding_jobs at a state file containing `jobs`, as if after a restart."""
    from jarvis import coding_jobs

    state = tmp_path / "coding_jobs_state.json"
    state.write_text(
        json.dumps({"jobs": jobs, "stats": {"completed": 0, "failed": 0, "cancelled": 0}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(coding_jobs, "_state_file", state)
    monkeypatch.setattr(coding_jobs, "_jobs", {})
    monkeypatch.setattr(coding_jobs, "_history", deque(maxlen=32))
    monkeypatch.setattr(coding_jobs, "_active_ids", set())
    monkeypatch.setattr(coding_jobs, "_stats", {"completed": 0, "failed": 0, "cancelled": 0})
    monkeypatch.setattr(coding_jobs, "_loaded", False)
    monkeypatch.setattr(coding_jobs, "_recovered", False)
    return coding_jobs


RUNNING_JOB = {
    "id": "be700505aeed",
    "label": "Learn topic",
    "pct": 3,
    "message": "Preparing coding model…",
    "done": False,
    "error": "",
    "started": 1787326657.6,
    "cancelled": False,
}


def test_interrupted_background_job_is_not_reported_as_running(monkeypatch, tmp_path):
    """The production symptom: a job killed by a restart still said done=False."""
    coding_jobs = _fresh_coding(monkeypatch, tmp_path, [dict(RUNNING_JOB)])

    recovered = coding_jobs.recover_stale_jobs()
    assert recovered == 1

    job = coding_jobs.get_job("be700505aeed")
    assert job is not None, "the interrupted job must stay discoverable"
    assert job["done"] is True, "a job nothing will finish must not report as running"
    assert job["result"]["ok"] is False
    assert "interrupted" in job["result"]["message"].lower()
    assert "restart" in job["result"]["message"].lower()
    assert "Learn topic" in job["result"]["message"], "must name the job it closed out"


def test_recovery_message_does_not_send_research_users_to_gallery(monkeypatch, tmp_path):
    coding_jobs = _fresh_coding(monkeypatch, tmp_path, [dict(RUNNING_JOB)])
    coding_jobs.recover_stale_jobs()
    msg = coding_jobs.get_job("be700505aeed")["result"]["message"]
    assert "gallery" not in msg.lower(), "a research job's recovery must not mention Gallery"


def test_completed_jobs_survive_restart_untouched(monkeypatch, tmp_path):
    """Phase 8A — a job that finished before the restart keeps its result."""
    done_job = {
        "id": "af1e196cbaef",
        "label": "Learn topic",
        "pct": 100,
        "message": "Complete",
        "done": True,
        "error": "",
        "started": 1787326757.2,
        "cancelled": False,
        "result": {"ok": True, "type": "knowledge_learned", "message": "**Learned about:** x"},
    }
    coding_jobs = _fresh_coding(monkeypatch, tmp_path, [done_job])
    assert coding_jobs.recover_stale_jobs() == 0

    job = coding_jobs.get_job("af1e196cbaef")
    assert job["done"] is True
    assert job["result"]["ok"] is True
    assert job["result"]["message"] == "**Learned about:** x"


def test_recovery_is_idempotent(monkeypatch, tmp_path):
    coding_jobs = _fresh_coding(monkeypatch, tmp_path, [dict(RUNNING_JOB)])
    assert coding_jobs.recover_stale_jobs() == 1
    assert coding_jobs.recover_stale_jobs() == 0


def test_recovery_result_is_persisted(monkeypatch, tmp_path):
    """The closed-out state must survive the *next* restart too."""
    coding_jobs = _fresh_coding(monkeypatch, tmp_path, [dict(RUNNING_JOB)])
    coding_jobs.recover_stale_jobs()
    saved = json.loads(coding_jobs._state_file.read_text(encoding="utf-8"))
    entry = next(j for j in saved["jobs"] if j["id"] == "be700505aeed")
    assert entry["done"] is True
    assert entry["error"] == "Interrupted by server restart"


def test_server_startup_recovers_both_registries():
    """Regression: the lifespan hook recovered media jobs but not coding jobs."""
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "jarvis" / "gui" / "server.py"
    lifespan = src.read_text(encoding="utf-8")
    start = lifespan.index("async def lifespan(")
    block = lifespan[start : start + 1500]
    assert "recover_stale_jobs()" in block, "media job recovery missing from startup"
    assert "recover_stale_coding_jobs()" in block, "coding/background job recovery missing"


def test_media_jobs_still_recover_and_can_resume(monkeypatch, tmp_path):
    """Phase 8B — media recovery (the correct pre-existing model) is unchanged."""
    from jarvis import media_jobs

    state = tmp_path / "media_jobs_state.json"
    state.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "m-interrupted",
                        "kind": "generate_image",
                        "label": "Image",
                        "done": False,
                        "pct": 40,
                        "message": "Rendering…",
                        "started": 1.0,
                        "resume": {
                            "action": "generate_image",
                            "params": {"prompt": "x"},
                            "message": "make an image",
                        },
                    },
                    {
                        "id": "m-nonresumable",
                        "kind": "generate_image",
                        "label": "Image",
                        "done": False,
                        "pct": 10,
                        "message": "Rendering…",
                        "started": 1.0,
                    },
                ],
                "stats": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(media_jobs, "_state_file", state)
    monkeypatch.setattr(media_jobs, "_jobs", {})
    monkeypatch.setattr(media_jobs, "_history", deque(maxlen=32))
    monkeypatch.setattr(media_jobs, "_recovered", False)

    media_jobs.recover_stale_jobs()

    resumable = media_jobs.get_job("m-interrupted")
    assert resumable["_needs_resume"] is True, "resumable media work must be requeued"
    assert resumable["done"] is False

    dead = media_jobs.get_job("m-nonresumable")
    assert dead["done"] is True, "non-resumable media work must be closed out"
    assert dead["result"]["ok"] is False
    assert "interrupted" in dead["result"]["message"].lower()
