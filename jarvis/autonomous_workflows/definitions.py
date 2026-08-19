"""Workflow and step definitions — the durable shape of autonomous work.

A workflow is an orchestration plan, not an implementation. Every step names an
existing ARIA capability and is executed by that capability under its own
permissions; nothing here re-implements research, coding, browsing or tools.

Not to be confused with two neighbouring systems: jarvis.workflow_learning mines
repeated action sequences from the action log, and jarvis.automation.pipelines
runs user-authored automation DAGs in process. This layer is the durable,
mission-backed one that composes the autonomous subsystems.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1

# Workflow states.
PENDING = "pending"
RUNNING = "running"
PAUSED = "paused"
WAITING = "waiting"
COMPLETED = "completed"
PARTIAL = "partial"
FAILED = "failed"
CANCELLED = "cancelled"
BLOCKED = "blocked"
STATES = (PENDING, RUNNING, PAUSED, WAITING, COMPLETED, PARTIAL, FAILED, CANCELLED, BLOCKED)
TERMINAL_STATES = (COMPLETED, PARTIAL, FAILED, CANCELLED)
LIVE_STATES = (PENDING, RUNNING, PAUSED, WAITING, BLOCKED)

# Step states.
STEP_PENDING = "pending"
STEP_READY = "ready"
STEP_RUNNING = "running"
STEP_SUCCEEDED = "succeeded"
STEP_FAILED = "failed"
STEP_SKIPPED = "skipped"
STEP_BLOCKED = "blocked"
STEP_CANCELLED = "cancelled"
STEP_TIMED_OUT = "timed_out"
STEP_STATES = (
    STEP_PENDING,
    STEP_READY,
    STEP_RUNNING,
    STEP_SUCCEEDED,
    STEP_FAILED,
    STEP_SKIPPED,
    STEP_BLOCKED,
    STEP_CANCELLED,
    STEP_TIMED_OUT,
)
STEP_TERMINAL = (
    STEP_SUCCEEDED,
    STEP_FAILED,
    STEP_SKIPPED,
    STEP_BLOCKED,
    STEP_CANCELLED,
    STEP_TIMED_OUT,
)
# A step that did not do its work, but not because it broke.
STEP_UNRESOLVED = (STEP_SKIPPED, STEP_BLOCKED, STEP_CANCELLED)

# What a step does when a dependency does not succeed.
ON_DEPENDENCY_FAILURE_BLOCK = "block"
ON_DEPENDENCY_FAILURE_SKIP = "skip"
ON_DEPENDENCY_FAILURE_RUN = "run_anyway"
DEPENDENCY_POLICIES = (
    ON_DEPENDENCY_FAILURE_BLOCK,
    ON_DEPENDENCY_FAILURE_SKIP,
    ON_DEPENDENCY_FAILURE_RUN,
)

# Conservative defaults. A workflow may lower these, never raise them.
LIMITS = {
    "max_steps": 40,
    "max_depth": 6,
    "max_parallel": 4,
    "max_runtime_s": 3600,
    "max_retries": 2,
    "max_child_agents": 8,
    "max_tool_calls": 40,
    "max_model_calls": 40,
    "max_browser_actions": 30,
    "max_output_bytes": 262144,
}

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class WorkflowDefinitionError(ValueError):
    """A workflow that must never be stored or executed."""


@dataclass(frozen=True)
class StepDefinition:
    """One unit of orchestrated work.

    `action` is a registered ARIA action; the workflow engine never implements
    the capability itself, so a step cannot do anything an action could not.
    """

    step_id: str
    action: str
    name: str = ""
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    agent_id: str = ""
    condition: dict[str, Any] = field(default_factory=dict)
    on_dependency_failure: str = ON_DEPENDENCY_FAILURE_BLOCK
    optional: bool = False
    max_retries: int = 1
    timeout_s: float = 300.0
    outputs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "name": self.name or self.step_id,
            "description": self.description,
            "params": dict(self.params),
            "depends_on": list(self.depends_on),
            "agent_id": self.agent_id,
            "condition": dict(self.condition),
            "on_dependency_failure": self.on_dependency_failure,
            "optional": self.optional,
            "max_retries": self.max_retries,
            "timeout_s": self.timeout_s,
            "outputs": list(self.outputs),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StepDefinition:
        if not isinstance(data, dict):
            raise WorkflowDefinitionError("A step must be an object")
        return cls(
            step_id=str(data.get("step_id") or "").strip(),
            action=str(data.get("action") or "").strip(),
            name=str(data.get("name") or "").strip(),
            description=str(data.get("description") or "").strip(),
            params=dict(data.get("params") or {}),
            depends_on=tuple(data.get("depends_on") or ()),
            agent_id=str(data.get("agent_id") or "").strip(),
            condition=dict(data.get("condition") or {}),
            on_dependency_failure=str(
                data.get("on_dependency_failure") or ON_DEPENDENCY_FAILURE_BLOCK
            ),
            optional=bool(data.get("optional")),
            max_retries=int(data.get("max_retries", 1)),
            timeout_s=float(data.get("timeout_s", 300.0)),
            outputs=tuple(data.get("outputs") or ()),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True)
class WorkflowDefinition:
    """An immutable plan. Once a run starts, its definition cannot change."""

    name: str
    steps: tuple[StepDefinition, ...]
    description: str = ""
    requester: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)
    template_id: str = ""
    template_version: str = ""
    schema_version: int = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def limit(self, name: str) -> int:
        """Effective limit. A workflow may tighten a bound, never loosen it."""
        default = LIMITS[name]
        asked = self.limits.get(name)
        if asked is None:
            return default
        return max(0, min(int(asked), default))

    def step(self, step_id: str) -> StepDefinition | None:
        for candidate in self.steps:
            if candidate.step_id == step_id:
                return candidate
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requester": self.requester,
            "inputs": dict(self.inputs),
            "limits": {k: self.limit(k) for k in LIMITS},
            "template_id": self.template_id,
            "template_version": self.template_version,
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        if not isinstance(data, dict):
            raise WorkflowDefinitionError("A workflow must be an object")
        raw_steps = data.get("steps")
        if not isinstance(raw_steps, list):
            raise WorkflowDefinitionError("steps must be a list")
        return cls(
            name=str(data.get("name") or "").strip(),
            description=str(data.get("description") or "").strip(),
            requester=str(data.get("requester") or "").strip(),
            inputs=dict(data.get("inputs") or {}),
            limits=dict(data.get("limits") or {}),
            template_id=str(data.get("template_id") or ""),
            template_version=str(data.get("template_version") or ""),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            metadata=dict(data.get("metadata") or {}),
            steps=tuple(StepDefinition.from_dict(s) for s in raw_steps),
        )
