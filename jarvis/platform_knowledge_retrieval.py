"""Attach Aria knowledge and retrieval to AI Platform without replacing behavior."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_knowledge_retrieval")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_knowledge_retrieval_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED") == "1"


def attach_platform_knowledge_retrieval(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort knowledge retrieval attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_KNOWLEDGE_RETRIEVAL", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.knowledge_retrieval import manager as knowledge_retrieval_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = knowledge_retrieval_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            logger.info(
                "Attached knowledge retrieval to AI Platform for %s (knowledge: %s)",
                application_id,
                report.platform_knowledge_root,
            )
        elif report.errors:
            logger.warning("Platform knowledge retrieval errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform knowledge retrieval warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform knowledge retrieval attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def knowledge_retrieval_metrics(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_knowledge_retrieval_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.knowledge_retrieval import manager as knowledge_retrieval_manager

        return knowledge_retrieval_manager.metrics(application_id)
    except Exception as exc:
        logger.debug("Platform knowledge retrieval metrics failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_knowledge_retrieval(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.knowledge_retrieval import manager as knowledge_retrieval_manager
    except ImportError:
        return []
    try:
        return knowledge_retrieval_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform knowledge retrieval validation failed: %s", exc)
        return [str(exc)]
