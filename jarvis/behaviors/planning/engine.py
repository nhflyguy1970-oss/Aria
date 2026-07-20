"""Planning engine — planner, timers, alarms, calendar, and scheduling decisions."""

from __future__ import annotations

import re
from typing import Any

from jarvis.behaviors.planning.context import PlanningContext
from jarvis.feature_flags import planner_enabled
from jarvis.response import err, ok


class PlanningEngine:
    """Isolated planning domain logic."""

    @classmethod
    def prepare_context(
        cls,
        ctx: PlanningContext,
        message: str,
        *,
        skip_project_context: bool = False,
    ) -> tuple[list[str], list[dict]]:
        import re

        parts: list[str] = []
        lower_msg = message.lower()
        if not skip_project_context and re.search(
            r"\b(journal|task|todo|to-do|today|priorit|what('s| is) on my plate)\b",
            lower_msg,
        ):
            open_tasks = ctx.journal.format_open_tasks(limit=8)
            if open_tasks != "No open journal tasks.":
                parts.append(f"Open bullet journal tasks:\n{open_tasks}")

        if re.search(
            r"\b(weather|forecast|temperature|rain|snow|tomorrow|today|tonight)\b",
            lower_msg,
        ):
            from jarvis.journal_weather import parse_weather_day, weather_forecast_text

            parts.append(weather_forecast_text(parse_weather_day(message), message=message))

        return parts, []

    @staticmethod
    def _disabled() -> dict:
        return err("Planner is disabled (JARVIS_PLANNER=0).", module="planner")

    @staticmethod
    def planning_context() -> dict[str, Any]:
        from jarvis.planner_store import planner_snapshot

        return planner_snapshot()

    @staticmethod
    def planning_context_markdown() -> str:
        from jarvis.planner_store import format_planner_lines

        return format_planner_lines()

    @classmethod
    def add_task(cls, _ctx: PlanningContext, params: dict, message: str) -> dict:
        if not planner_enabled():
            return cls._disabled()
        from jarvis.planner_store import add_task

        text = str(params.get("text") or "").strip()
        if not text:
            match = re.search(r"(?:add|create)\s+(?:a\s+)?task\s+(.+)", message, re.I)
            text = match.group(1).strip() if match else message.strip()
        try:
            task = add_task(text)
            return ok(f"Added task: **{task['text']}**", module="planner", type="planner")
        except ValueError as exc:
            return err(str(exc), module="planner")

    @classmethod
    def list_tasks(cls, _ctx: PlanningContext, params: dict, message: str) -> dict:
        if not planner_enabled():
            return cls._disabled()
        from jarvis.planner_store import list_tasks

        tasks = list_tasks()
        if not tasks:
            return ok("No open planner tasks.", module="planner", type="planner")
        lines = "\n".join(f"• {task['text']}" for task in tasks)
        return ok(f"**Planner tasks:**\n{lines}", module="planner", type="planner")

    @classmethod
    def set_timer(cls, _ctx: PlanningContext, params: dict, message: str) -> dict:
        if not planner_enabled():
            return cls._disabled()
        from jarvis.planner_store import set_timer

        duration = str(params.get("duration") or "").strip()
        label = str(params.get("label") or "").strip() or None
        if not duration:
            match = re.search(r"timer\s+(?:for\s+)?(.+)", message, re.I)
            duration = match.group(1).strip() if match else ""
        try:
            timer = set_timer(duration, label)
            minutes, seconds = divmod(timer["remaining_seconds"], 60)
            return ok(
                f"Timer **{timer['label']}** set for {minutes}m {seconds}s.",
                module="planner",
                type="planner",
            )
        except ValueError as exc:
            return err(str(exc), module="planner")

    @classmethod
    def set_alarm(cls, _ctx: PlanningContext, params: dict, message: str) -> dict:
        if not planner_enabled():
            return cls._disabled()
        from jarvis.planner_store import set_alarm

        time_str = str(params.get("time") or "").strip()
        label = str(params.get("label") or "").strip() or None
        if not time_str:
            match = re.search(r"alarm\s+(?:for\s+)?(.+)", message, re.I)
            time_str = match.group(1).strip() if match else ""
        try:
            alarm = set_alarm(time_str, label)
            fire_at = alarm.get("fire_at") or ""
            return ok(
                f"Alarm **{alarm['label']}** set for {fire_at[11:16]}.",
                module="planner",
                type="planner",
            )
        except ValueError as exc:
            return err(str(exc), module="planner")

    @classmethod
    def today(cls, _ctx: PlanningContext, params: dict, message: str) -> dict:
        if not planner_enabled():
            return cls._disabled()
        block = cls.planning_context_markdown()
        if not block:
            return ok("Planner is clear for today.", module="planner", type="planner")
        return ok(block, module="planner", type="planner")

    @classmethod
    def plan(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        """Generate an activity/trip/project plan (not documentation lookup)."""
        if not planner_enabled():
            return cls._disabled()
        from jarvis import llm

        query = str(params.get("query") or params.get("text") or message or "").strip()
        if not query:
            return err("What would you like me to plan?", module="planner")

        context_parts, _ = cls.prepare_context(ctx, query)
        planner_block = cls.planning_context_markdown()
        if planner_block:
            context_parts.append(f"Current planner context:\n{planner_block}")
        context = "\n\n".join(context_parts)

        system = (
            "You are Aria's planning assistant. Produce a clear, practical plan for the "
            "user's request. Use short sections and concrete next steps. "
            "Do not quote or invent product documentation filenames. "
            "Do not dump workstation application catalogs."
        )
        user = query if not context else f"Context:\n{context}\n\nPlan request: {query}"
        try:
            answer = llm.ask_with_system(
                llm.general_model(),
                system,
                user,
                role="planning",
            )
        except Exception as exc:
            return err(f"Planning failed: {exc}", module="planner")
        text = (answer or "").strip()
        if not text:
            return err("I couldn't draft a plan for that yet. Try adding a bit more detail.", module="planner")
        return ok(text, module="planner", type="planner_plan")

    @classmethod
    def add_event(cls, _ctx: PlanningContext, params: dict, message: str) -> dict:
        if not planner_enabled():
            return cls._disabled()
        from jarvis.planner_store import add_event

        title = str(params.get("title") or "").strip()
        when = str(params.get("date") or params.get("when") or "").strip() or None
        time_str = str(params.get("time") or "").strip() or None
        if not title:
            match = re.search(r"(?:schedule|event|meeting)\s+(.+)", message, re.I)
            title = match.group(1).strip() if match else message.strip()
        try:
            event = add_event(title, when=when, time_str=time_str)
            start_time = event.get("start_time") or ""
            return ok(
                f"Scheduled **{event['title']}** at {start_time[11:16]}.",
                module="planner",
                type="planner",
            )
        except ValueError as exc:
            return err(str(exc), module="planner")

    @staticmethod
    def _task_disambiguation(candidates: list[dict], hint: str = "") -> dict:
        lines = "\n".join(
            f"• {task.get('content', '?')} `[{str(task.get('id', ''))[:8]}]` "
            f"({task.get('section', '')})"
            for task in candidates[:8]
        )
        prefix = f" for “{hint}”" if hint else ""
        return ok(
            f"Which task{prefix}?\n{lines}\n\nSay the task name or include the bullet ID.",
            module="journal",
        )

    @classmethod
    def journal_schedule(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        from jarvis.modules.journal import _month_key

        month = params.get("month") or _month_key()
        task, candidates, hint = ctx.journal.match_open_task(
            message,
            bullet_id=params.get("bullet_id"),
            task_query=params.get("task_query"),
        )
        if not task:
            if not candidates:
                return ok("No open tasks to schedule.", module="journal")
            return cls._task_disambiguation(candidates, hint)
        bullet = ctx.journal.bullet_schedule(task["id"], month)
        if not bullet:
            return err("Could not schedule task.")
        return ok(
            f"Scheduled to future log ({month}): {bullet.get('content', '')}",
            module="journal",
        )

    @classmethod
    def journal_thread(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        from jarvis.modules.journal import _today

        day = params.get("day") or _today()
        duplicate = params.get("duplicate") in (True, "true", "1")
        task, candidates, hint = ctx.journal.match_open_task(
            message,
            bullet_id=params.get("bullet_id"),
            task_query=params.get("task_query"),
        )
        if not task:
            if not candidates:
                return ok("No open tasks to thread.", module="journal")
            return cls._task_disambiguation(candidates, hint)
        bullet = ctx.journal.bullet_thread_to_daily(task["id"], day, duplicate=duplicate)
        if not bullet:
            return err("Could not thread task to daily log.")
        verb = "Copied" if duplicate else "Migrated"
        return ok(f"{verb} to {day}: {bullet.get('content', '')}", module="journal")

    @classmethod
    def journal_log(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        text = params.get("text") or message
        text = re.sub(r"^(log|journal|add to journal)[:\s]+", "", text, flags=re.I).strip()
        bullets = ctx.journal.parse_rapid_log(text)
        lines = "\n".join(f"• {b['content']}" for b in bullets)
        return ok(f"Added to today's log:\n\n{lines}", module="journal")

    @classmethod
    def journal_today(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        day = params.get("day") or ""
        page = ctx.journal.format_page("daily", day or None)
        return ok(page, module="journal")

    @classmethod
    def journal_monthly(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        from jarvis.modules.journal import _month_key

        month = params.get("month") or _month_key()
        page = ctx.journal.format_page("monthly", month)
        return ok(page, module="journal")

    @classmethod
    def journal_open_tasks(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        tasks = ctx.journal.open_tasks()
        if not tasks:
            return ok("No open journal tasks — you're clear.", module="journal")
        from jarvis.modules.journal import _format_bullet

        lines = "\n".join(f"• [{t.get('section')}] {_format_bullet(t)}" for t in tasks)
        return ok(f"**Open tasks ({len(tasks)}):**\n\n{lines}", module="journal")

    @classmethod
    def journal_reflect(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        scope = "month" if "month" in message.lower() else "week" if "week" in message.lower() else "today"
        reflection = ctx.journal.ai_reflect(scope)
        return ok(reflection, module="journal")

    @classmethod
    def journal_migrate(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        from jarvis.modules.journal import _month_key

        mk = _month_key()
        year, month = map(int, mk.split("-"))
        next_month = f"{year:04d}-{month + 1:02d}" if month < 12 else f"{year + 1:04d}-01"
        result = ctx.journal.migrate_month(mk, next_month)
        return ok(f"Monthly migration: moved {result['migrated']} tasks to {next_month}.", module="journal")

    @classmethod
    def journal_search(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        query = params.get("query") or re.sub(r"^search journal\s*", "", message, flags=re.I)
        hits = ctx.journal.search(query)
        if not hits:
            return ok("No journal entries found.", module="journal")
        from jarvis.modules.journal import _format_bullet

        lines = "\n".join(f"[{h.get('section')}] {_format_bullet(h)}" for h in hits)
        return ok(lines, module="journal")

    @classmethod
    def journal_review(cls, ctx: PlanningContext, params: dict, message: str) -> dict:
        scope = "week" if "week" in message.lower() else "month"
        text = ctx.journal.ai_reflect_review(scope)
        return ok(text, module="journal")
