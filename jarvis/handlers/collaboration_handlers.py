"""Collaboration handlers — create, delegate, advance, inspect, aggregate.

Lifecycle operations (pause/resume/cancel/recover) delegate to the mission
actions, because a collaboration is executed by a mission.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _mission_id(collaboration_id: str) -> str:
    from jarvis.collaboration import store

    collaboration = store.get(collaboration_id)
    return (collaboration or {}).get("mission_id") or ""


@register_action("collab_create", module="general", description="Start a multi-agent collaboration")
def collab_create(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import engine

    objective = (params.get("objective") or message or "").strip()
    if not objective:
        return err("A collaboration needs an objective.", module="general")
    try:
        created = engine.create_collaboration(
            objective,
            initiator=(params.get("initiator") or "analysis_specialist").strip(),
            bounds=params.get("bounds") or {},
        )
    except engine.DelegationError as exc:
        return err(str(exc), module="general")
    return ok(
        f"Collaboration `{created['collaboration_id']}` started.", module="general", **created
    )


@register_action(
    "collab_delegate", module="general", description="Delegate a task to another specialist"
)
def collab_delegate(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import engine, graph

    cid = (params.get("collaboration_id") or "").strip()
    requester = (params.get("requester") or "").strip()
    objective = (params.get("objective") or "").strip()
    if not cid or not requester or not objective:
        return err(
            "collab_delegate needs collaboration_id, requester and objective.", module="general"
        )
    try:
        task = engine.delegate(
            cid,
            requester=requester,
            objective=objective,
            target=(params.get("target") or "").strip(),
            capability=(params.get("capability") or "").strip(),
            action=(params.get("action") or "").strip(),
            params=params.get("params") or {},
            depends_on=params.get("depends_on") or [],
        )
    except engine.BoundExceeded as exc:
        return err(str(exc), module="general", error_kind="bounded")
    except graph.GraphError as exc:
        return err(str(exc), module="general", error_kind="graph")
    except engine.DelegationError as exc:
        return err(str(exc), module="general", error_kind="delegation_denied")
    return ok(
        f"{task['requester']} → {task['target']}: {task['objective'][:70]}",
        module="general",
        task=task,
    )


@register_action(
    "collab_step",
    module="general",
    description="Advance a collaboration (used by the mission worker)",
)
def collab_step(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import engine

    cid = (params.get("collaboration_id") or "").strip()
    if not cid:
        return err("collab_step needs collaboration_id", module="general")
    try:
        outcome = engine.step(cid, assistant=assistant)
    except engine.DelegationError as exc:
        return err(str(exc), module="general")
    return ok(f"collaboration {cid} advanced", module="general", **outcome)


@register_action("collab_status", module="general", description="Show a collaboration", info=True)
def collab_status(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import engine

    cid = (params.get("collaboration_id") or params.get("id") or "").strip()
    snapshot = engine.status(cid) if cid else None
    if not snapshot:
        return err(f"No collaboration `{cid}`.", module="general")
    t = snapshot["tasks"]
    lines = [
        f"**Collaboration {snapshot['collaboration_id']}** — {snapshot['status']}",
        f"Objective: {snapshot['objective']}",
        f"Initiator: {snapshot['initiator']} · Participants: {', '.join(snapshot['participants']) or '—'}",
        f"Tasks: {t['total']} (ok {t['succeeded']}, partial {t['partial']}, "
        f"failed {t['failed']}, denied {t['denied']}, skipped {t['skipped']}, pending {t['pending']})",
    ]
    if snapshot["conflicts"]:
        lines.append(f"Conflicts: {len(snapshot['conflicts'])}")
    return ok("\n".join(lines), module="general", collaboration=snapshot)


@register_action("collab_list", module="general", description="List collaborations", info=True)
def collab_list(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import store

    items = store.list_collaborations(limit=int(params.get("limit") or 20))
    if not items:
        return ok("No collaborations yet.", module="general", collaborations=[])
    lines = [f"- `{c['id']}` [{c['status']}] {c['objective'][:70]}" for c in items]
    return ok("\n".join(lines), module="general", collaborations=items)


@register_action(
    "collab_graph", module="general", description="Show the delegation graph", info=True
)
def collab_graph(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import graph, store

    cid = (params.get("collaboration_id") or params.get("id") or "").strip()
    if not store.get(cid):
        return err(f"No collaboration `{cid}`.", module="general")
    data = graph.as_graph(store.tasks(cid))
    lines = [
        f"- {n['requester']} → {n['target']} [{n['status']}] {n['objective'][:60]}"
        for n in data["nodes"]
    ]
    return ok("\n".join(lines) or "No tasks.", module="general", graph=data)


@register_action(
    "collab_report",
    module="general",
    description="Show collaboration results and final synthesis",
    info=True,
)
def collab_report(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import engine

    cid = (params.get("collaboration_id") or params.get("id") or "").strip()
    data = engine.report(cid) if cid else None
    if not data:
        return err(f"No collaboration `{cid}`.", module="general")
    return ok(
        data.get("synthesis") or "Collaboration has not aggregated yet.",
        module="general",
        report=data,
    )


@register_action("collab_pause", module="general", description="Pause a collaboration")
def collab_pause(assistant, params: dict, message: str) -> dict:
    from jarvis.handlers.registry import call_action

    mid = _mission_id((params.get("collaboration_id") or "").strip())
    if not mid:
        return err("No such collaboration.", module="general")
    return call_action(assistant, "mission_pause", {"mission_id": mid}, message)


@register_action("collab_cancel", module="general", description="Cancel a collaboration")
def collab_cancel(assistant, params: dict, message: str) -> dict:
    from jarvis.collaboration import store
    from jarvis.handlers.registry import call_action

    cid = (params.get("collaboration_id") or "").strip()
    mid = _mission_id(cid)
    if not mid:
        return err("No such collaboration.", module="general")
    result = call_action(assistant, "mission_cancel", {"mission_id": mid}, message)
    if result.get("ok"):
        store.set_status(cid, store.CANCELLED, reason="cancelled by request")
    return result


@register_action(
    "collab_recover",
    module="general",
    description="Recover collaborations interrupted by a restart",
    info=True,
)
def collab_recover(assistant, params: dict, message: str) -> dict:
    from jarvis.handlers.registry import call_action

    return call_action(assistant, "mission_recover", {}, message)
