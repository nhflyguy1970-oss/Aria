"""Briefing behavior — morning briefing assembly and news detail expansion."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.briefing.context import BriefingContext
from jarvis.behaviors.briefing.engine import BriefingEngine
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action

_BRIEFING_ACTIONS: dict[str, tuple[Any, bool]] = {
    "morning_briefing": (BriefingEngine.morning_briefing, True),
    "briefing_news_detail": (BriefingEngine.briefing_news_detail, False),
}


@register_behavior
class BriefingBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="briefing",
            name="Briefing",
            category="Briefing",
            description="Morning briefing assembly, headlines, and news detail expansion",
            module_path="jarvis.behaviors.briefing",
            test_module="tests.test_behaviors",
            action_names=list(_BRIEFING_ACTIONS.keys()),
            dependencies=["journal", "memory", "capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: BriefingContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = BriefingContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _BRIEFING_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="briefing",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        spec = _BRIEFING_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or BriefingContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or BriefingContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
