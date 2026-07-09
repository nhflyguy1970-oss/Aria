"""Workflow and orchestration adapter — legacy job queues remain authoritative."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("jarvis.workflow_orchestration_adapter")

_APPLICATION_ID = "aria"
_SYNCED = False

T = TypeVar("T")


def workflow_orchestration_enabled() -> bool:
    if os.getenv("JARVIS_DISABLE_PLATFORM_WORKFLOW_ORCHESTRATION", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED") == "1":
        return True
    try:
        from jarvis.platform_workflow_orchestration import is_workflow_orchestration_attached

        return is_workflow_orchestration_attached()
    except ImportError:
        return False


def sync_workflows(application_id: str = _APPLICATION_ID) -> int:
    global _SYNCED
    if not workflow_orchestration_enabled():
        return 0
    try:
        from aiplatform.applications.workflow_orchestration.bridge import (
            queue_to_workflow,
            register_workflows,
        )

        workflows = []
        try:
            from jarvis.media_jobs import ACTION_LABELS, ETA_HINTS, QUEUED_ACTIONS

            for action in sorted(QUEUED_ACTIONS):
                workflows.append(
                    queue_to_workflow(
                        application_id,
                        "media",
                        action=action,
                        label=ACTION_LABELS.get(action, action),
                        description=f"Media queue workflow for {action}",
                        estimated_runtime=ETA_HINTS.get(action, ""),
                        requires_gpu=True,
                    )
                )
        except Exception as exc:
            logger.debug("Media workflow catalog skipped: %s", exc)
        try:
            from jarvis.background_jobs import ACTION_LABELS as BG_LABELS, BACKGROUND_ACTIONS

            for action in sorted(BACKGROUND_ACTIONS):
                workflows.append(
                    queue_to_workflow(
                        application_id,
                        "background",
                        action=action,
                        label=BG_LABELS.get(action, action),
                        description=f"Background orchestration workflow for {action}",
                        background=True,
                    )
                )
        except Exception as exc:
            logger.debug("Background workflow catalog skipped: %s", exc)
        for queue, label in (("coding", "Coding agent"), ("background", "Background queue")):
            workflows.append(
                queue_to_workflow(
                    application_id,
                    queue,
                    label=label,
                    description=f"Aria {queue} job orchestration",
                    background=True,
                )
            )
        count = register_workflows(application_id, workflows)
        _SYNCED = count > 0
        return count
    except Exception as exc:
        logger.warning("Workflow sync failed (continuing): %s", exc)
        return 0


def _queue_depth(queue: str) -> int:
    try:
        if queue == "media":
            from jarvis.media_jobs import job_stats

            return int(job_stats().get("pending", 0))
        if queue in ("coding", "background"):
            from jarvis.coding_jobs import job_stats

            return int(job_stats().get("pending", 0))
    except Exception:
        pass
    return 0


def workflow_enqueue(
    queue: str,
    workflow_key: str,
    legacy_submit: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    if workflow_orchestration_enabled() and not _SYNCED:
        sync_workflows()
    start = time.perf_counter()
    result = legacy_submit(*args, **kwargs)
    if workflow_orchestration_enabled():
        try:
            from aiplatform.applications.workflow_orchestration.bridge import workflow_id
            from aiplatform.applications.workflow_orchestration.metrics import record_execution

            latency_ms = (time.perf_counter() - start) * 1000
            record_execution(
                _APPLICATION_ID,
                workflow_id(_APPLICATION_ID, queue, workflow_key),
                elapsed_ms=0.0,
                orchestration_latency_ms=latency_ms,
                queue_depth=_queue_depth(queue),
                success=True,
                background=queue in ("background", "coding"),
            )
        except Exception as exc:
            logger.debug("Workflow enqueue metrics skipped: %s", exc)
    return result


def workflow_cancel(
    queue: str,
    workflow_key: str,
    legacy_cancel: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    result = legacy_cancel(*args, **kwargs)
    if workflow_orchestration_enabled():
        try:
            from aiplatform.applications.workflow_orchestration.bridge import workflow_id
            from aiplatform.applications.workflow_orchestration.metrics import (
                record_cancellation,
            )

            record_cancellation(
                _APPLICATION_ID,
                workflow_id(_APPLICATION_ID, queue, workflow_key),
            )
        except Exception as exc:
            logger.debug("Workflow cancel metrics skipped: %s", exc)
    return result
