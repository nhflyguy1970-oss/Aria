"""Queue metadata for media and background actions."""

from __future__ import annotations

from jarvis.background_jobs import ACTION_LABELS as BG_LABELS, BACKGROUND_ACTIONS
from jarvis.handlers.registry import register_queue
from jarvis.media_jobs import ACTION_LABELS as MEDIA_LABELS, QUEUED_ACTIONS


def register_queue_actions() -> None:
    for action in QUEUED_ACTIONS:
        register_queue(
            action,
            "media",
            module="image",
            description=MEDIA_LABELS.get(action, action),
        )
    for action in BACKGROUND_ACTIONS:
        register_queue(
            action,
            "background",
            description=BG_LABELS.get(action, action),
        )
    register_queue("coding_agent", "coding", description="Coding agent task")
    register_queue("coding_fix_tests", "fix_tests", description="Fix failing tests")
