"""Collaboration task graph — dependencies, cycle rejection, ready-set computation.

Delegation forms a directed acyclic graph. Cycles are rejected *before*
execution rather than caught by a runtime depth counter, because a cycle is a
definition error, not a resource problem: a task that (directly or indirectly)
depends on itself can never become ready.
"""

from __future__ import annotations

from typing import Any


class GraphError(ValueError):
    """The delegation graph is not executable."""


def detect_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """Return a cycle path if one exists, else None.

    edges maps task id -> ids it depends on. Iterative DFS with an explicit
    stack so a deep graph cannot blow the interpreter stack.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {node: WHITE for node in edges}

    for start in edges:
        if colour[start] != WHITE:
            continue
        stack: list[tuple[str, list[str]]] = [(start, [start])]
        while stack:
            node, path = stack.pop()
            if colour.get(node) == GREY:
                colour[node] = BLACK
                continue
            if colour.get(node) == BLACK:
                continue
            colour[node] = GREY
            stack.append((node, path))
            for dep in edges.get(node, []):
                if dep not in colour:
                    continue  # dependency on an unknown task is validated elsewhere
                if colour[dep] == GREY:
                    return path + [dep]
                if colour[dep] == WHITE:
                    stack.append((dep, path + [dep]))
    return None


def validate(tasks: list[dict[str, Any]]) -> None:
    """Reject self-dependency, unknown dependencies and cycles."""
    ids = {t["id"] for t in tasks}
    edges: dict[str, list[str]] = {}
    for task in tasks:
        deps = list(task.get("depends_on") or [])
        if task["id"] in deps:
            raise GraphError(f"Task {task['id']} depends on itself")
        unknown = [d for d in deps if d not in ids]
        if unknown:
            raise GraphError(f"Task {task['id']} depends on unknown task(s): {unknown}")
        edges[task["id"]] = deps
    cycle = detect_cycle(edges)
    if cycle:
        raise GraphError(f"Delegation cycle detected: {' -> '.join(cycle)}")


def would_create_cycle(
    tasks: list[dict[str, Any]], new_task_id: str, depends_on: list[str]
) -> bool:
    """Check a prospective task before it is persisted."""
    edges = {t["id"]: list(t.get("depends_on") or []) for t in tasks}
    edges[new_task_id] = list(depends_on)
    if new_task_id in depends_on:
        return True
    return detect_cycle(edges) is not None


def ready_tasks(tasks: list[dict[str, Any]], satisfied: tuple[str, ...]) -> list[dict[str, Any]]:
    """Pending tasks whose dependencies have all produced a usable result."""
    by_id = {t["id"]: t for t in tasks}
    out = []
    for task in tasks:
        if task["status"] != "pending":
            continue
        deps = task.get("depends_on") or []
        if all(by_id.get(d, {}).get("status") in satisfied for d in deps):
            out.append(task)
    return out


def blocked_tasks(tasks: list[dict[str, Any]], satisfied: tuple[str, ...]) -> list[dict[str, Any]]:
    """Pending tasks that can never run because a dependency did not succeed."""
    by_id = {t["id"]: t for t in tasks}
    out = []
    for task in tasks:
        if task["status"] != "pending":
            continue
        for dep in task.get("depends_on") or []:
            dep_task = by_id.get(dep)
            if not dep_task:
                continue
            if dep_task["status"] not in satisfied and dep_task["status"] != "pending":
                if dep_task["status"] != "running":
                    out.append(task)
                    break
    return out


def as_graph(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Inspectable structure for the UI/API."""
    return {
        "nodes": [
            {
                "id": t["id"],
                "requester": t["requester"],
                "target": t["target"],
                "objective": t["objective"],
                "status": t["status"],
                "depth": t["depth"],
                "attempts": t["attempts"],
            }
            for t in tasks
        ],
        "edges": [
            {"from": dep, "to": t["id"]} for t in tasks for dep in (t.get("depends_on") or [])
        ],
    }
