"""Mission execution loop — resumable, cancellable, checkpointed.

Deliberately thin. Steps are dispatched through ARIA's existing action registry
(jarvis.handlers.registry) rather than through a new agent framework, so
missions inherit the tools ARIA already has. A step is:

    {"name": "human label", "action": "registered_action", "params": {...}}

The loop's contract:
  * a step is only executed if no checkpoint already records it as done,
    so re-running a mission never repeats completed work;
  * the cancellation flag is re-read from disk at every step boundary, so a
    cancel issued by another process takes effect;
  * a checkpoint is written after each successful step, before the next begins.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol

from jarvis.missions import store

log = logging.getLogger("jarvis.missions")

# A runner receives (step, context) and returns a JSON-serialisable dict.
StepFn = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class StepRunner(Protocol):
    def __call__(self, step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]: ...


class RetryableError(RuntimeError):
    """Work that failed but may succeed later — leaves the mission resumable."""


class MissionCancelled(RuntimeError):
    """Raised internally when a cancellation request is observed."""


class ActionStepRunner:
    """Default runner: dispatch each step through ARIA's action registry."""

    def __init__(self, assistant: Any):
        self.assistant = assistant

    def __call__(self, step: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import call_action

        ensure_handlers_loaded()
        action = step.get("action")
        if not action:
            raise RetryableError(f"Step has no action: {step!r}")
        params = dict(step.get("params") or {})
        result = call_action(self.assistant, action, params, step.get("name") or action)
        return result if isinstance(result, dict) else {"result": result}


def create_mission(
    objective: str, steps: list[dict[str, Any]] | None = None, *, kind: str = "generic"
) -> str:
    return store.create(objective, steps=steps, kind=kind)


def _resume_point(mission_id: str) -> tuple[int, dict[str, Any]]:
    """Return (next step index, accumulated context) from the latest checkpoint."""
    checkpoint = store.latest_checkpoint(mission_id)
    if not checkpoint:
        return 0, {}
    payload = checkpoint.get("payload") or {}
    return int(checkpoint["step_index"]), dict(payload.get("context") or {})


def run(
    mission_id: str,
    runner: StepRunner | StepFn | None = None,
    *,
    assistant: Any = None,
    max_steps: int | None = None,
) -> dict[str, Any]:
    """Execute (or resume) a mission to completion, cancellation or failure.

    Returns the mission's final persisted record.
    """
    mission = store.get(mission_id)
    if not mission:
        raise store.MissionStateError(f"No such mission: {mission_id}")
    if mission["state"] in store.TERMINAL_STATES:
        return mission

    if runner is None:
        if assistant is None:
            raise ValueError("run() needs either a runner or an assistant")
        runner = ActionStepRunner(assistant)

    # Honour a cancellation requested before execution started.
    if store.cancel_requested(mission_id):
        return store.transition(mission_id, store.CANCELLED, detail="cancelled before start")

    steps = mission["steps"]
    start_index, context = _resume_point(mission_id)
    if start_index >= len(steps):
        return store.record_result(mission_id, {"context": context, "steps_run": 0})

    mission = store.transition(mission_id, store.RUNNING, detail=f"from step {start_index}")

    executed = 0
    try:
        for index in range(start_index, len(steps)):
            if max_steps is not None and executed >= max_steps:
                # Bounded execution: stop cleanly, remain resumable.
                store.transition(mission_id, store.PAUSED, detail="step budget exhausted")
                return store.get(mission_id)  # type: ignore[return-value]

            # Re-read from disk: another process may have requested cancellation.
            if store.cancel_requested(mission_id):
                raise MissionCancelled()

            step = steps[index]
            store.record_event(mission_id, "step:start", f"{index}:{step.get('name') or ''}")
            output = runner(step, context)
            if isinstance(output, dict):
                context.update(output)

            executed += 1
            store.save_checkpoint(
                mission_id,
                index + 1,
                {"context": context, "last_step": step.get("name") or step.get("action") or ""},
            )
    except MissionCancelled:
        return store.transition(mission_id, store.CANCELLED, detail="cancelled mid-execution")
    except RetryableError as exc:
        return store.record_failure(mission_id, str(exc), kind=store.RETRYABLE)
    except Exception as exc:  # noqa: BLE001 - any step failure must be persisted
        log.exception("Mission %s failed", mission_id)
        return store.record_failure(mission_id, f"{type(exc).__name__}: {exc}", kind=store.TERMINAL)

    return store.record_result(mission_id, {"context": context, "steps_run": executed})


def pause(mission_id: str) -> dict[str, Any]:
    return store.transition(mission_id, store.PAUSED, detail="paused by request")


def resume(
    mission_id: str, runner: StepRunner | StepFn | None = None, *, assistant: Any = None
) -> dict[str, Any]:
    """Resume a paused or interrupted mission from its latest checkpoint."""
    return run(mission_id, runner, assistant=assistant)


def cancel(mission_id: str) -> bool:
    return store.request_cancel(mission_id)


def recover() -> list[str]:
    """Find missions whose process died and make them resumable."""
    return store.recover_interrupted()


def status(mission_id: str) -> dict[str, Any] | None:
    """Everything a user needs to understand a mission's situation."""
    mission = store.get(mission_id)
    if not mission:
        return None
    checkpoint = store.latest_checkpoint(mission_id)
    total = mission["total_steps"]
    done = mission["completed_steps"]
    return {
        "id": mission["id"],
        "objective": mission["objective"],
        "state": mission["state"],
        "kind": mission["kind"],
        "progress": {
            "completed_steps": done,
            "total_steps": total,
            "percent": round(100.0 * done / total, 1) if total else None,
        },
        "checkpoint": (
            {"seq": checkpoint["seq"], "step_index": checkpoint["step_index"]}
            if checkpoint
            else None
        ),
        "error": mission.get("error"),
        "error_kind": mission.get("error_kind"),
        "result": mission.get("result"),
        "cancel_requested": mission.get("cancel_requested"),
        "created_at": mission.get("created_at"),
        "updated_at": mission.get("updated_at"),
    }
