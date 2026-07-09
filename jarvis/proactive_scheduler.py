"""Lightweight in-process scheduler for briefing nudges and task reminders."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from datetime import datetime

logger = logging.getLogger("jarvis.scheduler")

_stop = threading.Event()
_thread: threading.Thread | None = None
_last_briefing_day = ""
_last_nudge_day = ""


def _notify(title: str, body: str) -> None:
    try:
        subprocess.run(
            ["notify-send", "-a", "Jarvis", title, body[:240]],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception as exc:
        logger.debug("Scheduler notify failed: %s", exc)


def _maybe_briefing(now: datetime) -> None:
    from jarvis.modules.automation_event_adapter import automation_schedule_run

    automation_schedule_run("proactive", "briefing", _maybe_briefing_impl, now)


def _maybe_briefing_impl(now: datetime) -> None:
    global _last_briefing_day
    if os.getenv("JARVIS_SCHEDULER_BRIEFING", "1") == "0":
        from jarvis.modules.automation_event_adapter import automation_record_skipped

        automation_record_skipped("proactive", "briefing")
        return
    try:
        hour = int(os.getenv("JARVIS_SCHEDULE_BRIEFING_HOUR", "7"))
    except ValueError:
        hour = 7
    day = now.date().isoformat()
    if now.hour != hour or _last_briefing_day == day:
        return
    from jarvis.morning_briefing import briefing_enabled, should_show_launch_briefing

    if not briefing_enabled() or not should_show_launch_briefing(day=day):
        return
    _last_briefing_day = day
    _notify("ARIA", "Good morning — open ARIA for today's briefing.")
    logger.info("Proactive briefing nudge sent for %s", day)


def _maybe_task_nudge(now: datetime) -> None:
    from jarvis.modules.automation_event_adapter import automation_schedule_run

    automation_schedule_run("proactive", "task_nudge", _maybe_task_nudge_impl, now)


def _maybe_task_nudge_impl(now: datetime) -> None:
    global _last_nudge_day
    if os.getenv("JARVIS_SCHEDULER_NUDGE", "1") == "0":
        from jarvis.modules.automation_event_adapter import automation_record_skipped

        automation_record_skipped("proactive", "task_nudge")
        return
    try:
        hour = int(os.getenv("JARVIS_SCHEDULE_NUDGE_HOUR", "10"))
    except ValueError:
        hour = 10
    day = now.date().isoformat()
    if now.hour != hour or now.minute > 5 or _last_nudge_day == day:
        return
    try:
        from jarvis.movie_tiers import task_nudge_check

        nudge = task_nudge_check()
        if nudge.get("nudge") and nudge.get("message"):
            from jarvis.movie_tiers import mark_task_nudge_shown

            mark_task_nudge_shown()
            _last_nudge_day = day
            _notify("ARIA tasks", str(nudge["message"]).replace("**", "").replace("_", "")[:200])
            logger.info("Task nudge sent")
    except Exception as exc:
        logger.debug("Task nudge skipped: %s", exc)


def _loop() -> None:
    while not _stop.wait(60):
        try:
            now = datetime.now()
            _maybe_briefing(now)
            _maybe_task_nudge(now)
        except Exception as exc:
            logger.warning("Scheduler tick failed: %s", exc)


def start() -> None:
    from jarvis.modules.automation_event_adapter import automation_start

    automation_start(_start_impl)


def _start_impl() -> None:
    global _thread
    if os.getenv("JARVIS_SCHEDULER", "1") == "0":
        from jarvis.modules.automation_event_adapter import automation_record_skipped

        automation_record_skipped("proactive", "scheduler")
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, daemon=True, name="jarvis-scheduler")
    _thread.start()
    logger.info("Proactive scheduler started")


def stop() -> None:
    _stop.set()
    if _thread:
        _thread.join(timeout=2)
