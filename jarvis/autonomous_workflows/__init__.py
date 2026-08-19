"""Autonomous workflows — durable orchestration across ARIA's subsystems.

This layer composes; it does not reimplement. Missions provide durability and
recovery, the action registry provides dispatch, and agents, skills, MCP, model
routing, research, evidence, browsing and the coding agent each keep their own
permissions and provenance. A workflow can only ask for things that were
already possible.

Distinct from jarvis.workflow_learning (mining repeated action sequences) and
jarvis.automation.pipelines (user-authored in-process automation DAGs).
"""

from jarvis.autonomous_workflows.conditions import ConditionError
from jarvis.autonomous_workflows.conditions import describe as describe_condition
from jarvis.autonomous_workflows.conditions import evaluate as evaluate_condition
from jarvis.autonomous_workflows.definitions import (
    BLOCKED,
    CANCELLED,
    COMPLETED,
    FAILED,
    LIMITS,
    LIVE_STATES,
    PARTIAL,
    PAUSED,
    PENDING,
    RUNNING,
    STATES,
    STEP_BLOCKED,
    STEP_CANCELLED,
    STEP_FAILED,
    STEP_PENDING,
    STEP_RUNNING,
    STEP_SKIPPED,
    STEP_STATES,
    STEP_SUCCEEDED,
    STEP_TERMINAL,
    STEP_TIMED_OUT,
    TERMINAL_STATES,
    WAITING,
    StepDefinition,
    WorkflowDefinition,
    WorkflowDefinitionError,
)
from jarvis.autonomous_workflows.engine import (
    WorkflowError,
    attach_mission,
    cancel,
    create_workflow,
    pause,
    recover,
    resume,
    run,
    run_slice,
    status,
    validate,
)
from jarvis.autonomous_workflows.graph import GraphError, detect_cycle, ready_steps
from jarvis.autonomous_workflows.graph import topological_order as order_steps
from jarvis.autonomous_workflows.refs import ReferenceError, resolve_params
from jarvis.autonomous_workflows.store import (
    WorkflowStateError,
    events,
    get,
    list_workflows,
)
from jarvis.autonomous_workflows.templates import (
    TEMPLATE_VERSION,
    get_template,
    instantiate,
    list_templates,
)

__all__ = [
    "BLOCKED",
    "CANCELLED",
    "COMPLETED",
    "ConditionError",
    "FAILED",
    "GraphError",
    "LIMITS",
    "LIVE_STATES",
    "PARTIAL",
    "PAUSED",
    "PENDING",
    "RUNNING",
    "ReferenceError",
    "STATES",
    "STEP_BLOCKED",
    "STEP_CANCELLED",
    "STEP_FAILED",
    "STEP_PENDING",
    "STEP_RUNNING",
    "STEP_SKIPPED",
    "STEP_STATES",
    "STEP_SUCCEEDED",
    "STEP_TERMINAL",
    "STEP_TIMED_OUT",
    "StepDefinition",
    "TEMPLATE_VERSION",
    "TERMINAL_STATES",
    "WAITING",
    "WorkflowDefinition",
    "WorkflowDefinitionError",
    "WorkflowError",
    "WorkflowStateError",
    "attach_mission",
    "cancel",
    "create_workflow",
    "describe_condition",
    "detect_cycle",
    "evaluate_condition",
    "events",
    "get",
    "get_template",
    "instantiate",
    "list_templates",
    "list_workflows",
    "order_steps",
    "pause",
    "ready_steps",
    "recover",
    "resolve_params",
    "resume",
    "run",
    "run_slice",
    "status",
    "validate",
]
