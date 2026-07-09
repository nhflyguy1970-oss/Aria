"""Attach Aria workflow orchestration to AI Platform without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_workflow_orchestration")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_workflow_orchestration_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED") == "1"


def attach_platform_workflow_orchestration(
    application_id: str = _APPLICATION_ID,
) -> dict[str, Any]:
    """Best-effort workflow orchestration attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_WORKFLOW_ORCHESTRATION", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.workflow_orchestration import (
            manager as workflow_orchestration_manager,
        )
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = workflow_orchestration_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            try:
                from jarvis.modules.workflow_orchestration_adapter import sync_workflows

                registered = sync_workflows(application_id)
                payload["registered_workflows"] = registered
            except Exception as exc:
                logger.debug("Workflow sync deferred: %s", exc)
            logger.info(
                "Attached workflow orchestration to AI Platform for %s (%s workflows)",
                application_id,
                payload.get("registered_workflows", 0),
            )
        elif report.errors:
            logger.warning(
                "Platform workflow orchestration errors: %s",
                "; ".join(report.errors),
            )
        elif report.warnings:
            logger.info(
                "Platform workflow orchestration warnings: %s",
                "; ".join(report.warnings),
            )
        return payload
    except Exception as exc:
        logger.warning("Platform workflow orchestration attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def workflow_orchestration_metrics(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_workflow_orchestration_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.workflow_orchestration import (
            manager as workflow_orchestration_manager,
        )

        return workflow_orchestration_manager.metrics(application_id)
    except Exception as exc:
        logger.debug("Platform workflow orchestration metrics failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_workflow_orchestration(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.workflow_orchestration import (
            manager as workflow_orchestration_manager,
        )
    except ImportError:
        return []
    try:
        return workflow_orchestration_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform workflow orchestration validation failed: %s", exc)
        return [str(exc)]
