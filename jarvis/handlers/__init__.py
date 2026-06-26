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
    try:
        from jarvis.extensibility.loader import load_extensions

        load_extensions()
    except Exception:
        import logging

        logging.getLogger("jarvis.handlers").exception("Extension load failed")
    _loaded = True


__all__ = ["MediaHandler", "ensure_handlers_loaded"]
