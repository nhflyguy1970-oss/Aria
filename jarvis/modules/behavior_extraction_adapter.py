"""Sync extracted behaviors with AI Platform behavior extraction manager."""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("jarvis.modules.behavior_extraction_adapter")

_APPLICATION_ID = "aria"


def behavior_extraction_enabled() -> bool:
    import os

    if os.getenv("JARVIS_DISABLE_PLATFORM_BEHAVIOR_EXTRACTION", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    try:
        from jarvis.platform_behavior_extraction import is_behavior_extraction_attached

        return is_behavior_extraction_attached()
    except Exception:
        return False


def sync_behaviors(application_id: str = _APPLICATION_ID) -> int:
    if not behavior_extraction_enabled():
        return 0
    try:
        from jarvis.behaviors import behavior_descriptors, register_behaviors

        register_behaviors()
        payloads = behavior_descriptors(application_id)
        from aiplatform.applications.behavior_extraction.bridge import register_behaviors as platform_register

        return platform_register(application_id, payloads)
    except Exception as exc:
        logger.warning("Platform behavior sync failed (continuing): %s", exc)
        return 0


def record_behavior_invocation(
    application_id: str,
    behavior_id: str,
    *,
    action: str = "",
    runtime_ms: float = 0.0,
) -> None:
    if not behavior_extraction_enabled():
        return
    try:
        from aiplatform.applications.behavior_extraction.state import (
            load_behavior_extraction_state,
            save_behavior_extraction_state,
        )

        state = load_behavior_extraction_state(application_id)
        key = behavior_id or action
        if key:
            state.behavior_statistics[key] = state.behavior_statistics.get(key, 0) + 1
        state.updated_at = time.time()
        save_behavior_extraction_state(state)
    except Exception as exc:
        logger.debug("Could not record behavior invocation: %s", exc)
