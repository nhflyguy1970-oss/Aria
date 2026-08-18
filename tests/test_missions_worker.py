"""Continuous background mission execution — worker lifecycle, queue, recovery."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from jarvis import missions
from jarvis.missions import store, worker

REPO_ROOT = Path(__file__).resolve().parents[1]


def _steps(n: int) -> list[dict]:
    return [{"name": f"step-{i}", "action": "noop", "params": {"i": i}} for i in range(n)]


def _runner(calls: list[tuple[str, int]], delay: float = 0.0):
    def run_step(step: dict, context: dict) -> dict:
        calls.append((context.get("_mid", "?"), step["params"]["i"]))
        if delay:
            time.sleep(delay)
        return {}

    return run_step


@pytest.fixture(autouse=True)
def _stop_worker_after_each_test():
    """No test may leak a running worker thread into the next one."""
    yield
    worker.stop(timeout=5)
    assert not worker.is_running()


def _wait_for(predicate, timeout: float = 10.0, interval: float = 0.02):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


# --------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------


def test_worker_starts_and_stops_cleanly(data_dir: Path):
    assert worker.is_running() is False
    assert worker.start(_runner([])) is True
    assert worker.is_running() is True

    assert worker.stop(timeout=5) is True
    assert worker.is_running() is False
    assert worker.status()["running"] is False


def test_no_duplicate_worker_starts(data_dir: Path):
    assert worker.start(_runner([])) is True
    assert worker.start(_runner([])) is False, "second start created a second worker"
    assert worker.is_running() is True


def test_worker_disabled_by_env(data_dir: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("JARVIS_MISSION_WORKER", "0")
    assert worker.start(_runner([])) is False
    assert worker.is_running() is False


# --------------------------------------------------------------------------
# Automatic pickup — the point of the milestone
# --------------------------------------------------------------------------


def test_pending_mission_runs_without_explicit_mission_run(data_dir: Path):
    calls: list[tuple[str, int]] = []
    mission_id = missions.create_mission("auto", steps=_steps(3))

    worker.start(_runner(calls), poll_s=0.05)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.COMPLETED), (
        f"mission never completed: {missions.status(mission_id)}"
    )
    assert len(calls) == 3
    assert missions.get(mission_id)["completed_steps"] == 3


def test_mission_created_after_start_is_picked_up(data_dir: Path):
    calls: list[tuple[str, int]] = []
    worker.start(_runner(calls), poll_s=0.05)

    mission_id = missions.create_mission("late arrival", steps=_steps(2))
    worker.wake()
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.COMPLETED)


def test_multiple_missions_complete_independently(data_dir: Path):
    calls: list[tuple[str, int]] = []
    a = missions.create_mission("A", steps=_steps(6))
    b = missions.create_mission("B", steps=_steps(4))

    worker.start(_runner(calls), poll_s=0.05, slice_steps=2)
    assert _wait_for(
        lambda: (
            missions.get(a)["state"] == store.COMPLETED
            and missions.get(b)["state"] == store.COMPLETED
        )
    ), f"a={missions.status(a)} b={missions.status(b)}"

    assert missions.get(a)["completed_steps"] == 6
    assert missions.get(b)["completed_steps"] == 4
    # Neither mission picked up the other's history or errors.
    assert {e["mission_id"] for e in missions.history(a)} == {a}
    assert {e["mission_id"] for e in missions.history(b)} == {b}
    assert missions.get(a)["error"] is None
    assert missions.get(b)["error"] is None


def test_long_mission_does_not_starve_the_queue(data_dir: Path):
    """A bounded slice returns the worker to the queue."""
    calls: list[tuple[str, int]] = []
    long_id = missions.create_mission("long", steps=_steps(10))
    short_id = missions.create_mission("short", steps=_steps(1))

    worker.start(_runner(calls), poll_s=0.05, slice_steps=2)
    assert _wait_for(lambda: missions.get(short_id)["state"] == store.COMPLETED, timeout=10)
    # The short mission finished while the long one was still in flight.
    assert _wait_for(lambda: missions.get(long_id)["state"] == store.COMPLETED, timeout=15)


# --------------------------------------------------------------------------
# Queue durability
# --------------------------------------------------------------------------


def test_queue_is_durable_and_ordered(data_dir: Path):
    first = missions.create_mission("first", steps=_steps(1))
    time.sleep(0.01)
    second = missions.create_mission("second", steps=_steps(1))

    assert store.next_pending()["id"] == first
    assert store.pending_count() == 2

    import importlib

    importlib.reload(store)
    # Ordering survives a module reload because it lives in the database.
    assert store.next_pending()["id"] == first
    assert second in [m["id"] for m in store.list_missions(state=store.PENDING)]


# --------------------------------------------------------------------------
# Pause / resume
# --------------------------------------------------------------------------


def test_paused_mission_is_not_executed_by_worker(data_dir: Path):
    calls: list[tuple[str, int]] = []
    mission_id = missions.create_mission("paused", steps=_steps(2))
    store.transition(mission_id, store.RUNNING)
    missions.pause(mission_id)

    worker.start(_runner(calls), poll_s=0.05)
    time.sleep(0.4)
    assert missions.get(mission_id)["state"] == store.PAUSED
    assert calls == [], "worker executed a paused mission"


def test_resumed_mission_continues_from_checkpoint(data_dir: Path):
    calls: list[tuple[str, int]] = []
    mission_id = missions.create_mission("resume me", steps=_steps(4))
    missions.run(mission_id, _runner(calls), max_steps=2)
    assert len(calls) == 2
    assert missions.get(mission_id)["state"] == store.PAUSED

    # Explicit API transition back to runnable, as the state machine requires.
    store.make_runnable(mission_id)
    worker.start(_runner(calls), poll_s=0.05)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.COMPLETED)
    assert len(calls) == 4, "resumed mission repeated completed steps"


# --------------------------------------------------------------------------
# Cancellation
# --------------------------------------------------------------------------


def test_cancelled_while_waiting_never_starts(data_dir: Path):
    calls: list[tuple[str, int]] = []
    mission_id = missions.create_mission("cancel queued", steps=_steps(3))
    missions.cancel(mission_id)
    assert missions.get(mission_id)["state"] == store.CANCELLED

    worker.start(_runner(calls), poll_s=0.05)
    time.sleep(0.4)
    assert calls == [], "cancelled mission was executed by the worker"
    assert missions.get(mission_id)["state"] == store.CANCELLED


def test_cancel_during_execution_stops_at_step_boundary(data_dir: Path):
    seen: list[int] = []
    mission_id = missions.create_mission("cancel running", steps=_steps(8))

    def runner(step: dict, context: dict) -> dict:
        idx = step["params"]["i"]
        seen.append(idx)
        if idx == 1:
            store.request_cancel(mission_id)  # persisted, as another process would
        return {}

    worker.start(runner, poll_s=0.05, slice_steps=4)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.CANCELLED)
    assert seen == [0, 1], f"execution continued past cancellation: {seen}"
    # Completed work is still checkpointed — state is not corrupted.
    assert store.latest_checkpoint(mission_id)["step_index"] == 2


# --------------------------------------------------------------------------
# Failure / retry / backoff
# --------------------------------------------------------------------------


def test_terminal_failure_stays_terminal_and_is_not_retried(data_dir: Path):
    attempts: list[int] = []

    def boom(step: dict, context: dict) -> dict:
        attempts.append(1)
        raise ValueError("permanent")

    mission_id = missions.create_mission("terminal", steps=_steps(2))
    worker.start(boom, poll_s=0.05)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.FAILED)

    count = len(attempts)
    time.sleep(0.4)
    assert len(attempts) == count, "terminal failure was retried"
    assert missions.get(mission_id)["error_kind"] == store.TERMINAL


def test_retryable_failure_backs_off_instead_of_spinning(data_dir: Path):
    attempts: list[float] = []

    def flaky(step: dict, context: dict) -> dict:
        attempts.append(time.time())
        raise missions.RetryableError("busy")

    mission_id = missions.create_mission("retry", steps=_steps(1))
    worker.start(flaky, poll_s=0.02)
    assert _wait_for(lambda: len(attempts) >= 1)
    time.sleep(0.5)

    # Backoff starts at 2s, so a half-second window cannot produce a hot loop.
    assert len(attempts) <= 2, f"retryable failure spun: {len(attempts)} attempts"
    mission = missions.get(mission_id)
    assert mission["state"] == store.PAUSED
    assert mission["attempts"] >= 1
    assert mission["next_attempt_at"] is not None


def test_retry_budget_is_exhausted_into_terminal_failure(data_dir: Path):
    mission_id = missions.create_mission("exhaust", steps=_steps(1))
    store.transition(mission_id, store.RUNNING)  # a mission only fails while running
    store.record_failure(mission_id, "busy", kind=store.RETRYABLE)
    for _ in range(store.MAX_ATTEMPTS):
        if missions.get(mission_id)["state"] in store.TERMINAL_STATES:
            break
        store.schedule_retry(mission_id)

    mission = missions.get(mission_id)
    assert mission["state"] == store.FAILED
    assert mission["error_kind"] == store.TERMINAL


def test_backoff_is_bounded_and_increasing(data_dir: Path):
    assert store.backoff_seconds(1) < store.backoff_seconds(3)
    assert store.backoff_seconds(50) == store.BACKOFF_CAP_S


def test_due_retries_ignores_user_paused_missions(data_dir: Path):
    """A user-paused mission has no error_kind and must never be auto-resumed."""
    paused = missions.create_mission("user paused", steps=_steps(1))
    store.transition(paused, store.RUNNING)
    missions.pause(paused)

    retryable = missions.create_mission("retryable", steps=_steps(1))
    store.transition(retryable, store.RUNNING)
    store.record_failure(retryable, "busy", kind=store.RETRYABLE)
    store.schedule_retry(retryable)

    due = [m["id"] for m in store.due_retries(now=time.time() + 10_000)]
    assert retryable in due
    assert paused not in due


# --------------------------------------------------------------------------
# Shutdown
# --------------------------------------------------------------------------


def test_shutdown_leaves_unfinished_work_recoverable(data_dir: Path):
    calls: list[tuple[str, int]] = []
    mission_id = missions.create_mission("shutdown", steps=_steps(20))

    worker.start(_runner(calls, delay=0.02), poll_s=0.05, slice_steps=50)
    assert _wait_for(lambda: len(calls) >= 2)
    assert worker.stop(timeout=5) is True

    mission = missions.get(mission_id)
    assert mission["state"] in (store.PENDING, store.PAUSED), mission["state"]
    checkpoint = store.latest_checkpoint(mission_id)
    assert checkpoint is not None

    # Resumable, and it does not redo completed steps.
    done_before = checkpoint["step_index"]
    resumed: list[tuple[str, int]] = []
    store.make_runnable(mission_id, detail="test resume")
    missions.run(mission_id, _runner(resumed))
    assert missions.get(mission_id)["state"] == store.COMPLETED
    assert len(resumed) == 20 - done_before


# --------------------------------------------------------------------------
# Observability
# --------------------------------------------------------------------------


def test_worker_status_is_observable(data_dir: Path):
    mission_id = missions.create_mission("observe", steps=_steps(2))
    snapshot = worker.status()
    assert snapshot["running"] is False
    assert snapshot["pending"] == 1
    assert mission_id in snapshot["pending_ids"]

    worker.start(_runner([]), poll_s=0.05)
    assert _wait_for(lambda: worker.status()["running"] is True)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.COMPLETED)

    snapshot = worker.status()
    assert snapshot["completed"] >= 1
    assert snapshot["last_activity"] is not None
    assert snapshot["active"] == 0


def test_worker_status_action_is_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions, call_action

    ensure_handlers_loaded()
    assert "mission_worker_status" in {s["action"] for s in all_actions()}

    result = call_action(None, "mission_worker_status", {}, "")
    assert result["ok"] is True
    assert result["worker"]["running"] is False


# --------------------------------------------------------------------------
# Recovery from a real killed process
# --------------------------------------------------------------------------

_CRASH_WORKER = """
import os, sys, time
sys.path.insert(0, {repo!r})
os.environ["JARVIS_DATA_DIR"] = {data_dir!r}

from unittest.mock import MagicMock
sys.modules.setdefault("ollama", MagicMock())

from jarvis.missions import store, worker

mission_id = {mission_id!r}

def runner(step, context):
    idx = step["params"]["i"]
    if idx == 3:
        # Kill the worker's own process outright, mid-mission.
        os._exit(9)
    return {{}}

worker.start(runner, poll_s=0.02, slice_steps=50)
time.sleep(30)
"""


def test_worker_recovers_mission_after_real_process_death(data_dir: Path, tmp_path: Path):
    mission_id = missions.create_mission("worker crash", steps=_steps(8))

    script = tmp_path / "crash_worker.py"
    script.write_text(
        textwrap.dedent(_CRASH_WORKER).format(
            repo=str(REPO_ROOT), data_dir=str(data_dir), mission_id=mission_id
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["JARVIS_DATA_DIR"] = str(data_dir)
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120, env=env
    )
    assert proc.returncode == 9, f"child did not die as expected: {proc.stderr[-2000:]}"

    # Killed mid-flight: the mission is stranded in RUNNING on disk.
    assert missions.get(mission_id)["state"] == store.RUNNING
    checkpoint = store.latest_checkpoint(mission_id)
    assert checkpoint["step_index"] == 3, "checkpoints from the dead worker were not durable"

    # A fresh worker recovers it at startup and finishes it — without a user
    # ever calling mission_run.
    calls: list[tuple[str, int]] = []
    worker.start(_runner(calls), poll_s=0.05)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.COMPLETED, timeout=20), (
        f"worker did not recover the mission: {missions.status(mission_id)}"
    )
    assert len(calls) == 5, f"recovered worker redid completed steps: {calls}"
    kinds = [e["kind"] for e in missions.history(mission_id)]
    assert "recovered" in kinds


def test_worker_startup_recovery_reports_recovered_ids(data_dir: Path):
    mission_id = missions.create_mission("stranded", steps=_steps(2))
    store.transition(mission_id, store.RUNNING)  # simulate a stranded row

    worker.start(_runner([]), poll_s=0.05)
    assert _wait_for(lambda: missions.get(mission_id)["state"] == store.COMPLETED)
    assert mission_id in worker.status()["recovered"]
