"""Reusable workflow DAG engine — thin compatibility layer over Automation Pipelines.

Prefer jarvis.automation.pipelines for new code. This module keeps existing imports working.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from jarvis.automation.paths import WORKFLOW_DAGS_DIR
from jarvis.automation.pipelines.storage import (
    create_from_template as _create_from_template,
)
from jarvis.automation.pipelines.storage import get_pipeline, list_pipelines, save_pipeline
from jarvis.automation.pipelines.templates import TEMPLATES as _PIPE_TEMPLATES

WORKFLOW_DIR = WORKFLOW_DAGS_DIR

# Back-compat template key list for APIs that expect TEMPLATES dict of raw defs
TEMPLATES: dict[str, dict[str, Any]] = {
    tid: {
        "name": t["name"],
        "tags": t.get("tags") or [],
        "entry": t.get("entry"),
        "steps": t.get("steps") or [],
        "description": t.get("description") or "",
    }
    for tid, t in _PIPE_TEMPLATES.items()
}


@dataclass
class WorkflowStep:
    id: str
    name: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    next: list[str] = field(default_factory=list)
    on_success: list[str] = field(default_factory=list)
    on_failure: list[str] = field(default_factory=list)
    retries: int = 0
    retry_delay_sec: float = 0.5
    when: str = ""
    timeout_sec: float | None = None


@dataclass
class WorkflowDef:
    id: str
    name: str
    version: int = 1
    steps: list[WorkflowStep] = field(default_factory=list)
    entry: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


def _step_from_dict(d: dict[str, Any]) -> WorkflowStep:
    return WorkflowStep(
        id=str(d["id"]),
        name=str(d.get("name") or d["id"]),
        action=str(d.get("action") or ""),
        params=dict(d.get("params") or {}),
        next=list(d.get("next") or []),
        on_success=list(d.get("on_success") or []),
        on_failure=list(d.get("on_failure") or []),
        retries=int(d.get("retries") or 0),
        retry_delay_sec=float(d.get("retry_delay_sec") or 0.5),
        when=str(d.get("when") or ""),
        timeout_sec=float(d["timeout_sec"]) if d.get("timeout_sec") else None,
    )


def workflow_from_template(template_id: str, *, name: str | None = None) -> WorkflowDef:
    data = _create_from_template(template_id, name=name)
    return load_workflow(data["id"])


def save_workflow(wf: WorkflowDef) -> Path:
    payload = {
        "id": wf.id,
        "name": wf.name,
        "version": wf.version,
        "entry": wf.entry,
        "variables": wf.variables,
        "tags": wf.tags,
        "steps": [asdict(s) for s in wf.steps],
    }
    saved = save_pipeline(payload, bump_version=False)
    return WORKFLOW_DIR / f"{saved['id']}.json"


def load_workflow(workflow_id: str) -> WorkflowDef:
    data = get_pipeline(workflow_id)
    if not data:
        raise FileNotFoundError(workflow_id)
    return WorkflowDef(
        id=data["id"],
        name=data.get("name") or data["id"],
        version=int(data.get("version") or 1),
        entry=data.get("entry") or "",
        variables=dict(data.get("variables") or {}),
        tags=list(data.get("tags") or []),
        steps=[_step_from_dict(s) for s in data.get("steps") or []],
    )


def list_workflows() -> list[dict[str, Any]]:
    return list_pipelines()


def run_workflow(
    workflow_id: str,
    *,
    variables: dict[str, Any] | None = None,
    action_runner: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    dry_run: bool = False,
    approve_experimental: bool = False,
    from_step: str | None = None,
    trigger: str = "api",
    emit_bridges: bool = True,
) -> dict[str, Any]:
    """Run via Automation Pipelines engine. action_runner kept for rare custom injectors."""
    if action_runner is not None:
        # Legacy path: inject custom runner by temporarily wrapping execute
        from jarvis.automation.pipelines import actions as act_mod

        original = act_mod.execute_action

        def _wrapped(action, params, variables, *, dry_run=False, approve_experimental=False):
            if dry_run or action.startswith("builtin:"):
                return original(
                    action, params, variables, dry_run=dry_run, approve_experimental=approve_experimental
                )
            try:
                return action_runner(action, {**params, "variables": variables})
            except Exception as exc:
                return {"ok": False, "error": str(exc)}

        act_mod.execute_action = _wrapped  # type: ignore[assignment]
        try:
            from jarvis.automation.pipelines.engine import run_pipeline

            return run_pipeline(
                workflow_id,
                variables=variables,
                dry_run=dry_run,
                approve_experimental=approve_experimental,
                from_step=from_step,
                trigger=trigger,
                emit_bridges=emit_bridges,
            )
        finally:
            act_mod.execute_action = original  # type: ignore[assignment]

    from jarvis.automation.pipelines.engine import run_pipeline

    return run_pipeline(
        workflow_id,
        variables=variables,
        dry_run=dry_run,
        approve_experimental=approve_experimental,
        from_step=from_step,
        trigger=trigger,
        emit_bridges=emit_bridges,
    )
