"""Attach Aria inference runtime to AI Platform model management without replacing inference."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("jarvis.platform_inference")

_APPLICATION_ID = "aria"
_ATTACHED = False


def is_inference_attached() -> bool:
    return _ATTACHED or os.getenv("JARVIS_PLATFORM_INFERENCE_ATTACHED") == "1"


def attach_platform_inference(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    """Best-effort platform inference attachment. Never raises."""
    global _ATTACHED
    if os.getenv("JARVIS_DISABLE_PLATFORM_INFERENCE", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "disabled"}
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return {"attached": False, "reason": "platform_attachment_disabled"}
    try:
        from aiplatform.applications.inference import manager as inference_manager
    except ImportError:
        return {"attached": False, "reason": "aiplatform not available"}
    try:
        report = inference_manager.attach_to_process(application_id)
        payload = report.to_dict()
        if report.attached:
            _ATTACHED = True
            logger.info(
                "Attached inference to AI Platform for %s (%s installed / %s discovered)",
                application_id,
                report.installed_count,
                report.discovery_count,
            )
        elif report.errors:
            logger.warning("Platform inference attachment errors: %s", "; ".join(report.errors))
        elif report.warnings:
            logger.info("Platform inference attachment warnings: %s", "; ".join(report.warnings))
        return payload
    except Exception as exc:
        logger.warning("Platform inference attachment failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def installed_models() -> list[str]:
    """Return installed model names from the platform registry when attached."""
    if not is_inference_attached():
        return []
    try:
        from aiplatform.applications.inference.validator import refresh_models
        from aiplatform.models import models as model_registry

        refresh_models()
        return [model.name for model in model_registry.installed()]
    except Exception as exc:
        logger.debug("Platform installed model lookup failed: %s", exc)
        return []


def required_model_status(application_id: str = _APPLICATION_ID) -> dict[str, Any]:
    if not is_inference_attached():
        return {"attached": False}
    try:
        from aiplatform.applications.inference import manager as inference_manager

        return inference_manager.health_report(application_id)
    except Exception as exc:
        logger.debug("Platform required model status failed: %s", exc)
        return {"attached": False, "reason": str(exc)}


def validate_platform_inference(
    application_id: str = _APPLICATION_ID,
    *,
    strict: bool = False,
) -> list[str]:
    try:
        from aiplatform.applications.inference import manager as inference_manager
    except ImportError:
        return []
    try:
        return inference_manager.validate_startup(application_id, strict=strict)
    except Exception as exc:
        logger.warning("Platform inference validation failed: %s", exc)
        return [str(exc)]
