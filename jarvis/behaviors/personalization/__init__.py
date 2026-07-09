"""Personalization behavior — learned preferences."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action
from jarvis.personalization.store import format_preferences_markdown, snapshot


_PERSONALIZATION_ACTIONS = {
    "personalization_status": lambda _p, _m: _status(),
    "preferences": lambda _p, _m: _status(),
}


def _status() -> dict:
    data = snapshot()
    return {
        "ok": True,
        "message": format_preferences_markdown(data),
        "data": data,
    }


@register_behavior
class PersonalizationBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="personalization",
            name="Personalization",
            category="System",
            description="Learned workflow preferences — models, tools, projects, repos",
            module_path="jarvis.behaviors.personalization",
            action_names=list(_PERSONALIZATION_ACTIONS.keys()),
            dependencies=[],
            stability="stable",
            owner="application",
            version="1.0.0",
        )

    def attach(self) -> list[str]:
        for action, handler in _PERSONALIZATION_ACTIONS.items():
            register_action(
                action,
                info=True,
                module="personalization",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def execute(self, orchestrator: Any, action: str, params: dict, message: str) -> dict | None:
        handler = _PERSONALIZATION_ACTIONS.get(action)
        if handler is None:
            return None
        return handler(params, message)

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            return handler(params, message)

        return _entry
