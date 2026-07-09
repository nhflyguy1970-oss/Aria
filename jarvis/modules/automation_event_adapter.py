"""Automation and event adapter — legacy scheduling remains authoritative."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("jarvis.automation_event_adapter")

_APPLICATION_ID = "aria"
_SYNCED = False

T = TypeVar("T")


def automation_event_enabled() -> bool:
    if os.getenv("JARVIS_DISABLE_PLATFORM_AUTOMATION_EVENT", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_PLATFORM_AUTOMATION_EVENT_ATTACHED") == "1":
        return True
    try:
        from jarvis.platform_automation_event import is_automation_event_attached

        return is_automation_event_attached()
    except ImportError:
        return False


def sync_automations(application_id: str = _APPLICATION_ID) -> int:
    global _SYNCED
    if not automation_event_enabled():
        return 0
    try:
        from aiplatform.applications.automation_event.bridge import (
            default_aria_automations,
            register_automations,
        )

        count = register_automations(application_id, default_aria_automations(application_id))
        _SYNCED = count > 0
        return count
    except Exception as exc:
        logger.warning("Automation sync failed (continuing): %s", exc)
        return 0


def automation_start(legacy_start: Callable[[], None]) -> None:
    if automation_event_enabled() and not _SYNCED:
        sync_automations()
    legacy_start()


def automation_schedule_run(
    category: str,
    name: str,
    legacy_run: Callable[..., None],
    *args: Any,
    **kwargs: Any,
) -> None:
    if automation_event_enabled() and not _SYNCED:
        sync_automations()
    start = time.perf_counter()
    fired = False
    try:
        legacy_run(*args, **kwargs)
        fired = True
    finally:
        if automation_event_enabled():
            try:
                from aiplatform.applications.automation_event.bridge import (
                    automation_id,
                    shadow_verify_trigger,
                )
                from aiplatform.applications.automation_event.metrics import (
                    record_scheduled_execution,
                )

                auto_id = automation_id(_APPLICATION_ID, category, name)
                latency_ms = (time.perf_counter() - start) * 1000
                if fired:
                    record_scheduled_execution(
                        _APPLICATION_ID,
                        auto_id,
                        latency_ms=latency_ms,
                        reminder=name.endswith("nudge"),
                    )
                    shadow_verify_trigger(_APPLICATION_ID, auto_id)
            except Exception as exc:
                logger.debug("Automation schedule metrics skipped: %s", exc)


def automation_planner_call(
    name: str,
    legacy_call: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    if automation_event_enabled() and not _SYNCED:
        sync_automations()
    start = time.perf_counter()
    result = legacy_call(*args, **kwargs)
    if automation_event_enabled():
        try:
            from aiplatform.applications.automation_event.bridge import (
                automation_id,
                shadow_verify_trigger,
            )
            from aiplatform.applications.automation_event.metrics import (
                record_planner_event,
                record_trigger_execution,
            )

            auto_id = automation_id(_APPLICATION_ID, "planner", name)
            record_planner_event(_APPLICATION_ID, auto_id)
            record_trigger_execution(
                _APPLICATION_ID,
                auto_id,
                latency_ms=(time.perf_counter() - start) * 1000,
            )
            event_name = f"aria.planner.{name}" if name in ("timer", "alarm") else auto_id
            shadow_verify_trigger(_APPLICATION_ID, auto_id, event_name=event_name)
        except Exception as exc:
            logger.debug("Automation planner metrics skipped: %s", exc)
    return result


def automation_calendar_call(
    legacy_call: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    if automation_event_enabled() and not _SYNCED:
        sync_automations()
    result = legacy_call(*args, **kwargs)
    if automation_event_enabled():
        try:
            from aiplatform.applications.automation_event.bridge import automation_id
            from aiplatform.applications.automation_event.metrics import record_scheduled_execution

            auto_id = automation_id(_APPLICATION_ID, "calendar", "event")
            record_scheduled_execution(_APPLICATION_ID, auto_id, latency_ms=0.0)
        except Exception as exc:
            logger.debug("Automation calendar metrics skipped: %s", exc)
    return result


def automation_reminder_tick(
    legacy_tick: Callable[[], list[dict[str, str]]],
) -> list[dict[str, str]]:
    if automation_event_enabled() and not _SYNCED:
        sync_automations()
    start = time.perf_counter()
    notes = legacy_tick()
    if automation_event_enabled():
        try:
            from aiplatform.applications.automation_event.bridge import (
                automation_id,
                shadow_verify_trigger,
            )
            from aiplatform.applications.automation_event.metrics import (
                record_scheduled_execution,
                record_trigger_execution,
            )

            auto_id = automation_id(_APPLICATION_ID, "reminder", "tick")
            latency_ms = (time.perf_counter() - start) * 1000
            if notes:
                for _note in notes:
                    record_scheduled_execution(
                        _APPLICATION_ID,
                        auto_id,
                        latency_ms=latency_ms,
                        reminder=True,
                    )
                    record_trigger_execution(_APPLICATION_ID, auto_id, latency_ms=latency_ms)
                shadow_verify_trigger(
                    _APPLICATION_ID,
                    auto_id,
                    event_name="aria.reminder.tick",
                )
        except Exception as exc:
            logger.debug("Automation reminder metrics skipped: %s", exc)
    return notes


def automation_record_skipped(category: str, name: str) -> None:
    if not automation_event_enabled():
        return
    try:
        from aiplatform.applications.automation_event.bridge import automation_id
        from aiplatform.applications.automation_event.metrics import record_skipped_job

        record_skipped_job(_APPLICATION_ID, automation_id(_APPLICATION_ID, category, name))
    except Exception:
        pass
