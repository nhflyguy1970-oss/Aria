"""Attach Aria memory to AI Platform memory management without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_memory")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_memory_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1"


def attach_platform_memory(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort platform memory adapter attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_MEMORY", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.memory import manager as memory_adapter_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = memory_adapter_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            logger.info(
                "Attached memory adapter to AI Platform for %s (storage: %s)",
                application_id,
                report.platform_storage_path,
            )
        elif report.errors:
            logger.warning("Platform memory adapter errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform memory adapter warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform memory adapter attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def memory_adapter_metrics(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_memory_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.memory import manager as memory_adapter_manager

        return memory_adapter_manager.metrics(application_id)
    except Exception as exc:
        logger.debug("Platform memory adapter metrics failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_memory(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.memory import manager as memory_adapter_manager
    except ImportError:
        return []
    try:
        return memory_adapter_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform memory validation failed: %s", exc)
        return [str(exc)]
