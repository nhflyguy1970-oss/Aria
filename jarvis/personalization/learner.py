"""Learn preferences from workstation usage."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.personalization.learner")


def learn_from_chat(*, model: str, role: str = "general") -> None:
    try:
        from jarvis.personalization.store import record_model_use

        if model:
            record_model_use(role, model)
    except Exception as exc:
        logger.debug("learn_from_chat: %s", exc)


def learn_from_tool_result(tool_id: str, result: dict[str, Any]) -> None:
    try:
        from jarvis.personalization.store import record_tool_use

        record_tool_use(tool_id, success=bool(result.get("ok")))
    except Exception as exc:
        logger.debug("learn_from_tool: %s", exc)


def learn_from_git_sync(results: list[dict[str, Any]]) -> None:
    try:
        from jarvis.personalization.store import record_repo_use

        for item in results:
            state = item.get("state") or {}
            path = state.get("path") or item.get("repo")
            if path and item.get("ok"):
                record_repo_use(str(path))
    except Exception as exc:
        logger.debug("learn_from_git: %s", exc)


def learn_from_active_project() -> None:
    try:
        from jarvis.active_project import get_active_slug
        from jarvis.personalization.store import record_project_use

        slug = get_active_slug()
        if slug:
            record_project_use(slug)
    except Exception as exc:
        logger.debug("learn_from_project: %s", exc)
