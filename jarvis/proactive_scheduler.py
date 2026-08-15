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
_last_health_reminder_hour = ""
_last_integrity_scan_ts = 0.0
_integrity_startup_done = False


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
    """Background monitoring: diagnose and prepare plans. Execute only auto-approved safe modules."""
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
        from jarvis.repair_product import store as repair_store
        from jarvis.repair_product.engine import execute_repair, scan_issues
        from jarvis.repair_product.terminology import APPROVAL_SAFE

        check_services_health()
        from jarvis.repair_product import maintenance
        from jarvis.repair_product.monitoring import tick as monitor_tick

        try:
            monitor_tick()
        except Exception:
            pass

        if maintenance.should_suppress_recommendations():
            logger.debug("Maintenance mode on — guided repair recommendations delayed")
            return
        scan = scan_issues(force=False)
        issues = scan.get("issues") or []
        if not issues:
            return
        auto = set(repair_store.auto_approve_list())
        for iss in issues:
            mid = iss.get("module_id") or ""
            plan = iss.get("plan") or {}
            if mid not in auto:
                continue
            if plan.get("approval_class") != APPROVAL_SAFE or plan.get("destructive"):
                continue
            # Harmless maintenance only — still goes through verify path
            result = execute_repair(iss["id"], approved=False, actor="auto_approve")
            # approved=False but auto list should allow via is_auto_approved
            if result.get("approval_required"):
                # Force path: execute_repair checks auto list when approved=False
                continue
            if result.get("verified"):
                logger.info("Auto-approved repair verified: %s", iss.get("title"))
            else:
                logger.warning("Auto-approved repair did not verify: %s", iss.get("title"))
        # Notify when repairs need Jeff
        needs = [i for i in issues if (i.get("module_id") or "") not in auto]
        if needs and (scan.get("critical") or 0) > 0:
            titles = ", ".join((i.get("title") or "?")[:40] for i in needs[:3])
            _notify("Guided Repair", f"{len(needs)} issue(s) need approval: {titles}")
            logger.warning("Guided Repair: %s critical/attention issue(s) awaiting Jeff", len(needs))
    except Exception as exc:
        logger.debug("Guided Repair monitor skipped: %s", exc)


def _maybe_health_reminders(now: datetime) -> None:
    global _last_health_reminder_hour
    if os.getenv("JARVIS_SCHEDULER_HEALTH", "1") == "0":
        return
    key = now.strftime("%Y-%m-%d-%H")
    if _last_health_reminder_hour == key:
        return
    _last_health_reminder_hour = key
    try:
        from jarvis.health_product.reminders import fire_due_reminders

        fire_due_reminders()
    except Exception as exc:
        logger.debug("Health reminders skipped: %s", exc)


def _maybe_integrity_scan(now: datetime) -> None:
    """Lightweight Production Integrity scan — startup once + daily (never auto-deletes)."""
    global _last_integrity_scan_ts, _integrity_startup_done
    if os.getenv("JARVIS_SCHEDULER_INTEGRITY", "1") == "0":
        return
    try:
        interval = int(os.getenv("JARVIS_INTEGRITY_INTERVAL_HOURS", "24")) * 3600
    except ValueError:
        interval = 86400
    now_ts = time.time()
    trigger = None
    if not _integrity_startup_done:
        trigger = "startup"
        _integrity_startup_done = True
    elif interval > 0 and now_ts - _last_integrity_scan_ts >= interval:
        trigger = "daily"
    if not trigger:
        return
    _last_integrity_scan_ts = now_ts
    try:
        from jarvis.integrity_product.scanner import run_scan
        from jarvis.repair_product.engine import prepare_issue
        from jarvis.integrity_product.repair_module import ProductionIntegrityModule

        scan = run_scan(force=True, trigger=trigger)
        count = int((scan.get("counts") or {}).get("total") or 0)
        if count <= 0:
            logger.info("Production Integrity (%s): clean", trigger)
            return
        logger.warning("Production Integrity (%s): %s artifact(s) — recommending Guided Repair", trigger, count)
        detected = ProductionIntegrityModule().detect()
        if detected:
            prepare_issue(detected[0])
        _notify(
            "Production Integrity",
            f"{count} development artifact(s) found — open Mission Control → Recovery to review.",
        )
    except Exception as exc:
        logger.debug("Integrity scan skipped: %s", exc)


def _loop() -> None:
    while not _stop.wait(60):
        try:
            now = datetime.now()
            _maybe_briefing(now)
            _maybe_task_nudge(now)
            _maybe_git_sync(now)
            _maybe_auto_recover(now)
            _maybe_health_reminders(now)
            _maybe_integrity_scan(now)
            from jarvis.automation.ops import maybe_nightly_maintenance

            maybe_nightly_maintenance(now)
            try:
                from jarvis.flytying.nightly import run_scheduled as flytying_nightly

                memory = None
                try:
                    # C6: never construct a second assistant from the daemon scheduler.
                    from jarvis.assistant_instance import get_assistant_or_none

                    asst = get_assistant_or_none()
                    memory = getattr(asst, "memory", None) if asst else None
                except Exception:
                    memory = None
                flytying_nightly(now, memory=memory)
            except Exception as exc:
                logger.debug("Fly tying nightly skipped: %s", exc)
            try:
                from jarvis.sunlight_scene import tick_sunlight

                tick_sunlight()
            except Exception as exc:
                logger.debug("Sunlight tick skipped: %s", exc)
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
