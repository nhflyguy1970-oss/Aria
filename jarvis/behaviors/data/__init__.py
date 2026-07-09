"""Data behavior — dataset load, query, chart, export, and SQL."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.data.context import DataContext
from jarvis.behaviors.data.engine import DataActionEngine
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action

_DATA_ACTIONS: dict[str, tuple[Any, bool]] = {
    "data_load": (DataActionEngine.data_load, False),
    "data_query": (DataActionEngine.data_query, False),
    "data_summary": (DataActionEngine.data_summary, True),
    "data_clean": (DataActionEngine.data_clean, False),
    "data_export": (DataActionEngine.data_export, False),
    "data_chart": (DataActionEngine.data_chart, False),
    "data_sql": (DataActionEngine.data_sql, False),
}


@register_behavior
class DataBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="data",
            name="Data",
            category="Data",
            description="Dataset load, query, summary, clean, export, chart, and SQL",
            module_path="jarvis.behaviors.data",
            test_module="tests.test_behaviors",
            action_names=list(_DATA_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: DataContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = DataContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _DATA_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="data",
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
        spec = _DATA_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or DataContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or DataContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
