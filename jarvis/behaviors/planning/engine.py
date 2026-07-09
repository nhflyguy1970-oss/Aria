"""Planning engine — planner, timers, alarms, calendar, and scheduling decisions."""

from __future__ import annotations

import re
from typing import Any

from jarvis.behaviors.planning.context import PlanningContext
from jarvis.feature_flags import planner_enabled
from jarvis.response import err, ok


class PlanningEngine:
    """Isolated planning domain logic."""

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
