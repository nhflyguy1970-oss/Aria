"""Project journal handlers."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _project_slug(assistant, params: dict, message: str) -> str:
    from jarvis.project_journal import resolve_project

    return resolve_project(
        message,
        explicit=(params.get("project") or "").strip(),
        session_namespace=assistant.session.memory_namespace,
    )


@register_action("project_journal_list", module="journal", description="List project journals")
def project_journal_list(assistant, params: dict, message: str) -> dict:
    from jarvis.project_journal import list_projects

    projects = list_projects()
    if not projects:
        return ok(
            "No project journals yet. Say **log to jarvis project journal: shipped auth module**.",
            module="journal",
        )
    lines = [f"• **{p['title']}** (`{p['slug']}`) — {p['days']} day(s)" for p in projects]
    return ok("**Project journals**\n\n" + "\n".join(lines), module="journal")


@register_action("project_journal_today", module="journal", description="Today's project journal")
def project_journal_today(assistant, params: dict, message: str) -> dict:
    from jarvis.project_journal import ProjectJournal

    slug = _project_slug(assistant, params, message)
    day = (params.get("day") or "").strip() or None
    journal = ProjectJournal(slug)
    journal.ensure(title=slug)
    page = journal.format_daily(day)
    return ok(page, module="journal", project=slug)


@register_action("project_journal_log", module="journal", description="Log to project journal")
def project_journal_log(assistant, params: dict, message: str) -> dict:
    from jarvis.project_journal import ProjectJournal, parse_project_log_text

    slug = _project_slug(assistant, params, message)
    text = (params.get("text") or parse_project_log_text(message) or "").strip()
    text = re.sub(r"^(log|journal|project log)[:\s]+", "", text, flags=re.I).strip()
    if not text:
        return err(
            "What should I log? Example: **log to jarvis project journal: fixed router bug**",
            module="journal",
        )
    journal = ProjectJournal(slug)
    journal.ensure(title=slug)
    bullet_type = (params.get("bullet_type") or "note").strip().lower()
    bullet = journal.daily_add(text, bullet_type=bullet_type)
    assistant.session.note_memory_namespace(slug)
    auto = __import__("os").getenv("JARVIS_AUTO_JOURNAL_LEARN", "").lower() in ("1", "true", "yes")
    learn_note = ""
    if auto:
        from jarvis.journal_learning import learn_from_project_journal

        lr = learn_from_project_journal(assistant.memory, slug)
        if lr.get("ok"):
            learn_note = f"\n\n_Auto-learned {len(lr.get('facts') or [])} item(s)._"
            assistant.refresh_system_prompt()
    return ok(
        f"Logged to **{journal.data.get('title') or slug}** journal:\n\n• {bullet['content']}{learn_note}",
        module="journal",
        project=slug,
    )


@register_action("journal_learn", module="journal", description="Learn from journal pages")
def journal_learn(assistant, params: dict, message: str) -> dict:
    from jarvis.journal_learning import (
        format_learnings_markdown,
        learn_from_main_journal,
        learn_from_project_journal,
    )
    from jarvis.project_journal import resolve_project

    project = (params.get("project") or "").strip()
    if not project:
        if m := re.search(r"\blearn from\s+([\w-]+)\s+(?:project\s+)?journal\b", message, re.I):
            project = m.group(1)
        elif "project journal" in message.lower():
            project = resolve_project(message, session_namespace=assistant.session.memory_namespace)
        else:
            project = ""

    day = (params.get("day") or "").strip() or None
    if project and project not in ("main", "today", "journal"):
        result = learn_from_project_journal(assistant.memory, project, day=day, namespace=project)
    else:
        result = learn_from_main_journal(assistant.memory, day=day)

    if not result.get("ok"):
        return err(result.get("message", "Could not learn from journal."), module="journal")
    assistant.refresh_system_prompt()
    facts = result.get("facts") or []
    body = result["message"]
    if facts:
        body += "\n\n" + format_learnings_markdown([{"content": f} for f in facts])
    return ok(body, module="journal", facts=facts, project=result.get("project"))


@register_action("journal_learn_recall", module="journal", description="Recall journal learnings")
def journal_learn_recall(assistant, params: dict, message: str) -> dict:
    from jarvis.journal_learning import (
        format_learnings_markdown,
        list_journal_learnings,
        parse_journal_learn_recall_query,
    )

    query = (params.get("query") or parse_journal_learn_recall_query(message) or "").strip()
    project = (params.get("project") or _project_slug(assistant, params, message) if query else "").strip()
    if project in ("default", "main"):
        project = ""
    entries = list_journal_learnings(assistant.memory, query=query, project=project)
    if not entries:
        return ok(
            "No journal learnings yet. Log to a **project journal** and say **learn from project journal**.",
            module="journal",
        )
    title = f"Journal learnings about **{query}**" if query else "Journal learnings"
    return ok(title + "\n\n" + format_learnings_markdown(entries), module="journal")
