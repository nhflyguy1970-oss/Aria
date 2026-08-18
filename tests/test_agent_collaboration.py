"""Agent delegation and collaboration — graph, bounds, permissions, aggregation."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from jarvis import missions
from jarvis import specialized_agents as agents
from jarvis.collaboration import engine, graph, store
from jarvis.missions import store as mstore
from jarvis.specialized_agents import registry

REPO_ROOT = Path(__file__).resolve().parents[1]

ANALYSIS = "analysis_specialist"
RESEARCH = "research_specialist"
CODING = "coding_specialist"
GENERAL = "general_specialist"


@pytest.fixture(autouse=True)
def _clean_agent_registry():
    registry.reset()
    yield
    registry.reset()


def _collab(objective="shared objective", initiator=ANALYSIS, bounds=None) -> str:
    return engine.create_collaboration(objective, initiator=initiator, bounds=bounds or {})[
        "collaboration_id"
    ]


def _runner():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return lambda step, ctx: call_action(None, step["action"], step["params"], "")


# ------------------------------------------------------------ creation


def test_collaboration_creation_persists(data_dir: Path):
    cid = _collab("investigate something")
    row = store.get(cid)
    assert row["objective"] == "investigate something"
    assert row["initiator"] == ANALYSIS
    assert row["status"] == store.PENDING
    assert row["mission_id"]
    assert store.DB_PATH.is_file()


def test_collaboration_store_is_isolated(data_dir: Path):
    assert data_dir in store.DB_PATH.resolve().parents


def test_empty_objective_rejected(data_dir: Path):
    with pytest.raises(engine.DelegationError):
        engine.create_collaboration("   ")


def test_unknown_initiator_rejected(data_dir: Path):
    with pytest.raises(engine.DelegationError):
        engine.create_collaboration("x", initiator="nope")


def test_collaboration_creates_mission(data_dir: Path):
    cid = _collab()
    mission = missions.get(store.get(cid)["mission_id"])
    assert mission["kind"] == "collaboration"
    assert all(s["action"] == "collab_step" for s in mission["steps"])


# ------------------------------------------------------------ delegation


def test_valid_delegation_records_requester_and_target(data_dir: Path):
    cid = _collab()
    task = engine.delegate(cid, requester=ANALYSIS, objective="research the topic", target=RESEARCH)
    assert task["requester"] == ANALYSIS
    assert task["target"] == RESEARCH
    assert task["status"] == store.TASK_PENDING
    assert task["depth"] == 0


def test_delegation_selects_target_by_capability_and_explains(data_dir: Path):
    cid = _collab()
    task = engine.delegate(
        cid, requester=ANALYSIS, objective="gather sources", capability="research"
    )
    assert task["target"] == RESEARCH
    assert task["selection"]["selection_method"] == "explicit_capability"


def test_requester_without_delegate_permission_rejected(data_dir: Path):
    """coding_specialist is a worker, not a coordinator."""
    cid = _collab()
    with pytest.raises(engine.DelegationError, match="not permitted to delegate"):
        engine.delegate(cid, requester=CODING, objective="do something", target=GENERAL)


def test_unknown_requester_rejected(data_dir: Path):
    cid = _collab()
    with pytest.raises(engine.DelegationError):
        engine.delegate(cid, requester="ghost", objective="x", target=GENERAL)


def test_unavailable_specialist_rejected(data_dir: Path):
    cid = _collab()
    with pytest.raises(engine.DelegationError, match="No specialist available"):
        engine.delegate(cid, requester=ANALYSIS, objective="x", capability="time_travel")


def test_disabled_specialist_rejected(data_dir: Path):
    cid = _collab()
    agents.set_enabled(RESEARCH, False)
    with pytest.raises(engine.DelegationError, match="disabled"):
        engine.delegate(cid, requester=ANALYSIS, objective="x", target=RESEARCH)


def test_empty_objective_delegation_rejected(data_dir: Path):
    cid = _collab()
    with pytest.raises(engine.DelegationError):
        engine.delegate(cid, requester=ANALYSIS, objective="  ", target=GENERAL)


def test_delegation_to_terminal_collaboration_rejected(data_dir: Path):
    cid = _collab()
    store.set_status(cid, store.CANCELLED)
    with pytest.raises(engine.DelegationError):
        engine.delegate(cid, requester=ANALYSIS, objective="x", target=GENERAL)


# ------------------------------------------------------------ permissions


def test_delegation_cannot_escalate_privilege(data_dir: Path):
    """analysis may delegate, but cannot obtain an action research lacks."""
    cid = _collab()
    with pytest.raises(engine.DelegationError, match="not permitted to invoke action"):
        engine.delegate(
            cid, requester=ANALYSIS, objective="self fix", target=RESEARCH, action="aria_self_fix"
        )


def test_target_permissions_evaluated_independently(data_dir: Path):
    """analysis cannot run research_create itself, and cannot borrow it either."""
    assert agents.get(ANALYSIS).permits("research_create") is False
    cid = _collab()
    # Delegating it to a specialist that DOES have it is allowed...
    ok_task = engine.delegate(
        cid, requester=ANALYSIS, objective="do research", target=RESEARCH, action="research_create"
    )
    assert ok_task["target"] == RESEARCH
    # ...but routing it to one that does not is refused.
    with pytest.raises(engine.DelegationError):
        engine.delegate(
            cid,
            requester=ANALYSIS,
            objective="do research",
            target=CODING,
            action="research_create",
        )


def test_denied_action_yields_denied_task_status(data_dir: Path):
    cid = _collab()
    tid = store.add_task(
        cid, requester=ANALYSIS, target=ANALYSIS, objective="forbidden", action="aria_self_fix"
    )
    task = engine.execute_task(tid)
    assert task["status"] == store.TASK_DENIED
    assert "not permitted" in (task["error"] or "")


def test_delegation_does_not_mutate_agent_definitions(data_dir: Path):
    cid = _collab()
    before = agents.get(RESEARCH).to_dict()
    engine.delegate(cid, requester=ANALYSIS, objective="x", target=RESEARCH)
    assert agents.get(RESEARCH).to_dict() == before
    assert agents.get(CODING).permits("collab_delegate") is False


def test_wildcard_still_subject_to_deny(data_dir: Path):
    from jarvis.specialized_agents.definitions import AgentDefinition

    agents.register(
        AgentDefinition(
            id="wild_agent",
            name="Wild",
            role="testing",
            description="wildcard agent",
            capabilities=("testing",),
            allowed_actions=("*", "collab_delegate"),
            denied_actions=("aria_self_fix",),
        )
    )
    cid = _collab()
    with pytest.raises(engine.DelegationError):
        engine.delegate(
            cid, requester=ANALYSIS, objective="x", target="wild_agent", action="aria_self_fix"
        )


# ------------------------------------------------------------ graph


def test_self_dependency_rejected(data_dir: Path):
    tasks = [{"id": "a", "depends_on": ["a"]}]
    with pytest.raises(graph.GraphError, match="itself"):
        graph.validate(tasks)


def test_direct_cycle_rejected(data_dir: Path):
    tasks = [{"id": "a", "depends_on": ["b"]}, {"id": "b", "depends_on": ["a"]}]
    with pytest.raises(graph.GraphError, match="cycle"):
        graph.validate(tasks)


def test_indirect_cycle_rejected(data_dir: Path):
    tasks = [
        {"id": "a", "depends_on": ["c"]},
        {"id": "b", "depends_on": ["a"]},
        {"id": "c", "depends_on": ["b"]},
    ]
    with pytest.raises(graph.GraphError, match="cycle"):
        graph.validate(tasks)


def test_unknown_dependency_rejected(data_dir: Path):
    with pytest.raises(graph.GraphError, match="unknown"):
        graph.validate([{"id": "a", "depends_on": ["missing"]}])


def test_acyclic_graph_accepted(data_dir: Path):
    graph.validate(
        [
            {"id": "a", "depends_on": []},
            {"id": "b", "depends_on": ["a"]},
            {"id": "c", "depends_on": ["a"]},
            {"id": "d", "depends_on": ["b", "c"]},
        ]
    )


def test_delegation_creating_cycle_rejected(data_dir: Path):
    cid = _collab()
    a = engine.delegate(cid, requester=ANALYSIS, objective="a", target=GENERAL)["id"]
    b = engine.delegate(cid, requester=ANALYSIS, objective="b", target=GENERAL, depends_on=[a])[
        "id"
    ]
    # Making 'a' depend on 'b' would close the loop.
    assert graph.would_create_cycle(store.tasks(cid), a, [b]) is True


def test_ready_and_blocked_computation(data_dir: Path):
    tasks = [
        {"id": "a", "status": "success", "depends_on": []},
        {"id": "b", "status": "failed", "depends_on": []},
        {"id": "c", "status": "pending", "depends_on": ["a"]},
        {"id": "d", "status": "pending", "depends_on": ["b"]},
    ]
    assert [t["id"] for t in graph.ready_tasks(tasks, store.TASK_SATISFIED)] == ["c"]
    assert [t["id"] for t in graph.blocked_tasks(tasks, store.TASK_SATISFIED)] == ["d"]


def test_graph_is_persisted_and_inspectable(data_dir: Path):
    cid = _collab()
    a = engine.delegate(cid, requester=ANALYSIS, objective="a", target=RESEARCH)["id"]
    engine.delegate(cid, requester=ANALYSIS, objective="b", target=GENERAL, depends_on=[a])
    data = graph.as_graph(store.tasks(cid))
    assert len(data["nodes"]) == 2
    assert data["edges"] == [{"from": a, "to": data["nodes"][1]["id"]}]


# ------------------------------------------------------------ bounds


def test_max_tasks_enforced(data_dir: Path):
    cid = _collab(bounds={"max_tasks": 2})
    engine.delegate(cid, requester=ANALYSIS, objective="1", target=GENERAL)
    engine.delegate(cid, requester=ANALYSIS, objective="2", target=GENERAL)
    with pytest.raises(engine.BoundExceeded, match="max_tasks"):
        engine.delegate(cid, requester=ANALYSIS, objective="3", target=GENERAL)


def test_max_agents_enforced(data_dir: Path):
    cid = _collab(bounds={"max_agents": 2})
    engine.delegate(cid, requester=ANALYSIS, objective="1", target=RESEARCH)
    with pytest.raises(engine.BoundExceeded, match="max_agents"):
        engine.delegate(cid, requester=ANALYSIS, objective="2", target=CODING)


def test_max_depth_enforced(data_dir: Path):
    cid = _collab(bounds={"max_depth": 2})
    a = engine.delegate(cid, requester=ANALYSIS, objective="a", target=GENERAL)["id"]
    b = engine.delegate(cid, requester=ANALYSIS, objective="b", target=GENERAL, depends_on=[a])[
        "id"
    ]
    with pytest.raises(engine.BoundExceeded, match="max_depth"):
        engine.delegate(cid, requester=ANALYSIS, objective="c", target=GENERAL, depends_on=[b])


def test_recursive_delegation_cannot_run_away(data_dir: Path):
    """A specialist cannot spawn unlimited work: a bound always stops it."""
    cid = _collab(bounds={"max_tasks": 5, "max_depth": 10})
    created = 0
    with pytest.raises(engine.BoundExceeded):
        for i in range(50):
            engine.delegate(cid, requester=ANALYSIS, objective=f"t{i}", target=GENERAL)
            created += 1
    assert created == 5


def test_retry_budget_exhausts_into_failure(data_dir: Path):
    cid = _collab(bounds={"max_retries": 0})
    tid = store.add_task(
        cid, requester=ANALYSIS, target=ANALYSIS, objective="x", action="aria_self_fix"
    )
    engine.execute_task(tid)  # attempt 1 -> denied
    store.set_task_status(tid, store.TASK_PENDING)
    task = engine.execute_task(tid)
    assert task["status"] == store.TASK_FAILED
    assert "retry budget" in (task["error"] or "")


def test_bounds_defaults_are_conservative(data_dir: Path):
    assert engine.DEFAULT_BOUNDS["max_agents"] <= 6
    assert engine.DEFAULT_BOUNDS["max_depth"] <= 5
    assert engine.DEFAULT_BOUNDS["max_tasks"] <= 20


# ------------------------------------------------------------ results


def test_successful_task_produces_structured_result(data_dir: Path):
    cid = _collab()
    mid = missions.create_mission("target", steps=[])
    tid = store.add_task(
        cid,
        requester=ANALYSIS,
        target=RESEARCH,
        objective="check mission",
        action="mission_status",
        params={"mission_id": mid},
    )
    task = engine.execute_task(tid)
    assert task["status"] == store.TASK_SUCCESS
    result = task["result"]
    for key in ("task_id", "from_agent", "requested_by", "status", "output"):
        assert key in result
    assert result["from_agent"] == RESEARCH
    assert result["requested_by"] == ANALYSIS


def test_failed_inner_action_is_partial_not_success(data_dir: Path):
    """A delegated action that ran but reported failure must not read as success."""
    cid = _collab()
    tid = store.add_task(
        cid,
        requester=ANALYSIS,
        target=RESEARCH,
        objective="missing mission",
        action="mission_status",
        params={"mission_id": "does-not-exist"},
    )
    task = engine.execute_task(tid)
    assert task["status"] == store.TASK_PARTIAL


def test_downstream_receives_structured_upstream_results(data_dir: Path):
    cid = _collab()
    mid = missions.create_mission("t", steps=[])
    a = store.add_task(
        cid,
        requester=ANALYSIS,
        target=RESEARCH,
        objective="upstream",
        action="mission_status",
        params={"mission_id": mid},
    )
    engine.execute_task(a)
    b = store.add_task(
        cid, requester=ANALYSIS, target=ANALYSIS, objective="downstream", depends_on=[a]
    )
    context = engine._dependency_context(store.get_task(b), store.tasks(cid))
    assert context["inputs"][0]["from_agent"] == RESEARCH
    assert context["inputs"][0]["status"] == store.TASK_SUCCESS
    assert context["inputs"][0]["result"]["output"]["ok"] is True


def test_blocked_task_is_skipped_not_silently_dropped(data_dir: Path):
    cid = _collab()
    a = store.add_task(
        cid, requester=ANALYSIS, target=ANALYSIS, objective="will fail", action="aria_self_fix"
    )
    store.add_task(cid, requester=ANALYSIS, target=GENERAL, objective="downstream", depends_on=[a])
    engine.advance(cid)
    statuses = {t["objective"]: t["status"] for t in store.tasks(cid)}
    assert statuses["will fail"] == store.TASK_DENIED
    assert statuses["downstream"] == store.TASK_SKIPPED


# ------------------------------------------------------------ aggregation


def test_aggregation_preserves_attribution(data_dir: Path):
    cid = _collab("combined objective")
    mid = missions.create_mission("t", steps=[])
    for target in (RESEARCH, GENERAL):
        tid = store.add_task(
            cid,
            requester=ANALYSIS,
            target=target,
            objective=f"work for {target}",
            action="mission_status",
            params={"mission_id": mid},
        )
        engine.execute_task(tid)
    out = engine.aggregate(cid)
    assert out["succeeded"] == 2
    assert RESEARCH in out["synthesis"] and GENERAL in out["synthesis"]
    assert store.get(cid)["status"] == store.COMPLETED


def test_failed_delegation_does_not_yield_successful_collaboration(data_dir: Path):
    cid = _collab()
    tid = store.add_task(
        cid, requester=ANALYSIS, target=ANALYSIS, objective="bad", action="aria_self_fix"
    )
    engine.execute_task(tid)
    out = engine.aggregate(cid)
    assert out["failed"] == 1
    assert store.get(cid)["status"] == store.FAILED
    assert "Unresolved" in out["synthesis"]


def test_disagreement_between_specialists_preserved(data_dir: Path):
    cid = _collab()
    mid = missions.create_mission("t", steps=[])
    for target in (RESEARCH, GENERAL):
        tid = store.add_task(
            cid,
            requester=ANALYSIS,
            target=target,
            objective="same question",
            action="mission_status",
            params={"mission_id": mid},
        )
        engine.execute_task(tid)
    engine.aggregate(cid)
    rows = store.conflicts(cid)
    assert rows, "independent answers to the same question were not preserved"
    assert "2 specialists" in rows[0]["description"]


# ------------------------------------------------------------ missions


def test_collaboration_runs_through_the_mission_engine(data_dir: Path):
    cid = _collab()
    mid = store.get(cid)["mission_id"]
    target_mission = missions.create_mission("t", steps=[])
    a = engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="first",
        target=RESEARCH,
        action="mission_status",
        params={"mission_id": target_mission},
    )["id"]
    engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="second",
        target=GENERAL,
        action="mission_status",
        params={"mission_id": target_mission},
        depends_on=[a],
    )
    missions.run(mid, _runner())
    assert store.get(cid)["status"] == store.COMPLETED
    assert all(t["status"] == store.TASK_SUCCESS for t in store.tasks(cid))
    assert mstore.checkpoints(mid)


def test_collaboration_pause_resume_cancel(data_dir: Path):
    cid = _collab()
    mid = store.get(cid)["mission_id"]
    engine.delegate(cid, requester=ANALYSIS, objective="only", target=GENERAL)
    missions.run(mid, _runner(), max_steps=1)
    assert missions.get(mid)["state"] == mstore.PAUSED
    mstore.make_runnable(mid)
    missions.run(mid, _runner())
    assert missions.get(mid)["state"] == mstore.COMPLETED

    other = _collab("cancel me")
    assert missions.cancel(store.get(other)["mission_id"]) is True


def test_multiple_collaborations_do_not_interfere(data_dir: Path):
    a = _collab("A")
    b = _collab("B")
    mid = missions.create_mission("t", steps=[])
    engine.delegate(
        a,
        requester=ANALYSIS,
        objective="a work",
        target=RESEARCH,
        action="mission_status",
        params={"mission_id": mid},
    )
    engine.delegate(b, requester=ANALYSIS, objective="b bad", target=ANALYSIS, action="")
    store.set_task_status(store.tasks(b)[0]["id"], store.TASK_FAILED, error="boom")
    engine.advance(a)
    engine.aggregate(a)
    engine.aggregate(b)
    assert store.get(a)["status"] == store.COMPLETED
    assert store.get(b)["status"] == store.FAILED
    assert {t["collaboration_id"] for t in store.tasks(a)} == {a}
    assert {t["collaboration_id"] for t in store.tasks(b)} == {b}


# ------------------------------------------------------------ research/coding


def test_analysis_delegates_research_using_existing_engine(data_dir: Path, monkeypatch):
    from jarvis.research import engine as research_engine
    from jarvis.research import store as research_store

    monkeypatch.setattr(
        research_engine,
        "_default_search",
        lambda q, n: [{"url": "https://nasa.gov/a", "title": "A", "snippet": "supports"}],
    )
    monkeypatch.setattr(research_engine, "_default_fetch", lambda url: "body")

    cid = _collab("analysis needs research")
    tid = engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="research the topic",
        target=RESEARCH,
        action="research_create",
        params={"objective": "delegated research"},
    )["id"]
    task = engine.execute_task(tid)
    assert task["status"] == store.TASK_SUCCESS
    rid = task["result"]["output"]["research_id"]
    # Uses the one research store — no duplicate engine.
    assert research_store.get_job(rid)["objective"] == "delegated research"
    assert research_store.DB_PATH.name == "research.db"


def test_research_provenance_survives_delegation(data_dir: Path, monkeypatch):
    from jarvis.research import engine as research_engine

    monkeypatch.setattr(
        research_engine,
        "_default_search",
        lambda q, n: [
            {"url": "https://nasa.gov/a", "title": "A", "snippet": "supports"},
            {"url": "https://nih.gov/b", "title": "B", "snippet": "also supports"},
        ],
    )
    monkeypatch.setattr(research_engine, "_default_fetch", lambda url: "agreeing body")
    rid = research_engine.create_research("provenance")["research_id"]
    for phase in research_engine.PHASES:
        research_engine.run_phase(rid, phase)

    cid = _collab()
    tid = engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="report the research",
        target=RESEARCH,
        action="research_report",
        params={"research_id": rid},
    )["id"]
    task = engine.execute_task(tid)
    report = task["result"]["output"]["report"]
    assert report["claims"][0]["evidence"], "evidence lost through delegation"
    known = {s["url"] for s in report["sources"]}
    assert all(r["url"] in known for r in report["claims"][0]["evidence"])


def test_analysis_delegates_coding_task(data_dir: Path):
    cid = _collab("analysis needs code review")
    tid = engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="inspect the repository",
        target=CODING,
        action="git_status",
    )["id"]
    task = engine.execute_task(tid)
    assert task["result"]["from_agent"] == CODING
    assert task["status"] in (store.TASK_SUCCESS, store.TASK_PARTIAL)


def test_three_specialists_participate_and_aggregate(data_dir: Path):
    cid = _collab("multi-agent objective")
    mid = missions.create_mission("t", steps=[])
    for target in (RESEARCH, CODING, GENERAL):
        engine.delegate(
            cid,
            requester=ANALYSIS,
            objective=f"work for {target}",
            target=target,
            action="mission_status" if target != CODING else "git_status",
            params={"mission_id": mid} if target != CODING else {},
        )
    engine.advance(cid)
    out = engine.aggregate(cid)
    participants = set(engine.status(cid)["participants"])
    assert {RESEARCH, CODING, GENERAL} <= participants
    assert out["succeeded"] + out["partial"] >= 3


# ------------------------------------------------------------ handlers


def test_collaboration_actions_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {s["action"] for s in all_actions()}
    for action in (
        "collab_create",
        "collab_delegate",
        "collab_step",
        "collab_status",
        "collab_list",
        "collab_graph",
        "collab_report",
        "collab_pause",
        "collab_cancel",
        "collab_recover",
    ):
        assert action in names, f"{action} not registered"


def test_handler_round_trip(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    created = call_action(None, "collab_create", {"objective": "handler collab"}, "")
    assert created["ok"] is True
    cid = created["collaboration_id"]

    delegated = call_action(
        None,
        "collab_delegate",
        {
            "collaboration_id": cid,
            "requester": ANALYSIS,
            "objective": "sub task",
            "target": GENERAL,
        },
        "",
    )
    assert delegated["ok"] is True

    status = call_action(None, "collab_status", {"collaboration_id": cid}, "")
    assert status["ok"] is True
    assert status["collaboration"]["tasks"]["total"] == 1

    g = call_action(None, "collab_graph", {"collaboration_id": cid}, "")
    assert g["ok"] is True and g["graph"]["nodes"]

    listed = call_action(None, "collab_list", {}, "")
    assert any(c["id"] == cid for c in listed["collaborations"])


def test_handler_reports_denied_delegation(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    cid = _collab()
    out = call_action(
        None,
        "collab_delegate",
        {"collaboration_id": cid, "requester": CODING, "objective": "x", "target": GENERAL},
        "",
    )
    assert out["ok"] is False
    assert out["error_kind"] == "delegation_denied"


def test_module_reload_durability(data_dir: Path):
    import importlib

    cid = _collab("reload me")
    engine.delegate(cid, requester=ANALYSIS, objective="t", target=GENERAL)
    importlib.reload(store)
    assert store.get(cid)["objective"] == "reload me"
    assert len(store.tasks(cid)) == 1


# ------------------------------------------------------------ crash recovery

_CRASH = """
import os, sys
sys.path.insert(0, {repo!r})
os.environ["JARVIS_DATA_DIR"] = {data_dir!r}
from unittest.mock import MagicMock
sys.modules.setdefault("ollama", MagicMock())

from jarvis.collaboration import engine, store

cid = {cid!r}
first = {first!r}
engine.execute_task(first)
assert store.get_task(first)["status"] == store.TASK_SUCCESS
# Durable result written. Die before the remaining task runs.
os._exit(9)
"""


def test_collaboration_recovers_after_real_process_crash(data_dir: Path, tmp_path: Path):
    cid = _collab("crash collaboration")
    mid = missions.create_mission("t", steps=[])
    first = engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="first task",
        target=RESEARCH,
        action="mission_status",
        params={"mission_id": mid},
    )["id"]
    second = engine.delegate(
        cid,
        requester=ANALYSIS,
        objective="second task",
        target=GENERAL,
        action="mission_status",
        params={"mission_id": mid},
        depends_on=[first],
    )["id"]

    script = tmp_path / "crash_collab.py"
    script.write_text(
        textwrap.dedent(_CRASH).format(
            repo=str(REPO_ROOT), data_dir=str(data_dir), cid=cid, first=first
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["JARVIS_DATA_DIR"] = str(data_dir)
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120, env=env
    )
    assert proc.returncode == 9, f"child did not crash: {proc.stderr[-1500:]}"

    # The completed delegation survived the crash.
    assert store.get_task(first)["status"] == store.TASK_SUCCESS
    assert store.get_task(first)["result"]["from_agent"] == RESEARCH
    assert store.get_task(second)["status"] == store.TASK_PENDING

    attempts_before = store.get_task(first)["attempts"]
    engine.advance(cid)
    # The finished task was not re-run; the remaining one completed.
    assert store.get_task(first)["attempts"] == attempts_before
    assert store.get_task(second)["status"] == store.TASK_SUCCESS

    out = engine.aggregate(cid)
    assert out["succeeded"] == 2
    assert store.get(cid)["status"] == store.COMPLETED
