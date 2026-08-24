"""Phase 7 — user-facing failure messages must name the actual condition.

The Deep Research defect was an error-message defect as much as a routing one:
a 404 from the wrong registry was reported as "server restart", which sent the
owner hunting a crash that never happened and prompted a real restart that
destroyed a live job. These tests keep every async poller honest.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

STATIC = Path(__file__).resolve().parent.parent / "jarvis" / "gui" / "static"

# Pollers that fetch a job-status endpoint and render an outcome to the user.
JOB_POLLERS = [
    "chat_done.js",
    "coding_jobs.js",
    "media_jobs.js",
    "audio_studio.js",
    "gallery_view.js",
    "meme_studio.js",
    "video_studio.js",
]


def _code(name: str) -> str:
    """Source with `//` comment lines removed, so prose about a bug is ignored."""
    return "\n".join(
        line for line in (STATIC / name).read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("//")
    )


@pytest.mark.parametrize("name", JOB_POLLERS)
def test_poller_never_claims_a_server_restart(name):
    """A poller sees 404s, not restarts. It cannot know a restart happened."""
    assert "server restart" not in _code(name).lower(), (
        f"{name} claims a server restart it has no evidence for"
    )


@pytest.mark.parametrize("name", JOB_POLLERS)
def test_poller_never_reports_a_missing_job_as_a_timeout(name):
    """'Timed out' must mean we waited too long, not that the job vanished."""
    code = _code(name)
    # A timeout string on the same line/branch as an ok/404 check is the smell.
    for match in re.finditer(r"if \(!data\.ok\)[^\n]*", code):
        assert "timed out" not in match.group(0).lower(), (
            f"{name} reports a missing job as a timeout: {match.group(0).strip()}"
        )


def test_audio_poller_distinguishes_lost_from_timed_out():
    code = _code("audio_studio.js")
    assert "no longer tracked by the server" in code, (
        "audio poller must say the job is gone rather than claiming a timeout"
    )
    assert "Job timed out" in code, "a genuine timeout must still be reported as one"
    assert "lost = true" in code, "the two exit reasons must be distinguished"


def test_recovery_message_names_the_job_and_offers_a_next_step(monkeypatch, tmp_path):
    """A job closed out by restart recovery must be actionable, not generic."""
    import json
    from collections import deque

    from jarvis import coding_jobs

    state = tmp_path / "s.json"
    state.write_text(
        json.dumps({"jobs": [{
            "id": "j1", "label": "Learn topic", "done": False, "pct": 5,
            "message": "Preparing…", "started": 1.0, "error": "", "cancelled": False,
        }], "stats": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(coding_jobs, "_state_file", state)
    monkeypatch.setattr(coding_jobs, "_jobs", {})
    monkeypatch.setattr(coding_jobs, "_history", deque(maxlen=32))
    monkeypatch.setattr(coding_jobs, "_stats", {"completed": 0, "failed": 0, "cancelled": 0})
    monkeypatch.setattr(coding_jobs, "_loaded", False)
    monkeypatch.setattr(coding_jobs, "_recovered", False)

    coding_jobs.recover_stale_jobs()
    msg = coding_jobs.get_job("j1")["result"]["message"]
    assert "Learn topic" in msg, "must name which job was lost"
    assert "again" in msg.lower(), "must tell the user what to do next"
    assert "gallery" not in msg.lower(), "must not misdirect research users to Gallery"


def test_media_recovery_message_is_honest_about_uncertainty():
    """Media recovery may mention Gallery — the asset genuinely might exist."""
    from pathlib import Path as P

    src = (P(__file__).resolve().parent.parent / "jarvis" / "media_jobs.py").read_text("utf-8")
    assert "could not be resumed" in src
    assert "check Gallery if media may already exist" in src, (
        "media recovery should stay conditional rather than promising an asset"
    )
