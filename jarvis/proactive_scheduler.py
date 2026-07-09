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
_last_git_sync_ts = 0.0
_last_auto_recover_ts = 0.0


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


def _maybe_git_sync(now: datetime) -> None:
    global _last_git_sync_ts
    if os.getenv("JARVIS_SCHEDULER_GIT_SYNC", "1") == "0":
        return
    try:
        interval = int(os.getenv("JARVIS_GIT_SYNC_INTERVAL_MIN", "30")) * 60
    except ValueError:
        interval = 1800
    if interval <= 0:
        return
    now_ts = time.time()
    if now_ts - _last_git_sync_ts < interval:
        return
    _last_git_sync_ts = now_ts
    try:
        from jarvis.knowledge.git_sync import sync_all

        result = sync_all(force=False)
        logger.info("Scheduled git sync: %s repo(s), ok=%s", result.get("repos"), result.get("ok"))
    except Exception as exc:
        logger.debug("Scheduled git sync failed: %s", exc)


def _maybe_auto_recover(now: datetime) -> None:
    global _last_auto_recover_ts
    if os.getenv("JARVIS_AUTO_RECOVER", "1") == "0":
        return
    try:
        interval = int(os.getenv("JARVIS_AUTO_RECOVER_INTERVAL_MIN", "5")) * 60
    except ValueError:
        interval = 300
    now_ts = time.time()
    if now_ts - _last_auto_recover_ts < interval:
        return
    _last_auto_recover_ts = now_ts
    try:
        from jarvis.interrupt_policy import check_services_health
        from jarvis.workstation.operations import diagnose, recover_safe

        check_services_health()
        report = diagnose(force=False)
        if not report.get("ok") or report.get("warnings", 0) > 0:
            result = recover_safe(max_attempts=2)
            if result.get("ok"):
                logger.info("Auto-recover resolved workstation issues")
            elif report.get("critical", 0) > 0:
                logger.warning("Auto-recover could not fix critical issues")
    except Exception as exc:
        logger.debug("Auto-recover skipped: %s", exc)


def _loop() -> None:
    while not _stop.wait(60):
        try:
            now = datetime.now()
            _maybe_briefing(now)
            _maybe_task_nudge(now)
            _maybe_git_sync(now)
            _maybe_auto_recover(now)
            from jarvis.automation.ops import maybe_nightly_maintenance

            maybe_nightly_maintenance(now)
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
