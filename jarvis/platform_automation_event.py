"""Attach Aria automation to AI Platform without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_automation_event")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_automation_event_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_AUTOMATION_EVENT_ATTACHED") == "1"


def attach_platform_automation_event(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort automation event attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_AUTOMATION_EVENT", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.automation_event import manager as automation_event_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = automation_event_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            try:
                from jarvis.modules.automation_event_adapter import sync_automations

                registered = sync_automations(application_id)
                payload["registered_automations"] = registered
            except Exception as exc:
                logger.debug("Automation sync deferred: %s", exc)
            logger.info(
                "Attached automation to AI Platform for %s (%s automations)",
                application_id,
                payload.get("registered_automations", 0),
            )
        elif report.errors:
            logger.warning("Platform automation errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform automation warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform automation attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def automation_event_metrics(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_automation_event_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.automation_event import manager as automation_event_manager

        return automation_event_manager.metrics(application_id)
    except Exception as exc:
        logger.debug("Platform automation metrics failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_automation_event(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.automation_event import manager as automation_event_manager
    except ImportError:
        return []
    try:
        return automation_event_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform automation validation failed: %s", exc)
        return [str(exc)]
