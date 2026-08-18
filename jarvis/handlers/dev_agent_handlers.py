"""Coding Agent handlers — task lifecycle, commands, mission steps."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("dev_task_create", module="coding", description="Create an autonomous coding task")
def dev_task_create(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    objective = (params.get("objective") or message or "").strip()
    root = (params.get("workspace") or "").strip()
    if not objective or not root:
        return err("dev_task_create needs objective and workspace.", module="coding")
    try:
        task = dev_agent.create_task(
            objective, root, create_mission=bool(params.get("create_mission"))
        )
    except (dev_agent.CodingAgentError, dev_agent.WorkspaceError) as exc:
        return err(str(exc), module="coding", error_kind="coding_task")
    return ok(
        f"Coding task `{task['id']}` created.", module="coding", task_id=task["id"], task=task
    )


@register_action("dev_task_status", module="coding", description="Show a coding task", info=True)
def dev_task_status(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    task_id = (params.get("task_id") or params.get("id") or "").strip()
    snap = dev_agent.status(task_id) if task_id else None
    if not snap:
        return err(f"No coding task `{task_id}`.", module="coding")
    lines = [
        f"**Coding task {snap['task_id']}** — {snap['phase']}",
        f"Objective: {snap['objective']}",
        f"Workspace: {snap['workspace']} (branch {snap['branch'] or '—'})",
        f"Iterations: {snap['iterations']} · Test runs: {snap['test_runs']} · "
        f"Files changed: {len(snap['files_changed'])}",
    ]
    if snap["last_test"]:
        t = snap["last_test"]
        lines.append(f"Tests: {t.get('passed')} passed, {t.get('failed')} failed")
    if snap["stop_reason"]:
        lines.append(f"Stopped: {snap['stop_reason']}")
    return ok("\n".join(lines), module="coding", task=snap)


@register_action("dev_task_list", module="coding", description="List coding tasks", info=True)
def dev_task_list(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    items = dev_agent.list_tasks(limit=int(params.get("limit") or 20))
    if not items:
        return ok("No coding tasks.", module="coding", tasks=[])
    lines = [f"- `{t['id']}` [{t['phase']}] {t['objective'][:60]}" for t in items]
    return ok("\n".join(lines), module="coding", tasks=items)


@register_action("dev_task_run", module="coding", description="Run the coding development loop")
def dev_task_run(assistant, params: dict, message: str) -> dict:
    """Runs the bounded loop with the built-in editor unless one is injected."""
    from jarvis import dev_agent
    from jarvis.dev_agent import editors

    task_id = (params.get("task_id") or "").strip()
    if not dev_agent.get_task(task_id):
        return err(f"No coding task `{task_id}`.", module="coding")
    test_cmd = params.get("test_cmd") or ["pytest", "-q"]
    if not isinstance(test_cmd, list):
        return err("test_cmd must be a list.", module="coding")
    try:
        outcome = dev_agent.run_loop(
            task_id,
            editors.model_editor(assistant),
            test_cmd,
            max_iterations=int(params.get("max_iterations") or 0) or None,
        )
    except (dev_agent.CodingAgentError, dev_agent.WorkspaceError) as exc:
        return err(str(exc), module="coding", error_kind="coding_task")
    return ok(
        f"coding task {task_id} finished",
        module="coding",
        task=dev_agent.status(task_id),
        outcome_keys=sorted(outcome.keys()),
    )


@register_action("dev_task_commit", module="coding", description="Commit a coding task's changes")
def dev_task_commit(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    task_id = (params.get("task_id") or "").strip()
    if not dev_agent.get_task(task_id):
        return err(f"No coding task `{task_id}`.", module="coding")
    result = dev_agent.commit_task(task_id, str(params.get("message") or ""))
    if not result.get("ok"):
        return err(result.get("error") or "commit failed", module="coding", **result)
    return ok(
        f"Committed {len(result['files'])} file(s) → {result['commit'][:10]}",
        module="coding",
        **result,
    )


@register_action("dev_task_cancel", module="coding", description="Cancel a coding task")
def dev_task_cancel(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    task_id = (params.get("task_id") or "").strip()
    if not dev_agent.get_task(task_id):
        return err(f"No coding task `{task_id}`.", module="coding")
    return ok(
        f"Coding task `{task_id}` cancelled.", module="coding", task=dev_agent.cancel(task_id)
    )


@register_action(
    "dev_task_recover",
    module="coding",
    description="Recover coding tasks interrupted by a restart",
    info=True,
)
def dev_task_recover(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    ids = dev_agent.recover()
    return ok(f"Recovered {len(ids)} interrupted coding task(s).", module="coding", recovered=ids)


@register_action("dev_command", module="coding", description="Run a permitted development command")
def dev_command(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent

    task_id = (params.get("task_id") or "").strip()
    argv = params.get("argv") or []
    if not isinstance(argv, list) or not argv:
        return err("dev_command needs argv (a list).", module="coding")
    task = dev_agent.get_task(task_id)
    if not task:
        return err(f"No coding task `{task_id}`.", module="coding")
    try:
        ws = dev_agent.open_workspace(task["workspace"], task_id=task_id)
        result = dev_agent.run_command(argv, ws)
    except dev_agent.CommandDenied as exc:
        return err(str(exc), module="coding", error_kind="command_denied")
    except dev_agent.WorkspaceError as exc:
        return err(str(exc), module="coding", error_kind="workspace")
    if not result["ok"]:
        return err(result["error"] or "command failed", module="coding", **result)
    return ok(f"{' '.join(argv)} → exit {result['exit_code']}", module="coding", **result)


@register_action(
    "dev_step",
    module="coding",
    description="Run one coding phase as a mission step (used by the mission worker)",
)
def dev_step(assistant, params: dict, message: str) -> dict:
    from jarvis import dev_agent
    from jarvis.dev_agent import editors

    task_id = (params.get("task_id") or "").strip()
    phase = (params.get("phase") or "").strip()
    task = dev_agent.get_task(task_id)
    if not task or not phase:
        return err("dev_step needs task_id and phase.", module="coding")

    mission_id = task.get("mission_id") or ""
    cancel_check = None
    if mission_id:
        from jarvis.missions import store as mstore

        def cancel_check() -> bool:  # noqa: E306
            return mstore.cancel_requested(mission_id)

    test_cmd = params.get("test_cmd") or ["pytest", "-q"]
    try:
        if phase == "plan":
            out = dev_agent.phase_plan(task_id)
        elif phase == "inspect":
            out = dev_agent.phase_inspect(task_id, test_cmd=test_cmd)
        elif phase == "implement":
            out = dev_agent.phase_implement(task_id, editors.model_editor(assistant))
        elif phase == "test":
            out = dev_agent.phase_test(task_id, test_cmd, cancel_check=cancel_check)
        elif phase == "review":
            review = dev_agent.phase_review(task_id)
            out = {"review": review, "task": dev_agent.complete(task_id, review)}
        else:
            return err(f"Unknown coding phase: {phase}", module="coding")
    except (dev_agent.CodingAgentError, dev_agent.CodingTaskError, dev_agent.WorkspaceError) as exc:
        return err(str(exc), module="coding", error_kind="coding_task")
    return ok(f"coding {phase} done", module="coding", phase=phase, task_id=task_id, result=out)
