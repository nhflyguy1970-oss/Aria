"""Phase 1 foundation repairs — regressions for the defects the October 2026
assessment reproduced:

1. safe mode / autonomy policy bypassed by direct mission handlers, worker
   ticks, workflow slices, delegated agents and tool entry points, and
   approvals manufactured inside legacy wrappers;
2. context pruning permanently discarding the persisted conversation;
3. the tool-result memory sink calling the memory API with the wrong
   signature and swallowing the error;
4. research marking a claim verified from unrelated, unavailable or
   same-publisher evidence.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from jarvis import missions
from jarvis.integration import policy
from jarvis.missions import store as mission_store
from jarvis.missions import worker

SAFE = {"JARVIS_SAFE_MODE": "1"}


@pytest.fixture(autouse=True)
def _stop_worker():
    yield
    worker.stop(timeout=5)


def _probe_action(calls: list):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import register_action

    ensure_handlers_loaded()

    @register_action("phase1_probe_noop", module="general", description="test probe")
    def _noop(assistant, params, message):
        calls.append(params)
        return {"ok": True, "message": "probe ran"}

    return "phase1_probe_noop"


def _call(action: str, params: dict):
    from jarvis.handlers.registry import call_action

    return call_action(SimpleNamespace(), action, params, action)


# ============================================================ 1. execution policy


def test_safe_mode_blocks_direct_mission_run_without_touching_state(data_dir, monkeypatch):
    calls: list = []
    action = _probe_action(calls)
    mid = missions.create_mission("probe", steps=[{"name": "s", "action": action}])
    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")

    out = _call("mission_run", {"mission_id": mid})

    assert calls == [], "a step ran while safe mode was on"
    assert out["ok"] is False and out.get("error_kind") == "policy_denied"
    assert missions.status(mid)["state"] == mission_store.PENDING
    assert any(e["kind"] == "policy:refused" for e in mission_store.history(mid))

    # Lifting safe mode lets the very same mission run: nothing was lost.
    monkeypatch.delenv("JARVIS_SAFE_MODE")
    _call("mission_run", {"mission_id": mid})
    assert len(calls) == 1
    assert missions.status(mid)["state"] == mission_store.COMPLETED


def test_safe_mode_blocks_worker_tick_and_leaves_queue_intact(data_dir, monkeypatch):
    calls: list = []
    action = _probe_action(calls)
    mid = missions.create_mission("probe", steps=[{"name": "s", "action": action}])
    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    worker._stop.clear()

    assert worker.tick(assistant=SimpleNamespace()) is None
    assert calls == []
    assert missions.status(mid)["state"] == mission_store.PENDING
    assert "safe mode" in (worker.status()["last_error"] or "")

    monkeypatch.delenv("JARVIS_SAFE_MODE")
    assert worker.tick(assistant=SimpleNamespace()) == mid
    assert len(calls) == 1


def test_mission_engine_refuses_even_without_a_handler(data_dir, monkeypatch):
    ran: list = []
    mid = missions.create_mission("direct", steps=[{"name": "s", "action": "x"}])
    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    with pytest.raises(policy.PolicyError):
        missions.run(mid, lambda step, ctx: ran.append(step) or {"ok": True})
    assert ran == []


def test_autonomy_level_without_missions_is_enforced(data_dir, monkeypatch):
    mid = missions.create_mission("assisted", steps=[{"name": "s", "action": "x"}])
    monkeypatch.setenv("JARVIS_AUTONOMY", "assisted")  # assisted does not include missions
    with pytest.raises(policy.PolicyError, match="does not permit mission"):
        missions.run(mid, lambda step, ctx: {"ok": True})


def test_policy_refusal_mid_mission_pauses_with_checkpoint(data_dir):
    """A step that hits the policy pauses the mission; it is not failed."""

    def runner(step, ctx):
        if step["name"] == "second":
            raise policy.PolicyError("safe mode is on: workflow is not started")
        return {"ok": True, "first": 1}

    mid = missions.create_mission(
        "pausable", steps=[{"name": "first", "action": "a"}, {"name": "second", "action": "b"}]
    )
    with pytest.raises(policy.PolicyError):
        missions.run(mid, runner)
    snap = missions.status(mid)
    assert snap["state"] == mission_store.PAUSED
    assert snap["error_kind"] != mission_store.TERMINAL
    assert snap["checkpoint"]["step_index"] == 1, "completed step was not checkpointed"


def test_safe_mode_blocks_workflow_slices(data_dir, monkeypatch):
    from jarvis import autonomous_workflows as wf

    workflow = wf.create_workflow(
        {"name": "wf", "steps": [{"step_id": "one", "action": "mission_list", "params": {}}]},
        create_mission=False,
    )
    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")

    out = _call("workflow_start", {"workflow_id": workflow["id"]})

    assert out["ok"] is False and out.get("error_kind") == "policy_denied"
    assert wf.status(workflow["id"])["succeeded"] == 0
    assert any(e["kind"] == "policy:refused" for e in wf.events(workflow["id"]))


def test_safe_mode_blocks_delegated_agent_actions(data_dir, monkeypatch):
    from jarvis import specialized_agents as agents

    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    with patch("jarvis.specialized_agents.invoke.call_action") as call:
        out = agents.invoke("research_specialist", "look", action="research_status")
    call.assert_not_called()
    assert out["ok"] is False and out["error_kind"] == "permission_denied"
    assert out.get("policy_denied") is True


def test_safe_mode_blocks_managed_tools(data_dir, monkeypatch):
    from jarvis.tools import executor

    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    with patch("jarvis.tools.runner.run_sync") as run_sync:
        out = executor.execute_tool("claude_code", {"task": "edit files"})
    run_sync.assert_not_called()
    assert out["ok"] is False and out["error_kind"] == "policy_denied"


def test_safe_mode_blocks_skills(data_dir, monkeypatch):
    from jarvis import skills
    from jarvis.skills import registry
    from jarvis.skills.definitions import ANALYSIS, READ, SkillDefinition

    ran: list = []
    registry.reset()
    try:
        registry.register(
            SkillDefinition(
                skill_id="phase1_probe_skill",
                name="Probe",
                description="probe",
                version="1.0.0",
                category=ANALYSIS,
                impact=READ,
            ),
            lambda ctx, params: ran.append(params) or {"ok": True},
        )
        monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
        out = skills.execute("phase1_probe_skill", {})
    finally:
        registry.reset()
    assert ran == []
    assert out["status"] == "denied" and out["error_kind"] == "policy_denied"


def test_safe_mode_blocks_mcp_execution(monkeypatch):
    from jarvis.mcp import engine as mcp_engine

    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    with pytest.raises(mcp_engine.McpDenied, match="safe mode"):
        mcp_engine.check_authority(SimpleNamespace(provider_id="probe"), "tool")


def test_safe_mode_blocks_specialist_teams(data_dir, monkeypatch):
    from jarvis.specialists.engine import run_team

    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    with patch("jarvis.specialists.execute.run_specialist") as run:
        out = run_team(None, "plan something", confirm=True)
    run.assert_not_called()
    assert out["ok"] is False and out["error_kind"] == "policy_denied"


def test_legacy_trigger_no_longer_exempts_confirmation(data_dir):
    from jarvis.specialists.engine import run_team

    with patch("jarvis.specialists.execute.run_specialist") as run:
        out = run_team(None, "plan something", trigger="compat-legacy")
    run.assert_not_called()
    assert out["status"] == "permission_required"


def test_intelligence_api_defaults_to_unapproved(data_dir):
    import inspect

    from jarvis.intelligence import routes

    source = inspect.getsource(routes)
    assert 'body.get("approve_writes", True)' not in source
    assert 'body.get("confirm", True)' not in source


def test_agent_jobs_carry_only_the_write_approval_granted(data_dir):
    from jarvis.jobs import checkpointed

    seen: list[bool] = []

    def fake_run_team(*a, **kw):
        seen.append(kw["approve_writes"])
        return {"ok": True, "status": "succeeded", "steps": []}

    with patch("jarvis.specialists.engine.run_team", side_effect=fake_run_team):
        job = checkpointed.start_agent_job(None, "research a thing")
        checkpointed._threads.get(job.id) and checkpointed._threads[job.id].join(5)
        granted = checkpointed.start_agent_job(None, "write a thing", approve_writes=True)
        checkpointed._threads.get(granted.id) and checkpointed._threads[granted.id].join(5)
    assert seen == [False, True]
    assert checkpointed.load_job(job.id).checkpoint["approve_writes"] is False
    assert checkpointed.load_job(granted.id).checkpoint["approve_writes"] is True

    # A job recorded before approvals were stored resumes with none.
    legacy = checkpointed.load_job(job.id)
    legacy.status = "running"
    legacy.checkpoint.pop("approve_writes")
    checkpointed.save_job(legacy)
    seen.clear()
    with patch("jarvis.specialists.engine.run_team", side_effect=fake_run_team):
        checkpointed.resume_incomplete_jobs(None)
        thread = checkpointed._threads.get(legacy.id)
        thread and thread.join(5)
    assert seen == [False]


def test_default_policy_still_runs_authorized_work(data_dir):
    """Production defaults (bounded, no safe mode) keep working."""
    calls: list = []
    action = _probe_action(calls)
    mid = missions.create_mission("ok", steps=[{"name": "s", "action": action}])
    assert policy.refusal("mission") == ""
    _call("mission_run", {"mission_id": mid})
    assert calls and missions.status(mid)["state"] == mission_store.COMPLETED


# ============================================================ 2. conversation history


def _manager():
    from jarvis.branches import BranchManager

    return BranchManager()


def test_pruning_no_longer_discards_source_history_and_survives_restart(data_dir):
    from jarvis.branches import BRANCHES_FILE
    from jarvis.config import MAX_MESSAGES

    bm = _manager()
    conv = bm.get_conversation("main", "Synthetic system")
    conv.add_user("FIRST_TURN_SENTINEL")
    for i in range(30):
        conv.add_user(f"User {i}")
        conv.add_assistant(f"Assistant {i}")
    bm.persist()

    # Model context is still bounded exactly as before.
    persisted = json.loads(BRANCHES_FILE.read_text())["branches"]["main"]["messages"]
    assert len(persisted) <= MAX_MESSAGES
    assert not any("FIRST_TURN_SENTINEL" in m["content"] for m in persisted)

    # ...but the complete source history is kept, in order, and survives a restart.
    restarted = _manager()
    turns = restarted.archive_for("main").turns()
    contents = [t["content"] for t in turns]
    assert contents[0] == "FIRST_TURN_SENTINEL"
    assert len(contents) == 61
    assert contents[-1] == "Assistant 29"

    restarted.get_conversation("main", "Synthetic system").add_user("after restart")
    assert _manager().archive_for("main").turns()[-1]["content"] == "after restart"
    assert len(_manager().archive_for("main").turns()) == 62


def test_existing_branch_is_seeded_once_without_inventing_history(data_dir):
    from jarvis.branches import BRANCHES_FILE

    BRANCHES_FILE.write_text(
        json.dumps(
            {
                "active": "main",
                "branches": {
                    "main": {
                        "name": "Main",
                        "messages": [
                            {"role": "system", "content": "sys"},
                            {"role": "user", "content": "older surviving turn"},
                            {"role": "assistant", "content": "older reply"},
                        ],
                    }
                },
            }
        )
    )
    bm = _manager()
    bm.get_conversation("main", "sys").add_user("new turn")
    _manager().get_conversation("main", "sys")  # reopening must not re-seed

    events = bm.archive_for("main").read()
    seeds = [e for e in events if e["kind"] == "seed"]
    assert [s["content"] for s in seeds] == ["older surviving turn", "older reply"]
    assert all(s["origin"] == "chat_branches.json" for s in seeds)
    assert [e["content"] for e in events if e["kind"] == "message"] == ["new turn"]
    assert not any(e.get("role") == "system" for e in events)


def test_retraction_truncation_clear_and_delete_keep_the_record(data_dir):
    bm = _manager()
    conv = bm.get_conversation("main", "sys")
    conv.add_user("withdrawn question")
    assert conv.pop_last_user()
    conv.add_assistant("A long spoken answer " * 50)
    conv.truncate_last_assistant()
    bm.clear_messages("main", "sys")

    events = bm.archive_for("main").read()
    kinds = [e["kind"] for e in events]
    assert "retracted" in kinds and "truncated" in kinds and "cleared" in kinds
    full = [e for e in events if e["kind"] == "message" and e["role"] == "assistant"][0]
    assert full["content"].startswith("A long spoken answer") and len(full["content"]) > 400

    fork = bm.create_branch("side")
    bm.get_conversation(fork, "sys").add_user("only on the fork")
    # Delete a branch that this manager never loaded: seeded first, then marked.
    fresh = _manager()
    assert fresh.delete_branch(fork)
    archived = fresh.archive_for(fork).read()
    assert archived[-1]["kind"] == "deleted"
    assert any(e.get("content") == "only on the fork" for e in archived)


def test_archive_write_failure_is_visible_not_silent(data_dir, caplog):
    from jarvis import conversation_archive
    from jarvis.conversation import Conversation

    archive = conversation_archive.ConversationArchive("main", data_dir / "archive-ro")
    before = conversation_archive.status()["errors"]
    conv = Conversation("sys", archive=archive)
    with patch("builtins.open", side_effect=PermissionError("read-only")):
        with caplog.at_level(logging.ERROR, logger="jarvis.conversation_archive"):
            conv.add_user("hello")
    assert conv.messages[-1]["content"] == "hello", "chat must continue"
    assert conversation_archive.status()["errors"] == before + 1
    assert "archive write failed" in caplog.text


def test_branch_behaviour_is_unchanged(data_dir):
    bm = _manager()
    conv = bm.get_conversation("main", "sys")
    conv.add_user("u1")
    conv.add_assistant("a1")
    bm.persist()
    bid = bm.fork_at_display_index("fork", 0)
    assert [b["id"] for b in bm.list_branches()].count(bid) == 1
    forked = bm.get_conversation(bid, "sys")
    assert [m["content"] for m in forked.messages if m["role"] != "system"] == ["u1"]
    assert bm.archive_for(bid).read()[0]["origin"] == "fork:main"


# ============================================================ 3. tool-result memory
# Phase 2 moved outcomes from ACM (where they were stamped as user teaching) to
# the continuity store as tool-actor records; the Phase 1 guarantees still hold.


def test_tool_outcome_is_recorded_as_a_tool_reported_outcome(data_dir):
    from jarvis.continuity import store
    from jarvis.tools.memory_sink import record_tool_outcome

    receipt = record_tool_outcome("claude_code", "fix the bug", ok=True, summary="patched")
    assert receipt["recorded"] is True and receipt["store"] == "continuity"
    record = store.get_record(receipt["record_id"])
    assert record["actor"] == store.TOOL and record["kind"] == store.OUTCOME
    assert "fix the bug" in record["text"] and "patched" in record["text"]
    assert record["verified"] is False  # reported by the tool, not verified


def test_tool_outcome_failure_is_reported_not_swallowed(data_dir, caplog):
    from jarvis.tools import memory_sink

    before = memory_sink.status()["failed"]
    with (
        patch("jarvis.continuity.record_tool_outcome", side_effect=RuntimeError("disk full")),
        caplog.at_level(logging.WARNING, logger="jarvis.tools.memory_sink"),
    ):
        receipt = memory_sink.record_tool_outcome("claude_code", "task", ok=False)
    assert receipt["recorded"] is False and "disk full" in receipt["error"]
    assert memory_sink.status()["failed"] == before + 1
    assert "not recorded" in caplog.text


def test_execute_tool_attaches_memory_receipt(data_dir):
    from jarvis.tools import executor

    tool = SimpleNamespace(id="probe_tool", label="Probe", run=None, available=lambda: True)
    with (
        patch.object(executor, "get_tool", return_value=tool),
        patch("jarvis.tools.runner.build_command", return_value=(["true"], "")),
        patch("jarvis.tools.runner.run_sync", return_value={"ok": True, "stdout": "done"}),
    ):
        out = executor.execute_tool("probe_tool", {"task": "do it"})
    assert out["ok"] is True
    assert out["memory"]["recorded"] is True and out["memory"]["record_id"]


def test_background_run_keeps_its_memory_receipt_on_disk(data_dir):
    from jarvis.tools import runner

    run = runner.ToolRun(id="r1", tool_id="claude_code", task="t", status="failed", error="boom")
    with patch("jarvis.continuity.record_tool_outcome", side_effect=RuntimeError("disk full")):
        run.memory = runner._remember_run_outcome(run)
    runner.save_run(run)
    reloaded = runner.load_run("r1")
    assert reloaded.memory["recorded"] is False and "disk full" in reloaded.memory["error"]


def test_tool_outcome_survives_restart_and_never_enters_acm(data_dir, tmp_path, monkeypatch):
    from aria_core import acm_bridge, memory_manager

    from jarvis.continuity import store
    from jarvis.tools.memory_sink import record_tool_outcome

    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm.db"))
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    try:
        receipt = record_tool_outcome(
            "claude_code", "refactor the importer", ok=True, summary="tests passing"
        )
        store.reset_for_tests()  # restart: fresh handles on the same database
        acm_bridge.reset_for_tests()
        assert "refactor the importer" in store.get_record(receipt["record_id"])["text"]
        assert not any(
            "refactor the importer" in (e.summary or "")
            for e in acm_bridge.get_engine().store.experiences.values()
        )
    finally:
        memory_manager.reset_for_tests()
        acm_bridge.reset_for_tests()


# ============================================================ 4. research verification


def _research(objective: str, hits: list[dict], pages: dict[str, str]):
    from jarvis.research import engine, store

    rid = engine.create_research(objective)["research_id"]

    def fetch(url):
        if url not in pages:
            raise RuntimeError("not retrievable")
        return pages[url]

    for phase in engine.PHASES:
        engine.run_phase(rid, phase, search_fn=lambda q, n: hits[:n], fetch_fn=fetch)
    return store.claims(rid)[0], store.get_job(rid), engine._evidence_claims(rid)[0]


def test_unrelated_unavailable_snippets_cannot_verify(data_dir):
    """The assessment's reproduction: cheese moon, garden-soil snippets."""
    from jarvis.research import engine, store

    rid = store.create_job("The moon is made of cheese")
    for i in range(2):
        sid = store.add_source(rid, f"https://example.org/unrelated-{i}", snippet="Garden soil holds water.")
        store.mark_retrieval_failed(sid, "synthetic unavailable")
        store.add_evidence(rid, sid, "Garden soil holds water.")
    analysed = engine.phase_analyze(rid)
    engine.phase_synthesize(rid)

    assert analysed["verified"] is False and analysed["supports"] == 0
    assert analysed["unrelated"] == 2
    synthesis = store.get_job(rid)["synthesis"]
    assert "verified: yes" not in synthesis and "verified: no" in synthesis
    assert "evidence layer: insufficient_evidence" in synthesis
    assert any("did not address the claim" in u["text"] for u in store.unresolved(rid))


def test_relevant_snippets_from_unavailable_pages_cannot_verify(data_dir):
    hits = [
        {"url": "https://nasa.gov/a", "title": "A", "snippet": "Measurements say the sky is blue."},
        {"url": "https://nih.gov/b", "title": "B", "snippet": "The sky is blue at noon."},
    ]
    claim, job, shared = _research("the sky is blue", hits, pages={})
    assert claim["verified"] == 0
    assert claim["confidence"] != "high"
    assert shared["verification"]["result"] == "supported"
    assert "verified: no" in job["synthesis"]


def test_one_publisher_on_several_subdomains_cannot_verify(data_dir):
    hits = [
        {"url": "https://news.example.org/a", "title": "A", "snippet": ""},
        {"url": "https://blog.example.org/b", "title": "B", "snippet": ""},
    ]
    pages = {h["url"]: "Observers agree the sky is blue." for h in hits}
    claim, job, shared = _research("the sky is blue", hits, pages)
    assert claim["verified"] == 0
    assert shared["verification"]["result"] != "verified"
    assert shared["verification"]["independence"] == "not_independent"


def test_inspected_independent_relevant_sources_still_verify(data_dir):
    hits = [
        {"url": "https://nasa.gov/a", "title": "A", "snippet": ""},
        {"url": "https://nih.gov/b", "title": "B", "snippet": ""},
    ]
    pages = {h["url"]: "Measurements confirm the sky is blue." for h in hits}
    claim, job, shared = _research("the sky is blue", hits, pages)
    assert claim["verified"] == 1
    assert shared["verification"]["result"] == "verified"
    assert "verified: yes" in job["synthesis"]
    assert "evidence layer: verified" in job["synthesis"]


def test_evidence_layer_snippets_support_but_never_verify(data_dir):
    from jarvis import evidence as ev

    claim_id = ev.add_claim("water boils at 100C", context_id="ctx", origin="test")
    for url in ("https://nasa.gov/x", "https://nih.gov/y"):
        sid = ev.add_source(url, context_id="ctx")
        ev.mark_source_unavailable(sid, "blocked")
        eid = ev.add_evidence(
            sid, "water boils at 100C", context_id="ctx", claim_id=claim_id, evidence_type=ev.SNIPPET
        )
        ev.link(claim_id, eid, ev.SUPPORTS)
    for method in ("independent_sources", "direct_inspection"):
        result = ev.verify(claim_id, method=method, record=False)
        assert result["result"] != "verified", method


def test_publisher_of_groups_subdomains():
    from jarvis.evidence.store import publisher_of

    assert publisher_of("news.example.org") == publisher_of("blog.example.org") == "example.org"
    assert publisher_of("https://www.bbc.co.uk/news") == "bbc.co.uk"
    assert publisher_of("nasa.gov") != publisher_of("nih.gov")
