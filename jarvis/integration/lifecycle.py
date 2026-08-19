"""The lifecycle of autonomous work, expressed once for the whole environment.

Every subsystem already has its own states — missions, workflows, skills, MCP
invocations, coding tasks. This module does not replace any of them; it maps
them onto one vocabulary so a person can ask "what is ARIA doing?" without
knowing which subsystem is answering.

The mapping is deliberately pessimistic. Where a subsystem's state is ambiguous
it lands on the less flattering side, because the one thing this layer must
never do is report work as finished, verified or autonomous when it was not.
"""

from __future__ import annotations

from typing import Any

# The unified lifecycle.
REQUESTED = "requested"
PLANNED = "planned"
AUTHORIZED = "authorized"
EXECUTING = "executing"
WAITING = "waiting"
VERIFYING = "verifying"
COMPLETED = "completed"

PAUSED = "paused"
FAILED = "failed"
CANCELLED = "cancelled"
BLOCKED = "blocked"
PARTIAL = "partial"
UNRESOLVED = "unresolved"

STATES = (
    REQUESTED,
    PLANNED,
    AUTHORIZED,
    EXECUTING,
    WAITING,
    VERIFYING,
    COMPLETED,
    PAUSED,
    FAILED,
    CANCELLED,
    BLOCKED,
    PARTIAL,
    UNRESOLVED,
)
TERMINAL = (COMPLETED, FAILED, CANCELLED, PARTIAL, UNRESOLVED)
LIVE = (REQUESTED, PLANNED, AUTHORIZED, EXECUTING, WAITING, VERIFYING, PAUSED, BLOCKED)

# Subsystem state -> unified state. Anything unmapped becomes UNRESOLVED rather
# than being guessed at.
_WORKFLOW = {
    "pending": REQUESTED,
    "running": EXECUTING,
    "waiting": WAITING,
    "paused": PAUSED,
    "blocked": BLOCKED,
    "completed": COMPLETED,
    "partial": PARTIAL,
    "failed": FAILED,
    "cancelled": CANCELLED,
}

_MISSION = {
    "pending": REQUESTED,
    "running": EXECUTING,
    "paused": PAUSED,
    "completed": COMPLETED,
    "failed": FAILED,
    "cancelled": CANCELLED,
}

_RESEARCH = {
    "pending": REQUESTED,
    "planning": PLANNED,
    "running": EXECUTING,
    "searching": EXECUTING,
    "collecting": EXECUTING,
    "analyzing": VERIFYING,
    "synthesizing": VERIFYING,
    "completed": COMPLETED,
    "failed": FAILED,
    "cancelled": CANCELLED,
    "paused": PAUSED,
}

_CODING = {
    "pending": REQUESTED,
    "planning": PLANNED,
    "inspecting": EXECUTING,
    "implementing": EXECUTING,
    "testing": VERIFYING,
    "diagnosing": VERIFYING,
    "fixing": EXECUTING,
    "reviewing": VERIFYING,
    "completed": COMPLETED,
    "failed": FAILED,
    "cancelled": CANCELLED,
    "bounded": PARTIAL,
    "paused": PAUSED,
}

_KINDS = {
    "workflow": _WORKFLOW,
    "mission": _MISSION,
    "research": _RESEARCH,
    "coding": _CODING,
}


def unify(kind: str, state: str) -> str:
    """Map a subsystem state onto the environment lifecycle."""
    table = _KINDS.get(kind)
    if not table:
        return UNRESOLVED
    return table.get((state or "").strip().lower(), UNRESOLVED)


def is_terminal(state: str) -> bool:
    return state in TERMINAL


def is_successful(state: str) -> bool:
    """Only one state means the work actually got done."""
    return state == COMPLETED


def describe(state: str) -> str:
    return {
        REQUESTED: "queued, not started",
        PLANNED: "planned, not yet authorized to run",
        AUTHORIZED: "authorized, waiting to execute",
        EXECUTING: "running now",
        WAITING: "waiting on something external",
        VERIFYING: "checking its own work",
        COMPLETED: "finished successfully",
        PAUSED: "paused; no new work will start",
        FAILED: "failed",
        CANCELLED: "cancelled",
        BLOCKED: "blocked by a dependency that did not succeed",
        PARTIAL: "partly done: some work succeeded and some did not",
        UNRESOLVED: "state could not be determined from the subsystem",
    }.get(state, "unknown")


def summarise(states: list[str]) -> str:
    """One state for a set of work items, erring toward the truth.

    A single failure is not hidden behind a majority of successes, and anything
    still running keeps the whole set in EXECUTING.
    """
    if not states:
        return REQUESTED
    if any(s == CANCELLED for s in states):
        return CANCELLED
    live = [s for s in states if s in LIVE and s != PAUSED]
    if live:
        return EXECUTING
    if all(s == PAUSED for s in states):
        return PAUSED
    if any(s in (FAILED, BLOCKED) for s in states):
        return PARTIAL if any(s == COMPLETED for s in states) else FAILED
    if any(s == PARTIAL for s in states):
        return PARTIAL
    if any(s == UNRESOLVED for s in states):
        return UNRESOLVED
    return COMPLETED if all(s == COMPLETED for s in states) else PARTIAL


def as_dict(kind: str, state: str) -> dict[str, Any]:
    unified = unify(kind, state)
    return {
        "kind": kind,
        "subsystem_state": state,
        "state": unified,
        "description": describe(unified),
        "terminal": is_terminal(unified),
        "successful": is_successful(unified),
    }
