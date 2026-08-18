"""Deep research handlers — create, inspect, run/resume, pause, cancel, report.

Lifecycle operations delegate to the mission actions rather than duplicating
them: a research job is executed by a mission, so pausing/cancelling/recovering
research is pausing/cancelling/recovering that mission.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _mission_id(research_id: str) -> str:
    from jarvis.research import store

    job = store.get_job(research_id)
    return (job or {}).get("mission_id") or ""


@register_action(
    "research_step",
    module="general",
    description="Execute one phase of a research job (used by the mission worker)",
)
def research_step(assistant, params: dict, message: str) -> dict:
    from jarvis.research import engine

    research_id = (params.get("research_id") or "").strip()
    phase = (params.get("phase") or "").strip()
    if not research_id or not phase:
        return err("research_step needs research_id and phase", module="general")
    result = engine.run_phase(research_id, phase)
    return ok(f"research {research_id}: {phase} done", module="general", phase=phase, **result)


@register_action(
    "research_create", module="general", description="Start an autonomous deep research job"
)
def research_create(assistant, params: dict, message: str) -> dict:
    from jarvis.research import engine

    objective = (params.get("objective") or params.get("topic") or message or "").strip()
    if not objective:
        return err("Research needs an objective.", module="general")
    created = engine.create_research(objective)
    return ok(
        f"Research `{created['research_id']}` started — {objective}",
        module="general",
        **created,
    )


@register_action(
    "research_status", module="general", description="Show research progress", info=True
)
def research_status(assistant, params: dict, message: str) -> dict:
    from jarvis.research import engine

    research_id = (params.get("research_id") or params.get("id") or "").strip()
    if not research_id:
        return err("Which research? Pass research_id.", module="general")
    snapshot = engine.status(research_id)
    if not snapshot:
        return err(f"No research `{research_id}`.", module="general")
    mission = snapshot.get("mission") or {}
    progress = (mission.get("progress") or {}) if mission else {}
    lines = [
        f"**Research {snapshot['research_id']}** — {snapshot['status']}",
        f"Objective: {snapshot['objective']}",
        f"Questions: {len(snapshot['questions'])} · Searches: {snapshot['searches']} · "
        f"Sources: {snapshot['sources']} ({snapshot['sources_inspected']} inspected)",
        f"Evidence: {snapshot['evidence']} · Claims: {snapshot['claims']} · "
        f"Confidence: {snapshot['confidence'] or '—'}",
    ]
    if progress.get("total_steps"):
        lines.append(f"Phase progress: {progress['completed_steps']}/{progress['total_steps']}")
    if snapshot["unresolved"]:
        lines.append(f"Unresolved: {len(snapshot['unresolved'])}")
    return ok("\n".join(lines), module="general", research=snapshot)


@register_action("research_list", module="general", description="List research jobs", info=True)
def research_list(assistant, params: dict, message: str) -> dict:
    from jarvis.research import store

    jobs = store.list_jobs(limit=int(params.get("limit") or 20))
    if not jobs:
        return ok("No research jobs yet.", module="general", research=[])
    lines = [f"- `{j['id']}` [{j['status']}] {j['objective'][:70]}" for j in jobs]
    return ok("\n".join(lines), module="general", research=jobs)


@register_action(
    "research_report",
    module="general",
    description="Show research evidence, citations and synthesis",
    info=True,
)
def research_report(assistant, params: dict, message: str) -> dict:
    from jarvis.research import engine

    research_id = (params.get("research_id") or params.get("id") or "").strip()
    data = engine.report(research_id) if research_id else None
    if not data:
        return err(f"No research `{research_id}`.", module="general")
    return ok(
        data.get("synthesis") or "Research has not synthesised yet.", module="general", report=data
    )


@register_action("research_run", module="general", description="Run or resume a research job")
def research_run(assistant, params: dict, message: str) -> dict:
    from jarvis.handlers.registry import call_action

    research_id = (params.get("research_id") or params.get("id") or "").strip()
    mission_id = _mission_id(research_id)
    if not mission_id:
        return err(f"No research `{research_id}`.", module="general")
    return call_action(assistant, "mission_run", {"mission_id": mission_id}, message)


@register_action("research_pause", module="general", description="Pause a research job")
def research_pause(assistant, params: dict, message: str) -> dict:
    from jarvis.handlers.registry import call_action

    research_id = (params.get("research_id") or params.get("id") or "").strip()
    mission_id = _mission_id(research_id)
    if not mission_id:
        return err(f"No research `{research_id}`.", module="general")
    return call_action(assistant, "mission_pause", {"mission_id": mission_id}, message)


@register_action("research_cancel", module="general", description="Cancel a research job")
def research_cancel(assistant, params: dict, message: str) -> dict:
    from jarvis.handlers.registry import call_action
    from jarvis.research import store

    research_id = (params.get("research_id") or params.get("id") or "").strip()
    mission_id = _mission_id(research_id)
    if not mission_id:
        return err(f"No research `{research_id}`.", module="general")
    result = call_action(assistant, "mission_cancel", {"mission_id": mission_id}, message)
    if result.get("ok"):
        store.set_status(research_id, store.CANCELLED)
    return result


@register_action(
    "research_recover",
    module="general",
    description="Recover research interrupted by a restart",
    info=True,
)
def research_recover(assistant, params: dict, message: str) -> dict:
    from jarvis.handlers.registry import call_action

    return call_action(assistant, "mission_recover", {}, message)
