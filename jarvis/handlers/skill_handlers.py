"""Skill database handlers — save, list, show, and run reusable procedures."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("skill_list", module="general", description="List saved procedure skills", info=True)
def skill_list(assistant, params: dict, message: str) -> dict:
    from jarvis.skill_database import ensure_default_skills, list_skills

    ensure_default_skills()
    query = (params.get("query") or "").strip()
    items = list_skills(query=query)
    if not items:
        return ok(
            "No skills yet. Say **save skill install docker:** with numbered steps, "
            "or bundled defaults load on first list.",
            module="general",
        )
    lines = [
        f"• **{s['name']}** (`{s['slug']}`) — {len(s.get('steps') or [])} step(s)"
        for s in items
    ]
    return ok("**Procedure skills**\n\n" + "\n".join(lines), module="general")


@register_action("skill_show", module="general", description="Show a procedure skill", info=True)
def skill_show(assistant, params: dict, message: str) -> dict:
    from jarvis.skill_database import format_skill_markdown, resolve_skill

    slug = (params.get("slug") or params.get("skill") or "").strip()
    if not slug:
        if m := re.search(r"\bshow\s+skill[:\s]+(.+)", message, re.I):
            slug = m.group(1).strip()
        elif m := re.search(r"\bskill\s+show[:\s]+(.+)", message, re.I):
            slug = m.group(1).strip()
    skill = resolve_skill(slug) if slug else None
    if not skill:
        return err("Which skill? Example: **show skill install docker**", module="general")
    return ok(format_skill_markdown(skill), module="general", slug=skill["slug"])


@register_action("skill_save", module="general", description="Save a reusable procedure skill")
def skill_save(assistant, params: dict, message: str) -> dict:
    from jarvis.skill_database import parse_skill_save_message, save_skill

    name = (params.get("name") or "").strip()
    description = (params.get("description") or "").strip()
    steps = params.get("steps")
    tags = params.get("tags") or []
    slug = (params.get("slug") or "").strip()

    if not name:
        parsed = parse_skill_save_message(message)
        if parsed:
            name = parsed.get("name") or ""
            description = description or parsed.get("description") or ""
            if not steps:
                steps = parsed.get("steps")
    if not name:
        return err(
            "Define a skill like:\n"
            "**save skill install docker:**\n"
            "1. sudo apt-get update\n"
            "2. sudo apt-get install -y docker.io",
            module="general",
        )
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    skill = save_skill(
        name,
        description=description,
        steps=steps if isinstance(steps, list) else None,
        tags=tags if isinstance(tags, list) else None,
        slug=slug,
    )
    return ok(
        f"Saved skill **{skill['name']}** (`{skill['slug']}`) with {len(skill.get('steps') or [])} step(s).",
        module="general",
        slug=skill["slug"],
    )


@register_action("skill_run", module="general", description="Run a saved procedure skill")
def skill_run(assistant, params: dict, message: str) -> dict:
    from jarvis.skill_database import parse_skill_run_query, run_skill

    slug = (params.get("slug") or params.get("skill") or "").strip()
    confirm = (params.get("confirm") or params.get("exec") or "").lower() in ("1", "true", "yes")
    dry_run = params.get("dry_run")
    if dry_run is None:
        dry_run = not confirm

    if not slug:
        slug, parsed_confirm = parse_skill_run_query(message)
        if parsed_confirm:
            confirm = True
            dry_run = False

    if not slug:
        return err(
            "Which skill? Example: **run docker repair skill** or **run skill install-ollama confirm**",
            module="general",
        )

    if confirm:
        dry_run = False

    result = run_skill(slug, dry_run=bool(dry_run))
    if not result.get("ok") and not result.get("results"):
        return err(result.get("message", "Skill not found."), module="general")
    return ok(result["message"], module="general", slug=result.get("slug"), dry_run=result.get("dry_run"))


@register_action("skill_delete", module="general", description="Delete a saved skill")
def skill_delete(assistant, params: dict, message: str) -> dict:
    from jarvis.skill_database import delete_skill, resolve_skill, slugify

    slug = (params.get("slug") or "").strip()
    if not slug and (m := re.search(r"\bdelete\s+skill[:\s]+(.+)", message, re.I)):
        slug = m.group(1).strip()
    skill = resolve_skill(slug) if slug else None
    if not skill:
        return err("Skill not found.", module="general")
    delete_skill(skill["slug"])
    return ok(f"Deleted skill **{skill['name']}** (`{skill['slug']}`).", module="general")
