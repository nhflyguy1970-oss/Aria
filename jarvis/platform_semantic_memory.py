"""Attach Aria semantic memory to AI Platform vector store without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_semantic_memory")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_semantic_memory_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") == "1"


def attach_platform_semantic_memory(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort semantic memory attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_SEMANTIC_MEMORY", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.semantic import manager as semantic_memory_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = semantic_memory_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            logger.info(
                "Attached semantic memory to AI Platform for %s (index: %s)",
                application_id,
                report.platform_index_path,
            )
        elif report.errors:
            logger.warning("Platform semantic memory errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform semantic memory warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform semantic memory attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def semantic_memory_metrics(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_semantic_memory_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.semantic import manager as semantic_memory_manager

        return semantic_memory_manager.metrics(application_id)
    except Exception as exc:
        logger.debug("Platform semantic memory metrics failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_semantic_memory(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.semantic import manager as semantic_memory_manager
    except ImportError:
        return []
    try:
        return semantic_memory_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform semantic memory validation failed: %s", exc)
        return [str(exc)]
