"""Autonomous workflow handlers — create, validate, run, control, observe.

Named to avoid the older workflow_handlers, which serves learned action
sequences. Two actions here use distinct names (workflow_index, workflow_start)
because workflow_list and workflow_run already belong to that system.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _workflows():
    from jarvis import autonomous_workflows

    return autonomous_workflows


def _definition_from_params(params: dict):
    """Build a definition from an explicit body or from a template."""
    workflows = _workflows()
    template_id = (params.get("template_id") or "").strip()
    inputs = params.get("inputs")
    if inputs is not None and not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    if template_id:
        definition = workflows.instantiate(
            template_id, inputs or {}, requester=(params.get("requester") or "").strip()
        )
        if params.get("name"):
            definition["name"] = str(params["name"])
        return definition

    definition = params.get("definition") or params.get("workflow")
    if not isinstance(definition, dict):
        raise ValueError("workflow_create needs a definition object or a template_id")
    definition = dict(definition)
    if inputs is not None:
        definition["inputs"] = inputs
    if params.get("name"):
        definition["name"] = str(params["name"])
    return definition


@register_action("workflow_create", module="general", description="Create an autonomous workflow")
def workflow_create(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    try:
        definition = _definition_from_params(params)
    except (ValueError, KeyError) as exc:
        return err(str(exc), module="general", error_kind="invalid_definition")
    try:
        workflow = workflows.create_workflow(
            definition,
            requester=(params.get("requester") or params.get("agent_id") or "").strip(),
            create_mission=bool(params.get("mission", True)),
        )
    except workflows.WorkflowDefinitionError as exc:
        # An invalid workflow is refused before any work happens.
        return err(str(exc), module="general", error_kind="invalid_definition")
    except workflows.GraphError as exc:
        return err(str(exc), module="general", error_kind="invalid_graph")
    return ok(
        f"Workflow `{workflow['id']}` created — {workflow['name']}",
        module="general",
        workflow_id=workflow["id"],
        mission_id=workflow.get("mission_id", ""),
        steps=len(workflow.get("steps") or []),
    )


@register_action(
    "workflow_validate",
    module="general",
    description="Validate a workflow definition without running it",
    info=True,
)
def workflow_validate(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    try:
        definition = _definition_from_params(params)
        parsed = workflows.WorkflowDefinition.from_dict(definition)
        report = workflows.validate(parsed)
    except (ValueError, KeyError) as exc:
        return err(
            str(exc),
            module="general",
            error_kind="invalid_definition",
            report={"ok": False, "problems": [str(exc)]},
        )
    except workflows.GraphError as exc:
        return err(
            str(exc),
            module="general",
            error_kind="invalid_graph",
            report={"ok": False, "problems": [str(exc)]},
        )
    if not report["ok"]:
        return err(
            "; ".join(report["problems"])[:800],
            module="general",
            error_kind="invalid_definition",
            report=report,
        )
    return ok(
        f"Valid: {report['steps']} step(s), depth {report['depth']}.",
        module="general",
        report=report,
    )


@register_action(
    "workflow_status", module="general", description="Show an autonomous workflow", info=True
)
def workflow_status(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or params.get("id") or "").strip()
    snapshot = workflows.status(workflow_id) if workflow_id else None
    if not snapshot:
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    lines = [
        f"**Workflow {snapshot['workflow_id']}** — {snapshot['state']}",
        f"{snapshot['name']}",
        f"Steps: {snapshot['succeeded']}/{snapshot['steps_total']} succeeded"
        f" · {snapshot['failed']} failed · {snapshot['blocked']} blocked"
        f" · {snapshot['skipped']} skipped",
    ]
    if snapshot["current_step"]:
        lines.append(f"Current step: {snapshot['current_step']}")
    if snapshot["error"]:
        lines.append(f"Error: {snapshot['error']}")
    return ok("\n".join(lines), module="general", workflow=snapshot)


@register_action(
    "workflow_index", module="general", description="List autonomous workflows", info=True
)
def workflow_index(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    rows = workflows.list_workflows(
        state=(params.get("state") or "").strip(), limit=int(params.get("limit") or 20)
    )
    if not rows:
        return ok("No autonomous workflows.", module="general", workflows=[])
    lines = [f"- `{r['id']}` [{r['state']}] {r['name']}" for r in rows]
    return ok("\n".join(lines), module="general", workflows=rows)


@register_action(
    "workflow_start", module="general", description="Run or continue an autonomous workflow"
)
def workflow_start(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or "").strip()
    if not workflows.get(workflow_id):
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    max_steps = params.get("max_steps")
    try:
        workflows.run(
            workflow_id,
            assistant=assistant,
            max_steps=int(max_steps) if max_steps else None,
        )
    except workflows.WorkflowError as exc:
        return err(str(exc), module="general", error_kind="workflow")
    snapshot = workflows.status(workflow_id) or {}
    return ok(
        f"Workflow `{workflow_id}` — {snapshot.get('state')}"
        f" ({snapshot.get('succeeded')}/{snapshot.get('steps_total')} succeeded)",
        module="general",
        workflow=snapshot,
    )


@register_action("workflow_pause", module="general", description="Pause an autonomous workflow")
def workflow_pause(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or "").strip()
    if not workflows.get(workflow_id):
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    try:
        workflows.pause(workflow_id)
    except workflows.WorkflowStateError as exc:
        return err(str(exc), module="general", error_kind="illegal_transition")
    return ok(
        f"Workflow `{workflow_id}` paused.",
        module="general",
        workflow=workflows.status(workflow_id),
    )


@register_action("workflow_resume", module="general", description="Resume a paused workflow")
def workflow_resume(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or "").strip()
    if not workflows.get(workflow_id):
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    try:
        workflows.resume(workflow_id, assistant=assistant)
    except workflows.WorkflowStateError as exc:
        return err(str(exc), module="general", error_kind="illegal_transition")
    return ok(
        f"Workflow `{workflow_id}` resumed.",
        module="general",
        workflow=workflows.status(workflow_id),
    )


@register_action("workflow_cancel", module="general", description="Cancel an autonomous workflow")
def workflow_cancel(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or "").strip()
    if not workflows.get(workflow_id):
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    workflows.cancel(workflow_id)
    return ok(
        f"Workflow `{workflow_id}` cancelled.",
        module="general",
        workflow=workflows.status(workflow_id),
    )


@register_action(
    "workflow_recover",
    module="general",
    description="Recover workflows interrupted by a restart",
    info=True,
)
def workflow_recover(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    recovered = workflows.recover()
    if not recovered:
        return ok("No interrupted workflows.", module="general", recovered=[])
    joined = ", ".join(f"`{w}`" for w in recovered)
    return ok(
        f"Recovered {len(recovered)} workflow(s): {joined}. They can be resumed.",
        module="general",
        recovered=recovered,
    )


@register_action(
    "workflow_templates", module="general", description="List workflow templates", info=True
)
def workflow_templates(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    rows = workflows.list_templates()
    lines = [
        f"- `{t['template_id']}` v{t['version']} ({t['steps']} steps) — {t['name']}" for t in rows
    ]
    return ok("\n".join(lines), module="general", templates=rows)


@register_action(
    "workflow_events", module="general", description="Show a workflow's event log", info=True
)
def workflow_events(assistant, params: dict, message: str) -> dict:
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or "").strip()
    if not workflows.get(workflow_id):
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    rows = workflows.events(workflow_id, limit=int(params.get("limit") or 50))
    lines = [
        f"- {r['kind']}" + (f" [{r['step_id']}]" if r["step_id"] else "") + f": {r['detail']}"
        for r in rows
    ]
    return ok("\n".join(lines) or "No events.", module="general", events=rows)


@register_action(
    "workflow_step",
    module="general",
    description="Advance a workflow by one step (used by the mission worker)",
)
def workflow_step(assistant, params: dict, message: str) -> dict:
    """One durable slice of workflow progress, driven by the existing worker."""
    workflows = _workflows()
    workflow_id = (params.get("workflow_id") or "").strip()
    if not workflows.get(workflow_id):
        return err(f"No such workflow: {workflow_id}", module="general", error_kind="not_found")
    mission_id = (params.get("mission_id") or "").strip()

    cancel_check = None
    if mission_id:
        from jarvis.missions import store as mstore

        def cancel_check() -> bool:  # noqa: E306
            return mstore.cancel_requested(mission_id)

    result = workflows.run_slice(
        workflow_id,
        assistant=assistant,
        max_steps=int(params.get("max_steps") or 1),
        cancel_check=cancel_check,
    )
    workflow = result["workflow"]
    if workflow["state"] == workflows.CANCELLED:
        from jarvis.missions.engine import MissionCancelled

        # Cancelled is not failed: let the mission record it as cancelled.
        raise MissionCancelled(f"workflow {workflow_id} cancelled")
    if workflow["state"] == workflows.FAILED:
        # A returned dict counts as a completed step, so a failed workflow has
        # to raise or the mission would report work that did not happen.
        raise RuntimeError(f"workflow {workflow_id} failed: {workflow.get('error') or ''}")
    return ok(
        f"workflow {workflow_id}: {workflow['state']}",
        module="general",
        workflow_id=workflow_id,
        state=workflow["state"],
        ran=[r.get("step_id") for r in result.get("ran") or []],
    )
