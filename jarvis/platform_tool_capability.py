"""Attach Aria capabilities to AI Platform without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_tool_capability")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_tool_capability_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED") == "1"


def attach_platform_tool_capability(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort tool capability attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_TOOL_CAPABILITY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.tool_capability import manager as tool_capability_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = tool_capability_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            try:
                from jarvis.modules.capability_adapter import sync_capabilities

                registered = sync_capabilities(application_id)
                payload["registered_capabilities"] = registered
            except Exception as exc:
                logger.debug("Capability sync deferred: %s", exc)
            logger.info(
                "Attached tool capabilities to AI Platform for %s (%s registered)",
                application_id,
                payload.get("registered_capabilities", 0),
            )
        elif report.errors:
            logger.warning("Platform tool capability errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform tool capability warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform tool capability attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def tool_capability_metrics(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_tool_capability_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.tool_capability import manager as tool_capability_manager

        return tool_capability_manager.metrics(application_id)
    except Exception as exc:
        logger.debug("Platform tool capability metrics failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_tool_capability(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.tool_capability import manager as tool_capability_manager
    except ImportError:
        return []
    try:
        return tool_capability_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform tool capability validation failed: %s", exc)
        return [str(exc)]
