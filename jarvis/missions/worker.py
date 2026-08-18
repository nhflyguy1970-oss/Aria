"""Background mission worker — runs durable missions without a live request.

Follows the in-process worker convention already used by
jarvis.proactive_scheduler: a module-level stop Event plus a single daemon
thread, with start()/stop() driven from ARIA's existing runtime lifecycle. No
new daemon, no new port, no second process.

Execution model:
  * one bounded worker thread, so concurrency can never run away;
  * missions are taken from the durable queue (the missions table) oldest
    first, and each gets a bounded slice of steps before the worker returns to
    the queue — that is what stops one long mission starving the others;
  * every decision is re-read from the database, so cancellation, pausing and
    recovery all work across process boundaries.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

from jarvis.missions import engine, store

logger = logging.getLogger("jarvis.missions.worker")

# Steps a single mission may run before the worker goes back to the queue.
DEFAULT_SLICE = 5
DEFAULT_POLL_S = 1.0

_stop = threading.Event()
_wake = threading.Event()
_thread: threading.Thread | None = None
_lock = threading.Lock()

_state: dict[str, Any] = {
    "started_at": None,
    "last_tick": None,
    "last_activity": None,
    "last_error": None,
    "current_mission": None,
    "completed": 0,
    "recovered": [],
}


def _runner_for(assistant: Any):
    """Default step runner — ARIA's action registry, as in Milestone 1."""
    return engine.ActionStepRunner(assistant)


def _should_continue() -> bool:
    return not _stop.is_set()


def _promote_due_retries() -> None:
    """Return retry-eligible missions to the queue once their backoff elapses."""
    for mission in store.due_retries():
        store.clear_retry_state(mission["id"])
        store.make_runnable(mission["id"], detail="retry backoff elapsed")


def _recover_interrupted() -> list[str]:
    """Missions left RUNNING by a dead process become runnable again."""
    recovered = store.recover_interrupted()
    for mission_id in recovered:
        store.make_runnable(mission_id, detail="resumed after interruption")
    if recovered:
        logger.info("Recovered %d interrupted mission(s)", len(recovered))
    return recovered


def tick(runner=None, *, assistant: Any = None, slice_steps: int = DEFAULT_SLICE) -> str | None:
    """Advance at most one mission by at most slice_steps. Returns its id.

    Exposed separately from the loop so the scheduling logic is testable
    without threads.
    """
    _promote_due_retries()
    mission = store.next_pending()
    if not mission:
        return None

    mission_id = mission["id"]
    _state["current_mission"] = mission_id
    try:
        if runner is None and assistant is None:
            # Nothing can execute this mission; leave it queued rather than
            # failing it, so a later worker with an assistant can pick it up.
            return None
        result = engine.run(
            mission_id,
            runner,
            assistant=assistant,
            max_steps=slice_steps,
            should_continue=_should_continue,
        )
        state = result["state"]

        if state == store.PAUSED:
            if result.get("error_kind") == store.RETRYABLE:
                store.schedule_retry(mission_id)
            elif _stop.is_set():
                # Stopped mid-slice by shutdown: requeue so it resumes later.
                store.make_runnable(mission_id, detail="requeued after worker stop")
            else:
                # Yielded because the step budget ran out — back to the queue
                # so other missions get a turn.
                store.make_runnable(mission_id, detail="yielded for fairness")
        elif state == store.COMPLETED:
            _state["completed"] += 1

        _state["last_activity"] = time.time()
        return mission_id
    except Exception as exc:  # noqa: BLE001 - a worker must never die on one mission
        logger.exception("Mission worker tick failed for %s", mission_id)
        _state["last_error"] = f"{type(exc).__name__}: {exc}"
        return mission_id
    finally:
        _state["current_mission"] = None


def _loop(runner, assistant: Any, poll_s: float, slice_steps: int) -> None:
    try:
        _state["recovered"] = _recover_interrupted()
    except Exception as exc:  # noqa: BLE001 - startup recovery must never kill the worker
        logger.exception("Mission worker startup recovery failed")
        _state["last_error"] = f"recovery: {type(exc).__name__}: {exc}"
    while not _stop.is_set():
        _state["last_tick"] = time.time()
        try:
            worked = tick(runner, assistant=assistant, slice_steps=slice_steps)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Mission worker loop error")
            _state["last_error"] = f"{type(exc).__name__}: {exc}"
            worked = None
        if worked:
            # More work may be waiting; don't sleep between missions.
            continue
        # Idle: sleep until woken by new work, stopped, or the poll interval.
        _wake.wait(poll_s)
        _wake.clear()
    logger.info("Mission worker stopped")


def start(
    runner=None,
    *,
    assistant: Any = None,
    poll_s: float = DEFAULT_POLL_S,
    slice_steps: int = DEFAULT_SLICE,
) -> bool:
    """Start the worker thread. Idempotent — a second call is a no-op."""
    global _thread
    # Disabled by default until the background worker is explicitly promoted to
    # production. Set JARVIS_MISSION_WORKER=1 to opt in.
    if os.getenv("JARVIS_MISSION_WORKER", "0") != "1":
        logger.info("Mission worker disabled (JARVIS_MISSION_WORKER is not 1)")
        return False
    with _lock:
        if _thread and _thread.is_alive():
            return False
        _stop.clear()
        _wake.clear()
        _state.update(
            {
                "started_at": time.time(),
                "last_error": None,
                "current_mission": None,
                "completed": 0,
            }
        )
        _thread = threading.Thread(
            target=_loop,
            args=(runner, assistant, poll_s, slice_steps),
            daemon=True,
            name="jarvis-mission-worker",
        )
        _thread.start()
    logger.info("Mission worker started")
    return True


def stop(timeout: float = 5.0) -> bool:
    """Signal the worker to stop and wait for the thread to finish."""
    global _thread
    _stop.set()
    _wake.set()
    thread = _thread
    if thread and thread.is_alive():
        thread.join(timeout=timeout)
        alive = thread.is_alive()
    else:
        alive = False
    with _lock:
        if not alive:
            _thread = None
    _state["started_at"] = None
    return not alive


def wake() -> None:
    """Nudge an idle worker — call after enqueuing a mission."""
    _wake.set()


def is_running() -> bool:
    return bool(_thread and _thread.is_alive())


def status() -> dict[str, Any]:
    """Observable worker state for handlers and diagnostics."""
    return {
        "running": is_running(),
        "started_at": _state["started_at"],
        "last_tick": _state["last_tick"],
        "last_activity": _state["last_activity"],
        "last_error": _state["last_error"],
        "current_mission": _state["current_mission"],
        "completed": _state["completed"],
        "recovered": list(_state["recovered"] or []),
        "pending": store.pending_count(),
        "active": store.active_count(),
        "pending_ids": [m["id"] for m in store.list_missions(state=store.PENDING, limit=20)],
    }
