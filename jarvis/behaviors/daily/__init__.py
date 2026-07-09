"""Daily workflow behavior — proactive answers for Jeff's day."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action
from jarvis.workflows import daily as daily_workflow

_DAILY_ACTIONS = {
    "what_am_i_working_on": "what_am_i_working_on",
    "what_changed_since_yesterday": "what_changed_since_yesterday",
    "anything_broken": "anything_broken",
    "repos_need_attention": "repos_need_attention",
    "overnight_summary": "overnight_summary",
    "what_should_i_work_on_next": "what_should_i_work_on_next",
    "review_current_branch": "review_current_branch",
    "today_recommendations": "today_recommendations",
    "daily_status": "today_recommendations",
}


def _run(intent: str, assistant: Any) -> dict:
    return daily_workflow.dispatch(intent, assistant)


@register_behavior
class DailyWorkflowBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="daily",
            name="Daily Workflow",
            category="Workflow",
            description="Proactive daily answers — status, changes, recommendations",
            module_path="jarvis.behaviors.daily",
            action_names=list(_DAILY_ACTIONS.keys()),
            dependencies=[],
            stability="stable",
            owner="application",
            version="1.0.0",
        )

    def attach(self) -> list[str]:
        for action, intent in _DAILY_ACTIONS.items():
            register_action(
                action,
                info=True,
                module="daily",
                description=intent.replace("_", " "),
            )(self._bind(intent))
        return []

    def execute(self, orchestrator: Any, action: str, params: dict, message: str) -> dict | None:
        intent = _DAILY_ACTIONS.get(action)
        if intent is None:
            return None
        return _run(intent, orchestrator)

    def _bind(self, intent: str):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            return _run(intent, orchestrator)

        return _entry
