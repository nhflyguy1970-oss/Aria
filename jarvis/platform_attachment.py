"""Attach Aria to AI Platform infrastructure without changing application behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_attachment")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_ATTACHED") == "1"


def attach_platform_infrastructure(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort platform infrastructure attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "disabled"}
    try:
        from aiplatform.applications.attachment import manager as attachment_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = attachment_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            logger.info(
                "Attached to AI Platform infrastructure for %s (legacy data: %s)",
                application_id,
                (report.paths.legacy_data_dir if report.paths else "?"),
            )
        elif report.errors:
            logger.warning("Platform attachment warnings: %s", "; ".join(report.errors))
        return payload
    except Exception as exc:
        logger.warning("Platform attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_startup(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.attachment import manager as attachment_manager
    except ImportError:
        return []
    try:
        return attachment_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform startup validation failed: %s", exc)
        return [str(exc)]
