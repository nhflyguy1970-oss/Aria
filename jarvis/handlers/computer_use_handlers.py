"""Browser / computer-use handlers — sessions, actions, mission steps, retention."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action(
    "browser_use_open", module="browser", description="Open a computer-use browser session"
)
def browser_use_open(assistant, params: dict, message: str) -> dict:
    from jarvis import computer_use as cu

    session = cu.open_session(
        # The invoking agent's identity is stamped into the payload, and takes
        # precedence over a supplied owner: a session an agent opened must not
        # be recorded as somebody else's, or as nobody's.
        owner=(params.get("agent_id") or params.get("owner") or "").strip(),
        task_id=(params.get("task_id") or "").strip(),
        label=(params.get("label") or "").strip(),
    )
    return ok(
        f"Browser session `{session['id']}` open.",
        module="browser",
        session_id=session["id"],
        session=session,
    )


@register_action(
    "browser_use_act", module="browser", description="Perform a browser/computer-use action"
)
def browser_use_act(assistant, params: dict, message: str) -> dict:
    from jarvis import computer_use as cu

    session_id = (params.get("session_id") or "").strip()
    action = (params.get("action") or "").strip()
    if not session_id or not action:
        return err("browser_use_act needs session_id and action.", module="browser")
    action_params = params.get("params") or {}
    if not isinstance(action_params, dict):
        return err("params must be an object.", module="browser")

    outcome = cu.perform(
        session_id,
        action,
        action_params,
        agent_id=(params.get("agent_id") or "").strip(),
        owner=(params.get("owner") or "").strip(),
        allow_local=bool(params.get("allow_local")),
    )
    if not outcome["ok"]:
        return err(outcome["error"] or "browser action failed", module="browser", **outcome)
    return ok(f"{action} → {outcome['url'] or 'ok'}", module="browser", **outcome)


@register_action(
    "browser_use_sessions", module="browser", description="List browser sessions", info=True
)
def browser_use_sessions(assistant, params: dict, message: str) -> dict:
    from jarvis import computer_use as cu

    items = cu.list_sessions(include_closed=bool(params.get("include_closed")))
    if not items:
        return ok("No browser sessions.", module="browser", sessions=[])
    lines = [
        f"- `{s['id']}` [{s['state']}] owner={s['owner']} actions={s['actions']} {s['url'][:50]}"
        for s in items
    ]
    return ok("\n".join(lines), module="browser", sessions=items)


@register_action(
    "browser_use_close", module="browser", description="Close a computer-use browser session"
)
def browser_use_close(assistant, params: dict, message: str) -> dict:
    from jarvis import computer_use as cu

    session_id = (params.get("session_id") or "").strip()
    if not cu.get_session(session_id):
        return err(f"No session `{session_id}`.", module="browser")
    cu.perform(session_id, "close", {}, agent_id=(params.get("agent_id") or "").strip())
    return ok(f"Session `{session_id}` closed.", module="browser")


@register_action(
    "browser_use_capabilities",
    module="browser",
    description="Show browser actions and their impact classes",
    info=True,
)
def browser_use_capabilities(assistant, params: dict, message: str) -> dict:
    from jarvis import computer_use as cu

    data = {
        "read": list(cu.READ_ACTIONS),
        "interact": list(cu.INTERACT_ACTIONS),
        "high_impact": list(cu.HIGH_IMPACT_ACTIONS),
        "limits": dict(cu.LIMITS),
        "gates": {
            "read": cu.READ_ACTION,
            "interact": cu.INTERACT_ACTION,
            "high_impact": cu.HIGH_IMPACT_ACTION,
        },
    }
    lines = [
        f"read: {', '.join(data['read'])}",
        f"interact: {', '.join(data['interact'])}",
        f"high_impact (restricted): {', '.join(data['high_impact'])}",
    ]
    return ok("\n".join(lines), module="browser", capabilities=data)


@register_action(
    "browser_step",
    module="browser",
    description="Run a browser action as a mission step (used by the mission worker)",
)
def browser_step(assistant, params: dict, message: str) -> dict:
    """Mission-backed browser work; honours mission cancellation at each boundary."""
    from jarvis import computer_use as cu

    session_id = (params.get("session_id") or "").strip()
    action = (params.get("action") or "").strip()
    mission_id = (params.get("mission_id") or "").strip()
    if not session_id or not action:
        return err("browser_step needs session_id and action.", module="browser")

    cancel_check = None
    if mission_id:
        from jarvis.missions import store as mstore

        def cancel_check() -> bool:  # noqa: E306
            return mstore.cancel_requested(mission_id)

    outcome = cu.perform(
        session_id,
        action,
        params.get("params") or {},
        agent_id=(params.get("agent_id") or "").strip(),
        owner=(params.get("owner") or "").strip(),
        allow_local=bool(params.get("allow_local")),
        cancel_check=cancel_check,
    )
    if not outcome["ok"]:
        return err(outcome["error"] or "browser step failed", module="browser", **outcome)
    return ok(f"{action} ok", module="browser", **outcome)


@register_action(
    "browser_use_artifacts",
    module="browser",
    description="Inspect or prune browser artifact storage",
    info=True,
)
def browser_use_artifacts(assistant, params: dict, message: str) -> dict:
    from jarvis import computer_use as cu

    if str(params.get("prune") or "").strip() in ("1", "true", "yes"):
        pruned = cu.prune_screenshots()
        after = cu.usage()
        return ok(
            f"Pruned {pruned['pruned']} screenshot(s), freed {pruned['bytes_freed']} bytes.",
            module="browser",
            pruned=pruned,
            usage=after,
        )
    data = cu.usage()
    return ok(
        f"screenshots: {data['screenshots']} ({data['screenshot_bytes']} bytes), "
        f"over limit: {data['over_limit']}; profile files: {data['profile_files']}",
        module="browser",
        usage=data,
    )
