"""Workflow learning handlers — scan, list, run learned action sequences."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("workflow_list", module="general", description="List learned workflows", info=True)
def workflow_list(assistant, params: dict, message: str) -> dict:
    from jarvis.workflow_learning import list_workflows

    query = (params.get("query") or "").strip()
    items = list_workflows(query=query)
    if not items:
        return ok(
            "No learned workflows yet. Repeat the same action sequence a few times, "
            "or say **scan workflows** to mine the action log.",
            module="general",
        )
    lines = [
        f"• **{w['name']}** (`{w['slug']}`) — {len(w.get('steps') or [])} steps, seen {w.get('count', 1)}×"
        for w in items
    ]
    return ok("**Learned workflows**\n\n" + "\n".join(lines), module="general")


@register_action("workflow_show", module="general", description="Show a learned workflow", info=True)
def workflow_show(assistant, params: dict, message: str) -> dict:
    from jarvis.workflow_learning import format_workflow_markdown, resolve_workflow

    slug = (params.get("slug") or "").strip()
    if not slug and (m := re.search(r"\bshow\s+workflow[:\s]+(.+)", message, re.I)):
        slug = m.group(1).strip()
    wf = resolve_workflow(slug) if slug else None
    if not wf:
        return err("Which workflow? Example: **show workflow morning routine**", module="general")
    return ok(format_workflow_markdown(wf), module="general", slug=wf["slug"])


@register_action("workflow_scan", module="general", description="Scan action log for repeated workflows")
def workflow_scan(assistant, params: dict, message: str) -> dict:
    from jarvis.workflow_learning import auto_remember, remember_workflow, scan_action_log

    min_rep = int(params.get("min_repeats") or 0) or None
    found = scan_action_log(min_repeats=min_rep)
    if not found:
        return ok(
            "No repeated action sequences found yet. Need at least "
            f"{min_rep or 3} matching runs in the action log.",
            module="general",
        )
    remembered = 0
    if auto_remember():
        for wf in found:
            remembered += len(remember_workflow(assistant.memory, wf))
        if remembered:
            assistant.refresh_system_prompt()
    lines = [f"• **{w['name']}** (`{w['slug']}`) — {w.get('count', 1)}×" for w in found]
    body = f"Learned **{len(found)}** workflow(s) from action history:\n\n" + "\n".join(lines)
    if remembered:
        body += f"\n\n_Remembered {remembered} workflow summary(ies)._"
    return ok(body, module="general", workflows=found)


@register_action("workflow_learn", module="general", description="Alias for workflow scan")
def workflow_learn(assistant, params: dict, message: str) -> dict:
    return workflow_scan(assistant, params, message)


@register_action("workflow_run", module="general", description="Run a learned workflow")
def workflow_run(assistant, params: dict, message: str) -> dict:
    from jarvis.workflow_learning import parse_workflow_run_query, run_workflow

    slug = (params.get("slug") or "").strip()
    confirm = (params.get("confirm") or "").lower() in ("1", "true", "yes")
    if not slug:
        slug, parsed_confirm = parse_workflow_run_query(message)
        if parsed_confirm:
            confirm = True
    if not slug:
        return err(
            "Which workflow? Example: **run morning routine workflow** or **run workflow NAME confirm**",
            module="general",
        )
    result = run_workflow(slug, assistant=None if not confirm else assistant, dry_run=not confirm)
    if not result.get("results") and not result.get("ok"):
        return err(result.get("message", "Workflow not found."), module="general")
    return ok(result["message"], module="general", slug=result.get("slug"), dry_run=result.get("dry_run"))


@register_action("workflow_to_skill", module="general", description="Convert workflow to skill")
def workflow_to_skill(assistant, params: dict, message: str) -> dict:
    from jarvis.workflow_learning import parse_workflow_to_skill_query, workflow_to_skill as convert

    slug = (params.get("slug") or "").strip()
    if not slug:
        slug = parse_workflow_to_skill_query(message)
    if not slug:
        return err("Example: **save workflow morning routine as skill**", module="general")
    result = convert(slug)
    if not result.get("ok"):
        return err(result.get("message", "Could not convert."), module="general")
    return ok(result["message"], module="general", skill=result.get("skill"))


@register_action("workflow_recall", module="general", description="Recall learned workflows", info=True)
def workflow_recall(assistant, params: dict, message: str) -> dict:
    return workflow_list(assistant, params, message)
