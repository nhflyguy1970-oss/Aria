"""Unified job queue interface (media, coding, background)."""

from __future__ import annotations

from typing import Any, Callable

QUEUES = ("media", "coding", "background", "audio")


def stats(queue: str) -> dict[str, Any]:
    if queue == "media":
        from jarvis.media_jobs import job_stats

        return job_stats()
    if queue == "coding":
        from jarvis.coding_jobs import job_stats

        return job_stats()
    if queue == "background":
        from jarvis.coding_jobs import job_stats

        return job_stats()
    if queue == "audio":
        from jarvis.audio_progress import job_stats

        return job_stats()
    raise ValueError(f"Unknown queue: {queue}")


def get_job(queue: str, job_id: str) -> dict[str, Any] | None:
    if queue == "media":
        from jarvis.media_jobs import get_job as _get

        return _get(job_id)
    if queue in ("coding", "background"):
        from jarvis.coding_jobs import get_job as _get

        return _get(job_id)
    if queue == "audio":
        from jarvis.audio_progress import get_job as _get

        return _get(job_id)
    raise ValueError(f"Unknown queue: {queue}")


def cancel(queue: str, job_id: str) -> bool:
    if queue == "media":
        from jarvis.media_jobs import cancel_job

        return cancel_job(job_id)
    if queue in ("coding", "background"):
        from jarvis.coding_jobs import cancel_job

        return cancel_job(job_id)
    if queue == "audio":
        from jarvis.audio_progress import cancel_job

        return cancel_job(job_id)
    raise ValueError(f"Unknown queue: {queue}")


def list_recent(queue: str, limit: int = 10) -> list[dict]:
    if queue == "media":
        from jarvis.media_jobs import list_recent

        return list_recent(limit)
    if queue in ("coding", "background"):
        from jarvis.coding_jobs import list_recent

        return list_recent(limit)
    if queue == "audio":
        from jarvis.audio_progress import list_recent

        return list_recent(limit)
    raise ValueError(f"Unknown queue: {queue}")


def submit(queue: str, label: str, fn: Callable[[], dict]) -> str:
    if queue == "media":
        from jarvis.media_jobs import submit as _submit

        return _submit(label, fn)
    if queue in ("coding", "background"):
        from jarvis.coding_jobs import submit as _submit

        return _submit(label, fn)
    raise ValueError(f"Queue {queue} does not support generic submit")


def submit_assistant_action(assistant, action: str, params: dict, message: str) -> str:
    """Submit based on registry queue metadata."""
    from jarvis.background_jobs import submit_action as submit_background
    from jarvis.handlers.registry import get_queue
    from jarvis.media_jobs import submit_assistant_action as submit_media

    queue = get_queue(action)
    if queue == "media":
        return submit_media(assistant, action, params, message)
    if queue == "background":
        return submit_background(assistant, action, params, message)
    raise ValueError(f"Action {action} is not a queued action (queue={queue})")
