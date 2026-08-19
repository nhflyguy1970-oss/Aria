"""Autonomous workflows — graph, execution, durability, provenance, security."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from jarvis import autonomous_workflows as wf
from jarvis import specialized_agents as agents
from jarvis.autonomous_workflows import conditions, dispatch, graph, refs
from jarvis.autonomous_workflows import store as wf_store
from jarvis.specialized_agents import registry as agent_registry

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean():
    agent_registry.reset()
    yield
    agent_registry.reset()


def definition(**kw) -> dict:
    base = {
        "name": "test workflow",
        "steps": [{"step_id": "one", "action": "mission_list", "params": {"limit": 1}}],
    }
    base.update(kw)
    return base


def _call(action: str, params: dict, assistant=None):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return call_action(assistant, action, params, action)


# --------------------------------------------------------------- A/B: create


def test_a_workflow_creation(data_dir: Path):
    workflow = wf.create_workflow(definition(), requester="tester", create_mission=False)
    assert workflow["id"].startswith("wf_")
    assert workflow["state"] == wf.PENDING
    assert workflow["requester"] == "tester"
    assert len(workflow["steps"]) == 1


def test_b_persistence(data_dir: Path):
    workflow = wf.create_workflow(definition(inputs={"topic": "tides"}), create_mission=False)
    reloaded = wf.get(workflow["id"])
    assert reloaded["inputs"] == {"topic": "tides"}
    assert reloaded["definition"]["steps"][0]["action"] == "mission_list"
    assert data_dir in wf_store.DB_PATH.resolve().parents


def test_b2_events_are_recorded(data_dir: Path):
    workflow = wf.create_workflow(definition(), create_mission=False)
    wf.run(workflow["id"])
    kinds = [e["kind"] for e in wf.events(workflow["id"])]
    assert "created" in kinds
    assert "state" in kinds


# ------------------------------------------------------- C/D: state machine


def test_c_state_transitions(data_dir: Path):
    workflow = wf.create_workflow(definition(), create_mission=False)
    wid = workflow["id"]
    assert wf_store.set_state(wid, wf.RUNNING)["state"] == wf.RUNNING
    assert wf_store.set_state(wid, wf.PAUSED)["state"] == wf.PAUSED
    assert wf_store.set_state(wid, wf.RUNNING)["state"] == wf.RUNNING
    assert wf_store.set_state(wid, wf.COMPLETED)["state"] == wf.COMPLETED


def test_d_illegal_transitions_rejected(data_dir: Path):
    workflow = wf.create_workflow(definition(), create_mission=False)
    wid = workflow["id"]
    with pytest.raises(wf.WorkflowStateError, match="Illegal workflow transition"):
        wf_store.set_state(wid, wf.COMPLETED)  # pending cannot complete directly
    wf_store.set_state(wid, wf.RUNNING)
    wf_store.set_state(wid, wf.COMPLETED)
    with pytest.raises(wf.WorkflowStateError):
        wf_store.set_state(wid, wf.RUNNING)  # a finished workflow does not restart


def test_d2_unknown_state_rejected(data_dir: Path):
    workflow = wf.create_workflow(definition(), create_mission=False)
    with pytest.raises(wf.WorkflowStateError, match="Unknown workflow state"):
        wf_store.set_state(workflow["id"], "vibing")


# --------------------------------------------------------- E/F: graph safety


def test_e_graph_validation_rejects_unknown_dependency(data_dir: Path):
    bad = definition(
        steps=[
            {"step_id": "one", "action": "mission_list", "depends_on": ["ghost"]},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert report["ok"] is False
    assert any("unknown step" in p for p in report["problems"])


def test_e2_self_dependency_rejected(data_dir: Path):
    bad = definition(
        steps=[
            {"step_id": "one", "action": "mission_list", "depends_on": ["one"]},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("depends on itself" in p for p in report["problems"])


def test_e3_duplicate_step_ids_rejected(data_dir: Path):
    bad = definition(
        steps=[
            {"step_id": "one", "action": "mission_list"},
            {"step_id": "one", "action": "mission_list"},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("duplicate step_id" in p for p in report["problems"])


def test_f_cycle_detection(data_dir: Path):
    bad = definition(
        steps=[
            {"step_id": "a", "action": "mission_list", "depends_on": ["b"]},
            {"step_id": "b", "action": "mission_list", "depends_on": ["a"]},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("cycle" in p for p in report["problems"])
    with pytest.raises(wf.WorkflowDefinitionError):
        wf.create_workflow(bad, create_mission=False)


def test_f2_indirect_cycle_detection(data_dir: Path):
    edges = {"a": ["b"], "b": ["c"], "c": ["a"]}
    assert wf.detect_cycle(edges) is not None
    assert wf.detect_cycle({"a": ["b"], "b": ["c"], "c": []}) is None


def test_f3_deep_chain_is_iterative(data_dir: Path):
    """A chain far deeper than the recursion limit must validate, not crash."""
    steps = [{"step_id": "s0", "action": "mission_list"}]
    for i in range(1, 500):
        steps.append({"step_id": f"s{i}", "action": "mission_list", "depends_on": [f"s{i - 1}"]})
    edges = {s["step_id"]: list(s.get("depends_on") or []) for s in steps}
    assert wf.detect_cycle(edges) is None
    assert graph.depth_of(edges) == 500


def test_f4_depth_limit_enforced(data_dir: Path):
    steps = [{"step_id": "s0", "action": "mission_list"}]
    for i in range(1, wf.LIMITS["max_depth"] + 4):
        steps.append({"step_id": f"s{i}", "action": "mission_list", "depends_on": [f"s{i - 1}"]})
    report = wf.validate(wf.WorkflowDefinition.from_dict(definition(steps=steps)))
    assert any("exceeds max_depth" in p for p in report["problems"])


# ------------------------------------------------------- G/H/I: execution


def test_g_sequential_execution(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "first", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "second",
                    "action": "mission_list",
                    "depends_on": ["first"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    assert final["state"] == wf.COMPLETED
    states = wf_store.step_states(workflow["id"])
    assert states == {"first": wf.STEP_SUCCEEDED, "second": wf.STEP_SUCCEEDED}


def test_h_dependency_fan_in(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {"step_id": "b", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "join",
                    "action": "mission_list",
                    "depends_on": ["a", "b"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    assert final["state"] == wf.COMPLETED
    order = wf.order_steps(wf.WorkflowDefinition.from_dict(final["definition"]))
    assert order.index("join") > order.index("a")
    assert order.index("join") > order.index("b")


def test_i_blocked_dependency(data_dir: Path):
    """A failed dependency blocks its dependent — it does not fail it."""
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
                {
                    "step_id": "after",
                    "action": "mission_list",
                    "depends_on": ["boom"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    states = wf_store.step_states(workflow["id"])
    assert states["boom"] == wf.STEP_FAILED
    assert states["after"] == wf.STEP_BLOCKED
    assert final["state"] == wf.FAILED


def test_i2_skip_policy(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
                {
                    "step_id": "after",
                    "action": "mission_list",
                    "depends_on": ["boom"],
                    "on_dependency_failure": "skip",
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    assert wf_store.step_states(workflow["id"])["after"] == wf.STEP_SKIPPED


def test_i3_run_anyway_policy(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
                {
                    "step_id": "after",
                    "action": "mission_list",
                    "depends_on": ["boom"],
                    "on_dependency_failure": "run_anyway",
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    assert wf_store.step_states(workflow["id"])["after"] == wf.STEP_SUCCEEDED


# --------------------------------------------------- J/K: failure and partial


def test_j_failure_propagation_is_truthful(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "ok", "action": "mission_list", "params": {"limit": 1}},
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    # Some work succeeded and some failed: that is partial, never success.
    assert final["state"] == wf.PARTIAL
    snapshot = wf.status(workflow["id"])
    assert snapshot["partial"] is True
    assert snapshot["succeeded"] == 1 and snapshot["failed"] == 1


def test_j2_all_failed_is_failed(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
            ]
        ),
        create_mission=False,
    )
    assert wf.run(workflow["id"])["state"] == wf.FAILED


def test_j3_action_reporting_failure_is_not_success(data_dir: Path):
    """An action that ran and returned ok=False is a failed step."""
    outcome = dispatch.dispatch(
        wf.StepDefinition(step_id="x", action="mission_status"),
        {"mission_id": "does_not_exist"},
    )
    assert outcome["status"] == dispatch.FAILED
    assert outcome["output"] is None


def test_k_partial_results_are_preserved(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "good", "action": "mission_list", "params": {"limit": 1}},
                {"step_id": "bad", "action": "mission_status", "params": {"mission_id": "nope"}},
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    stored = wf.get(workflow["id"])
    good = [s for s in stored["steps"] if s["step_id"] == "good"][0]
    bad = [s for s in stored["steps"] if s["step_id"] == "bad"][0]
    assert good["output"] is not None
    assert bad["error"]
    assert stored["outputs"].get("good") is not None


def test_k2_optional_failure_still_completes(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "good", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "meh",
                    "action": "mission_status",
                    "params": {"mission_id": "nope"},
                    "optional": True,
                },
            ]
        ),
        create_mission=False,
    )
    assert wf.run(workflow["id"])["state"] == wf.PARTIAL


# ------------------------------------------------------- L/M/N: retry, cancel


def test_l_retry_on_retryable_failure(data_dir: Path, monkeypatch):
    attempts = []

    def flaky(step, params, **kw):
        attempts.append(step.step_id)
        if len(attempts) < 2:
            return {
                "status": dispatch.FAILED,
                "step_id": step.step_id,
                "action": step.action,
                "error": "transient",
                "error_kind": "exception",
                "retryable": True,
                "output": None,
                "provenance": {},
                "duration_ms": 1.0,
            }
        return {
            "status": dispatch.OK,
            "step_id": step.step_id,
            "action": step.action,
            "output": {"ok": True},
            "error": None,
            "error_kind": "",
            "retryable": False,
            "provenance": {},
            "duration_ms": 1.0,
        }

    monkeypatch.setattr(dispatch, "dispatch", flaky)
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "flaky", "action": "mission_list", "max_retries": 2},
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    assert final["state"] == wf.COMPLETED
    assert len(attempts) == 2
    stored = wf.get(workflow["id"])["steps"][0]
    assert stored["attempts"] == 2


def test_l2_permission_denial_is_never_retried(data_dir: Path, monkeypatch):
    """A refusal is a decision; retrying would try to talk it out of it."""
    attempts = []

    def denied(step, params, **kw):
        attempts.append(step.step_id)
        return {
            "status": dispatch.DENIED,
            "step_id": step.step_id,
            "action": step.action,
            "error": "not permitted",
            "error_kind": "permission_denied",
            "retryable": False,
            "output": None,
            "provenance": {},
            "duration_ms": 1.0,
        }

    monkeypatch.setattr(dispatch, "dispatch", denied)
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "nope", "action": "mission_list", "max_retries": 2},
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    assert len(attempts) == 1


def test_m_timeout_is_recorded_as_timed_out(data_dir: Path, monkeypatch):
    def slow(step, params, **kw):
        return {
            "status": dispatch.TIMED_OUT,
            "step_id": step.step_id,
            "action": step.action,
            "error": "took too long",
            "error_kind": "timeout",
            "retryable": False,
            "output": None,
            "provenance": {},
            "duration_ms": 1.0,
        }

    monkeypatch.setattr(dispatch, "dispatch", slow)
    workflow = wf.create_workflow(definition(), create_mission=False)
    final = wf.run(workflow["id"])
    assert wf_store.step_states(workflow["id"])["one"] == wf.STEP_TIMED_OUT
    assert final["state"] == wf.FAILED, "a timed-out workflow must not read as successful"


def test_n_cancellation_stops_queued_work(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "b",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "params": {"limit": 1},
                },
                {
                    "step_id": "c",
                    "action": "mission_list",
                    "depends_on": ["b"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wid = workflow["id"]
    wf.run_slice(wid, max_steps=1)  # a succeeds
    wf.cancel(wid)
    states = wf_store.step_states(wid)
    assert states["a"] == wf.STEP_SUCCEEDED
    assert states["b"] == wf.STEP_CANCELLED
    assert states["c"] == wf.STEP_CANCELLED
    assert wf.get(wid)["state"] == wf.CANCELLED


def test_n2_cancelled_workflow_does_not_resume(data_dir: Path):
    workflow = wf.create_workflow(definition(), create_mission=False)
    wf.cancel(workflow["id"])
    result = wf.run(workflow["id"])
    assert result["state"] == wf.CANCELLED
    assert wf_store.step_states(workflow["id"])["one"] != wf.STEP_SUCCEEDED


def test_n3_cancellation_propagates_to_the_mission(data_dir: Path):

    workflow = wf.create_workflow(definition(), create_mission=True)
    mission_id = workflow["mission_id"]
    assert mission_id
    wf.cancel(workflow["id"])
    from jarvis.missions import store as mstore

    assert mstore.cancel_requested(mission_id) is True


# --------------------------------------------------------- O/P/Q: durability


def test_o_pause_and_resume(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
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
    wf.run_slice(wid, max_steps=1)
    wf.pause(wid)
    assert wf.get(wid)["state"] == wf.PAUSED

    # A paused workflow starts no new work.
    wf.run_slice(wid)
    assert wf_store.step_states(wid)["b"] == wf.STEP_PENDING

    wf.resume(wid)
    assert wf.get(wid)["state"] == wf.COMPLETED
    assert wf_store.step_states(wid)["b"] == wf.STEP_SUCCEEDED


def test_o2_resume_requires_a_paused_workflow(data_dir: Path):
    workflow = wf.create_workflow(definition(), create_mission=False)
    with pytest.raises(wf.WorkflowStateError, match="not paused"):
        wf.resume(workflow["id"])


def test_q_recovery_does_not_repeat_completed_work(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
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
    wf.run_slice(wid, max_steps=1)
    # Simulate a process dying mid-step.
    wf_store.set_step(wid, "b", state=wf.STEP_RUNNING)
    wf_store.set_state(wid, wf.RUNNING)

    recovered = wf.recover()
    assert wid in recovered
    states = wf_store.step_states(wid)
    assert states["a"] == wf.STEP_SUCCEEDED, "completed work was undone"
    assert states["b"] == wf.STEP_PENDING, "an interrupted step must be retried"

    assert wf.run(wid)["state"] == wf.COMPLETED
    stored = {s["step_id"]: s for s in wf.get(wid)["steps"]}
    assert stored["a"]["attempts"] == 1, "a completed step was run twice"


def test_p_crash_recovery_across_a_real_process(data_dir: Path):
    """A workflow interrupted by os._exit(9) survives and resumes."""
    script = textwrap.dedent(f"""
        import os, sys
        sys.path.insert(0, {str(REPO_ROOT)!r})
        os.environ["JARVIS_DATA_DIR"] = {str(data_dir)!r}
        from unittest.mock import MagicMock
        sys.modules.setdefault("ollama", MagicMock())
        from jarvis import autonomous_workflows as wf
        from jarvis.autonomous_workflows import store as s
        w = wf.create_workflow({{
            "name": "crash probe",
            "steps": [
                {{"step_id": "a", "action": "mission_list", "params": {{"limit": 1}}}},
                {{"step_id": "b", "action": "mission_list", "depends_on": ["a"],
                  "params": {{"limit": 1}}}},
            ],
        }}, create_mission=False)
        wf.run_slice(w["id"], max_steps=1)
        s.set_step(w["id"], "b", state="running")
        print(w["id"], flush=True)
        os._exit(9)
    """)
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=180
    )
    assert proc.returncode == 9, proc.stderr[-500:]
    workflow_id = proc.stdout.strip().splitlines()[-1]

    assert wf.get(workflow_id) is not None, "workflow did not survive the crash"
    assert wf_store.step_states(workflow_id)["a"] == wf.STEP_SUCCEEDED

    assert workflow_id in wf.recover()
    final = wf.run(workflow_id)
    assert final["state"] == wf.COMPLETED
    stored = {s["step_id"]: s for s in wf.get(workflow_id)["steps"]}
    assert stored["a"]["attempts"] == 1, "recovery repeated completed work"


# --------------------------------------------------- R/S/T: data and conditions


def test_r_workflow_inputs_reach_steps(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            inputs={"how_many": 2},
            steps=[
                {
                    "step_id": "one",
                    "action": "mission_list",
                    "params": {"limit": "${input.how_many}"},
                }
            ],
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    assert wf_store.step_states(workflow["id"])["one"] == wf.STEP_SUCCEEDED


def test_s_step_outputs_feed_later_steps(data_dir: Path):
    resolved = refs.resolve_params(
        {"value": "${steps.first.output.count}", "text": "count is ${steps.first.output.count}"},
        inputs={},
        context={},
        step_outputs={"first": {"output": {"count": 7}, "state": "succeeded"}},
    )
    assert resolved["value"] == 7  # whole-string reference keeps its type
    assert resolved["text"] == "count is 7"


def test_s2_output_reference_requires_a_declared_dependency(data_dir: Path):
    """Otherwise the value may simply not exist yet when the step runs."""
    bad = definition(
        steps=[
            {"step_id": "a", "action": "mission_list"},
            {"step_id": "b", "action": "mission_list", "params": {"x": "${steps.a.output.foo}"}},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("without depending on it" in p for p in report["problems"])


def test_s3_unknown_reference_rejected_at_validation(data_dir: Path):
    bad = definition(
        steps=[
            {"step_id": "a", "action": "mission_list", "params": {"x": "${steps.ghost.output.y}"}},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("unknown step" in p for p in report["problems"])


def test_t_conditional_step_runs_and_skips(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            inputs={"deep": False},
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "extra",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "condition": {"op": "truthy", "ref": "${input.deep}"},
                    "params": {"limit": 1},
                },
            ],
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    assert wf_store.step_states(workflow["id"])["extra"] == wf.STEP_SKIPPED

    workflow2 = wf.create_workflow(
        definition(
            inputs={"deep": True},
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "extra",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "condition": {"op": "truthy", "ref": "${input.deep}"},
                    "params": {"limit": 1},
                },
            ],
        ),
        create_mission=False,
    )
    wf.run(workflow2["id"])
    assert wf_store.step_states(workflow2["id"])["extra"] == wf.STEP_SUCCEEDED


def test_t2_condition_operators(data_dir: Path):
    ctx = {
        "inputs": {"n": 5, "name": "aria", "tags": ["a", "b"]},
        "context": {},
        "step_outputs": {},
    }

    def ev(cond):
        return conditions.evaluate(cond, **ctx)

    assert ev({"op": "equals", "ref": "${input.name}", "value": "aria"}) is True
    assert ev({"op": "not_equals", "ref": "${input.name}", "value": "other"}) is True
    assert ev({"op": "greater_than", "ref": "${input.n}", "value": 3}) is True
    assert ev({"op": "less_than", "ref": "${input.n}", "value": 3}) is False
    assert ev({"op": "contains", "ref": "${input.tags}", "value": "a"}) is True
    assert ev({"op": "exists", "ref": "${input.n}"}) is True
    assert ev({"op": "missing", "ref": "${input.ghost}"}) is True
    assert (
        ev(
            {
                "op": "all_of",
                "conditions": [
                    {"op": "truthy", "ref": "${input.n}"},
                    {"op": "exists", "ref": "${input.name}"},
                ],
            }
        )
        is True
    )
    assert (
        ev(
            {
                "op": "any_of",
                "conditions": [
                    {"op": "missing", "ref": "${input.n}"},
                    {"op": "exists", "ref": "${input.name}"},
                ],
            }
        )
        is True
    )
    assert ev({"op": "not", "condition": {"op": "missing", "ref": "${input.n}"}}) is True


def test_t3_comparison_against_missing_data_is_false_not_an_error(data_dir: Path):
    assert (
        conditions.evaluate(
            {"op": "equals", "ref": "${steps.nope.output.x}", "value": 1},
            inputs={},
            context={},
            step_outputs={},
        )
        is False
    )


# ------------------------------------------------------------ U: bounds


def test_u_step_count_bound(data_dir: Path):
    steps = [
        {"step_id": f"s{i}", "action": "mission_list"} for i in range(wf.LIMITS["max_steps"] + 5)
    ]
    report = wf.validate(wf.WorkflowDefinition.from_dict(definition(steps=steps)))
    assert any("exceeds max_steps" in p for p in report["problems"])


def test_u2_a_workflow_may_tighten_a_limit_never_raise_it(data_dir: Path):
    parsed = wf.WorkflowDefinition.from_dict(definition(limits={"max_steps": 999999}))
    assert parsed.limit("max_steps") == wf.LIMITS["max_steps"]
    tighter = wf.WorkflowDefinition.from_dict(definition(limits={"max_steps": 2}))
    assert tighter.limit("max_steps") == 2


def test_u3_action_budget_stops_a_runaway_workflow(data_dir: Path):
    steps = [{"step_id": "s0", "action": "mission_list", "params": {"limit": 1}}]
    for i in range(1, 6):
        steps.append(
            {
                "step_id": f"s{i}",
                "action": "mission_list",
                "depends_on": [f"s{i - 1}"],
                "params": {"limit": 1},
            }
        )
    workflow = wf.create_workflow(
        definition(steps=steps, limits={"max_tool_calls": 3}), create_mission=False
    )
    final = wf.run(workflow["id"])
    assert final["state"] in (wf.PARTIAL, wf.FAILED, wf.BLOCKED)
    snapshot = wf.status(workflow["id"])
    assert snapshot["usage"]["actions"] <= 4
    assert snapshot["succeeded"] < len(steps)


def test_u4_retry_bound_is_capped(data_dir: Path):
    bad = definition(steps=[{"step_id": "a", "action": "mission_list", "max_retries": 99}])
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("max_retries" in p for p in report["problems"])


def test_u5_reference_values_are_bounded(data_dir: Path):
    huge = "x" * (refs.MAX_VALUE_BYTES + 5000)
    resolved = refs.resolve_params(
        "${steps.a.output.text}",
        inputs={},
        context={},
        step_outputs={"a": {"output": {"text": huge}, "state": "succeeded"}},
    )
    assert len(resolved) <= refs.MAX_VALUE_BYTES


# ------------------------------------------------ V/W: agents, collaboration


def test_v_agent_step_runs_under_the_agent(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {
                    "step_id": "ask",
                    "action": "mission_status",
                    "agent_id": "research_specialist",
                    "params": {"mission_id": "nope"},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    stored = wf.get(workflow["id"])["steps"][0]
    # The action ran under the agent and reported its own failure honestly.
    assert stored["state"] == wf.STEP_FAILED
    assert stored["agent_id"] == "research_specialist"


def test_v2_agent_permission_is_checked_at_validation(data_dir: Path):
    """An impossible workflow never starts and then fails half way through."""
    bad = definition(
        steps=[
            {"step_id": "x", "action": "dev_task_create", "agent_id": "research_specialist"},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("may not invoke" in p for p in report["problems"])
    with pytest.raises(wf.WorkflowDefinitionError, match="may not invoke"):
        wf.create_workflow(bad, create_mission=False)


def test_v3_unknown_agent_rejected(data_dir: Path):
    bad = definition(
        steps=[
            {"step_id": "x", "action": "mission_list", "agent_id": "ghost_specialist"},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("unknown agent" in p for p in report["problems"])


def test_w_different_agents_in_one_workflow(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {
                    "step_id": "research",
                    "action": "mission_status",
                    "agent_id": "research_specialist",
                    "params": {"mission_id": "x"},
                },
                {
                    "step_id": "analysis",
                    "action": "mission_status",
                    "agent_id": "analysis_specialist",
                    "params": {"mission_id": "x"},
                    "on_dependency_failure": "run_anyway",
                    "depends_on": ["research"],
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    stored = {s["step_id"]: s for s in wf.get(workflow["id"])["steps"]}
    assert stored["research"]["agent_id"] == "research_specialist"
    assert stored["analysis"]["agent_id"] == "analysis_specialist"


# --------------------------------------------- X-AD: subsystem integration


def test_x_research_capability_is_reachable(data_dir: Path):
    parsed = wf.WorkflowDefinition.from_dict(
        wf.instantiate("research_with_evidence", {"objective": "tides"})
    )
    report = wf.validate(parsed)
    assert report["ok"] is True, report["problems"]


def test_ab_skill_workflow_validates(data_dir: Path):
    parsed = wf.WorkflowDefinition.from_dict(wf.instantiate("coding_task", {"task_id": "cod_x"}))
    assert wf.validate(parsed)["ok"] is True


def test_ad_model_routing_workflow_validates(data_dir: Path):
    parsed = wf.WorkflowDefinition.from_dict(
        wf.instantiate("routed_answer", {"question": "what is a tide?"})
    )
    assert wf.validate(parsed)["ok"] is True


def test_ad2_model_routed_step_records_the_model(data_dir: Path, monkeypatch):
    import importlib

    mr_execute = importlib.import_module("jarvis.model_routing.execute")
    from jarvis.model_routing import capabilities as caps
    from jarvis.model_routing import health, profiles
    from jarvis.model_routing.profiles import ModelProfile

    profiles.reset()
    health.reset()
    profiles.register_profile(
        ModelProfile(
            provider="ollama",
            model_id="tiny:1b",
            capabilities={
                caps.GENERAL_CHAT: caps.SUPPORTED,
                caps.LOCAL_ONLY: caps.SUPPORTED,
                caps.STRUCTURED_OUTPUT: caps.SUPPORTED,
            },
            capability_evidence={},
            context_window=32768,
            parameter_size_b=1.0,
        )
    )
    monkeypatch.setattr(mr_execute, "default_invoker", lambda m, p: "hello from " + m)

    workflow = wf.create_workflow(
        definition(
            steps=[
                {
                    "step_id": "answer",
                    "action": "model_execute",
                    "agent_id": "general_specialist",
                    "params": {"prompt": "hi", "latency_preference": "fast"},
                },
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    stored = wf.get(workflow["id"])["steps"][0]
    assert stored["state"] == wf.STEP_SUCCEEDED
    assert stored["provenance"].get("model") == "tiny:1b"
    profiles.reset()
    health.reset()


# ------------------------------------------------------------- AE: provenance


def test_ae_provenance_records_the_chain(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
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
    snapshot = wf.status(workflow["id"])
    entry = snapshot["provenance"][0]
    assert entry["step_id"] == "one"
    assert entry["action"] == "mission_list"
    assert entry["agent"] == "general_specialist"
    assert entry["state"] == wf.STEP_SUCCEEDED


def test_ae2_missing_provenance_is_recorded_honestly(data_dir: Path):
    """A capability that reports nothing must not be given invented provenance."""
    outcome = dispatch.dispatch(wf.StepDefinition(step_id="x", action="mission_list"), {"limit": 1})
    assert outcome["status"] == dispatch.OK
    assert outcome["provenance"]["note"] == "capability reported no provenance"


# ------------------------------------------------ AL/AM: malformed and missing


def test_al_malformed_definition_rejected(data_dir: Path):
    with pytest.raises(wf.WorkflowDefinitionError):
        wf.WorkflowDefinition.from_dict({"name": "x"})  # no steps list
    with pytest.raises(wf.WorkflowDefinitionError):
        wf.create_workflow({"name": "", "steps": []}, create_mission=False)


def test_am_unavailable_capability_rejected_before_running(data_dir: Path):
    bad = definition(steps=[{"step_id": "x", "action": "no_such_action_at_all"}])
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("unknown ARIA action" in p for p in report["problems"])
    with pytest.raises(wf.WorkflowDefinitionError):
        wf.create_workflow(bad, create_mission=False)


def test_am2_capability_that_vanishes_is_reported_not_retried(data_dir: Path):
    outcome = dispatch.dispatch(wf.StepDefinition(step_id="x", action="vanished_action"), {})
    assert outcome["status"] == dispatch.UNAVAILABLE
    assert outcome["retryable"] is False


# ------------------------------------------------------------- AI: templates


def test_ai_templates_are_versioned_and_validated(data_dir: Path):
    listed = wf.list_templates()
    assert listed
    for meta in listed:
        template = wf.get_template(meta["template_id"])
        assert template["template_version"] == wf.TEMPLATE_VERSION
        parsed = wf.WorkflowDefinition.from_dict(template)
        report = wf.validate(parsed)
        assert report["ok"] is True, (meta["template_id"], report["problems"])


def test_ai2_instantiating_does_not_mutate_the_template(data_dir: Path):
    first = wf.instantiate("routed_answer", {"question": "a"})
    first["steps"][0]["params"]["prompt"] = "tampered"
    second = wf.instantiate("routed_answer", {"question": "b"})
    assert second["steps"][0]["params"].get("prompt") != "tampered"


def test_ai3_unknown_template_rejected(data_dir: Path):
    with pytest.raises(KeyError):
        wf.instantiate("no_such_template", {})


# ---------------------------------------------------------- AF/AG: security


def test_security_1_workflow_cannot_grant_an_agent_new_permissions(data_dir: Path):
    coder = agents.get("coding_specialist")
    before = (set(coder.allowed_actions), set(coder.denied_actions))
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "x", "action": "dev_task_list", "agent_id": "coding_specialist"},
            ]
        ),
        create_mission=False,
    )
    wf.run(workflow["id"])
    after = agents.get("coding_specialist")
    assert (set(after.allowed_actions), set(after.denied_actions)) == before


def test_security_2_workflow_cannot_bypass_agent_restrictions(data_dir: Path):
    """Even if validation were skipped, dispatch still goes through the agent."""
    outcome = dispatch.dispatch(
        wf.StepDefinition(step_id="x", action="dev_task_create", agent_id="research_specialist"),
        {"objective": "x", "workspace": "/tmp"},
    )
    assert outcome["status"] == dispatch.DENIED
    assert outcome["error_kind"] == "permission_denied"


def test_security_3_workflow_cannot_bypass_skill_restrictions(data_dir: Path):
    from jarvis import skills

    skills.ensure_catalog_loaded()
    outcome = dispatch.dispatch(
        wf.StepDefinition(step_id="x", action="skill_invoke", agent_id="general_specialist"),
        {"skill_id": "prepare_commit", "inputs": {"task_id": "x", "message": "m"}},
    )
    assert outcome["status"] in (dispatch.DENIED, dispatch.FAILED)
    assert outcome["output"] is None


def test_security_4_workflow_cannot_bypass_mcp_policy(data_dir: Path):
    outcome = dispatch.dispatch(
        wf.StepDefinition(step_id="x", action="mcp_invoke", agent_id="research_specialist"),
        {"provider_id": "never_registered", "tool": "anything"},
    )
    assert outcome["status"] in (dispatch.UNAVAILABLE, dispatch.FAILED, dispatch.DENIED)
    assert outcome["output"] is None


def test_security_5_workflow_cannot_bypass_browser_safety(data_dir: Path):
    """Browser gates belong to the coding specialist's denied list, not the workflow."""
    bad = definition(
        steps=[
            {"step_id": "x", "action": "browser_use_act", "agent_id": "coding_specialist"},
        ]
    )
    report = wf.validate(wf.WorkflowDefinition.from_dict(bad))
    assert any("may not invoke" in p for p in report["problems"])


def test_security_6_workflow_cannot_bypass_coding_confinement(data_dir: Path):
    """The coding agent's own workspace rules still apply to a workflow step."""
    outcome = dispatch.dispatch(
        wf.StepDefinition(step_id="x", action="dev_command", agent_id="coding_specialist"),
        {"task_id": "no_such_task", "argv": ["rm", "-rf", "/"]},
    )
    assert outcome["status"] != dispatch.OK
    assert outcome["output"] is None


def test_security_7_workflow_cannot_override_routing_hard_requirements(data_dir: Path):
    from jarvis.model_routing import capabilities as caps
    from jarvis.model_routing import health, profiles
    from jarvis.model_routing.profiles import ModelProfile

    profiles.reset()
    health.reset()
    profiles.register_profile(
        ModelProfile(
            provider="ollama",
            model_id="textonly:7b",
            capabilities={
                caps.GENERAL_CHAT: caps.SUPPORTED,
                caps.VISION: caps.UNSUPPORTED,
                caps.LOCAL_ONLY: caps.SUPPORTED,
            },
            capability_evidence={},
            context_window=32768,
        )
    )
    outcome = dispatch.dispatch(
        wf.StepDefinition(step_id="x", action="model_route"),
        {"require_vision": True},
    )
    assert outcome["status"] != dispatch.OK, "routing let a workflow past a hard requirement"
    profiles.reset()
    health.reset()


def test_security_8_conditions_cannot_execute_python(data_dir: Path):
    """A condition is an object, never a string of code."""
    for hostile in (
        {"op": "__import__('os').system('touch /tmp/pwned')"},
        {"op": "equals", "ref": "__import__('os')", "value": 1},
        {"op": "eval", "ref": "${input.x}", "value": 1},
    ):
        with pytest.raises(conditions.ConditionError):
            conditions.validate(hostile)


def test_security_9_references_cannot_reach_the_filesystem_or_objects(data_dir: Path):
    for hostile in (
        "${file./etc/passwd}",
        "${os.environ}",
        "${input.__class__}",
    ):
        with pytest.raises(refs.ReferenceError):
            refs.resolve_reference(hostile, inputs={"x": 1}, context={}, step_outputs={})

    # A path into a live object is refused rather than followed.
    class Sneaky:
        secret = "nope"

    with pytest.raises(refs.ReferenceError, match="cannot index into"):
        refs.resolve_reference(
            "${input.obj.secret}", inputs={"obj": Sneaky()}, context={}, step_outputs={}
        )


def test_security_10_recursion_is_bounded(data_dir: Path):
    """A workflow cannot spawn workflows without limit."""
    bad = definition(
        steps=[
            {
                "step_id": "spawn",
                "action": "workflow_create",
                "params": {"template_id": "routed_answer"},
            },
        ]
    )
    # Creating one is allowed; the bounds are what stop an explosion.
    parsed = wf.WorkflowDefinition.from_dict(bad)
    assert parsed.limit("max_steps") <= wf.LIMITS["max_steps"]
    assert parsed.limit("max_depth") <= wf.LIMITS["max_depth"]


def test_security_11_cancellation_does_not_trigger_hidden_work(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
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
    wf.cancel(wid)
    before = wf.get(wid)["usage"].get("actions", 0)
    wf.run(wid)
    assert wf.get(wid)["usage"].get("actions", 0) == before, "work ran after cancellation"
    assert wf.get(wid)["state"] == wf.CANCELLED


def test_security_12_failed_work_cannot_become_success(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
            ]
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    assert final["state"] != wf.COMPLETED
    assert wf.status(workflow["id"])["succeeded"] == 0


# --------------------------------------------------------------- actions/API


def test_workflow_actions_are_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {a["action"] for a in all_actions()}
    for action in (
        "workflow_create",
        "workflow_validate",
        "workflow_status",
        "workflow_index",
        "workflow_start",
        "workflow_pause",
        "workflow_resume",
        "workflow_cancel",
        "workflow_recover",
        "workflow_templates",
        "workflow_events",
        "workflow_step",
    ):
        assert action in names, action


def test_older_workflow_actions_still_exist(data_dir: Path):
    """The learned-workflow system keeps its own action names."""
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {a["action"] for a in all_actions()}
    for action in ("workflow_list", "workflow_run", "workflow_scan", "workflow_show"):
        assert action in names, action


def test_earlier_milestone_actions_survive(data_dir: Path):
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
    ):
        assert action in names, action


def test_create_and_run_through_actions(data_dir: Path):
    created = _call(
        "workflow_create",
        {
            "definition": definition(
                steps=[
                    {"step_id": "one", "action": "mission_list", "params": {"limit": 1}},
                ]
            ),
            "mission": False,
        },
    )
    assert created["ok"] is True
    wid = created["workflow_id"]
    started = _call("workflow_start", {"workflow_id": wid})
    assert started["ok"] is True
    assert started["workflow"]["state"] == wf.COMPLETED
    status = _call("workflow_status", {"workflow_id": wid})
    assert status["workflow"]["succeeded"] == 1


def test_validate_action_rejects_a_bad_definition(data_dir: Path):
    out = _call(
        "workflow_validate",
        {
            "definition": definition(
                steps=[
                    {"step_id": "a", "action": "mission_list", "depends_on": ["ghost"]},
                ]
            )
        },
    )
    assert out["ok"] is False
    assert out["error_kind"] == "invalid_definition"
    assert out["report"]["problems"]


def test_template_action_and_creation(data_dir: Path):
    listed = _call("workflow_templates", {})
    assert listed["ok"] is True
    assert listed["templates"]
    created = _call(
        "workflow_create",
        {
            "template_id": "routed_answer",
            "inputs": {"question": "hi"},
            "mission": False,
        },
    )
    assert created["ok"] is True


def test_lifecycle_actions(data_dir: Path):
    created = _call(
        "workflow_create",
        {
            "definition": definition(
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
            "mission": False,
        },
    )
    wid = created["workflow_id"]
    assert _call("workflow_pause", {"workflow_id": wid})["ok"] is True
    assert _call("workflow_resume", {"workflow_id": wid})["ok"] is True
    assert _call("workflow_cancel", {"workflow_id": wid})["ok"] is True
    assert _call("workflow_index", {})["ok"] is True
    assert _call("workflow_events", {"workflow_id": wid})["ok"] is True
    assert _call("workflow_recover", {})["ok"] is True


def test_actions_report_unknown_workflows(data_dir: Path):
    for action in ("workflow_status", "workflow_start", "workflow_pause", "workflow_cancel"):
        out = _call(action, {"workflow_id": "wf_does_not_exist"})
        assert out["ok"] is False, action
        assert out["error_kind"] == "not_found", action


# ------------------------------------------------- AH: mission-backed running


def test_ah_workflow_runs_through_the_mission_worker(data_dir: Path):
    from jarvis import missions

    created = wf.create_workflow(
        definition(
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
    mission_id = created["mission_id"]
    assert mission_id

    missions.run(mission_id, missions.ActionStepRunner(None))
    assert wf.get(created["id"])["state"] == wf.COMPLETED
    assert missions.checkpoints(mission_id), "no mission checkpoint was written"


def test_ah2_failed_workflow_does_not_complete_its_mission(data_dir: Path):
    from jarvis import missions

    created = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "boom", "action": "mission_status", "params": {"mission_id": "nope"}},
            ]
        ),
        create_mission=True,
    )
    missions.run(created["mission_id"], missions.ActionStepRunner(None))
    assert missions.status(created["mission_id"])["state"] != missions.COMPLETED


def test_ah3_cancelled_workflow_lands_its_mission_cancelled(data_dir: Path):
    from jarvis import missions

    created = wf.create_workflow(definition(), create_mission=True)
    wf.cancel(created["id"])
    missions.run(created["mission_id"], missions.ActionStepRunner(None))
    assert missions.status(created["mission_id"])["state"] == missions.CANCELLED


def test_a_pending_workflow_can_be_paused_before_it_starts(data_dir: Path):
    """Pausing is most useful precisely before any work begins."""
    workflow = wf.create_workflow(definition(), create_mission=False)
    wid = workflow["id"]
    assert wf.pause(wid)["state"] == wf.PAUSED
    wf.run(wid)
    assert wf_store.step_states(wid)["one"] == wf.STEP_PENDING, "paused work still started"
    wf.resume(wid)
    assert wf.get(wid)["state"] == wf.COMPLETED


def test_workflow_actions_are_reachable_by_agents(data_dir: Path):
    """Regression, found live: every workflow action came back permission_denied.

    Registering an action is not enough — if no agent may call it, the whole
    orchestration layer is unreachable from the running service.
    """
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions
    from jarvis.specialized_agents import definitions as agent_defs

    ensure_handlers_loaded()
    registered = {a["action"] for a in all_actions()}
    assert set(agent_defs.WORKFLOW_USE) <= registered
    for action in agent_defs.WORKFLOW_USE:
        assert any(a.permits(action) for a in agent_defs.BUILTIN_AGENTS), (
            f"registered but unreachable: {action}"
        )


def test_agent_orchestration_grants_no_new_authority(data_dir: Path):
    """An agent can drive a workflow, but not one whose steps it could not run."""
    bad = definition(
        steps=[
            {"step_id": "x", "action": "dev_task_create", "agent_id": "research_specialist"},
        ]
    )
    out = _call("workflow_create", {"definition": bad, "mission": False})
    assert out["ok"] is False
    assert "may not invoke" in out["message"]


def test_agent_can_create_and_run_a_workflow_end_to_end(data_dir: Path):
    out = agents.invoke(
        "general_specialist",
        "orchestrate",
        action="workflow_create",
        params={
            "definition": definition(
                steps=[
                    {"step_id": "one", "action": "mission_list", "params": {"limit": 1}},
                ]
            ),
            "mission": False,
        },
    )
    assert out["ok"] is True
    wid = out["result"]["workflow_id"]
    started = agents.invoke(
        "general_specialist", "run", action="workflow_start", params={"workflow_id": wid}
    )
    assert started["ok"] is True
    assert started["result"]["workflow"]["state"] == wf.COMPLETED


def test_max_steps_bounds_the_whole_call_not_one_slice(data_dir: Path):
    """Regression, found live: asking for two steps ran the whole workflow.

    Without this there is no way to advance a workflow part-way and inspect it,
    which is exactly what a bounded, resumable engine is for.
    """
    workflow = wf.create_workflow(
        definition(
            steps=[
                {
                    "step_id": f"s{i}",
                    "action": "mission_list",
                    "params": {"limit": 1},
                    **({"depends_on": [f"s{i - 1}"]} if i else {}),
                }
                for i in range(4)
            ]
        ),
        create_mission=False,
    )
    wid = workflow["id"]

    wf.run(wid, max_steps=2)
    states = wf_store.step_states(wid)
    assert sum(1 for s in states.values() if s == wf.STEP_SUCCEEDED) == 2
    assert wf.get(wid)["state"] == wf.RUNNING, "a part-way workflow must stay running"

    # Continuing finishes the rest without repeating anything.
    wf.run(wid)
    assert wf.get(wid)["state"] == wf.COMPLETED
    assert wf.get(wid)["usage"]["actions"] == 4, "a step was executed twice"


def test_partially_run_workflow_survives_and_resumes(data_dir: Path):
    """The property crash recovery depends on: stop, reload, continue."""
    workflow = wf.create_workflow(
        definition(
            steps=[
                {
                    "step_id": f"s{i}",
                    "action": "mission_list",
                    "params": {"limit": 1},
                    **({"depends_on": [f"s{i - 1}"]} if i else {}),
                }
                for i in range(3)
            ]
        ),
        create_mission=False,
    )
    wid = workflow["id"]
    wf.run(wid, max_steps=1)
    assert wf_store.step_states(wid)["s0"] == wf.STEP_SUCCEEDED
    assert wf_store.step_states(wid)["s1"] == wf.STEP_PENDING

    reloaded = wf.get(wid)
    assert reloaded["state"] == wf.RUNNING
    assert wf.run(wid)["state"] == wf.COMPLETED
    assert wf.get(wid)["usage"]["actions"] == 3


def test_one_graph_problem_does_not_manufacture_false_reference_errors(data_dir: Path):
    """Regression, found live: a depth violation made every reference look broken.

    Ancestor traversal was skipped whenever the graph had any problem at all, so
    a single real error reported a pile of spurious "does not depend on it"
    failures alongside it.
    """
    steps = [{"step_id": "s0", "action": "mission_list"}]
    for i in range(1, 20):  # deliberately deeper than max_depth
        steps.append(
            {
                "step_id": f"s{i}",
                "action": "mission_list",
                "depends_on": [f"s{i - 1}"],
                "params": {"x": f"${{steps.s{i - 1}.output.value}}"},
            }
        )
    report = wf.validate(wf.WorkflowDefinition.from_dict(definition(steps=steps)))
    assert report["ok"] is False
    assert any("exceeds max_depth" in p for p in report["problems"])
    # The references are all legitimate; only the depth is wrong.
    assert not [p for p in report["problems"] if "without depending on it" in p]


def test_a_real_multi_system_chain_fits_within_the_depth_bound(data_dir: Path):
    """route -> research -> run -> evidence -> claim -> verify -> summarise -> synthesis."""
    chain = [
        "route",
        "research",
        "run_research",
        "source",
        "claim",
        "verify",
        "summarise",
        "synthesis",
    ]
    steps = []
    for i, step_id in enumerate(chain):
        steps.append(
            {
                "step_id": step_id,
                "action": "mission_list",
                **({"depends_on": [chain[i - 1]]} if i else {}),
            }
        )
    report = wf.validate(wf.WorkflowDefinition.from_dict(definition(steps=steps)))
    assert report["ok"] is True, report["problems"]
    assert report["depth"] == len(chain)


def test_depth_is_still_bounded(data_dir: Path):
    steps = [{"step_id": "s0", "action": "mission_list"}]
    for i in range(1, wf.LIMITS["max_depth"] + 3):
        steps.append({"step_id": f"s{i}", "action": "mission_list", "depends_on": [f"s{i - 1}"]})
    report = wf.validate(wf.WorkflowDefinition.from_dict(definition(steps=steps)))
    assert any("exceeds max_depth" in p for p in report["problems"])


def test_a_workflow_with_a_step_in_flight_is_not_finalised(data_dir: Path):
    """Regression, found live: a workflow reported partial mid-step.

    Its mission drives it from the worker while a direct call can run another
    slice, so finalising on "nothing ready" declared the whole workflow finished
    while another executor still had a step running.
    """
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "slow", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "after",
                    "action": "mission_list",
                    "depends_on": ["slow"],
                    "params": {"limit": 1},
                },
            ]
        ),
        create_mission=False,
    )
    wid = workflow["id"]
    # Pretend another executor picked up "slow" and is still working on it.
    wf_store.set_state(wid, wf.RUNNING)
    wf_store.set_step(wid, "slow", state=wf.STEP_RUNNING)

    result = wf.run_slice(wid)
    assert result["workflow"]["state"] == wf.RUNNING, "finalised while a step was in flight"
    assert wf.get(wid)["state"] not in wf.TERMINAL_STATES


def test_in_flight_guard_does_not_block_bounded_stops(data_dir: Path):
    """A bound still stops the workflow, even with something running."""
    workflow = wf.create_workflow(
        definition(
            steps=[
                {"step_id": "a", "action": "mission_list", "params": {"limit": 1}},
                {
                    "step_id": "b",
                    "action": "mission_list",
                    "depends_on": ["a"],
                    "params": {"limit": 1},
                },
            ],
            limits={"max_tool_calls": 1},
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    assert final["state"] in wf.TERMINAL_STATES


def test_agent_bound_counts_distinct_agents_not_every_step(data_dir: Path):
    """Regression, found live: an 11-step workflow stopped after 8.

    Every step named an agent, and each one was counted against
    max_child_agents — but how many steps run is already bounded by max_steps.
    The agent bound is about how many different agents get involved.
    """
    steps = []
    for i in range(10):
        steps.append(
            {
                "step_id": f"s{i}",
                "action": "mission_list",
                "agent_id": "general_specialist",
                "params": {"limit": 1},
                **({"depends_on": [f"s{i - 1}"]} if i else {}),
            }
        )
    workflow = wf.create_workflow(definition(steps=steps), create_mission=False)
    final = wf.run(workflow["id"])
    assert final["state"] == wf.COMPLETED, wf.status(workflow["id"])["steps_by_state"]
    usage = wf.get(workflow["id"])["usage"]
    assert usage["agents"] == ["general_specialist"]
    assert usage["actions"] == 10


def test_too_many_distinct_agents_is_still_bounded(data_dir: Path):
    workflow = wf.create_workflow(
        definition(
            steps=[
                {
                    "step_id": "a",
                    "action": "model_route",
                    "agent_id": "general_specialist",
                    "params": {"task_type": "general"},
                },
                {
                    "step_id": "b",
                    "action": "model_route",
                    "agent_id": "research_specialist",
                    "depends_on": ["a"],
                    "params": {"task_type": "general"},
                },
                {
                    "step_id": "c",
                    "action": "model_route",
                    "agent_id": "analysis_specialist",
                    "depends_on": ["b"],
                    "params": {"task_type": "general"},
                },
            ],
            limits={"max_child_agents": 1},
        ),
        create_mission=False,
    )
    final = wf.run(workflow["id"])
    assert final["state"] in wf.TERMINAL_STATES
    assert final["state"] != wf.COMPLETED
