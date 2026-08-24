"""Chat job routing: background jobs must poll the coding registry, not the media one.

Learn topic / Deep Research is queued on the coding worker registry and is only
readable at /api/coding/job/<id>. It used to be routed to the media poller purely
because the response carried ``pending: true``, which 404s forever at
/api/media/job/<id> and made the UI claim a server restart that never happened.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
STATIC = REPO / "jarvis" / "gui" / "static"
HARNESS = Path(__file__).resolve().parent / "js" / "job_routing_harness.mjs"


def _read(name: str) -> str:
    return (STATIC / name).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Behavioural: run the real static JS under node and record fetched endpoints.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def harness_results() -> dict[str, dict]:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed — skipping frontend behavioural tests")
    proc = subprocess.run(
        [node, str(HARNESS), str(STATIC)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO,
    )
    assert proc.returncode == 0, f"harness crashed:\n{proc.stderr}"
    payload = json.loads(proc.stdout)
    return {r["name"]: r for r in payload["results"]}


def _assert_check(results: dict[str, dict], name: str) -> None:
    assert name in results, f"harness did not run check {name!r}"
    assert results[name]["ok"], f"{name} failed: {results[name]['detail']}"


@pytest.mark.parametrize(
    "check",
    [
        "resolve_background_job",
        "resolve_coding_job",
        "resolve_media_job",
        "resolve_untyped_pending_stays_media",
        "resolve_streamed_result_type",
        "resolve_coding_queue_hint",
        "resolve_no_job_id",
        "resolve_not_a_job",
    ],
)
def test_job_kind_resolution(harness_results, check):
    """Job *type* selects the poller — `pending` is only a legacy untyped fallback."""
    _assert_check(harness_results, check)


def test_learn_topic_never_polls_media_endpoint(harness_results):
    """Test 1 — a background_job response must not touch /api/media/job/<id>."""
    _assert_check(harness_results, "t1_no_media_endpoint")
    _assert_check(harness_results, "t1_uses_coding_endpoint")


def test_coding_job_behaviour_unchanged(harness_results):
    """Test 2 — coding jobs still poll /api/coding/job/<id>."""
    _assert_check(harness_results, "t2_coding_endpoint")
    _assert_check(harness_results, "t2_no_media_endpoint")


def test_media_job_behaviour_unchanged(harness_results):
    """Test 3 — typed and legacy untyped media jobs still poll /api/media/job/<id>."""
    _assert_check(harness_results, "t3_media_endpoint")
    _assert_check(harness_results, "t3_untyped_media_endpoint")


def test_background_completion_renders_result(harness_results):
    """Test 4 — a completed Learn topic job stops polling and renders its result."""
    for check in (
        "t4_result_rendered",
        "t4_polling_stopped",
        "t4_not_tracked_after_done",
        "t4_no_gallery_reference",
        "t4_no_restart_claim",
    ):
        _assert_check(harness_results, check)


def test_missing_job_does_not_claim_restart(harness_results):
    """Test 5 — a 404 is not evidence of a restart, for either poller."""
    for check in (
        "t5_media_no_restart_claim",
        "t5_background_no_restart_claim",
        "t5_background_no_gallery",
    ):
        _assert_check(harness_results, check)


# --------------------------------------------------------------------------
# Source-level guards (run even without node).
# --------------------------------------------------------------------------


JOB_POLLER_FILES = ("chat_done.js", "coding_jobs.js", "media_jobs.js")


def _code_without_line_comments(name: str) -> str:
    """Source with `//` comment bodies dropped, so prose about the bug is ignored."""
    lines = []
    for line in _read(name).splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        lines.append(line)
    return "\n".join(lines)


@pytest.mark.parametrize("name", JOB_POLLER_FILES)
def test_job_pollers_never_claim_a_server_restart(name):
    """A 404 is not evidence of a restart — no poller may tell the user one happened.

    Only the job-polling files are in scope: the deliberate restart control in
    movie_tiers.js and the unrelated chat_branches.js hint are not job recovery.
    """
    code = _code_without_line_comments(name).lower()
    assert "server restart" not in code, f"{name} still claims a server restart"


def test_old_false_recovery_message_is_gone():
    media = _read("media_jobs.js")
    assert "Lost track of this job after a server restart" not in media
    assert "Check <strong>Gallery</strong> for your image" not in media


def test_background_jobs_are_routed_to_the_coding_poller():
    chat_done = _read("chat_done.js")
    assert '"background_job"' in chat_done
    assert "jarvisPollBackgroundJob" in chat_done
    # The media poller must no longer be reachable via a bare `pending` check.
    assert 'data.result_type === "media_job" || data.pending' not in chat_done


def test_background_poller_uses_the_coding_endpoint():
    coding = _read("coding_jobs.js")
    assert "window.jarvisPollBackgroundJob" in coding
    assert "/api/coding/job/" in coding
    assert "/api/media/job/" not in coding


def test_background_actions_stay_on_the_coding_registry():
    """The frontend contract depends on background jobs living in coding_jobs."""
    from jarvis.background_jobs import ACTION_LABELS, BACKGROUND_ACTIONS

    assert "learn_about" in BACKGROUND_ACTIONS
    assert ACTION_LABELS["learn_about"] == "Learn topic"
    assert "from jarvis.coding_jobs import submit" in (
        REPO / "jarvis" / "background_jobs.py"
    ).read_text(encoding="utf-8")


def test_enqueue_background_emits_background_job_type():
    """_enqueue_background must keep tagging responses so routing can see them."""
    assistant_src = (REPO / "jarvis" / "assistant.py").read_text(encoding="utf-8")
    start = assistant_src.index("def _enqueue_background")
    block = assistant_src[start : start + 1200]
    assert 'type="background_job"' in block
    assert "pending=True" in block
