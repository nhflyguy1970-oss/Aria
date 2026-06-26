"""Registered action handlers."""

from jarvis.handlers.media import MediaHandler

_loaded = False


def ensure_handlers_loaded() -> None:
    global _loaded
    if _loaded:
        return
    from jarvis.handlers import git_handlers, journal_handlers, meta  # noqa: F401
    from jarvis.handlers.queues import register_queue_actions

    register_queue_actions()
    _loaded = True


__all__ = ["MediaHandler", "ensure_handlers_loaded"]
