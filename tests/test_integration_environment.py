"""ARIA environment integration — lifecycle, policy, status, provenance, recovery."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from jarvis import autonomous_workflows as wf
from jarvis import integration as env
from jarvis import specialized_agents as agents
from jarvis.integration import context as env_context
from jarvis.integration import lifecycle, policy, recovery
from jarvis.specialized_agents import registry as agent_registry

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    agent_registry.reset()
    monkeypatch.delenv(policy.SAFE_MODE_ENV, raising=False)
    monkeypatch.delenv(policy.AUTONOMY_ENV, raising=False)
    yield
    agent_registry.reset()


def _call(action: str, params: dict, assistant=None):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return call_action(assistant, action, params, action)


def simple_workflow(**kw) -> dict:
    base = {
        "name": "env test",
        "steps": [{"step_id": "one", "action": "mission_list", "params": {"limit": 1}}],
    }
    base.update(kw)
    return base


def _two_step() -> dict:
    """A workflow that reaches a live state after one step, leaving one to interrupt."""
    return simple_workflow(
        steps=[
            {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
            {"step_id": "b", "action": "mission_list", "depends_on": ["a"], "params": {"limit": 1}},
        ]
    )


# ------------------------------------------------------------ lifecycle


def test_lifecycle_maps_every_subsystem(data_dir: Path):
    assert lifecycle.unify("workflow", "partial") == lifecycle.PARTIAL
    assert lifecycle.unify("mission", "running") == lifecycle.EXECUTING
    assert lifecycle.unify("research", "synthesizing") == lifecycle.VERIFYING
    assert lifecycle.unify("coding", "bounded") == lifecycle.PARTIAL
    assert lifecycle.unify("coding", "testing") == lifecycle.VERIFYING


def test_unknown_state_is_unresolved_not_guessed(data_dir: Path):
    assert lifecycle.unify("workflow", "vibing") == lifecycle.UNRESOLVED
    assert lifecycle.unify("nonsense", "running") == lifecycle.UNRESOLVED


def test_only_completed_counts_as_success(data_dir: Path):
    assert lifecycle.is_successful(lifecycle.COMPLETED) is True
    for state in (
        lifecycle.PARTIAL,
        lifecycle.FAILED,
        lifecycle.CANCELLED,
        lifecycle.BLOCKED,
        lifecycle.UNRESOLVED,
    ):
        assert lifecycle.is_successful(state) is False


def test_summary_never_hides_a_failure(data_dir: Path):
    """A single failure is not outvoted by successes."""
    assert lifecycle.summarise([lifecycle.COMPLETED] * 5 + [lifecycle.FAILED]) == (
        lifecycle.PARTIAL
    )
    assert lifecycle.summarise([lifecycle.FAILED, lifecycle.FAILED]) == lifecycle.FAILED
    assert lifecycle.summarise([lifecycle.COMPLETED, lifecycle.CANCELLED]) == (lifecycle.CANCELLED)
    assert lifecycle.summarise([lifecycle.COMPLETED, lifecycle.EXECUTING]) == (lifecycle.EXECUTING)
    assert lifecycle.summarise([lifecycle.COMPLETED] * 3) == lifecycle.COMPLETED


def test_running_work_keeps_the_whole_set_executing(data_dir: Path):
    assert lifecycle.summarise([lifecycle.FAILED, lifecycle.EXECUTING]) == lifecycle.EXECUTING


# --------------------------------------------------------------- context


def test_execution_context_is_correlation_only(data_dir: Path):
    ctx = env.create(requester="tester", autonomy=policy.BOUNDED, timeout_s=60)
    payload = ctx.to_dict()
    for field in (
        "request_id",
        "workflow_id",
        "mission_id",
        "requester",
        "agent_id",
        "skill_id",
        "model",
        "provider",
        "tools",
        "sources",
        "evidence",
    ):
        assert field in payload
    # Not a memory system: no content fields at all.
    assert not any(k in payload for k in ("prompt", "response", "messages", "memory"))


def test_context_binding_is_scoped(data_dir: Path):
    assert env.current() is None
    ctx = env.create(requester="a")
    with env.bind(ctx):
        assert env.current().request_id == ctx.request_id
        inner = ctx.with_(agent_id="research_specialist")
        with env.bind(inner):
            assert env.current().agent_id == "research_specialist"
        assert env.current().agent_id == ""
    assert env.current() is None


def test_correlate_stamps_identifiers_without_overriding(data_dir: Path):
    ctx = env.create(requester="a").with_(workflow_id="wf_1", mission_id="m_1")
    with env.bind(ctx):
        stamped = env.correlate({"limit": 1})
        assert stamped["workflow_id"] == "wf_1"
        assert stamped["mission_id"] == "m_1"
        # An explicit value from the caller wins.
        assert env.correlate({"workflow_id": "wf_other"})["workflow_id"] == "wf_other"


def test_context_deadline(data_dir: Path):
    ctx = env.create(timeout_s=0.0)
    assert ctx.expired() is False and ctx.remaining_s() is None
    bounded = env.create(timeout_s=100)
    assert bounded.remaining_s() > 0 and bounded.expired() is False


def test_context_lists_are_bounded(data_dir: Path):
    ctx = env.create().with_(tools=[f"t{i}" for i in range(200)])
    assert len(ctx.tools) <= env_context.MAX_TOOLS_TRACKED


# ---------------------------------------------------------------- policy


def test_autonomy_levels_are_ordered(data_dir: Path, monkeypatch):
    assert policy.effective_level(policy.DIRECT) == policy.DIRECT
    assert policy.permits("workflow", policy.DIRECT) is False
    assert policy.permits("workflow", policy.BOUNDED) is True
    assert policy.permits("scheduled", policy.BOUNDED) is False
    # Continuous is above the default ceiling, so the deployment has to allow it
    # before asking for it means anything.
    assert policy.permits("scheduled", policy.CONTINUOUS) is False
    monkeypatch.setenv(policy.AUTONOMY_ENV, policy.CONTINUOUS)
    assert policy.permits("scheduled", policy.CONTINUOUS) is True


def test_requested_autonomy_cannot_exceed_the_deployment(data_dir: Path, monkeypatch):
    monkeypatch.setenv(policy.AUTONOMY_ENV, policy.ASSISTED)
    assert policy.effective_level(policy.CONTINUOUS) == policy.ASSISTED
    assert policy.permits("workflow", policy.CONTINUOUS) is False


def test_bounds_only_tighten(data_dir: Path):
    tightened = policy.apply_bounds({"max_steps": 999, "max_runtime_s": 999999}, policy.ASSISTED)
    assert tightened["max_steps"] <= policy.bounds_for(policy.ASSISTED)["max_steps"]
    assert tightened["max_runtime_s"] <= policy.bounds_for(policy.ASSISTED)["max_runtime_s"]
    # An already-tighter request is respected.
    assert policy.apply_bounds({"max_steps": 2}, policy.BOUNDED)["max_steps"] == 2


def test_unknown_autonomy_level_rejected(data_dir: Path):
    with pytest.raises(policy.PolicyError, match="Unknown autonomy level"):
        policy.normalise("unlimited")


def test_safe_mode_stops_new_work_but_not_inspection(data_dir: Path, monkeypatch):
    monkeypatch.setenv(policy.SAFE_MODE_ENV, "1")
    assert policy.safe_mode() is True
    assert policy.configured_level() == policy.DIRECT
    with pytest.raises(policy.PolicyError, match="safe mode"):
        policy.check("workflow")
    # Answering a question is still allowed.
    policy.check("answer")


def test_safe_mode_preserves_stored_state(data_dir: Path, monkeypatch):
    workflow = wf.create_workflow(simple_workflow(), create_mission=False)
    monkeypatch.setenv(policy.SAFE_MODE_ENV, "1")
    assert wf.get(workflow["id"])["state"] == wf.PENDING
    assert wf.status(workflow["id"])["steps_total"] == 1
    monkeypatch.delenv(policy.SAFE_MODE_ENV)
    assert wf.run(workflow["id"])["state"] == wf.COMPLETED


# ------------------------------------------------------------- triage


def test_simple_request_stays_simple(data_dir: Path):
    """AH: a question must not acquire a workflow, mission or research job."""
    for request in ("what is 2+2?", "hello", "who wrote Hamlet?", "explain gravity"):
        decision = env.triage(request)
        assert decision["route"] == env.ANSWER, request
        assert decision["escalated"] is False
        assert decision["capabilities"] == []


def test_simple_request_creates_nothing(data_dir: Path):
    from jarvis import missions

    before = (len(wf.list_workflows(limit=100)), len(missions.list_missions(limit=100)))
    env.triage("what is the capital of France?")
    after = (len(wf.list_workflows(limit=100)), len(missions.list_missions(limit=100)))
    assert before == after, "triage created durable work for a plain question"


def test_multi_capability_request_escalates_to_a_workflow(data_dir: Path):
    decision = env.triage("research the Roche limit then refactor the parser")
    assert decision["route"] == env.WORKFLOW
    assert len(decision["capabilities"]) >= 2
    assert decision["reasons"]


def test_single_capability_request_uses_an_agent(data_dir: Path):
    decision = env.triage("research the history of tides")
    assert decision["route"] == env.AGENT
    assert decision["capabilities"] == ["research"]
    assert env.suggested_agent(decision["capabilities"]) == "research_specialist"


def test_triage_is_explainable(data_dir: Path):
    decision = env.triage("browse https://example.com and verify the sources")
    assert decision["explanation"]
    assert decision["signals"]
    for signal in decision["signals"]:
        assert signal["matched_text"]


def test_triage_respects_autonomy(data_dir: Path, monkeypatch):
    monkeypatch.setenv(policy.AUTONOMY_ENV, policy.DIRECT)
    decision = env.triage("research the Roche limit then refactor the parser")
    assert decision["route"] == env.ANSWER
    assert any("does not permit" in r or "only a direct answer" in r for r in decision["reasons"])


def test_triage_is_deterministic(data_dir: Path):
    request = "research tides then implement a parser"
    first = env.triage(request)
    for _ in range(5):
        assert env.triage(request)["route"] == first["route"]


def test_suggested_agent_uses_existing_roles(data_dir: Path):
    assert env.suggested_agent(["coding"]) == "coding_specialist"
    assert env.suggested_agent(["browser"]) == "research_specialist"
    assert env.suggested_agent([]) == "general_specialist"


# ---------------------------------------------------------------- status


def test_status_reports_idle_when_nothing_runs(data_dir: Path):
    snapshot = env.environment_status()
    assert snapshot["busy"] is False
    assert snapshot["state"] == "idle"
    assert snapshot["doing"] == ["nothing is running"]


def test_status_answers_the_questions_a_person_asks(data_dir: Path):
    snapshot = env.environment_status()
    for section in (
        "workflows",
        "missions",
        "research",
        "coding",
        "models",
        "providers",
        "policy",
        "controls",
        "doing",
        "state",
    ):
        assert section in snapshot, section
    assert "pause" in snapshot["controls"] and "cancel" in snapshot["controls"]


def test_status_shows_running_workflow_with_agent_and_step(data_dir: Path):
    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {
                    "step_id": "a",
                    "action": "mission_list",
                    "agent_id": "general_specialist",
                    "params": {"limit": 1},
                },
                {
                    "step_id": "b",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"], max_steps=1)

    snapshot = env.environment_status()
    assert snapshot["busy"] is True
    active = snapshot["workflows"]["active"]
    assert active and active[0]["workflow_id"] == workflow["id"]
    assert active[0]["state"] == lifecycle.EXECUTING
    assert "general_specialist" in active[0]["agents"]
    assert active[0]["controllable"] is True
    assert any(workflow["id"] in line for line in snapshot["doing"])


def test_status_survives_an_unavailable_subsystem(data_dir: Path, monkeypatch):
    """One broken subsystem must not blind the whole status."""
    from jarvis.integration import status as status_mod

    def boom(_limit):
        raise RuntimeError("research store exploded")

    monkeypatch.setattr(status_mod, "_research", boom)
    snapshot = env.environment_status()
    assert "research" in snapshot["unavailable"]
    assert snapshot["research"] == {"unavailable": True}
    # Everything else still answers.
    assert "workflows" in snapshot and "policy" in snapshot


def test_status_reports_safe_mode(data_dir: Path, monkeypatch):
    monkeypatch.setenv(policy.SAFE_MODE_ENV, "1")
    snapshot = env.environment_status()
    assert snapshot["policy"]["safe_mode"] is True
    assert snapshot["policy"]["autonomy"] == policy.DIRECT


# ------------------------------------------------------------ provenance


def test_provenance_assembles_the_chain(data_dir: Path):
    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {
                    "step_id": "one",
                    "action": "mission_list",
                    "agent_id": "general_specialist",
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])

    graph = env.for_workflow(workflow["id"])
    assert graph["ok"] is True
    kinds = {n["kind"] for n in graph["nodes"]}
    assert "workflow" in kinds and "step" in kinds
    step = [n for n in graph["nodes"] if n["kind"] == "step"][0]
    assert step["agent"] == "general_specialist"
    assert step["action"] == "mission_list"


def test_provenance_reports_gaps_rather_than_inventing_them(data_dir: Path):
    workflow = wf.create_workflow(simple_workflow(), create_mission=False)
    wf.run(workflow["id"])
    graph = env.for_workflow(workflow["id"])
    # mission_list reports no provenance of its own; that is stated, not filled in.
    assert graph["unestablished_links"]
    assert "note" in graph


def test_provenance_of_an_unknown_workflow(data_dir: Path):
    assert env.for_workflow("wf_nope")["ok"] is False


def test_provenance_records_model_fallback(data_dir: Path, monkeypatch):
    """W: a fallback is part of the truth of what ran."""
    import importlib

    mr_execute = importlib.import_module("jarvis.model_routing.execute")
    from jarvis.model_routing import capabilities as caps
    from jarvis.model_routing import health, profiles
    from jarvis.model_routing.profiles import ModelProfile

    profiles.reset()
    health.reset()
    for name, strength in (("first:7b", 0.99), ("second:7b", 0.5)):
        profiles.register_profile(
            ModelProfile(
                provider="ollama",
                model_id=name,
                capabilities={
                    caps.GENERAL_CHAT: caps.SUPPORTED,
                    caps.LOCAL_ONLY: caps.SUPPORTED,
                    caps.STRUCTURED_OUTPUT: caps.SUPPORTED,
                },
                capability_evidence={},
                context_window=32768,
                general_strength=strength,
            )
        )

    def flaky(model, payload):
        if model == "first:7b":
            raise ConnectionError("down")
        return "recovered"

    monkeypatch.setattr(mr_execute, "default_invoker", flaky)
    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {
                    "step_id": "answer",
                    "action": "model_execute",
                    "agent_id": "general_specialist",
                    "params": {"prompt": "hi"},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])

    graph = env.for_workflow(workflow["id"])
    step = [n for n in graph["nodes"] if n["kind"] == "step"][0]
    assert step["model"] == "second:7b"
    assert step["model_fallbacks"] == 1
    profiles.reset()
    health.reset()


# ------------------------------------------------------- reachability


def _registered_actions() -> set[str]:
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    return {a["action"] for a in all_actions()}


def test_every_granted_action_name_is_real(data_dir: Path):
    """The recurring defect: a capability listed but unreachable.

    An allow-list name that matches no registered action grants nothing while
    reading as authority. Impact *gates* are exempt — they are checked inside a
    subsystem rather than dispatched. Deny-side names are exempt too: denying an
    action that does not exist yet is deliberate.
    """
    from jarvis.computer_use import permissions as browser_permissions

    gates = set(browser_permissions.GATE.values())
    real = _registered_actions()
    for agent in agents.list_agents():
        ghosts = (set(agent.allowed_actions) - real) - gates
        assert not ghosts, f"{agent.id} is granted names that are not actions: {sorted(ghosts)}"


def test_browser_is_reachable_by_the_agents_granted_it(data_dir: Path):
    """The gates guarded a door no specialist could open: every registered
    browser action was missing from every allow list."""
    for agent_id in ("research_specialist", "analysis_specialist"):
        agent = agents.get(agent_id)
        assert agent.permits("browser_use_open"), f"{agent_id} cannot open a browser"
        assert agent.permits("browser_use_act"), f"{agent_id} cannot drive a browser"
    # Deny still beats allow where browser authority was never intended.
    for agent_id in ("coding_specialist", "general_specialist"):
        assert not agents.get(agent_id).permits("browser_use_act")


def test_browser_authority_is_still_gated_by_impact(data_dir: Path):
    """Granting the actions must not widen authority past the impact classes."""
    from jarvis.computer_use import permissions as browser_permissions

    agent = agents.get("research_specialist")
    assert agent.permits(browser_permissions.READ_ACTION)
    assert not agent.permits(browser_permissions.HIGH_IMPACT_ACTION)
    analysis = agents.get("analysis_specialist")
    assert not analysis.permits(browser_permissions.INTERACT_ACTION), "read-only agent may interact"


def test_browser_calls_carry_the_real_agent_identity(data_dir: Path, monkeypatch):
    """The browser reads the acting agent from its payload, so a specialist
    could otherwise borrow another agent's browser authority by naming it."""
    import jarvis.handlers.registry as registry
    from jarvis.specialized_agents.invoke import call_action as agent_call_action

    seen: dict = {}
    monkeypatch.setattr(
        registry, "call_action", lambda assistant, action, params, message: seen.update(params)
    )
    agent_call_action(
        agents.get("research_specialist"),
        None,
        "browser_use_act",
        {"agent_id": "coding_specialist", "session_id": "s", "action": "click"},
    )
    assert seen["agent_id"] == "research_specialist", "payload identity was trusted"


def test_a_browser_session_records_the_agent_that_opened_it(data_dir: Path, monkeypatch):
    """Provenance has to name someone: agent-opened sessions were recorded as
    'unattributed', and a supplied owner must not override the real caller."""
    import jarvis.handlers.registry as registry
    from jarvis.specialized_agents.invoke import call_action as agent_call_action

    opened: dict = {}

    def fake_open(**kwargs):
        opened.update(kwargs)
        return {"id": "cus_test", "owner": kwargs.get("owner")}

    import jarvis.computer_use as cu

    monkeypatch.setattr(cu, "open_session", fake_open)
    real_call = registry.call_action
    agent_call_action(
        agents.get("research_specialist"), None, "browser_use_open", {"owner": "somebody_else"}
    )
    assert real_call is registry.call_action
    assert opened["owner"] == "research_specialist"


def test_a_session_refuses_to_read_a_page_something_else_moved(data_dir: Path):
    """Computer-use sessions share one browser page, so a session could return
    another session's page as its own — and that content became evidence
    attributed to a source it never came from."""
    from jarvis.computer_use import engine, sessions

    class FakeDriver:
        """Reports a page that has moved since the session's last action."""

        def state(self):
            return {"url": "https://somewhere-else.example/", "title": "not ours"}

        def extract(self, limit):  # pragma: no cover - must never be reached
            raise AssertionError("read a page the session does not own")

    session = sessions.create(owner="research_specialist")
    sessions.record_action(session["id"], action="navigate", url="https://example.com/", title="")

    out = engine.perform(session["id"], "extract", {}, driver=FakeDriver())
    assert out["ok"] is False
    assert out["error_kind"] == engine.ERR_DIVERGED
    assert "example.com" in out["error"] and "somewhere-else" in out["error"]


def test_a_session_reads_its_own_page_normally(data_dir: Path):
    """The guard must not block a session whose page is where it left it."""
    from jarvis.computer_use import engine, sessions

    class FakeDriver:
        def state(self):
            return {"url": "https://example.com/", "title": "Example Domain"}

        def extract(self, limit):
            return {"text": "Example Domain", "url": "https://example.com/"}

    session = sessions.create(owner="research_specialist")
    sessions.record_action(session["id"], action="navigate", url="https://example.com/", title="")

    out = engine.perform(session["id"], "extract", {}, driver=FakeDriver())
    assert out["ok"] is True, out.get("error")
    assert out["result"]["text"] == "Example Domain"


def test_collaboration_can_actually_be_opened(data_dir: Path):
    """Delegation needs a collaboration to delegate into; only delegate was
    granted, so every collaboration_id a specialist could name did not exist."""
    for agent_id in ("research_specialist", "analysis_specialist", "general_specialist"):
        agent = agents.get(agent_id)
        assert agent.permits("collab_create"), f"{agent_id} cannot open a collaboration"
        assert agent.permits("collab_delegate")


def test_an_unregistered_action_reports_itself_clearly(data_dir: Path):
    """A stale name should say so, not surface as a bare KeyError."""
    from jarvis.handlers.registry import UnknownAction, call_action

    with pytest.raises(UnknownAction) as excinfo:
        call_action(None, "definitely_not_an_action", {}, "probe")
    assert "definitely_not_an_action" in str(excinfo.value)


# -------------------------------------------------------------- recovery


def test_recovery_touches_every_durable_subsystem(data_dir: Path):
    outcome = recovery.recover_all()
    assert set(outcome["recovered"]) == {"missions", "workflows", "coding_tasks"}
    assert outcome["ok"] is True


def test_recovery_makes_interrupted_work_resumable(data_dir: Path):
    from jarvis.autonomous_workflows import store as wf_store

    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "b",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wid = workflow["id"]
    wf.run(wid, max_steps=1)
    wf_store.set_step(wid, "b", state=wf.STEP_RUNNING)

    outcome = recovery.recover_all()
    assert wid in outcome["recovered"]["workflows"]
    states = wf_store.step_states(wid)
    assert states["a"] == wf.STEP_SUCCEEDED, "completed work was undone"
    assert states["b"] == wf.STEP_PENDING
    assert wf.run(wid)["state"] == wf.COMPLETED


def test_on_demand_recovery_reports_instead_of_mutating(data_dir: Path):
    """A dry run must tell the truth about what it would touch, and touch nothing."""
    from jarvis.autonomous_workflows import store as wf_store

    workflow = wf.create_workflow(_two_step(), create_mission=False)
    wid = workflow["id"]
    wf.run(wid, max_steps=1)
    wf_store.set_step(wid, "b", state=wf.STEP_RUNNING)

    outcome = recovery.recover_on_demand()
    assert outcome["applied"] is False
    assert wid in outcome["recovered"]["workflows"], "a dry run still reports what it would touch"
    assert wf_store.step_states(wid)["b"] == wf.STEP_RUNNING, "dry run mutated a live step"


def test_on_demand_recovery_refuses_to_apply_without_force(data_dir: Path):
    """After startup a live state means 'executing', not 'abandoned'."""
    from jarvis.autonomous_workflows import store as wf_store

    wid = wf.create_workflow(_two_step(), create_mission=False)["id"]
    wf.run(wid, max_steps=1)
    wf_store.set_step(wid, "b", state=wf.STEP_RUNNING)

    outcome = recovery.recover_on_demand(apply=True)
    assert outcome["applied"] is False
    assert outcome["refused"]
    assert wf_store.step_states(wid)["b"] == wf.STEP_RUNNING

    forced = recovery.recover_on_demand(apply=True, force=True)
    assert forced["applied"] is True and forced["forced"] is True
    assert wf_store.step_states(wid)["b"] == wf.STEP_PENDING


def test_recovery_does_not_cause_an_in_flight_step_to_run_twice(data_dir: Path):
    """The defect this guards: recovery reset an executing step, so a second
    driver picked it up and the side effect happened twice."""
    import threading
    import time

    from jarvis.autonomous_workflows import store as wf_store
    from jarvis.handlers.registry import register_action
    from jarvis.response import ok

    calls: list[float] = []

    @register_action("test_slow_side_effect", module="general", description="probe")
    def _slow(assistant, params, message):
        calls.append(time.time())
        time.sleep(2.0)
        return ok("done", module="general")

    wid = wf.create_workflow(
        simple_workflow(steps=[{"step_id": "a", "action": "test_slow_side_effect", "params": {}}]),
        create_mission=False,
    )["id"]
    driver = threading.Thread(target=lambda: wf.run(wid), daemon=True)
    driver.start()
    for _ in range(100):
        if wf_store.step_states(wid).get("a") == wf.STEP_RUNNING:
            break
        time.sleep(0.02)

    recovery.recover_on_demand(apply=True)  # the operator-facing path
    assert wf_store.step_states(wid)["a"] == wf.STEP_RUNNING, "an executing step was reset"

    threading.Thread(target=lambda: wf.run(wid), daemon=True).start()
    driver.join(timeout=20)
    time.sleep(1.0)
    assert len(calls) == 1, f"side effect ran {len(calls)} times"


def test_startup_recovery_is_recorded_and_visible(data_dir: Path):
    """Startup logging happens before the log handlers attach, so status is the
    only place an operator can see that recovery ran."""
    outcome = recovery.recover_on_startup()
    assert recovery.last_startup_recovery() == outcome
    assert outcome["applied"] is True and outcome["at"]
    snapshot = env.environment_status()
    assert snapshot["startup_recovery"]["total"] == outcome["total"]


def test_recovery_survives_a_broken_subsystem(data_dir: Path, monkeypatch):
    def boom():
        raise RuntimeError("mission store exploded")

    monkeypatch.setattr(recovery, "_missions", boom)
    outcome = recovery.recover_all()
    assert outcome["ok"] is False
    assert "missions" in outcome["errors"]
    # The others still ran.
    assert "workflows" in outcome["recovered"]


def test_recovery_runs_even_in_safe_mode(data_dir: Path, monkeypatch):
    """Knowing what was interrupted is inspection, not execution."""
    monkeypatch.setenv(policy.SAFE_MODE_ENV, "1")
    outcome = recovery.recover_on_startup()
    assert outcome["safe_mode"] is True
    assert "recovered" in outcome


def test_startup_recovery_is_wired_into_the_service(data_dir: Path):
    """AI: the lifespan must recover before the worker takes new work."""
    source = (REPO_ROOT / "jarvis" / "gui" / "server.py").read_text()
    assert "recover_on_startup" in source
    recovery_at = source.index("recover_on_startup")
    worker_at = source.index("mission_worker.start")
    assert recovery_at < worker_at, "recovery must run before the worker starts"


def test_shutdown_still_stops_the_worker(data_dir: Path):
    """AJ: shutdown ordering is preserved."""
    source = (REPO_ROOT / "jarvis" / "gui" / "server.py").read_text()
    assert "mission_worker.stop()" in source
    assert "auto_checkpoint" in source


def test_safe_mode_prevents_worker_start_in_the_service(data_dir: Path):
    source = (REPO_ROOT / "jarvis" / "gui" / "server.py").read_text()
    assert "environment_policy.safe_mode()" in source
    assert "elif mission_worker.start" in source


# ------------------------------------------------------------- actions/API


def test_environment_actions_registered_and_reachable(data_dir: Path):
    """AL/AK: registered is not enough — an agent must be able to call them."""
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions
    from jarvis.specialized_agents import definitions as agent_defs

    ensure_handlers_loaded()
    registered = {a["action"] for a in all_actions()}
    assert set(agent_defs.ENVIRONMENT_USE) <= registered
    for action in agent_defs.ENVIRONMENT_USE:
        assert any(a.permits(action) for a in agent_defs.BUILTIN_AGENTS), (
            f"registered but unreachable: {action}"
        )


def test_every_prior_milestone_action_survives(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {a["action"] for a in all_actions()}
    for action in (
        "mission_create",
        "research_create",
        "evidence_verify",
        "collab_delegate",
        "browser_use_act",
        "dev_task_create",
        "skill_invoke",
        "mcp_invoke",
        "model_route",
        "workflow_create",
        "workflow_start",
        "workflow_list",
        "workflow_run",
    ):
        assert action in names, action


def test_status_action(data_dir: Path):
    out = _call("aria_status", {})
    assert out["ok"] is True
    assert "environment" in out
    assert out["environment"]["policy"]["autonomy"]


def test_plan_action_explains(data_dir: Path):
    out = _call("aria_plan", {"request": "research tides then refactor the parser"})
    assert out["ok"] is True
    assert out["plan"]["route"] == env.WORKFLOW
    assert out["plan"]["suggested_agent"]
    assert out["message"]


def test_plan_action_needs_a_request(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    assert call_action(None, "aria_plan", {}, "")["ok"] is False


def test_autonomy_action(data_dir: Path):
    out = _call("aria_autonomy", {})
    assert out["ok"] is True
    assert out["policy"]["capabilities"]


def test_recover_action(data_dir: Path):
    out = _call("aria_recover", {})
    assert out["ok"] is True
    assert "recovery" in out


def test_provenance_action(data_dir: Path):
    workflow = wf.create_workflow(simple_workflow(), create_mission=False)
    wf.run(workflow["id"])
    out = _call("aria_provenance", {"workflow_id": workflow["id"]})
    assert out["ok"] is True
    assert out["provenance"]["counts"]["step"] == 1
    assert _call("aria_provenance", {})["ok"] is False
    assert _call("aria_provenance", {"workflow_id": "wf_nope"})["ok"] is False


def test_lifecycle_action(data_dir: Path):
    out = _call("aria_lifecycle", {"kind": "coding", "state": "bounded"})
    assert out["ok"] is True
    assert out["lifecycle"]["state"] == lifecycle.PARTIAL
    assert _call("aria_lifecycle", {"kind": "coding"})["ok"] is False


def test_agent_can_reach_the_control_surface(data_dir: Path):
    out = agents.invoke("general_specialist", "status", action="aria_status", params={})
    assert out["ok"] is True
    assert out["result"]["environment"]["state"] in ("idle", *lifecycle.STATES)


# --------------------------------------------------- integration behaviour


def test_human_control_is_available_for_running_work(data_dir: Path):
    """G/7: a long-running task must not become opaque."""
    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "b",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wid = workflow["id"]
    wf.run(wid, max_steps=1)

    assert _call("aria_status", {})["environment"]["busy"] is True
    assert _call("workflow_pause", {"workflow_id": wid})["ok"] is True
    assert wf.get(wid)["state"] == wf.PAUSED
    assert _call("workflow_resume", {"workflow_id": wid})["ok"] is True
    assert wf.get(wid)["state"] == wf.COMPLETED


def test_cancellation_is_never_a_retry_or_a_success(data_dir: Path):
    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "b",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=True,
    )
    wid = workflow["id"]
    _call("workflow_cancel", {"workflow_id": wid})
    final = wf.get(wid)
    assert final["state"] == wf.CANCELLED
    assert lifecycle.unify("workflow", final["state"]) == lifecycle.CANCELLED
    assert lifecycle.is_successful(lifecycle.unify("workflow", final["state"])) is False
    from jarvis.missions import store as mstore

    assert mstore.cancel_requested(final["mission_id"]) is True


def test_partial_work_is_never_reported_complete(data_dir: Path):
    workflow = wf.create_workflow(
        simple_workflow(
            steps=[
                {"step_id": "ok", "action": "mission_list", "params": {"limit": 1}},
                {"step_id": "bad", "action": "mission_status", "params": {"mission_id": "nope"}},
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    unified = lifecycle.unify("workflow", final["state"])
    assert unified == lifecycle.PARTIAL
    assert lifecycle.is_successful(unified) is False


def test_restart_continuity(data_dir: Path):
    """AN: a long-running task survives a real process death and resumes."""
    script = textwrap.dedent(f"""
        import os, sys
        sys.path.insert(0, {str(REPO_ROOT)!r})
        os.environ["JARVIS_DATA_DIR"] = {str(data_dir)!r}
        from unittest.mock import MagicMock
        sys.modules.setdefault("ollama", MagicMock())
        from jarvis import autonomous_workflows as wf
        from jarvis.autonomous_workflows import store as s
        w = wf.create_workflow({{
            "name": "continuity",
            "steps": [
                {{"step_id": "a", "action": "mission_list", "params": {{"limit": 1}}}},
                {{"step_id": "b", "action": "mission_list", "depends_on": ["a"],
                  "params": {{"limit": 1}}}},
            ],
        }}, create_mission=False)
        wf.run(w["id"], max_steps=1)
        s.set_step(w["id"], "b", state="running")
        print(w["id"], flush=True)
        os._exit(9)
    """)
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=180
    )
    assert proc.returncode == 9, proc.stderr[-400:]
    workflow_id = proc.stdout.strip().splitlines()[-1]

    # The environment knows about it after the "restart".
    snapshot = env.environment_status()
    assert any(w["workflow_id"] == workflow_id for w in snapshot["workflows"]["active"])

    outcome = recovery.recover_on_startup()
    assert workflow_id in outcome["recovered"]["workflows"]
    assert wf.run(workflow_id)["state"] == wf.COMPLETED
    assert wf.get(workflow_id)["usage"]["actions"] == 2, "recovery repeated completed work"


# ------------------------------------------------------------- security


def test_security_1_workflow_cannot_grant_an_agent_permissions(data_dir: Path):
    out = _call(
        "workflow_create",
        {
            "definition": {
                "name": "escalate",
                "steps": [
                    {"step_id": "x", "action": "dev_task_create", "agent_id": "research_specialist"}
                ],
            },
            "mission": False,
        },
    )
    assert out["ok"] is False
    assert "may not invoke" in out["message"]


def test_security_2_environment_does_not_widen_agent_authority(data_dir: Path):
    coder = agents.get("coding_specialist")
    before = (set(coder.allowed_actions), set(coder.denied_actions))
    _call("aria_status", {})
    _call("aria_plan", {"request": "refactor everything"})
    after = agents.get("coding_specialist")
    assert (set(after.allowed_actions), set(after.denied_actions)) == before
    for forbidden in ("browser_use_read", "evidence_verify", "research_create"):
        assert after.permits(forbidden) is False


def test_security_3_autonomy_cannot_be_raised_by_a_request(data_dir: Path, monkeypatch):
    monkeypatch.setenv(policy.AUTONOMY_ENV, policy.DIRECT)
    out = _call("aria_plan", {"request": "research and refactor", "autonomy": "continuous"})
    assert out["plan"]["autonomy"] == policy.DIRECT
    assert out["plan"]["route"] == env.ANSWER


def test_security_4_safe_mode_cannot_be_bypassed_by_a_parameter(data_dir: Path, monkeypatch):
    monkeypatch.setenv(policy.SAFE_MODE_ENV, "1")
    assert policy.effective_level(policy.CONTINUOUS) == policy.DIRECT
    with pytest.raises(policy.PolicyError):
        policy.check("workflow", level=policy.CONTINUOUS)


def test_security_5_environment_executes_nothing_itself(data_dir: Path):
    """The integration layer must not become a way to run things directly."""
    import inspect

    from jarvis.integration import plan as plan_mod
    from jarvis.integration import policy as policy_mod
    from jarvis.integration import status as status_mod

    for module in (plan_mod, policy_mod, status_mod):
        source = inspect.getsource(module)
        assert "call_action" not in source, f"{module.__name__} can execute actions"
        assert "eval(" not in source and "exec(" not in source


def test_security_6_context_is_not_promoted_into_memory(data_dir: Path):
    import inspect

    from jarvis.integration import context as context_mod

    source = inspect.getsource(context_mod)
    # Code, not prose: the module docstring states the guarantee, so matching
    # bare words would flag the very sentence that promises it.
    code = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#"))
    for forbidden in (
        "import acm",
        "acm_bridge",
        "memory_manager",
        "brain_memory",
        "remember(",
        "ml_memory",
    ):
        assert forbidden not in code, f"context reaches into {forbidden}"


def test_security_7_failed_verification_stays_unverified(data_dir: Path):
    from jarvis import evidence as ev

    claim = ev.add_claim("unsupported assertion", context_id="env_sec_ctx")
    verdict = ev.verify(claim)
    assert verdict["result"] != "verified"
    assert lifecycle.is_successful(lifecycle.unify("workflow", "partial")) is False


def test_security_8_provenance_cannot_be_fabricated(data_dir: Path):
    """A capability that reported nothing is recorded as reporting nothing."""
    workflow = wf.create_workflow(simple_workflow(), create_mission=False)
    wf.run(workflow["id"])
    graph = env.for_workflow(workflow["id"])
    step = [n for n in graph["nodes"] if n["kind"] == "step"][0]
    assert step["model"] == "" and step["skill"] == "" and step["provider"] == ""
    assert graph["unestablished_links"]
