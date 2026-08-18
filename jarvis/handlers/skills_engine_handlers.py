"""Skills system handlers — discovery, description, invocation, history.

Named skills_engine_handlers to sit alongside skill_handlers, which serves the
older procedure-playbook store. The two are complementary: playbooks are one
category exposed through this layer.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _skills():
    from jarvis import skills

    skills.ensure_catalog_loaded()
    return skills


@register_action(
    "skill_discover", module="general", description="Discover reusable skills", info=True
)
def skill_discover(assistant, params: dict, message: str) -> dict:
    skills = _skills()
    hits = skills.discover(
        query=(params.get("query") or "").strip(),
        skill_id=(params.get("skill_id") or "").strip(),
        category=(params.get("category") or "").strip(),
        tag=(params.get("tag") or "").strip(),
        capability=(params.get("capability") or "").strip(),
        action=(params.get("action") or "").strip(),
        agent_id=(params.get("agent_id") or "").strip(),
        impact_at_most=(params.get("impact_at_most") or "").strip(),
        include_disabled=bool(params.get("include_disabled")),
    )
    if not hits:
        return ok("No skills matched.", module="general", skills=[], count=0)
    lines = [
        f"- `{h['skill_id']}@{h['version']}` [{h['effective_impact']}] {h['name']}"
        f" — {', '.join(h['match_reasons'])}"
        for h in hits
    ]
    return ok("\n".join(lines), module="general", skills=hits, count=len(hits))


@register_action(
    "skill_describe", module="general", description="Explain one skill in full", info=True
)
def skill_describe(assistant, params: dict, message: str) -> dict:
    skills = _skills()
    skill_id = (params.get("skill_id") or params.get("skill") or "").strip()
    if not skill_id:
        return err("Which skill? Pass skill_id.", module="general")
    detail = skills.explain(skill_id, (params.get("version") or "").strip())
    if not detail:
        return err(f"No such skill: {skill_id}", module="general", error_kind="not_found")
    lines = [
        f"**{detail['name']}** `{detail['ref']}` [{detail['effective_impact']}]",
        detail["description"],
        f"Category: {detail['category']} · Versions: {', '.join(detail['versions'])}",
        f"Actions: {', '.join(detail['effective_actions']) or '—'}",
        f"Dependencies: {', '.join(d[0] for d in detail['dependencies']) or '—'}",
        f"Enabled: {detail['enabled']}",
    ]
    return ok("\n".join(lines), module="general", skill=detail)


@register_action("skill_invoke", module="general", description="Run a reusable skill")
def skill_invoke(assistant, params: dict, message: str) -> dict:
    skills = _skills()
    skill_id = (params.get("skill_id") or params.get("skill") or "").strip()
    if not skill_id:
        return err("Which skill? Pass skill_id.", module="general")
    inputs = params.get("inputs")
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):
        return err("inputs must be an object.", module="general", error_kind="input_contract")
    envelope = skills.execute(
        skill_id,
        inputs,
        version=(params.get("version") or "").strip(),
        strategy=(params.get("strategy") or "compatible").strip(),
        requester=(params.get("requester") or params.get("agent_id") or "").strip(),
        assistant=assistant,
        mission_id=(params.get("mission_id") or "").strip(),
        authorized_high_impact=bool(params.get("authorized_high_impact")),
        max_depth=int(params["max_depth"]) if params.get("max_depth") is not None else None,
    )
    text = (
        f"`{envelope['skill_id']}@{envelope['version']}` → {envelope['status']}"
        f" ({envelope['duration_ms']}ms)"
    )
    if envelope["status"] != skills.SUCCESS:
        return err(
            envelope.get("error") or text,
            module="general",
            error_kind=envelope.get("error_kind") or envelope["status"],
            envelope=envelope,
        )
    return ok(text, module="general", envelope=envelope, output=envelope["output"])


@register_action(
    "skill_invoke_high_impact",
    module="general",
    description="Permission gate for high-impact skills (never called directly)",
)
def skill_invoke_high_impact(assistant, params: dict, message: str) -> dict:
    """A gate token, not an operation.

    It exists in the registry so high-impact skill authority is expressed in the
    same permission system as everything else; invoking it does nothing.
    """
    return err(
        "skill_invoke_high_impact is a permission gate, not an operation. "
        "Use skill_invoke with authorized_high_impact.",
        module="general",
        error_kind="gate_only",
    )


@register_action(
    "skill_history", module="general", description="Show skill invocation history", info=True
)
def skill_history(assistant, params: dict, message: str) -> dict:
    skills = _skills()
    invocation_id = (params.get("invocation_id") or "").strip()
    if invocation_id:
        record = skills.status_of(invocation_id)
        if not record:
            return err(f"No such invocation: {invocation_id}", module="general")
        return ok(
            f"`{record['skill_id']}@{record['version']}` — {record['status']}",
            module="general",
            invocation=record,
        )
    rows = skills.history(
        skill_id=(params.get("skill_id") or "").strip(),
        root_id=(params.get("root_id") or "").strip(),
        requester=(params.get("requester") or "").strip(),
        limit=int(params.get("limit") or 20),
    )
    if not rows:
        return ok("No skill invocations recorded.", module="general", invocations=[])
    lines = [
        f"- `{r['id']}` {r['skill_id']}@{r['version']} [{r['status']}]"
        f" depth={r['depth']} by {r['requester'] or 'system'}"
        for r in rows
    ]
    return ok("\n".join(lines), module="general", invocations=rows)


@register_action(
    "skill_step",
    module="general",
    description="Run a skill as a mission step (used by the mission worker)",
)
def skill_step(assistant, params: dict, message: str) -> dict:
    """Mission-backed skill execution; honours mission cancellation."""
    skills = _skills()
    skill_id = (params.get("skill_id") or "").strip()
    if not skill_id:
        return err("skill_step needs skill_id.", module="general")
    mission_id = (params.get("mission_id") or "").strip()

    cancel_check = None
    if mission_id:
        from jarvis.missions import store as mstore

        def cancel_check() -> bool:  # noqa: E306
            return mstore.cancel_requested(mission_id)

    inputs = params.get("inputs") or {}
    if not isinstance(inputs, dict):
        return err("inputs must be an object.", module="general", error_kind="input_contract")
    envelope = skills.execute(
        skill_id,
        inputs,
        version=(params.get("version") or "").strip(),
        requester=(params.get("requester") or "").strip(),
        assistant=assistant,
        mission_id=mission_id,
        cancel_check=cancel_check,
        authorized_high_impact=bool(params.get("authorized_high_impact")),
    )
    if envelope["status"] != skills.SUCCESS:
        return err(
            envelope.get("error") or f"skill {skill_id} {envelope['status']}",
            module="general",
            error_kind=envelope.get("error_kind") or envelope["status"],
            envelope=envelope,
        )
    return ok(f"skill {skill_id} ok", module="general", envelope=envelope)


@register_action(
    "skill_catalog", module="general", description="List every registered skill", info=True
)
def skill_catalog(assistant, params: dict, message: str) -> dict:
    skills = _skills()
    defs = skills.list_skills(include_disabled=True)
    rows = [
        {
            "skill_id": d.skill_id,
            "version": d.version,
            "name": d.name,
            "category": d.category,
            "impact": d.impact,
            "effective_impact": skills.effective_impact(d),
            "enabled": d.enabled,
        }
        for d in defs
    ]
    lines = [
        f"- `{r['skill_id']}@{r['version']}` [{r['category']}/{r['effective_impact']}] {r['name']}"
        for r in rows
    ]
    return ok("\n".join(lines) or "No skills registered.", module="general", skills=rows)
