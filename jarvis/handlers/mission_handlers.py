"""Mission handlers — create, inspect, run, pause/resume and cancel missions.

Thin wrappers over jarvis.missions so the persistent task engine is reachable
from the assistant through the same action registry as every other capability.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _format_status(snapshot: dict) -> str:
    progress = snapshot.get("progress") or {}
    lines = [
        f"**Mission {snapshot['id']}** — {snapshot['state']}",
        f"Objective: {snapshot['objective']}",
    ]
    if progress.get("total_steps"):
        pct = progress.get("percent")
        lines.append(
            f"Progress: {progress['completed_steps']}/{progress['total_steps']}"
            + (f" ({pct}%)" if pct is not None else "")
        )
    checkpoint = snapshot.get("checkpoint")
    if checkpoint:
        lines.append(f"Last checkpoint: seq {checkpoint['seq']} at step {checkpoint['step_index']}")
    if snapshot.get("error"):
        lines.append(f"Error ({snapshot.get('error_kind')}): {snapshot['error']}")
    if snapshot.get("result"):
        lines.append("Result recorded.")
    return "\n".join(lines)


@register_action(
    "mission_create", module="general", description="Create a durable autonomous mission"
)
def mission_create(assistant, params: dict, message: str) -> dict:
    objective = (params.get("objective") or params.get("task") or message or "").strip()
    if not objective:
        return err("A mission needs an objective.", module="general")
    steps = params.get("steps") or []
    if not isinstance(steps, list):
        return err("Mission steps must be a list.", module="general")
    from jarvis import missions

    mission_id = missions.create_mission(
        objective, steps=steps, kind=(params.get("kind") or "generic")
    )
    return ok(
        f"Created mission `{mission_id}` — {objective}", module="general", mission_id=mission_id
    )


@register_action(
    "mission_status", module="general", description="Show a mission's state", info=True
)
def mission_status(assistant, params: dict, message: str) -> dict:
    from jarvis import missions

    mission_id = (params.get("mission_id") or params.get("id") or "").strip()
    if not mission_id:
        return err("Which mission? Pass mission_id.", module="general")
    snapshot = missions.status(mission_id)
    if not snapshot:
        return err(f"No mission `{mission_id}`.", module="general")
    return ok(_format_status(snapshot), module="general", mission=snapshot)


@register_action("mission_list", module="general", description="List missions", info=True)
def mission_list(assistant, params: dict, message: str) -> dict:
    from jarvis import missions

    state = (params.get("state") or "").strip() or None
    items = missions.list_missions(state=state, limit=int(params.get("limit") or 20))
    if not items:
        return ok("No missions yet.", module="general", missions=[])
    lines = [
        f"- `{m['id']}` [{m['state']}] {m['objective'][:80]}"
        f" ({m['completed_steps']}/{m['total_steps']})"
        for m in items
    ]
    return ok("\n".join(lines), module="general", missions=items)


@register_action("mission_run", module="general", description="Run or resume a mission")
def mission_run(assistant, params: dict, message: str) -> dict:
    from jarvis import missions

    mission_id = (params.get("mission_id") or params.get("id") or "").strip()
    if not mission_id:
        return err("Which mission? Pass mission_id.", module="general")
    if not missions.get(mission_id):
        return err(f"No mission `{mission_id}`.", module="general")
    max_steps = params.get("max_steps")
    missions.run(
        mission_id,
        assistant=assistant,
        max_steps=int(max_steps) if max_steps else None,
    )
    snapshot = missions.status(mission_id)
    return ok(_format_status(snapshot or {}), module="general", mission=snapshot)


@register_action("mission_pause", module="general", description="Pause a running mission")
def mission_pause(assistant, params: dict, message: str) -> dict:
    from jarvis import missions

    mission_id = (params.get("mission_id") or params.get("id") or "").strip()
    if not mission_id or not missions.get(mission_id):
        return err(f"No mission `{mission_id}`.", module="general")
    try:
        missions.pause(mission_id)
    except missions.MissionStateError as exc:
        return err(str(exc), module="general")
    return ok(f"Mission `{mission_id}` paused.", module="general")


@register_action("mission_cancel", module="general", description="Cancel a mission")
def mission_cancel(assistant, params: dict, message: str) -> dict:
    from jarvis import missions

    mission_id = (params.get("mission_id") or params.get("id") or "").strip()
    if not mission_id or not missions.get(mission_id):
        return err(f"No mission `{mission_id}`.", module="general")
    if not missions.cancel(mission_id):
        return err(f"Mission `{mission_id}` is already finished.", module="general")
    return ok(f"Cancellation requested for mission `{mission_id}`.", module="general")


@register_action(
    "mission_recover",
    module="general",
    description="Find missions interrupted by a process restart",
    info=True,
)
def mission_recover(assistant, params: dict, message: str) -> dict:
    from jarvis import missions

    recovered = missions.recover()
    if not recovered:
        return ok("No interrupted missions.", module="general", recovered=[])
    joined = ", ".join(f"`{m}`" for m in recovered)
    return ok(
        f"Recovered {len(recovered)} interrupted mission(s): {joined}. They can be resumed.",
        module="general",
        recovered=recovered,
    )
