"""Registered action handlers."""

from jarvis.handlers.media import MediaHandler

_loaded = False


def ensure_handlers_loaded() -> None:
    global _loaded
    if _loaded:
        return
    from jarvis.behaviors import register_behaviors
    from jarvis.handlers import journal_handlers, meta  # noqa: F401

    register_behaviors()
    from jarvis.handlers.queues import register_queue_actions

    register_queue_actions()
    from jarvis.handlers import (  # noqa: F401
        aria_coder_handlers,
        knowledge_handlers,
        self_upgrade_handlers,
        skill_handlers,
        workflow_handlers,
    )

    try:
        from jarvis.extensibility.loader import load_extensions

        load_extensions()
    except Exception:
        import logging

        logging.getLogger("jarvis.handlers").exception("Extension load failed")
    _loaded = True


__all__ = ["MediaHandler", "ensure_handlers_loaded"]
