"""Persistent autonomous task engine — durability, resume, cancellation, history."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from jarvis import missions
from jarvis.missions import store

REPO_ROOT = Path(__file__).resolve().parents[1]


def _steps(n: int) -> list[dict]:
    return [{"name": f"step-{i}", "action": "noop", "params": {"i": i}} for i in range(n)]


def _counting_runner(calls: list[int]):
    def run_step(step: dict, context: dict) -> dict:
        idx = step["params"]["i"]
        calls.append(idx)
        return {f"out_{idx}": idx}

    return run_step


# --------------------------------------------------------------------------
# Creation and persistence
# --------------------------------------------------------------------------


def test_mission_creation_persists(data_dir: Path):
    mission_id = missions.create_mission("index the house", steps=_steps(2))
    assert mission_id

    # Read through a fresh query — nothing cached in memory.
    mission = missions.get(mission_id)
    assert mission["objective"] == "index the house"
    assert mission["state"] == store.PENDING
    assert mission["total_steps"] == 2
    assert store.DB_PATH.is_file()


def test_mission_store_is_inside_the_isolated_root(data_dir: Path):
    assert data_dir in store.DB_PATH.resolve().parents


def test_state_transitions_persist(data_dir: Path):
    mission_id = missions.create_mission("transition test", steps=_steps(1))
    store.transition(mission_id, store.RUNNING)
    assert missions.get(mission_id)["state"] == store.RUNNING
    store.transition(mission_id, store.PAUSED)
    assert missions.get(mission_id)["state"] == store.PAUSED


def test_illegal_transition_is_rejected(data_dir: Path):
    mission_id = missions.create_mission("illegal", steps=_steps(1))
    store.transition(mission_id, store.RUNNING)
    store.transition(mission_id, store.COMPLETED)
    with pytest.raises(store.MissionStateError):
        store.transition(mission_id, store.RUNNING)


# --------------------------------------------------------------------------
# Checkpoints and execution
# --------------------------------------------------------------------------


def test_checkpoint_creation_persists(data_dir: Path):
    mission_id = missions.create_mission("checkpoints", steps=_steps(3))
    store.save_checkpoint(mission_id, 1, {"context": {"a": 1}})
    store.save_checkpoint(mission_id, 2, {"context": {"a": 2}})

    latest = store.latest_checkpoint(mission_id)
    assert latest["seq"] == 2
    assert latest["step_index"] == 2
    assert latest["payload"]["context"] == {"a": 2}
    assert len(store.checkpoints(mission_id)) == 2


def test_run_executes_all_steps_and_completes(data_dir: Path):
    calls: list[int] = []
    mission_id = missions.create_mission("full run", steps=_steps(3))
    final = missions.run(mission_id, _counting_runner(calls))

    assert calls == [0, 1, 2]
    assert final["state"] == store.COMPLETED
    assert final["completed_steps"] == 3
    assert final["result"]["steps_run"] == 3


def test_bounded_run_pauses_and_resumes_from_checkpoint(data_dir: Path):
    calls: list[int] = []
    runner = _counting_runner(calls)
    mission_id = missions.create_mission("bounded", steps=_steps(4))

    missions.run(mission_id, runner, max_steps=2)
    assert calls == [0, 1]
    assert missions.get(mission_id)["state"] == store.PAUSED

    missions.resume(mission_id, runner)
    # Resumed from the checkpoint: steps 0 and 1 were not repeated.
    assert calls == [0, 1, 2, 3]
    assert missions.get(mission_id)["state"] == store.COMPLETED


def test_completed_work_is_not_repeated(data_dir: Path):
    """Idempotency: re-running a finished mission does no further work."""
    calls: list[int] = []
    runner = _counting_runner(calls)
    mission_id = missions.create_mission("idempotent", steps=_steps(2))

    missions.run(mission_id, runner)
    assert calls == [0, 1]

    missions.run(mission_id, runner)
    assert calls == [0, 1], "completed mission re-executed its steps"


# --------------------------------------------------------------------------
# Failure handling
# --------------------------------------------------------------------------


def test_terminal_failure_is_persisted(data_dir: Path):
    def boom(step: dict, context: dict) -> dict:
        raise ValueError("exploded")

    mission_id = missions.create_mission("failing", steps=_steps(2))
    final = missions.run(mission_id, boom)

    assert final["state"] == store.FAILED
    assert final["error_kind"] == store.TERMINAL
    assert "exploded" in final["error"]
    # Survives a fresh read.
    assert missions.get(mission_id)["error_kind"] == store.TERMINAL


def test_retryable_failure_leaves_mission_resumable(data_dir: Path):
    attempts: list[int] = []

    def flaky(step: dict, context: dict) -> dict:
        attempts.append(step["params"]["i"])
        if len(attempts) == 1:
            raise missions.RetryableError("service busy")
        return {"ok": True}

    mission_id = missions.create_mission("flaky", steps=_steps(2))
    final = missions.run(mission_id, flaky)
    assert final["state"] == store.PAUSED
    assert final["error_kind"] == store.RETRYABLE

    final = missions.resume(mission_id, flaky)
    assert final["state"] == store.COMPLETED


# --------------------------------------------------------------------------
# Cancellation
# --------------------------------------------------------------------------


def test_cancellation_persists_before_start(data_dir: Path):
    mission_id = missions.create_mission("cancel early", steps=_steps(2))
    assert missions.cancel(mission_id) is True
    assert missions.get(mission_id)["state"] == store.CANCELLED

    calls: list[int] = []
    missions.run(mission_id, _counting_runner(calls))
    assert calls == [], "cancelled mission executed steps"


def test_cancellation_observed_mid_execution(data_dir: Path):
    """Cancellation is re-read from disk at each step boundary."""
    calls: list[int] = []
    mission_id = missions.create_mission("cancel mid", steps=_steps(4))

    def runner(step: dict, context: dict) -> dict:
        idx = step["params"]["i"]
        calls.append(idx)
        if idx == 1:
            # Simulates another process requesting cancellation.
            store.request_cancel(mission_id)
        return {}

    final = missions.run(mission_id, runner)
    assert final["state"] == store.CANCELLED
    assert calls == [0, 1], "execution continued past the cancellation request"
    # State is not corrupted: checkpoints for completed work survive.
    assert store.latest_checkpoint(mission_id)["step_index"] == 2


def test_cancel_returns_false_for_finished_mission(data_dir: Path):
    mission_id = missions.create_mission("done", steps=_steps(1))
    missions.run(mission_id, _counting_runner([]))
    assert missions.cancel(mission_id) is False


# --------------------------------------------------------------------------
# History and isolation between missions
# --------------------------------------------------------------------------


def test_history_is_retained(data_dir: Path):
    mission_id = missions.create_mission("history", steps=_steps(2))
    missions.run(mission_id, _counting_runner([]))
    kinds = [e["kind"] for e in missions.history(mission_id)]

    assert "created" in kinds
    assert "state:running" in kinds
    assert "state:completed" in kinds
    assert kinds.count("checkpoint") == 2
    assert kinds.count("step:start") == 2


def test_multiple_missions_do_not_corrupt_each_other(data_dir: Path):
    a_calls: list[int] = []
    b_calls: list[int] = []
    a = missions.create_mission("mission A", steps=_steps(3))
    b = missions.create_mission("mission B", steps=_steps(2))

    missions.run(a, _counting_runner(a_calls), max_steps=1)

    def failing(step: dict, context: dict) -> dict:
        b_calls.append(step["params"]["i"])
        raise ValueError("b fails")

    missions.run(b, failing)

    assert missions.get(a)["state"] == store.PAUSED
    assert missions.get(b)["state"] == store.FAILED
    assert missions.get(a)["error"] is None, "mission A picked up mission B's error"
    assert store.latest_checkpoint(a)["step_index"] == 1
    assert store.latest_checkpoint(b) is None

    # Histories are per-mission: no event leaks across missions.
    a_events = missions.history(a)
    b_events = missions.history(b)
    assert {e["mission_id"] for e in a_events} == {a}
    assert {e["mission_id"] for e in b_events} == {b}
    assert "error" not in [e["kind"] for e in a_events]
    assert "error" in [e["kind"] for e in b_events]
    assert b_calls == [0]

    missions.resume(a, _counting_runner(a_calls))
    assert missions.get(a)["state"] == store.COMPLETED
    assert missions.get(b)["state"] == store.FAILED


def test_status_snapshot_is_observable(data_dir: Path):
    mission_id = missions.create_mission("observable", steps=_steps(4))
    missions.run(mission_id, _counting_runner([]), max_steps=2)
    snapshot = missions.status(mission_id)

    assert snapshot["id"] == mission_id
    assert snapshot["objective"] == "observable"
    assert snapshot["state"] == store.PAUSED
    assert snapshot["progress"] == {
        "completed_steps": 2,
        "total_steps": 4,
        "percent": 50.0,
    }
    assert snapshot["checkpoint"]["step_index"] == 2


# --------------------------------------------------------------------------
# Crash recovery — a real killed process, not a simulated one
# --------------------------------------------------------------------------

_CRASH_SCRIPT = """
import os, sys
sys.path.insert(0, {repo!r})
os.environ["JARVIS_DATA_DIR"] = {data_dir!r}

from unittest.mock import MagicMock
sys.modules.setdefault("ollama", MagicMock())

from jarvis import missions
from jarvis.missions import store

mission_id = {mission_id!r}

def runner(step, context):
    idx = step["params"]["i"]
    if idx == 2:
        # Hard-kill this process mid-mission: no cleanup, no exception handling,
        # no chance for the engine to write a terminal state.
        os._exit(9)
    return {{"done_%d" % idx: idx}}

missions.run(mission_id, runner)
"""


def test_interrupted_mission_is_recoverable_after_process_death(data_dir: Path, tmp_path: Path):
    mission_id = missions.create_mission("survives a crash", steps=_steps(5))

    script = tmp_path / "crash_runner.py"
    script.write_text(
        textwrap.dedent(_CRASH_SCRIPT).format(
            repo=str(REPO_ROOT), data_dir=str(data_dir), mission_id=mission_id
        ),
        encoding="utf-8",
    )

    env = dict(os.environ)
    env["JARVIS_DATA_DIR"] = str(data_dir)
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120, env=env
    )

    # The child really was killed, not returned from cleanly.
    assert proc.returncode == 9, (
        f"expected SIGKILL-style exit, got {proc.returncode}: {proc.stderr[-2000:]}"
    )

    # The mission is left RUNNING on disk because nothing got to finalise it.
    mission = missions.get(mission_id)
    assert mission["state"] == store.RUNNING

    # It is discoverable as interrupted.
    interrupted = [m["id"] for m in store.interrupted_missions()]
    assert mission_id in interrupted

    # Recovery makes it resumable, from the checkpoint the dead process wrote.
    assert missions.recover() == [mission_id]
    assert missions.get(mission_id)["state"] == store.PAUSED
    checkpoint = store.latest_checkpoint(mission_id)
    assert checkpoint["step_index"] == 2, "checkpoint from the killed process was not durable"

    # Resuming continues from the checkpoint without redoing steps 0 and 1.
    calls: list[int] = []
    final = missions.resume(mission_id, _counting_runner(calls))
    assert calls == [2, 3, 4], f"resumed from the wrong point: {calls}"
    assert final["state"] == store.COMPLETED
    assert "recovered" in [e["kind"] for e in missions.history(mission_id)]


def test_mission_survives_module_reload(data_dir: Path):
    """State comes from disk, not module-level memory."""
    import importlib

    mission_id = missions.create_mission("reload me", steps=_steps(2))
    missions.run(mission_id, _counting_runner([]), max_steps=1)

    # Only the store is reloaded. Reloading the engine would rebind its
    # exception classes, so a RetryableError raised by an already-imported
    # caller would no longer match the reloaded engine's except clause and
    # would be misclassified as terminal in every later test.
    importlib.reload(store)

    reloaded = store.get(mission_id)
    assert reloaded["state"] == store.PAUSED
    assert store.latest_checkpoint(mission_id)["step_index"] == 1


# --------------------------------------------------------------------------
# Assistant-facing interface
# --------------------------------------------------------------------------


def test_mission_actions_are_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {spec["action"] for spec in all_actions()}
    for action in (
        "mission_create",
        "mission_status",
        "mission_list",
        "mission_run",
        "mission_pause",
        "mission_cancel",
        "mission_recover",
    ):
        assert action in names, f"{action} not registered"


def test_mission_handlers_round_trip(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    created = call_action(None, "mission_create", {"objective": "handler round trip"}, "")
    assert created["ok"] is True
    mission_id = created["mission_id"]

    status = call_action(None, "mission_status", {"mission_id": mission_id}, "")
    assert status["ok"] is True
    assert status["mission"]["state"] == store.PENDING

    listed = call_action(None, "mission_list", {}, "")
    assert any(m["id"] == mission_id for m in listed["missions"])

    cancelled = call_action(None, "mission_cancel", {"mission_id": mission_id}, "")
    assert cancelled["ok"] is True
    assert missions.get(mission_id)["state"] == store.CANCELLED


def test_json_payloads_survive_a_round_trip(data_dir: Path):
    """Result/context must be JSON-durable, not pickled objects."""
    mission_id = missions.create_mission("json", steps=_steps(1))

    def runner(step: dict, context: dict) -> dict:
        return {"nested": {"list": [1, 2, 3], "text": "ok"}}

    missions.run(mission_id, runner)
    result = missions.get(mission_id)["result"]
    assert result["context"]["nested"] == {"list": [1, 2, 3], "text": "ok"}
    json.dumps(result)
