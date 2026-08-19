"""The workflow engine — validation, bounded execution, recovery.

Execution happens in slices. Each slice takes the steps whose dependencies have
succeeded, runs them, and records the result durably before returning. That is
what makes a workflow survive a restart: progress is on disk after every step,
so recovery resumes rather than repeats.

Durability comes from the mission engine — a workflow's mission dispatches
`workflow_step` slices through the existing worker. There is no second worker,
queue or checkpoint system here.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from jarvis.autonomous_workflows import conditions, dispatch, graph, refs, store
from jarvis.autonomous_workflows.definitions import (
    CANCELLED,
    COMPLETED,
    FAILED,
    LIMITS,
    ON_DEPENDENCY_FAILURE_BLOCK,
    ON_DEPENDENCY_FAILURE_RUN,
    ON_DEPENDENCY_FAILURE_SKIP,
    PARTIAL,
    PAUSED,
    PENDING,
    RUNNING,
    STEP_BLOCKED,
    STEP_CANCELLED,
    STEP_FAILED,
    STEP_PENDING,
    STEP_RUNNING,
    STEP_SKIPPED,
    STEP_SUCCEEDED,
    STEP_TERMINAL,
    STEP_TIMED_OUT,
    StepDefinition,
    WorkflowDefinition,
    WorkflowDefinitionError,
)

log = logging.getLogger("jarvis.autonomous_workflows")


class WorkflowError(RuntimeError):
    pass


# --------------------------------------------------------------- validation


def validate(definition: WorkflowDefinition) -> dict[str, Any]:
    """Everything that can be checked before doing any work."""
    problems: list[str] = []

    if not (definition.name or "").strip():
        problems.append("workflow name is required")
    if not definition.steps:
        problems.append("a workflow needs at least one step")

    max_steps = definition.limit("max_steps")
    if len(definition.steps) > max_steps:
        problems.append(f"{len(definition.steps)} steps exceeds max_steps {max_steps}")

    structure = graph.validate_graph(definition)
    problems.extend(structure["problems"])

    known_ids = {s.step_id for s in definition.steps}
    for step in definition.steps:
        if not step.action:
            problems.append(f"{step.step_id}: no action")
        elif not dispatch.known_action(step.action):
            problems.append(f"{step.step_id}: unknown ARIA action {step.action!r}")
        if step.agent_id:
            from jarvis import specialized_agents as agents

            agent = agents.get(step.agent_id)
            if agent is None:
                problems.append(f"{step.step_id}: unknown agent {step.agent_id!r}")
            elif step.action and not agent.permits(step.action):
                # Caught here rather than at run time so an impossible workflow
                # never starts and then fails half way through.
                problems.append(
                    f"{step.step_id}: agent {step.agent_id} may not invoke {step.action!r}"
                )
        if step.max_retries < 0 or step.max_retries > LIMITS["max_retries"]:
            problems.append(
                f"{step.step_id}: max_retries must be between 0 and {LIMITS['max_retries']}"
            )
        if step.timeout_s <= 0:
            problems.append(f"{step.step_id}: timeout_s must be positive")
        if step.on_dependency_failure not in (
            ON_DEPENDENCY_FAILURE_BLOCK,
            ON_DEPENDENCY_FAILURE_SKIP,
            ON_DEPENDENCY_FAILURE_RUN,
        ):
            problems.append(
                f"{step.step_id}: unknown on_dependency_failure {step.on_dependency_failure!r}"
            )
        try:
            conditions.validate(step.condition)
        except conditions.ConditionError as exc:
            problems.append(f"{step.step_id}: {exc}")

        ancestors = graph.ancestors_of(definition, step.step_id) if structure["ok"] else set()
        for reference in refs.references_in(step.params):
            problems.extend(_reference_problems(step, reference, known_ids, ancestors))

    return {
        "ok": not problems,
        "problems": problems,
        "steps": len(definition.steps),
        "depth": structure["depth"],
        "limits": {k: definition.limit(k) for k in LIMITS},
    }


def _reference_problems(
    step: StepDefinition,
    reference: str,
    known_ids: set[str],
    ancestors: set[str] | None = None,
) -> list[str]:
    """A reference must point at something that will actually exist."""
    body = reference.strip()[2:-1]
    namespace, _, rest = body.partition(".")
    if namespace not in refs.NAMESPACES:
        return [f"{step.step_id}: unknown reference namespace in {reference}"]
    if namespace != refs.STEPS:
        return []
    target = rest.split(".")[0] if rest else ""
    if not target:
        return [f"{step.step_id}: {reference} does not name a step"]
    if target not in known_ids:
        return [f"{step.step_id}: {reference} refers to unknown step {target!r}"]
    if target not in (ancestors if ancestors is not None else set(step.depends_on)):
        # Otherwise the value may simply not be there yet when the step runs.
        return [
            f"{step.step_id}: uses output of {target!r} without depending on it, "
            "directly or transitively"
        ]
    return []


# ------------------------------------------------------------------ creation


def create_workflow(
    definition: dict[str, Any] | WorkflowDefinition,
    *,
    requester: str = "",
    create_mission: bool = False,
) -> dict[str, Any]:
    """Validate and store a workflow. Invalid definitions never reach the store."""
    parsed = (
        definition
        if isinstance(definition, WorkflowDefinition)
        else WorkflowDefinition.from_dict(definition)
    )
    report = validate(parsed)
    if not report["ok"]:
        raise WorkflowDefinitionError("; ".join(report["problems"]))

    workflow_id = store.create(parsed.to_dict(), requester=requester)
    if create_mission:
        attach_mission(workflow_id)
    return store.get(workflow_id)  # type: ignore[return-value]


def attach_mission(workflow_id: str) -> str:
    """Give a workflow a mission, so the existing worker can drive it."""
    from jarvis import missions

    workflow = store.get(workflow_id)
    if not workflow:
        raise WorkflowError(f"No such workflow: {workflow_id}")
    if workflow.get("mission_id"):
        return workflow["mission_id"]

    definition = WorkflowDefinition.from_dict(workflow["definition"])
    # One mission step per workflow step: the worker calls back into the engine,
    # which decides what is actually ready.
    steps = [
        {
            "name": f"workflow:{workflow_id}",
            "action": "workflow_step",
            "params": {"workflow_id": workflow_id},
        }
        for _ in definition.steps
    ]
    mission_id = missions.create_mission(
        f"Workflow: {definition.name}", steps=steps, kind="workflow"
    )
    from jarvis.missions import store as mission_store

    for step in steps:
        step["params"]["mission_id"] = mission_id
    mission_store.set_steps(mission_id, steps)
    store.update(workflow_id, mission_id=mission_id)
    store.record_event(workflow_id, "mission", f"attached mission {mission_id}")
    return mission_id


# ----------------------------------------------------------------- execution


def _bounds_exceeded(workflow: dict[str, Any], definition: WorkflowDefinition) -> str:
    usage = workflow.get("usage") or {}
    for counter, limit_name in (
        ("actions", "max_tool_calls"),
        ("model_calls", "max_model_calls"),
        ("agent_calls", "max_child_agents"),
        ("browser_actions", "max_browser_actions"),
    ):
        limit = definition.limit(limit_name)
        if int(usage.get(counter, 0)) >= limit:
            return f"{limit_name} ({limit}) reached"
    started = workflow.get("started_at")
    if started:
        runtime = time.time() - float(started)
        if runtime > definition.limit("max_runtime_s"):
            return f"max_runtime_s ({definition.limit('max_runtime_s')}) reached"
    return ""


def _dependency_verdict(step: StepDefinition, states: dict[str, str]) -> tuple[bool, str, str]:
    """Whether a step may run given its dependencies.

    Returns (runnable, resulting_state, reason).
    """
    bad = [
        dep
        for dep in step.depends_on
        if states.get(dep, STEP_PENDING) in STEP_TERMINAL and states[dep] != STEP_SUCCEEDED
    ]
    if not bad:
        return True, "", ""
    reason = f"dependencies did not succeed: {', '.join(sorted(bad))}"
    if step.on_dependency_failure == ON_DEPENDENCY_FAILURE_RUN:
        return True, "", reason
    if step.on_dependency_failure == ON_DEPENDENCY_FAILURE_SKIP:
        return False, STEP_SKIPPED, reason
    return False, STEP_BLOCKED, reason


def run_slice(
    workflow_id: str,
    *,
    assistant: Any = None,
    max_steps: int | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Advance a workflow by up to `max_steps` ready steps, then return.

    Bounded on purpose: the caller (the mission worker, or a direct run) decides
    how much work to do at once, and every step is durable before the next
    begins.
    """
    workflow = store.get(workflow_id)
    if not workflow:
        raise WorkflowError(f"No such workflow: {workflow_id}")
    definition = WorkflowDefinition.from_dict(workflow["definition"])

    if workflow["state"] in ("completed", "partial", "failed", "cancelled"):
        return {"workflow": workflow, "ran": [], "done": True}
    if workflow["state"] == PAUSED:
        return {"workflow": workflow, "ran": [], "paused": True}

    def cancelled() -> bool:
        if store.cancel_requested(workflow_id):
            return True
        return bool(cancel_check and cancel_check())

    if cancelled():
        return {"workflow": _finalise_cancelled(workflow_id), "ran": [], "cancelled": True}

    if workflow["state"] == PENDING:
        store.set_state(workflow_id, RUNNING, detail="execution started")

    budget = max_steps if max_steps is not None else definition.limit("max_parallel")
    ran: list[dict[str, Any]] = []

    for _ in range(max(1, budget)):
        if cancelled():
            return {"workflow": _finalise_cancelled(workflow_id), "ran": ran, "cancelled": True}

        current = store.get(workflow_id) or {}
        exceeded = _bounds_exceeded(current, definition)
        if exceeded:
            store.record_event(workflow_id, "bounded", exceeded)
            return {
                "workflow": _finalise(workflow_id, definition, bounded=exceeded),
                "ran": ran,
                "bounded": exceeded,
            }

        states = store.step_states(workflow_id)
        ready = graph.ready_steps(definition, states, limit=1)
        if not ready:
            break
        step = definition.step(ready[0])
        if step is None:
            break
        ran.append(
            _run_step(workflow_id, definition, step, assistant=assistant, cancel_check=cancelled)
        )

    return {"workflow": _finalise(workflow_id, definition), "ran": ran}


def _run_step(
    workflow_id: str,
    definition: WorkflowDefinition,
    step: StepDefinition,
    *,
    assistant: Any = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Run one step to a terminal state, retrying only where that can help."""
    states = store.step_states(workflow_id)
    runnable, blocked_state, reason = _dependency_verdict(step, states)
    if not runnable:
        store.set_step(
            workflow_id, step.step_id, state=blocked_state, reason=reason, finished_at=time.time()
        )
        store.record_event(workflow_id, blocked_state, reason, step_id=step.step_id)
        return {"step_id": step.step_id, "status": blocked_state, "reason": reason}

    workflow = store.get(workflow_id) or {}
    outputs = store.step_outputs(workflow_id)
    inputs = workflow.get("inputs") or {}
    context = workflow.get("context") or {}

    try:
        should_run = conditions.evaluate(
            step.condition, inputs=inputs, context=context, step_outputs=outputs
        )
    except conditions.ConditionError as exc:
        store.set_step(
            workflow_id,
            step.step_id,
            state=STEP_FAILED,
            error=str(exc),
            error_kind="condition",
            finished_at=time.time(),
        )
        store.record_event(workflow_id, "condition_error", str(exc), step_id=step.step_id)
        return {"step_id": step.step_id, "status": STEP_FAILED, "error": str(exc)}

    if not should_run:
        detail = f"condition not met: {conditions.describe(step.condition)}"
        store.set_step(
            workflow_id, step.step_id, state=STEP_SKIPPED, reason=detail, finished_at=time.time()
        )
        store.record_event(workflow_id, STEP_SKIPPED, detail, step_id=step.step_id)
        return {"step_id": step.step_id, "status": STEP_SKIPPED, "reason": detail}

    try:
        params = refs.resolve_params(
            step.params, inputs=inputs, context=context, step_outputs=outputs
        )
    except refs.ReferenceError as exc:
        store.set_step(
            workflow_id,
            step.step_id,
            state=STEP_FAILED,
            error=str(exc),
            error_kind="reference",
            finished_at=time.time(),
        )
        store.record_event(workflow_id, "reference_error", str(exc), step_id=step.step_id)
        return {"step_id": step.step_id, "status": STEP_FAILED, "error": str(exc)}

    store.set_step(workflow_id, step.step_id, state=STEP_RUNNING, started_at=time.time())
    store.update(workflow_id, current_step=step.step_id)

    attempts = 0
    outcome: dict[str, Any] = {}
    while attempts <= max(0, step.max_retries):
        attempts += 1
        if cancel_check is not None and cancel_check():
            store.set_step(
                workflow_id,
                step.step_id,
                state=STEP_CANCELLED,
                attempts=attempts,
                reason="cancelled",
                finished_at=time.time(),
            )
            return {"step_id": step.step_id, "status": STEP_CANCELLED}

        store.bump_usage(workflow_id, "actions")
        if step.agent_id:
            store.bump_usage(workflow_id, "agent_calls")
        outcome = dispatch.dispatch(
            step,
            params,
            assistant=assistant,
            workflow_id=workflow_id,
            cancel_check=cancel_check,
        )
        if outcome["status"] == dispatch.OK:
            break
        if outcome["status"] in (dispatch.DENIED, dispatch.CANCELLED):
            # A refusal or a cancellation is a decision. Retrying would override it.
            break
        if not outcome.get("retryable"):
            break

    state = {
        dispatch.OK: STEP_SUCCEEDED,
        dispatch.CANCELLED: STEP_CANCELLED,
        dispatch.TIMED_OUT: STEP_TIMED_OUT,
    }.get(outcome["status"], STEP_FAILED)

    store.set_step(
        workflow_id,
        step.step_id,
        state=state,
        attempts=attempts,
        output=outcome.get("output"),
        error=outcome.get("error"),
        error_kind=outcome.get("error_kind", ""),
        provenance=outcome.get("provenance") or {},
        finished_at=time.time(),
        duration_ms=outcome.get("duration_ms", 0.0),
    )
    store.record_event(
        workflow_id,
        state,
        f"{step.action} -> {outcome['status']}"
        + (f": {outcome.get('error')}" if outcome.get("error") else ""),
        step_id=step.step_id,
    )
    return {"step_id": step.step_id, "status": state, **outcome}


def _finalise_cancelled(workflow_id: str) -> dict[str, Any]:
    """Stop a workflow, marking work that never started as cancelled."""
    states = store.step_states(workflow_id)
    for step_id, state in states.items():
        if state not in STEP_TERMINAL:
            store.set_step(
                workflow_id,
                step_id,
                state=STEP_CANCELLED,
                reason="workflow cancelled",
                finished_at=time.time(),
            )
    workflow = store.get(workflow_id) or {}
    if workflow.get("state") not in ("cancelled", "completed", "partial", "failed"):
        store.set_state(workflow_id, CANCELLED, detail="cancelled")
    return store.get(workflow_id)  # type: ignore[return-value]


def _finalise(
    workflow_id: str, definition: WorkflowDefinition, *, bounded: str = ""
) -> dict[str, Any]:
    """Decide the workflow's state from its steps, without flattering the result."""
    states = store.step_states(workflow_id)
    outstanding = [s for s, st in states.items() if st not in STEP_TERMINAL]
    succeeded = [s for s, st in states.items() if st == STEP_SUCCEEDED]
    failed = [s for s, st in states.items() if st in (STEP_FAILED, STEP_TIMED_OUT)]
    blocked = [s for s, st in states.items() if st == STEP_BLOCKED]
    skipped = [s for s, st in states.items() if st == STEP_SKIPPED]
    cancelled = [s for s, st in states.items() if st == STEP_CANCELLED]

    workflow = store.get(workflow_id) or {}
    if workflow.get("state") in ("completed", "partial", "failed", "cancelled"):
        return workflow

    if outstanding and not bounded:
        # Still work to do, unless nothing can become ready.
        ready = graph.ready_steps(definition, states)
        if ready:
            return workflow
        # Nothing ready and nothing running: the rest is held by failures.
        for step_id in outstanding:
            step = definition.step(step_id)
            if step is None:
                continue
            _, blocked_state, reason = _dependency_verdict(step, states)
            if blocked_state:
                store.set_step(
                    workflow_id,
                    step_id,
                    state=blocked_state,
                    reason=reason,
                    finished_at=time.time(),
                )
        states = store.step_states(workflow_id)
        blocked = [s for s, st in states.items() if st == STEP_BLOCKED]
        skipped = [s for s, st in states.items() if st == STEP_SKIPPED]
        outstanding = [s for s, st in states.items() if st not in STEP_TERMINAL]

    if cancelled:
        state = CANCELLED
    elif failed or blocked or outstanding:
        # Some real work landed, but not all of it: partial, never success.
        required_failed = [
            s for s in failed if not (definition.step(s) and definition.step(s).optional)
        ]
        if succeeded and not required_failed and not outstanding:
            state = PARTIAL if (blocked or failed or skipped) else COMPLETED
        elif succeeded:
            state = PARTIAL
        else:
            state = FAILED
    else:
        state = COMPLETED

    detail = (
        f"{len(succeeded)} succeeded, {len(failed)} failed, {len(blocked)} blocked, "
        f"{len(skipped)} skipped"
    )
    if bounded:
        detail = f"{bounded}; {detail}"
    store.update(workflow_id, outputs=_collect_outputs(workflow_id))
    return store.set_state(workflow_id, state, detail=detail)


def _collect_outputs(workflow_id: str) -> dict[str, Any]:
    outputs = store.step_outputs(workflow_id)
    return {
        step_id: data.get("output")
        for step_id, data in outputs.items()
        if data.get("state") == STEP_SUCCEEDED and data.get("output") is not None
    }


# ------------------------------------------------- lifecycle and observability


def run(workflow_id: str, *, assistant: Any = None, max_steps: int | None = None) -> dict[str, Any]:
    """Drive a workflow forward, at most `max_steps` steps in total.

    max_steps bounds the whole call, not the width of one slice: asking to
    advance a workflow by two steps has to actually stop after two, or there is
    no way to inspect a workflow part-way through — which is what a bounded,
    resumable engine exists for.
    """
    definition_steps = len((store.get(workflow_id) or {}).get("definition", {}).get("steps") or [])
    executed = 0
    slices = 0
    while slices <= definition_steps + 2:
        slices += 1
        if max_steps is not None and executed >= max_steps:
            return store.get(workflow_id)  # type: ignore[return-value]
        result = run_slice(workflow_id, assistant=assistant, max_steps=1)
        executed += len(result.get("ran") or [])
        workflow = result["workflow"]
        if workflow["state"] in ("completed", "partial", "failed", "cancelled", "paused"):
            return workflow
        if not result["ran"]:
            return workflow
    return store.get(workflow_id)  # type: ignore[return-value]


def pause(workflow_id: str) -> dict[str, Any]:
    workflow = store.get(workflow_id)
    if not workflow:
        raise WorkflowError(f"No such workflow: {workflow_id}")
    return store.set_state(workflow_id, PAUSED, detail="paused by request")


def resume(workflow_id: str, *, assistant: Any = None) -> dict[str, Any]:
    workflow = store.get(workflow_id)
    if not workflow:
        raise WorkflowError(f"No such workflow: {workflow_id}")
    if workflow["state"] != PAUSED:
        raise store.WorkflowStateError(f"Workflow is {workflow['state']}, not paused")
    store.set_state(workflow_id, RUNNING, detail="resumed")
    return run(workflow_id, assistant=assistant)


def cancel(workflow_id: str) -> dict[str, Any]:
    if not store.request_cancel(workflow_id):
        workflow = store.get(workflow_id)
        if not workflow:
            raise WorkflowError(f"No such workflow: {workflow_id}")
        return workflow
    from jarvis import missions

    workflow = store.get(workflow_id) or {}
    if workflow.get("mission_id"):
        # Cancellation flows outward to the mission that drives the workflow.
        missions.cancel(workflow["mission_id"])
    return _finalise_cancelled(workflow_id)


def recover() -> list[str]:
    """Find workflows a dead process left running and make them resumable."""
    recovered: list[str] = []
    for workflow_id in store.interrupted():
        states = store.step_states(workflow_id)
        for step_id, state in states.items():
            if state == STEP_RUNNING:
                # A step that was in flight has no trustworthy result.
                store.set_step(
                    workflow_id,
                    step_id,
                    state=STEP_PENDING,
                    reason="interrupted by process restart; will be retried",
                )
        store.record_event(workflow_id, "recovered", "resumable after interruption")
        recovered.append(workflow_id)
    return recovered


def status(workflow_id: str) -> dict[str, Any] | None:
    """Everything an operator needs, without private reasoning."""
    workflow = store.get(workflow_id)
    if not workflow:
        return None
    states = store.step_states(workflow_id)
    by_state: dict[str, list[str]] = {}
    for step_id, state in sorted(states.items()):
        by_state.setdefault(state, []).append(step_id)

    definition = WorkflowDefinition.from_dict(workflow["definition"])
    provenance = [
        {
            "step_id": s["step_id"],
            "action": s["action"],
            "state": s["state"],
            "agent": s.get("agent_id") or "",
            "provenance": s.get("provenance") or {},
        }
        for s in workflow["steps"]
    ]
    elapsed = None
    if workflow.get("started_at"):
        end = workflow.get("finished_at") or time.time()
        elapsed = round(end - float(workflow["started_at"]), 2)

    return {
        "workflow_id": workflow["id"],
        "name": workflow["name"],
        "state": workflow["state"],
        "requester": workflow["requester"],
        "current_step": workflow["current_step"],
        "mission_id": workflow["mission_id"],
        "steps_total": len(definition.steps),
        "steps_by_state": by_state,
        "succeeded": len(by_state.get(STEP_SUCCEEDED, [])),
        "failed": len(by_state.get(STEP_FAILED, [])) + len(by_state.get(STEP_TIMED_OUT, [])),
        "blocked": len(by_state.get(STEP_BLOCKED, [])),
        "skipped": len(by_state.get(STEP_SKIPPED, [])),
        "pending": len(by_state.get(STEP_PENDING, [])),
        "attempts": sum(int(s.get("attempts") or 0) for s in workflow["steps"]),
        "elapsed_s": elapsed,
        "usage": workflow.get("usage") or {},
        "limits": {k: definition.limit(k) for k in LIMITS},
        "outputs": workflow.get("outputs") or {},
        "context": workflow.get("context") or {},
        "error": workflow.get("error"),
        "cancel_requested": workflow.get("cancel_requested"),
        "provenance": provenance,
        "partial": workflow["state"] == PARTIAL,
    }
