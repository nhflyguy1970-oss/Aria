"""Coding Agent — persistent, bounded, permissioned autonomous development.

Layered on ARIA's existing coding infrastructure (CodingAgent, git_util,
patch_util, fs) and executed through the existing mission system.
"""

from jarvis.dev_agent.commands import (
    DEVELOPMENT,
    FORBIDDEN_BINARIES,
    FORBIDDEN_GIT,
    HIGH_IMPACT,
    READ_ONLY,
    CommandDenied,
    classify,
    parse_test_output,
)
from jarvis.dev_agent.commands import run as run_command
from jarvis.dev_agent.engine import (
    CodingAgentError,
    cancel,
    commit_task,
    complete,
    create_task,
    phase_diagnose,
    phase_implement,
    phase_inspect,
    phase_plan,
    phase_review,
    phase_test,
    recover,
    resolve_model,
    run_loop,
    status,
)
from jarvis.dev_agent.store import (
    BOUNDS,
    PHASES,
    TERMINAL,
    CodingTaskError,
    list_tasks,
    lock_holder,
)
from jarvis.dev_agent.store import events as task_events
from jarvis.dev_agent.store import get as get_task
from jarvis.dev_agent.workspace import (
    PathEscape,
    Workspace,
    WorkspaceError,
    open_workspace,
    repo_state,
    unrelated_changes_preserved,
)

__all__ = [
    "BOUNDS",
    "DEVELOPMENT",
    "FORBIDDEN_BINARIES",
    "FORBIDDEN_GIT",
    "HIGH_IMPACT",
    "PHASES",
    "READ_ONLY",
    "TERMINAL",
    "CodingAgentError",
    "CodingTaskError",
    "CommandDenied",
    "PathEscape",
    "Workspace",
    "WorkspaceError",
    "cancel",
    "classify",
    "commit_task",
    "complete",
    "create_task",
    "get_task",
    "list_tasks",
    "lock_holder",
    "open_workspace",
    "parse_test_output",
    "phase_diagnose",
    "phase_implement",
    "phase_inspect",
    "phase_plan",
    "phase_review",
    "phase_test",
    "recover",
    "repo_state",
    "resolve_model",
    "run_command",
    "run_loop",
    "status",
    "task_events",
    "unrelated_changes_preserved",
]
