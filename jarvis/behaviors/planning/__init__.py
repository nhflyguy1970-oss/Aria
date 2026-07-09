"""Planning behavior — planner, reminders, calendar, and scheduling decisions."""

from __future__ import annotations

import os
from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.behaviors.planning.context import PlanningContext
from jarvis.behaviors.planning.engine import PlanningEngine
from jarvis.handlers.registry import register_action

_PLANNING_ACTIONS: dict[str, tuple[Any, bool]] = {
    "planner_add_task": (PlanningEngine.add_task, False),
    "planner_list_tasks": (PlanningEngine.list_tasks, True),
    "planner_set_timer": (PlanningEngine.set_timer, False),
    "planner_set_alarm": (PlanningEngine.set_alarm, False),
    "planner_today": (PlanningEngine.today, True),
    "planner_add_event": (PlanningEngine.add_event, False),
    "journal_schedule": (PlanningEngine.journal_schedule, False),
    "journal_thread": (PlanningEngine.journal_thread, False),
}

_PLANNING_DEPENDENCIES = ["automation_event", "journal", "capability_registry"]


def ensure_planning_engine(orchestrator: Any) -> PlanningEngine:
    behavior = get_planning_behavior()
    if behavior is not None:
        behavior.initialize(orchestrator)
    return PlanningEngine()


def get_planning_behavior() -> PlanningBehavior | None:
    from jarvis.behaviors import get_behavior

    behavior = get_behavior("planning")
    return behavior if isinstance(behavior, PlanningBehavior) else None


@register_behavior
class PlanningBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="planning",
            name="Planning",
            category="Planning",
            description=(
                "Planner tasks, timers, alarms, calendar events, and scheduling decisions"
            ),
            module_path="jarvis.behaviors.planning",
            test_module="tests.test_behaviors",
            action_names=list(_PLANNING_ACTIONS.keys()),
            dependencies=list(_PLANNING_DEPENDENCIES),
            stability="stable",
            owner="application",
        )
        self._context: PlanningContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = PlanningContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _PLANNING_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="planner" if action.startswith("planner_") else "journal",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def validate(self) -> list[str]:
        checks = {
            "automation_event": "JARVIS_PLATFORM_AUTOMATION_EVENT_ATTACHED",
            "journal": "JARVIS_PLATFORM_MEMORY_ATTACHED",
            "capability_registry": "JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED",
        }
        warnings: list[str] = []
        for dep in self.dependencies:
            env_key = checks.get(dep)
            if env_key and os.getenv(env_key) != "1":
                warnings.append(f"dependency not attached: {dep}")
        return warnings

    def prepare_context(
        self,
        orchestrator: Any,
        message: str,
        *,
        skip_project_context: bool = False,
        **kwargs: Any,
    ) -> tuple[list[str], list[dict]]:
        self.initialize(orchestrator)
        ctx = self._context or PlanningContext.from_orchestrator(orchestrator)
        return PlanningEngine.prepare_context(
            ctx, message, skip_project_context=skip_project_context
        )

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        spec = _PLANNING_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or PlanningContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def health(self) -> dict[str, Any]:
        report = super().health()
        report["validation_warnings"] = self.validate()
        report["planning_context"] = PlanningEngine.planning_context()
        report["stability"] = self.stability
        report["owner"] = self.owner
        return report

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or PlanningContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
