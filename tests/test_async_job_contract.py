"""Phase 6 — frontend/backend contract for every queued (asynchronous) action.

For each action the handler registry marks as queued, the chat response's job
type must classify to the poller whose endpoint reads the registry the job was
actually submitted to. The Deep Research defect was exactly this contract
breaking silently: a background_job landed in the coding registry but the
frontend sent its id to the media endpoint.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
STATIC = REPO / "jarvis" / "gui" / "static"
HARNESS = Path(__file__).resolve().parent / "js" / "job_contract_harness.mjs"

# queue -> (registry module that owns the job, endpoint the frontend must poll)
QUEUE_REGISTRY = {
    "media": ("jarvis.media_jobs", "/api/media/job/"),
    "coding": ("jarvis.coding_jobs", "/api/coding/job/"),
    "background": ("jarvis.coding_jobs", "/api/coding/job/"),
    "fix_tests": ("jarvis.coding_jobs", "/api/coding/job/"),
}


_DISCOVERY = """
import json
from jarvis.handlers import ensure_handlers_loaded
from jarvis.handlers.registry import all_actions, get_queue

ensure_handlers_loaded()
names = sorted(a["action"] if isinstance(a, dict) else str(a) for a in all_actions())
out = []
for name in names:
    try:
        queue = get_queue(name)
    except Exception:
        queue = None
    if queue:
        out.append([name, queue])
print(json.dumps(out))
"""


def _queued_actions() -> list[tuple[str, str]]:
    """Discover queued actions in a clean interpreter.

    Other tests register probe actions into the process-global handler registry,
    so discovering in-process makes this order-dependent. A subprocess sees only
    what ARIA itself registers.
    """
    proc = subprocess.run(
        [sys.executable, "-c", _DISCOVERY],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=REPO,
    )
    assert proc.returncode == 0, f"action discovery failed:\n{proc.stderr}"
    return [(name, queue) for name, queue in json.loads(proc.stdout.strip().splitlines()[-1])]


class _StubAssistant:
    """Captures the enqueue call without running any worker."""

    def __init__(self):
        self.submitted: list[str] = []

    # _enqueue_* helpers are taken from the real assistant class below.
    def _engineering_resolve_path(self, path):
        return path or "x.py"


def _build_responses(monkeypatch) -> list[dict]:
    """Drive the real dispatch cascade with the job submitters stubbed out."""
    from jarvis.assistant import JarvisAssistant
    from jarvis.conversation_pipeline import dispatch_action

    fake_id = "deadbeef0001"
    monkeypatch.setattr("jarvis.media_jobs.submit_assistant_action", lambda *a, **k: fake_id)
    monkeypatch.setattr("jarvis.background_jobs.submit_action", lambda *a, **k: fake_id)
    monkeypatch.setattr("jarvis.coding_jobs.submit_coding_agent", lambda *a, **k: fake_id)
    monkeypatch.setattr("jarvis.coding_jobs.submit_fix_tests", lambda *a, **k: fake_id)
    monkeypatch.setattr(
        "jarvis.resource_router.check_media_enqueue",
        lambda action: {"blocked": False, "queue_position": 1},
    )

    assistant = JarvisAssistant.__new__(JarvisAssistant)
    assistant._engineering_resolve_path = lambda p: p or "x.py"

    out = []
    for action, queue in _queued_actions():
        params = {"prompt": "t", "topic": "t", "task": "t", "path": "x.py"}
        result = dispatch_action(assistant, action, params, "do the thing")
        out.append({"action": action, "queue": queue, "response": result})
    return out


@pytest.fixture(scope="module")
def contract(request) -> list[dict]:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    mp = pytest.MonkeyPatch()
    request.addfinalizer(mp.undo)
    responses = _build_responses(mp)
    proc = subprocess.run(
        [node, str(HARNESS), str(STATIC)],
        input=json.dumps(responses),
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO,
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    classified = {c["action"]: c for c in json.loads(proc.stdout)}
    for entry in responses:
        entry["frontend"] = classified[entry["action"]]
    return responses


def test_every_queued_action_is_discovered(contract):
    """Guard the inventory itself — a new queued action must not slip in untested."""
    actions = {e["action"] for e in contract}
    expected = {
        "aria_self_fix", "coding_agent", "coding_fix_tests", "document_summarize",
        "edit_image", "generate_image", "generate_meme", "generate_video",
        "inpaint_image", "knowledge_research_run", "learn_about", "self_upgrade_run",
        "storyboard_video", "upscale_image",
    }
    assert actions == expected, (
        "queued-action inventory changed; extend the async certification matrix "
        f"(added={actions - expected}, removed={expected - actions})"
    )


def test_every_queued_action_returns_a_job_handle(contract):
    for e in contract:
        r = e["response"]
        assert r.get("job_id"), f"{e['action']} returned no job_id: {r}"
        assert r.get("pending") is True, f"{e['action']} is not marked pending: {r}"
        assert r.get("type"), f"{e['action']} returned no job type: {r}"


def test_job_type_is_explicit_never_inferred_from_pending(contract):
    """Classification must come from `type`, so it survives losing `pending`."""
    for e in contract:
        assert e["response"]["type"] in {"media_job", "background_job", "coding_job"}, (
            f"{e['action']} has unroutable type {e['response']['type']!r}"
        )


def test_frontend_routes_each_action_to_its_own_registry(contract):
    """The core contract: frontend endpoint == endpoint of the owning registry."""
    failures = []
    for e in contract:
        _module, expected_endpoint = QUEUE_REGISTRY[e["queue"]]
        actual = e["frontend"]["endpoint"]
        if actual != expected_endpoint:
            failures.append(
                f"{e['action']} (queue={e['queue']}, type={e['response']['type']}): "
                f"frontend polls {actual} but the job lives at {expected_endpoint}"
            )
    assert not failures, "registry/endpoint mismatch:\n  " + "\n  ".join(failures)


def test_every_classified_kind_has_a_real_poller(contract):
    for e in contract:
        assert e["frontend"]["poller_defined"], (
            f"{e['action']} classified as {e['frontend']['kind']} but no such poller exists"
        )


def test_no_queued_action_falls_through_to_the_media_poller(contract):
    """The canonical Deep Research defect, generalised to every queued action."""
    for e in contract:
        if e["queue"] in ("coding", "background", "fix_tests"):
            assert e["frontend"]["endpoint"] != "/api/media/job/", (
                f"{e['action']} would send a coding-registry id to the media endpoint"
            )
        if e["queue"] == "media":
            assert e["frontend"]["endpoint"] != "/api/coding/job/", (
                f"{e['action']} would send a media-registry id to the coding endpoint"
            )


def test_job_framework_resolves_every_queue(contract):
    """job_framework must know every queue the registry can emit."""
    from jarvis import job_framework

    unknown = []
    for e in contract:
        try:
            job_framework.get_job(e["queue"], "nonexistent-id")
        except ValueError:
            unknown.append(f"{e['action']}: job_framework cannot resolve queue {e['queue']!r}")
    assert not unknown, "\n  ".join(unknown)
