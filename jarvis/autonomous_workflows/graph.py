"""Dependency graph for workflow steps.

Iterative throughout, matching the collaboration and skills graphs: a deep
workflow must not be limited by Python's recursion depth, and a cycle must be
found before any work is done rather than discovered by hanging.
"""

from __future__ import annotations

from typing import Any

from jarvis.autonomous_workflows.definitions import (
    STEP_SUCCEEDED,
    STEP_TERMINAL,
    WorkflowDefinition,
)


class GraphError(ValueError):
    """A dependency structure that cannot be executed."""


def edges_of(definition: WorkflowDefinition) -> dict[str, list[str]]:
    return {s.step_id: list(s.depends_on) for s in definition.steps}


def detect_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """Return a cycle path if one exists, else None.

    Iterative DFS with an explicit stack, so a deeply chained workflow cannot
    overflow the interpreter stack while being validated.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = dict.fromkeys(edges, WHITE)
    for node in edges:
        for dep in edges[node]:
            colour.setdefault(dep, WHITE)

    for start in list(colour):
        if colour[start] != WHITE:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        path: list[str] = [start]
        colour[start] = GREY
        while stack:
            node, index = stack[-1]
            children = edges.get(node) or []
            if index < len(children):
                stack[-1] = (node, index + 1)
                child = children[index]
                state = colour.get(child, WHITE)
                if state == GREY:
                    return [*path[path.index(child) :], child]
                if state == WHITE:
                    colour[child] = GREY
                    path.append(child)
                    stack.append((child, 0))
            else:
                colour[node] = BLACK
                stack.pop()
                if path:
                    path.pop()
    return None


def depth_of(edges: dict[str, list[str]]) -> int:
    """Longest dependency chain. Assumes the graph is already acyclic."""
    memo: dict[str, int] = {}
    for start in edges:
        if start in memo:
            continue
        stack = [(start, False)]
        while stack:
            node, expanded = stack.pop()
            if expanded:
                deps = edges.get(node) or []
                memo[node] = 1 + max((memo.get(d, 0) for d in deps), default=0)
                continue
            if node in memo:
                continue
            stack.append((node, True))
            for dep in edges.get(node) or []:
                if dep not in memo:
                    stack.append((dep, False))
    return max(memo.values(), default=0)


def topological_order(definition: WorkflowDefinition) -> list[str]:
    """Dependencies first, then by step id, so ordering is reproducible."""
    edges = edges_of(definition)
    cycle = detect_cycle(edges)
    if cycle:
        raise GraphError(f"dependency cycle: {' -> '.join(cycle)}")
    remaining = {k: set(v) for k, v in edges.items()}
    order: list[str] = []
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if not deps - set(order))
        if not ready:
            raise GraphError("unresolvable dependencies")
        for node in ready:
            order.append(node)
            remaining.pop(node, None)
    return order


def ready_steps(
    definition: WorkflowDefinition, states: dict[str, str], *, limit: int | None = None
) -> list[str]:
    """Steps whose dependencies have all settled and which have not run yet.

    Settled, not succeeded: a step whose dependency failed still has to be
    reached so its on_dependency_failure policy can decide whether it is
    blocked, skipped or runs anyway. Deciding that here would put the policy in
    two places.

    Returned in topological then alphabetical order, so a run is reproducible
    even when several steps become ready at once.
    """
    ready: list[str] = []
    order = topological_order(definition)
    for step_id in order:
        if states.get(step_id, "pending") not in ("pending", "ready"):
            continue
        step = definition.step(step_id)
        if step is None:
            continue
        if all(states.get(dep, "pending") in STEP_TERMINAL for dep in step.depends_on):
            ready.append(step_id)
        if limit is not None and len(ready) >= limit:
            break
    return ready


def unresolved_dependencies(
    definition: WorkflowDefinition, states: dict[str, str]
) -> dict[str, list[str]]:
    """Which steps are held up, and by which dependencies."""
    held: dict[str, list[str]] = {}
    for step in definition.steps:
        if states.get(step.step_id, "pending") in ("pending", "ready"):
            bad = [
                dep for dep in step.depends_on if states.get(dep) and states[dep] != STEP_SUCCEEDED
            ]
            if bad:
                held[step.step_id] = bad
    return held


def ancestors_of(definition: WorkflowDefinition, step_id: str) -> set[str]:
    """Every step that must have finished before this one starts.

    Transitive: if C depends on B and B on A, then A has completed by the time
    C runs, so C may legitimately use A's output.
    """
    edges = edges_of(definition)
    seen: set[str] = set()
    stack = list(edges.get(step_id) or [])
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(edges.get(node) or [])
    return seen


def validate_graph(definition: WorkflowDefinition) -> dict[str, Any]:
    """Reject a structure that cannot be executed, before any work happens."""
    problems: list[str] = []
    seen: set[str] = set()
    for step in definition.steps:
        if not step.step_id:
            problems.append("a step has no step_id")
            continue
        if step.step_id in seen:
            problems.append(f"duplicate step_id: {step.step_id}")
        seen.add(step.step_id)
        if step.step_id in step.depends_on:
            problems.append(f"{step.step_id} depends on itself")
    for step in definition.steps:
        for dep in step.depends_on:
            if dep not in seen:
                problems.append(f"{step.step_id} depends on unknown step {dep!r}")

    edges = edges_of(definition)
    cycle = detect_cycle(edges) if not problems else None
    if cycle:
        problems.append(f"dependency cycle: {' -> '.join(cycle)}")

    depth = 0 if problems else depth_of(edges)
    max_depth = definition.limit("max_depth")
    if depth > max_depth:
        problems.append(f"dependency depth {depth} exceeds max_depth {max_depth}")

    return {"ok": not problems, "problems": problems, "depth": depth, "steps": len(seen)}
