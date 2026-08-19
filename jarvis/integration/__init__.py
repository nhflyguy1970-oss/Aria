"""ARIA as one integrated autonomous environment.

This layer adds no capability of its own. It gives the thirteen subsystems built
so far a shared vocabulary — one lifecycle, one execution context, one status,
one provenance graph — plus the two things that were genuinely missing: a bounded
autonomy policy with a safe mode, and recovery that actually runs at startup.

Every authority decision still belongs to the system that owns it. Missions,
workflows, agents, skills, MCP, model routing, research, evidence, browsing and
the coding agent are unchanged; this is the seam between them, not a replacement
for any of them.
"""

from jarvis.integration.context import (
    ExecutionContext,
    bind,
    correlate,
    create,
    current,
    new_request_id,
)
from jarvis.integration.lifecycle import (
    AUTHORIZED,
    BLOCKED,
    CANCELLED,
    COMPLETED,
    EXECUTING,
    FAILED,
    LIVE,
    PARTIAL,
    PAUSED,
    PLANNED,
    REQUESTED,
    STATES,
    TERMINAL,
    UNRESOLVED,
    VERIFYING,
    WAITING,
    describe,
    is_successful,
    is_terminal,
    summarise,
    unify,
)
from jarvis.integration.plan import (
    AGENT,
    ANSWER,
    ROUTES,
    SKILL,
    WORKFLOW,
    suggested_agent,
    triage,
)
from jarvis.integration.policy import (
    ASSISTED,
    BOUNDED,
    CONTINUOUS,
    DIRECT,
    LEVELS,
    PolicyError,
    apply_bounds,
    bounds_for,
    check,
    configured_level,
    effective_level,
    permits,
    safe_mode,
    worker_enabled,
)
from jarvis.integration.policy import snapshot as policy_snapshot
from jarvis.integration.provenance import for_request, for_workflow
from jarvis.integration.recovery import (
    last_startup_recovery,
    pending_recovery,
    recover_all,
    recover_on_demand,
    recover_on_startup,
)
from jarvis.integration.status import environment_status

__all__ = [
    "AGENT",
    "ANSWER",
    "ASSISTED",
    "AUTHORIZED",
    "BLOCKED",
    "BOUNDED",
    "CANCELLED",
    "COMPLETED",
    "CONTINUOUS",
    "DIRECT",
    "EXECUTING",
    "ExecutionContext",
    "FAILED",
    "LEVELS",
    "LIVE",
    "PARTIAL",
    "PAUSED",
    "PLANNED",
    "PolicyError",
    "REQUESTED",
    "ROUTES",
    "SKILL",
    "STATES",
    "TERMINAL",
    "UNRESOLVED",
    "VERIFYING",
    "WAITING",
    "WORKFLOW",
    "apply_bounds",
    "bind",
    "bounds_for",
    "check",
    "configured_level",
    "correlate",
    "create",
    "current",
    "describe",
    "effective_level",
    "environment_status",
    "for_request",
    "for_workflow",
    "is_successful",
    "is_terminal",
    "new_request_id",
    "permits",
    "policy_snapshot",
    "last_startup_recovery",
    "pending_recovery",
    "recover_all",
    "recover_on_demand",
    "recover_on_startup",
    "safe_mode",
    "suggested_agent",
    "summarise",
    "triage",
    "unify",
    "worker_enabled",
]
