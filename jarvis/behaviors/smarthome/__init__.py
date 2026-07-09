"""Smart home behavior — Home Assistant status, control, scenes, and setup."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.behaviors.smarthome.context import SmartHomeContext
from jarvis.behaviors.smarthome.engine import SmartHomeEngine
from jarvis.handlers.registry import register_action

_SMARTHOME_ACTIONS: dict[str, tuple[Any, bool]] = {
    "ha_status": (SmartHomeEngine.ha_status, True),
    "ha_control": (SmartHomeEngine.ha_control, False),
    "ha_scene": (SmartHomeEngine.ha_scene, False),
    "ha_query": (SmartHomeEngine.ha_query, False),
    "ha_set_token": (SmartHomeEngine.ha_set_token, False),
}


@register_behavior
class SmartHomeBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="smarthome",
            name="Smart Home",
            category="Automation",
            description="Home Assistant status, entity control, scenes, and token setup",
            module_path="jarvis.behaviors.smarthome",
            test_module="tests.test_behaviors",
            action_names=list(_SMARTHOME_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: SmartHomeContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = SmartHomeContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _SMARTHOME_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="automation",
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
        spec = _SMARTHOME_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or SmartHomeContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or SmartHomeContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
