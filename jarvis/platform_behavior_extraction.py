"""Attach Aria behavior extraction to AI Platform without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_behavior_extraction")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_behavior_extraction_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_BEHAVIOR_EXTRACTION_ATTACHED") == "1"


def attach_platform_behavior_extraction(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort behavior extraction attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_BEHAVIOR_EXTRACTION", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.behavior_extraction import manager as behavior_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = behavior_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            try:
                from jarvis.modules.behavior_extraction_adapter import sync_behaviors

                registered = sync_behaviors(application_id)
                payload["registered_behaviors"] = registered
            except Exception as exc:
                logger.debug("Behavior sync deferred: %s", exc)
            logger.info(
                "Attached behavior extraction to AI Platform for %s (%s behaviors)",
                application_id,
                payload.get("registered_behaviors", 0),
            )
        elif report.errors:
            logger.warning("Platform behavior extraction errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform behavior extraction warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform behavior extraction attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_behavior_extraction(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.behavior_extraction import manager as behavior_manager
    except ImportError:
        return []
    try:
        return behavior_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform behavior extraction validation failed: %s", exc)
        return [str(exc)]
