"""Agent delegation and collaboration — specialists working toward a shared goal.

Extends the specialized-agent framework: delegation is permissioned on both
sides, the task graph is acyclic and bounded, results are structured, and
execution durability comes from the existing mission system.
"""

from jarvis.collaboration.engine import (
    DEFAULT_BOUNDS,
    BoundExceeded,
    DelegationError,
    advance,
    aggregate,
    bounds_for,
    create_collaboration,
    delegate,
    execute_task,
    report,
    status,
    step,
)
from jarvis.collaboration.graph import GraphError, as_graph, detect_cycle, ready_tasks, validate
from jarvis.collaboration.store import (
    TASK_DENIED,
    TASK_FAILED,
    TASK_PARTIAL,
    TASK_PENDING,
    TASK_SKIPPED,
    TASK_SUCCESS,
    TASK_UNRESOLVED,
    conflicts,
    get,
    history,
    list_collaborations,
    tasks,
)

__all__ = [
    "DEFAULT_BOUNDS",
    "BoundExceeded",
    "DelegationError",
    "GraphError",
    "TASK_DENIED",
    "TASK_FAILED",
    "TASK_PARTIAL",
    "TASK_PENDING",
    "TASK_SKIPPED",
    "TASK_SUCCESS",
    "TASK_UNRESOLVED",
    "advance",
    "aggregate",
    "as_graph",
    "bounds_for",
    "conflicts",
    "create_collaboration",
    "delegate",
    "detect_cycle",
    "execute_task",
    "get",
    "history",
    "list_collaborations",
    "ready_tasks",
    "report",
    "status",
    "step",
    "tasks",
    "validate",
]
