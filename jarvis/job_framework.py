"""Unified job queue interface (media, coding, background)."""

from __future__ import annotations

from typing import Any, Callable

# "background" and "fix_tests" are routing labels, not separate registries: both
# submit to the coding worker registry and are read at /api/coding/job/<id>.
QUEUES = ("media", "coding", "background", "fix_tests", "audio")

# Queue label -> the registry that actually owns the job.
CODING_QUEUES = ("coding", "background", "fix_tests")


def stats(queue: str | None = None) -> dict[str, Any]:
    if queue == "media":
        from jarvis.media_jobs import job_stats

        return job_stats()
    if queue in CODING_QUEUES:
        from jarvis.coding_jobs import job_stats

        return job_stats()
    if queue == "audio":
        from jarvis.audio_progress import job_stats

        return job_stats()
    raise ValueError(f"Unknown queue: {queue}")


def get_job(queue: str | None, job_id: str | None) -> dict | None:
    if queue == "media":
        from jarvis.media_jobs import get_job as _get

        return _get(job_id)
    if queue in CODING_QUEUES:
        from jarvis.coding_jobs import get_job as _get

        return _get(job_id)
    if queue == "audio":
        from jarvis.audio_progress import get_job as _get

        return _get(job_id)
    raise ValueError(f"Unknown queue: {queue}")


def cancel(queue: str | None, job_id: str | None) -> bool:
    if queue == "media":
        from jarvis.media_jobs import cancel_job

        return cancel_job(job_id)
    if queue in CODING_QUEUES:
        from jarvis.coding_jobs import cancel_job

        return cancel_job(job_id)
    if queue == "audio":
        from jarvis.audio_progress import cancel_job

        return cancel_job(job_id)
    raise ValueError(f"Unknown queue: {queue}")


def list_recent(queue: str | None, limit: int | None = None) -> list[dict]:
    limit = limit or 10
    if queue == "media":
        from jarvis.media_jobs import list_recent as _list

        return _list(limit)
    if queue in CODING_QUEUES:
        from jarvis.coding_jobs import list_recent as _list

        return _list(limit)
    if queue == "audio":
        from jarvis.audio_progress import list_recent as _list

        return _list(limit)
    raise ValueError(f"Unknown queue: {queue}")


def submit(queue: str | None, label: str | None, fn: Callable[[], dict] | None) -> str:
    if queue == "media":
        from jarvis.media_jobs import submit as _submit

        action = label or "job"
        return _submit(action, label or action, fn)
    if queue in CODING_QUEUES:
        from jarvis.coding_jobs import submit as _submit

        return _submit(label or queue or "job", fn)
    raise ValueError(f"Queue {queue} does not support generic submit")


def submit_assistant_action(
    assistant: Any,
    action: str,
    params: dict,
    message: str,
) -> str:
    """Submit based on registry queue metadata."""
    from jarvis.background_jobs import submit_action as submit_background
    from jarvis.handlers.registry import get_queue
    from jarvis.media_jobs import submit_assistant_action as submit_media

    queue = get_queue(action)
    if queue == "media":
        return submit_media(assistant, action, params, message)
    if queue == "background":
        return submit_background(assistant, action, params, message)
    if queue in CODING_QUEUES:
        # Queued, but the coding submitters take different arguments — say so
        # instead of claiming the action is not queued at all.
        raise ValueError(
            f"Action {action} is queued on the coding worker (queue={queue}); "
            "submit via coding_jobs.submit_coding_agent/submit_fix_tests"
        )
    raise ValueError(f"Action {action} is not a queued action (queue={queue})")
