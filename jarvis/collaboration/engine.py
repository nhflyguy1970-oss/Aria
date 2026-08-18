"""Collaboration engine — bounded delegation, execution and aggregation.

Delegation is a permissioned act on both sides. The requester needs the
`collab_delegate` action, and the target is evaluated independently against its
own definition — so asking another specialist to do something is never a way to
obtain authority you were not granted.

Execution durability comes from the existing mission system: a collaboration
creates a mission whose steps advance it, and the background worker runs them.
No second queue, worker or checkpoint mechanism.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from jarvis import specialized_agents as agents
from jarvis.collaboration import graph, store
from jarvis.specialized_agents.definitions import DELEGATE_ACTION

log = logging.getLogger("jarvis.collaboration")

# Conservative defaults. A specialist must never be able to spawn unbounded work.
DEFAULT_BOUNDS: dict[str, int] = {
    "max_agents": 4,
    "max_depth": 3,
    "max_tasks": 12,
    "max_retries": 2,
    "max_waves": 8,
}


class DelegationError(RuntimeError):
    """A delegation request was rejected."""


class BoundExceeded(DelegationError):
    """A collaboration safety limit was reached."""


def bounds_for(collaboration: dict[str, Any]) -> dict[str, int]:
    merged = dict(DEFAULT_BOUNDS)
    merged.update({k: int(v) for k, v in (collaboration.get("bounds") or {}).items()})
    return merged


# --------------------------------------------------------------- creation


def create_collaboration(
    objective: str, *, initiator: str = "analysis_specialist", bounds: dict[str, int] | None = None
) -> dict[str, str]:
    """Create a collaboration and the mission that will drive it."""
    if not (objective or "").strip():
        raise DelegationError("A collaboration needs an objective")
    if not agents.get(initiator):
        raise DelegationError(f"Unknown initiating agent: {initiator}")

    from jarvis import missions

    cid = store.create(objective, initiator, bounds=bounds or {})
    mission_id = missions.create_mission(
        f"Collaboration: {objective}",
        steps=[
            {
                "name": f"collab wave {i + 1}",
                "action": "collab_step",
                "params": {"collaboration_id": cid},
            }
            for i in range(bounds_for({"bounds": bounds or {}})["max_waves"])
        ],
        kind="collaboration",
    )
    store.set_mission(cid, mission_id)
    missions.worker.wake()
    return {"collaboration_id": cid, "mission_id": mission_id}


# -------------------------------------------------------------- delegation


def delegate(
    collaboration_id: str,
    *,
    requester: str,
    objective: str,
    target: str = "",
    capability: str = "",
    action: str = "",
    params: dict[str, Any] | None = None,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    """Register one agent's request for work from another.

    Returns the created task, or raises DelegationError with a specific reason:
    the caller must be able to distinguish forbidden, unavailable and invalid.
    """
    collaboration = store.get(collaboration_id)
    if not collaboration:
        raise DelegationError(f"No collaboration {collaboration_id}")
    if collaboration["status"] in store.TERMINAL_STATES:
        raise DelegationError(f"Collaboration is {collaboration['status']}")
    if not (objective or "").strip():
        raise DelegationError("A delegated task needs an objective")

    limits = bounds_for(collaboration)
    existing = store.tasks(collaboration_id)

    # 1. The requester must be permitted to delegate at all.
    requester_agent = agents.get(requester)
    if not requester_agent:
        raise DelegationError(f"Unknown requesting agent: {requester}")
    if not requester_agent.permits(DELEGATE_ACTION):
        raise DelegationError(f"Agent {requester!r} is not permitted to delegate work")

    # 2. Resolve the target, recording why it was chosen.
    selection: dict[str, Any] = {}
    if target:
        target_agent = agents.get(target)
        selection = {"selection_method": "explicit_target", "agent_id": target}
    else:
        selection = agents.select(objective, required_capability=capability)
        target_agent = agents.get(selection.get("agent_id") or "")
    if not target_agent:
        raise DelegationError(f"No specialist available for capability {capability or objective!r}")
    if not target_agent.enabled:
        raise DelegationError(f"Specialist {target_agent.id!r} is disabled")

    # 3. The target's own permissions decide what it may do — never the requester's.
    if action and not target_agent.permits(action):
        raise DelegationError(
            f"Agent {target_agent.id!r} is not permitted to invoke action {action!r}"
        )

    # 4. Bounds.
    if len(existing) >= limits["max_tasks"]:
        raise BoundExceeded(f"max_tasks ({limits['max_tasks']}) reached")
    participants = {t["target"] for t in existing} | {collaboration["initiator"], target_agent.id}
    if len(participants) > limits["max_agents"]:
        raise BoundExceeded(f"max_agents ({limits['max_agents']}) reached")

    deps = list(depends_on or [])
    by_id = {t["id"]: t for t in existing}
    depth = 1 + max((by_id[d]["depth"] for d in deps if d in by_id), default=-1)
    if depth >= limits["max_depth"]:
        raise BoundExceeded(f"max_depth ({limits['max_depth']}) reached")

    # 5. Cycles are a definition error and are rejected before persistence.
    provisional_id = "__new__"
    if graph.would_create_cycle(existing, provisional_id, deps):
        raise graph.GraphError("Delegation would create a cycle")

    task_id = store.add_task(
        collaboration_id,
        requester=requester,
        target=target_agent.id,
        objective=objective,
        capability=capability,
        action=action,
        params=params or {},
        depends_on=deps,
        depth=depth,
        selection=selection,
    )
    return store.get_task(task_id)  # type: ignore[return-value]


# --------------------------------------------------------------- execution


def _dependency_context(task: dict[str, Any], all_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Structured results from upstream tasks, so a receiver sees real outcomes."""
    by_id = {t["id"]: t for t in all_tasks}
    inputs = []
    for dep in task.get("depends_on") or []:
        upstream = by_id.get(dep)
        if not upstream:
            continue
        inputs.append(
            {
                "task_id": upstream["id"],
                "from_agent": upstream["target"],
                "status": upstream["status"],
                "objective": upstream["objective"],
                "result": upstream.get("result"),
            }
        )
    return {"inputs": inputs}


def execute_task(task_id: str, *, assistant: Any = None) -> dict[str, Any]:
    """Run one delegated task through the target agent's own permissions."""
    task = store.get_task(task_id)
    if not task:
        raise DelegationError(f"No task {task_id}")
    collaboration = store.get(task["collaboration_id"])
    limits = bounds_for(collaboration or {})

    if task["attempts"] >= limits["max_retries"] + 1:
        store.set_task_status(task_id, store.TASK_FAILED, error="retry budget exhausted")
        return store.get_task(task_id)  # type: ignore[return-value]

    store.set_task_status(task_id, store.TASK_RUNNING, bump_attempts=True)
    context = _dependency_context(task, store.tasks(task["collaboration_id"]))

    outcome = agents.invoke(
        task["target"],
        task["objective"],
        assistant=assistant,
        action=task["action"],
        params=task["params"],
        context=context,
    )

    if not outcome.get("ok"):
        status = (
            store.TASK_DENIED
            if outcome.get("error_kind") == "permission_denied"
            else store.TASK_FAILED
        )
        store.set_task_status(task_id, status, result=outcome, error=outcome.get("error") or "")
        store.record_event(
            task["collaboration_id"], f"task:{status}", f"{task['target']}: {outcome.get('error')}"
        )
        return store.get_task(task_id)  # type: ignore[return-value]

    # A delegated action that ran but reported failure is a partial result, not
    # a success — the receiving agent must be able to tell the difference.
    inner = outcome.get("result")
    status = store.TASK_SUCCESS
    if isinstance(inner, dict) and inner.get("ok") is False:
        status = store.TASK_PARTIAL

    result = {
        "task_id": task_id,
        "from_agent": task["target"],
        "requested_by": task["requester"],
        "status": status,
        "output": inner,
        "model": outcome.get("model"),
        "duration_ms": outcome.get("duration_ms"),
    }
    store.set_task_status(task_id, status, result=result)
    store.record_event(task["collaboration_id"], f"task:{status}", task["target"])
    return store.get_task(task_id)  # type: ignore[return-value]


def advance(collaboration_id: str, *, assistant: Any = None) -> dict[str, Any]:
    """Run every currently-ready task. One wave; the mission supplies the loop."""
    collaboration = store.get(collaboration_id)
    if not collaboration:
        raise DelegationError(f"No collaboration {collaboration_id}")
    if collaboration["status"] in store.TERMINAL_STATES:
        return {"done": True, "status": collaboration["status"], "executed": 0}

    store.set_status(collaboration_id, store.RUNNING)
    all_tasks = store.tasks(collaboration_id)
    graph.validate(all_tasks)

    ready = graph.ready_tasks(all_tasks, store.TASK_SATISFIED)
    executed = 0
    for task in ready:
        execute_task(task["id"], assistant=assistant)
        executed += 1

    all_tasks = store.tasks(collaboration_id)
    pending = [t for t in all_tasks if t["status"] in (store.TASK_PENDING, store.TASK_RUNNING)]
    blocked = graph.blocked_tasks(all_tasks, store.TASK_SATISFIED)
    for task in blocked:
        store.set_task_status(task["id"], store.TASK_SKIPPED, error="dependency did not succeed")

    remaining = [
        t
        for t in store.tasks(collaboration_id)
        if t["status"] in (store.TASK_PENDING, store.TASK_RUNNING)
    ]
    done = not remaining
    return {
        "done": done,
        "executed": executed,
        "pending": len(pending),
        "blocked": len(blocked),
        "status": store.get(collaboration_id)["status"],
    }


# ------------------------------------------------------------- aggregation


def aggregate(collaboration_id: str) -> dict[str, Any]:
    """Combine results while preserving attribution, conflicts and gaps."""
    collaboration = store.get(collaboration_id)
    if not collaboration:
        raise DelegationError(f"No collaboration {collaboration_id}")
    all_tasks = store.tasks(collaboration_id)

    succeeded = [t for t in all_tasks if t["status"] == store.TASK_SUCCESS]
    partial = [t for t in all_tasks if t["status"] == store.TASK_PARTIAL]
    failed = [t for t in all_tasks if t["status"] in (store.TASK_FAILED, store.TASK_DENIED)]
    skipped = [t for t in all_tasks if t["status"] == store.TASK_SKIPPED]

    # Disagreement is preserved, never resolved by picking the first result.
    by_objective: dict[str, list[dict[str, Any]]] = {}
    for task in succeeded + partial:
        by_objective.setdefault(task["objective"].strip().lower(), []).append(task)
    for objective, group in by_objective.items():
        agents_involved = {t["target"] for t in group}
        if len(agents_involved) > 1:
            store.add_conflict(
                collaboration_id,
                f"{len(agents_involved)} specialists answered {objective[:80]!r} independently",
                [t["id"] for t in group],
            )

    lines = [f"# Collaboration: {collaboration['objective']}", ""]
    lines.append(f"Initiator: {collaboration['initiator']}")
    participants = sorted({t["target"] for t in all_tasks})
    lines.append(f"Participants: {', '.join(participants) or 'none'}")
    lines.append("")
    lines.append("## Delegated results")
    if not all_tasks:
        lines.append("- no tasks were delegated")
    for task in all_tasks:
        lines.append(
            f"- `{task['id']}` {task['requester']} → {task['target']} [{task['status']}]: "
            f"{task['objective'][:90]}"
        )
        if task["status"] in (store.TASK_FAILED, store.TASK_DENIED) and task.get("error"):
            lines.append(f"    reason: {task['error'][:140]}")

    conflict_rows = store.conflicts(collaboration_id)
    if conflict_rows:
        lines.append("")
        lines.append("## Conflicting / independent answers")
        for c in conflict_rows:
            lines.append(f"- {c['description']}")

    unresolved = failed + skipped
    if unresolved:
        lines.append("")
        lines.append("## Unresolved")
        for task in unresolved:
            lines.append(f"- {task['target']}: {task['objective'][:90]} ({task['status']})")

    synthesis = "\n".join(lines)
    # A collaboration whose delegated work failed must not report success.
    if failed or skipped:
        store.update(collaboration_id, synthesis=synthesis)
        store.set_status(
            collaboration_id,
            store.FAILED,
            reason=f"{len(failed)} failed, {len(skipped)} skipped",
        )
    else:
        store.save_synthesis(collaboration_id, synthesis)

    return {
        "collaboration_id": collaboration_id,
        "status": store.get(collaboration_id)["status"],
        "succeeded": len(succeeded),
        "partial": len(partial),
        "failed": len(failed),
        "skipped": len(skipped),
        "conflicts": len(conflict_rows),
        "synthesis": synthesis,
    }


# ------------------------------------------------------- mission step + views


def step(collaboration_id: str, *, assistant: Any = None) -> dict[str, Any]:
    """One mission step: advance a wave, aggregating once nothing remains."""
    collaboration = store.get(collaboration_id)
    if not collaboration:
        raise DelegationError(f"No collaboration {collaboration_id}")
    if collaboration["status"] in store.TERMINAL_STATES:
        return {"done": True, "status": collaboration["status"]}

    # A collaboration with no delegated work yet is waiting, not finished.
    # Aggregating here would complete it on an empty task set and reject the
    # delegations still on their way. The wave budget bounds the wait.
    if not store.tasks(collaboration_id):
        store.set_status(collaboration_id, store.RUNNING)
        return {"done": False, "waiting": True, "executed": 0, "status": store.RUNNING}

    outcome = advance(collaboration_id, assistant=assistant)
    if outcome["done"]:
        return {**outcome, **aggregate(collaboration_id)}
    return outcome


def status(collaboration_id: str) -> dict[str, Any] | None:
    from jarvis import missions

    collaboration = store.get(collaboration_id)
    if not collaboration:
        return None
    all_tasks = store.tasks(collaboration_id)
    mission = (
        missions.status(collaboration["mission_id"]) if collaboration.get("mission_id") else None
    )
    return {
        "collaboration_id": collaboration["id"],
        "objective": collaboration["objective"],
        "initiator": collaboration["initiator"],
        "status": collaboration["status"],
        "reason": collaboration.get("reason"),
        "bounds": bounds_for(collaboration),
        "participants": sorted({t["target"] for t in all_tasks}),
        "tasks": {
            "total": len(all_tasks),
            "pending": sum(1 for t in all_tasks if t["status"] == store.TASK_PENDING),
            "succeeded": sum(1 for t in all_tasks if t["status"] == store.TASK_SUCCESS),
            "partial": sum(1 for t in all_tasks if t["status"] == store.TASK_PARTIAL),
            "failed": sum(1 for t in all_tasks if t["status"] == store.TASK_FAILED),
            "denied": sum(1 for t in all_tasks if t["status"] == store.TASK_DENIED),
            "skipped": sum(1 for t in all_tasks if t["status"] == store.TASK_SKIPPED),
        },
        "graph": graph.as_graph(all_tasks),
        "conflicts": [c["description"] for c in store.conflicts(collaboration_id)],
        "mission": mission,
        "synthesis": collaboration.get("synthesis"),
    }


def report(collaboration_id: str) -> dict[str, Any] | None:
    collaboration = store.get(collaboration_id)
    if not collaboration:
        return None
    return {
        "collaboration": collaboration,
        "tasks": store.tasks(collaboration_id),
        "graph": graph.as_graph(store.tasks(collaboration_id)),
        "conflicts": store.conflicts(collaboration_id),
        "history": store.history(collaboration_id),
        "synthesis": collaboration.get("synthesis"),
    }


def json_safe(value: Any) -> str:
    return json.dumps(value, default=str)
