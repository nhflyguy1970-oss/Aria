"""Journal read handlers."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import ok


@register_action("journal_today", module="journal", description="Today's daily journal page")
def journal_today(assistant, params: dict, message: str) -> dict:
    day = params.get("day") or ""
    page = assistant.journal.format_page("daily", day or None)
    return ok(page, module="journal")


@register_action("journal_monthly", module="journal", description="Monthly journal page")
def journal_monthly(assistant, params: dict, message: str) -> dict:
    from jarvis.modules.journal import _month_key

    month = params.get("month") or _month_key()
    page = assistant.journal.format_page("monthly", month)
    return ok(page, module="journal")


@register_action("journal_open_tasks", module="journal", description="Open journal tasks")
def journal_open_tasks(assistant, params: dict, message: str) -> dict:
    tasks = assistant.journal.open_tasks()
    if not tasks:
        return ok("No open journal tasks — you're clear.", module="journal")
    from jarvis.modules.journal import _format_bullet

    lines = "\n".join(f"• [{t.get('section')}] {_format_bullet(t)}" for t in tasks)
    return ok(f"**Open tasks ({len(tasks)}):**\n\n{lines}", module="journal")
