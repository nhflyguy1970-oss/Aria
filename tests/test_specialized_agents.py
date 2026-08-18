"""Specialized agents — definitions, registry, discovery, permissions, invocation."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis import missions
from jarvis import specialized_agents as agents
from jarvis.missions import store as mstore
from jarvis.specialized_agents import definitions as defs
from jarvis.specialized_agents import registry


@pytest.fixture(autouse=True)
def _clean_registry():
    """Registry is rebuilt per test so ordering can never leak state."""
    registry.reset()
    yield
    registry.reset()


def _definition(**overrides) -> defs.AgentDefinition:
    base = {
        "id": "test_agent",
        "name": "Test Agent",
        "role": "testing",
        "description": "A test specialist",
        "capabilities": ("testing",),
        "allowed_actions": ("mission_status",),
    }
    base.update(overrides)
    return defs.AgentDefinition(**base)


# ------------------------------------------------------------ definitions


def test_valid_definition_passes_validation(data_dir: Path):
    assert defs.validate(_definition()).id == "test_agent"


@pytest.mark.parametrize(
    "overrides",
    [
        {"id": ""},
        {"name": ""},
        {"role": ""},
        {"description": ""},
        {"capabilities": ()},
        {"allowed_actions": ()},
        {"version": 0},
        {"id": "bad id!"},
    ],
)
def test_invalid_definitions_are_rejected(data_dir: Path, overrides):
    with pytest.raises(defs.AgentDefinitionError):
        defs.validate(_definition(**overrides))


def test_allow_and_deny_conflict_is_rejected(data_dir: Path):
    with pytest.raises(defs.AgentDefinitionError):
        defs.validate(
            _definition(allowed_actions=("mission_status",), denied_actions=("mission_status",))
        )


def test_definition_is_immutable(data_dir: Path):
    agent = _definition()
    with pytest.raises(Exception):
        agent.allowed_actions = ("*",)  # type: ignore[misc]


def test_enable_disable_produces_new_definition(data_dir: Path):
    agent = _definition()
    disabled = agent.with_enabled(False)
    assert agent.enabled is True and disabled.enabled is False


def test_versioning_and_schema_exposed(data_dir: Path):
    data = _definition(version=3).to_dict()
    assert data["version"] == 3
    assert data["schema_version"] == defs.SCHEMA_VERSION


def test_instructions_hidden_unless_requested(data_dir: Path):
    agent = _definition(system_instructions="secret-ish guidance")
    assert "system_instructions" not in agent.to_dict()
    assert agent.to_dict(include_instructions=True)["system_instructions"]


# ------------------------------------------------------------ registry


def test_builtin_agents_are_registered(data_dir: Path):
    ids = {a.id for a in agents.list_agents()}
    assert {
        "research_specialist",
        "coding_specialist",
        "analysis_specialist",
        "general_specialist",
    } <= ids


def test_all_builtins_are_valid(data_dir: Path):
    for agent in defs.BUILTIN_AGENTS:
        defs.validate(agent)


def test_register_lookup_and_unregister(data_dir: Path):
    agents.register(_definition())
    assert agents.get("test_agent") is not None
    assert agents.unregister("test_agent") is True
    assert agents.get("test_agent") is None


def test_duplicate_registration_rejected_unless_replacing(data_dir: Path):
    agents.register(_definition())
    with pytest.raises(defs.AgentDefinitionError):
        agents.register(_definition())
    agents.register(_definition(description="v2"), replace_existing=True)
    assert agents.get("test_agent").description == "v2"


def test_disabled_agent_hidden_from_listing(data_dir: Path):
    agents.set_enabled("coding_specialist", False)
    assert "coding_specialist" not in {a.id for a in agents.list_agents()}
    assert "coding_specialist" in {a.id for a in agents.list_agents(include_disabled=True)}


def test_listing_is_deterministic(data_dir: Path):
    assert [a.id for a in agents.list_agents()] == sorted(a.id for a in agents.list_agents())


def test_registry_reset_restores_builtins(data_dir: Path):
    agents.unregister("coding_specialist")
    registry.reset()
    assert agents.get("coding_specialist") is not None


def test_module_reload_keeps_registry_usable(data_dir: Path):
    import importlib

    importlib.reload(registry)
    assert {a.id for a in registry.list_agents()} >= {"general_specialist"}


def test_capability_index(data_dir: Path):
    caps = agents.capabilities()
    assert "research" in caps and "research_specialist" in caps["research"]
    assert "coding" in caps and "coding_specialist" in caps["coding"]


# ------------------------------------------------------------ discovery


@pytest.mark.parametrize(
    "task,expected",
    [
        ("debug this failing pytest traceback in the repo", "coding_specialist"),
        ("research the sources and citations for this topic", "research_specialist"),
        ("compare and evaluate these two options", "analysis_specialist"),
        ("hello, what can you do", "general_specialist"),
    ],
)
def test_task_selects_expected_specialist(data_dir: Path, task, expected):
    assert agents.select(task)["agent_id"] == expected


def test_selection_is_explainable(data_dir: Path):
    sel = agents.select("debug this crash in the code")
    assert sel["matched"] is True
    assert sel["selection_method"] == "keyword_capability_match"
    assert sel["matched_capabilities"]
    assert "coding_specialist" in sel["candidates"]
    assert sel["agent"]["role"] == "coding"
    assert "matched" in sel["reason"].lower()


def test_unmatched_task_falls_back_and_says_so(data_dir: Path):
    sel = agents.select("zzzz qqqq")
    assert sel["agent_id"] == defs.FALLBACK_AGENT_ID
    assert sel["matched"] is False
    assert sel["selection_method"] == "fallback"


def test_explicit_capability_selection(data_dir: Path):
    sel = agents.select("anything", required_capability="evidence")
    assert sel["agent_id"] == "research_specialist"
    assert sel["selection_method"] == "explicit_capability"


def test_unsupported_capability_reports_clearly(data_dir: Path):
    sel = agents.select("anything", required_capability="time_travel")
    assert sel["agent_id"] is None
    assert sel["matched"] is False
    assert "time_travel" in sel["reason"]


def test_selection_is_deterministic(data_dir: Path):
    first = agents.select("debug the failing test")
    for _ in range(5):
        assert agents.select("debug the failing test") == first


def test_find_by_capability(data_dir: Path):
    assert {a.id for a in agents.find_by_capability("research")} == {"research_specialist"}
    assert agents.find_by_capability("nope") == []


# ------------------------------------------------------------ permissions


def test_allowed_action_permitted(data_dir: Path):
    assert agents.get("research_specialist").permits("research_create") is True


def test_denied_action_refused(data_dir: Path):
    assert agents.get("research_specialist").permits("aria_self_fix") is False


def test_action_outside_allowlist_refused(data_dir: Path):
    assert agents.get("analysis_specialist").permits("run_tests") is False


def test_deny_beats_wildcard(data_dir: Path):
    agent = _definition(allowed_actions=("*",), denied_actions=("aria_self_fix",))
    assert agent.permits("anything") is True
    assert agent.permits("aria_self_fix") is False


def test_check_permission_raises(data_dir: Path):
    from jarvis.specialized_agents.invoke import PermissionDenied, check_permission

    with pytest.raises(PermissionDenied):
        check_permission(agents.get("analysis_specialist"), "run_tests")


def test_invoke_rejects_unauthorized_action(data_dir: Path):
    out = agents.invoke("analysis_specialist", "try something", action="aria_self_fix")
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"
    assert "not permitted" in out["error"]


def test_permissions_cannot_be_broadened_at_runtime(data_dir: Path):
    agent = agents.get("analysis_specialist")
    snapshot = agent.to_dict()
    snapshot["allowed_actions"].append("aria_self_fix")  # mutating the copy
    assert agents.get("analysis_specialist").permits("aria_self_fix") is False


def test_coding_specialist_cannot_run_research(data_dir: Path):
    assert agents.get("coding_specialist").permits("research_create") is False


# ------------------------------------------------------------ invocation


def test_invoke_returns_assignment_and_contract_fields(data_dir: Path):
    out = agents.invoke("research_specialist", "study something")
    assert out["ok"] is True
    for key in agents.get("research_specialist").output_contract:
        assert key in out
    assert out["agent_id"] == "research_specialist"
    assert out["duration_ms"] >= 0


def test_invoke_validates_input_contract(data_dir: Path):
    out = agents.invoke("research_specialist", "   ")
    assert out["ok"] is False
    assert out["error_kind"] == "contract"


def test_invoke_unknown_agent(data_dir: Path):
    assert agents.invoke("nope", "task")["ok"] is False


def test_invoke_disabled_agent_refused(data_dir: Path):
    agents.set_enabled("analysis_specialist", False)
    out = agents.invoke("analysis_specialist", "task")
    assert out["ok"] is False and "disabled" in out["error"]


def test_invoke_executes_permitted_action(data_dir: Path):
    mid = missions.create_mission("agent action target", steps=[])
    out = agents.invoke(
        "research_specialist", "check mission", action="mission_status", params={"mission_id": mid}
    )
    assert out["ok"] is True
    assert out["result"]["ok"] is True
    assert out["action"] == "mission_status"


def test_invoke_reports_execution_error(data_dir: Path):
    out = agents.invoke(
        "research_specialist", "bad", action="mission_status", params={"mission_id": "missing"}
    )
    # The action itself reports failure; invocation surfaces it rather than raising.
    assert out["ok"] is True
    assert out["result"]["ok"] is False


def test_model_integration_uses_existing_interface(data_dir: Path):
    model = agents.resolve_model(agents.get("coding_specialist"))
    assert isinstance(model, str)


def test_select_and_invoke_carries_selection(data_dir: Path):
    out = agents.select_and_invoke("research citations for this topic")
    assert out["ok"] is True
    assert out["agent_id"] == "research_specialist"
    assert out["selection"]["matched"] is True


def test_select_and_invoke_unsupported_capability(data_dir: Path):
    out = agents.select_and_invoke("x", required_capability="time_travel")
    assert out["ok"] is False


def test_concurrent_invocations_do_not_corrupt_registry(data_dir: Path):
    import threading

    results: list[dict] = []
    errors: list[Exception] = []

    def worker(i: int):
        try:
            results.append(agents.invoke("general_specialist", f"task {i}"))
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors
    assert len(results) == 12
    assert all(r["ok"] for r in results)
    assert len(agents.list_agents()) == len(defs.BUILTIN_AGENTS)


# ------------------------------------------------------------ mission integration


def test_agent_backed_mission_runs_and_persists(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    steps = [
        {
            "name": "analysis step",
            "action": "agent_step",
            "params": {"agent_id": "analysis_specialist", "task": "analyse the inputs"},
        },
        {
            "name": "general step",
            "action": "agent_step",
            "params": {"agent_id": "general_specialist", "task": "summarise"},
        },
    ]
    mid = missions.create_mission("agent mission", steps=steps)
    missions.run(mid, lambda step, ctx: call_action(None, step["action"], step["params"], ""))

    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert len(mstore.checkpoints(mid)) == 2
    assert missions.get(mid)["result"]["context"]["agent_id"] == "general_specialist"


def test_agent_mission_failure_is_represented(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    steps = [
        {
            "name": "denied",
            "action": "agent_step",
            "params": {
                "agent_id": "analysis_specialist",
                "task": "do something forbidden",
                "action": "aria_self_fix",
            },
        }
    ]
    mid = missions.create_mission("denied mission", steps=steps)
    out = call_action(None, "agent_step", steps[0]["params"], "")
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"
    assert missions.get(mid)["state"] == mstore.PENDING


def test_agent_mission_pause_resume_and_cancel(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    runner = lambda step, ctx: call_action(None, step["action"], step["params"], "")  # noqa: E731
    steps = [
        {
            "name": f"step{i}",
            "action": "agent_step",
            "params": {"agent_id": "general_specialist", "task": f"t{i}"},
        }
        for i in range(4)
    ]
    mid = missions.create_mission("pausing agent mission", steps=steps)
    missions.run(mid, runner, max_steps=2)
    assert missions.get(mid)["state"] == mstore.PAUSED
    mstore.make_runnable(mid)
    missions.run(mid, runner)
    assert missions.get(mid)["state"] == mstore.COMPLETED

    other = missions.create_mission("cancel agent mission", steps=steps)
    assert missions.cancel(other) is True
    assert missions.get(other)["state"] == mstore.CANCELLED


def test_agent_mission_recovery_does_not_corrupt_state(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    runner = lambda step, ctx: call_action(None, step["action"], step["params"], "")  # noqa: E731
    steps = [
        {
            "name": f"s{i}",
            "action": "agent_step",
            "params": {"agent_id": "general_specialist", "task": f"t{i}"},
        }
        for i in range(3)
    ]
    mid = missions.create_mission("recovering agent mission", steps=steps)
    missions.run(mid, runner, max_steps=1)
    mstore.transition(mid, mstore.RUNNING)  # simulate a stranded mission
    assert missions.recover() == [mid]
    mstore.make_runnable(mid)
    missions.run(mid, runner)
    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert len(agents.list_agents()) == len(defs.BUILTIN_AGENTS)


# ------------------------------------------------------------ research integration


def test_research_specialist_uses_existing_research_engine(data_dir: Path, monkeypatch):
    """No second research implementation: the specialist drives jarvis.research."""
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.research import engine as research_engine
    from jarvis.research import store as research_store

    ensure_handlers_loaded()
    monkeypatch.setattr(
        research_engine,
        "_default_search",
        lambda q, n: [{"url": "https://nasa.gov/a", "title": "A", "snippet": "supporting"}],
    )
    monkeypatch.setattr(research_engine, "_default_fetch", lambda url: "body text")

    out = agents.invoke(
        "research_specialist",
        "research the topic",
        action="research_create",
        params={"objective": "specialist research"},
    )
    assert out["ok"] is True
    rid = out["result"]["research_id"]
    # The job lives in the existing research store, not a duplicate one.
    assert research_store.get_job(rid)["objective"] == "specialist research"
    assert research_store.DB_PATH.name == "research.db"


def test_research_specialist_evidence_stays_traceable(data_dir: Path, monkeypatch):
    from jarvis.research import engine as research_engine

    monkeypatch.setattr(
        research_engine,
        "_default_search",
        lambda q, n: [
            {"url": "https://nasa.gov/a", "title": "A", "snippet": "supports it"},
            {"url": "https://nih.gov/b", "title": "B", "snippet": "also supports"},
        ],
    )
    monkeypatch.setattr(research_engine, "_default_fetch", lambda url: "agreeing body")
    rid = research_engine.create_research("traceable via specialist")["research_id"]
    for phase in research_engine.PHASES:
        research_engine.run_phase(rid, phase)

    rep = research_engine.report(rid)
    assert rep["claims"][0]["evidence"]
    known = {s["url"] for s in rep["sources"]}
    assert all(r["url"] in known for r in rep["claims"][0]["evidence"])


def test_coding_specialist_permission_boundary_with_real_actions(data_dir: Path):
    """Coding specialist may check git status but not start research."""
    allowed = agents.invoke("coding_specialist", "inspect repo", action="git_status")
    assert allowed.get("error_kind") != "permission_denied"

    denied = agents.invoke("coding_specialist", "do research", action="research_create")
    assert denied["ok"] is False
    assert denied["error_kind"] == "permission_denied"


# ------------------------------------------------------------ handlers


def test_agent_actions_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {s["action"] for s in all_actions()}
    for action in (
        "agent_list",
        "agent_get",
        "agent_select",
        "agent_invoke",
        "agent_capabilities",
        "agent_step",
    ):
        assert action in names, f"{action} not registered"


def test_handler_round_trips(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    listed = call_action(None, "agent_list", {}, "")
    assert listed["ok"] is True
    assert len(listed["agents"]) == len(defs.BUILTIN_AGENTS)

    got = call_action(None, "agent_get", {"agent_id": "coding_specialist"}, "")
    assert got["ok"] is True
    assert got["agent"]["system_instructions"]

    sel = call_action(None, "agent_select", {"task": "debug failing tests"}, "")
    assert sel["ok"] is True
    assert sel["selection"]["agent_id"] == "coding_specialist"

    caps = call_action(None, "agent_capabilities", {}, "")
    assert caps["ok"] is True and caps["capabilities"]

    inv = call_action(None, "agent_invoke", {"task": "compare these options"}, "")
    assert inv["ok"] is True
    assert inv["agent_id"] == "analysis_specialist"


def test_handler_reports_denied_action(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    out = call_action(
        None,
        "agent_invoke",
        {"task": "forbidden", "agent_id": "analysis_specialist", "action": "aria_self_fix"},
        "",
    )
    assert out["ok"] is False
    assert out["error_kind"] == "permission_denied"


def test_agent_get_unknown(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    assert call_action(None, "agent_get", {"agent_id": "nope"}, "")["ok"] is False
