"""Git read-only behavior — repository status and diff queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.behaviors import register_behavior
from jarvis.handlers.registry import register_action
from jarvis.response import ok

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant


@register_behavior
class GitBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="git",
            name="Git",
            category="Coding",
            description="Read-only git repository status and diff queries",
            module_path="jarvis.behaviors.git",
            test_module="tests.test_extensions",
            action_names=["git_status", "git_diff"],
        )

    def attach(self) -> list[str]:
        register_action("git_status", module="coding", description="Git working tree status")(
            self.git_status
        )
        register_action("git_diff", module="coding", description="Git diff for file or repo")(
            self.git_diff
        )
        return []

    def execute(
        self,
        assistant: JarvisAssistant,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        if action == "git_status":
            return self.git_status(assistant, params, message)
        if action == "git_diff":
            return self.git_diff(assistant, params, message)
        return None

    @staticmethod
    def git_status(assistant, params: dict, message: str) -> dict:
        from jarvis import git_util

        return ok(f"```\n{git_util.status()}\n```", module="coding")

    @staticmethod
    def git_diff(assistant, params: dict, message: str) -> dict:
        from jarvis import git_util

        file_name = params.get("file", "")
        diff = git_util.diff(file=file_name or None)
        return ok(f"```diff\n{diff[:8000]}\n```", module="coding")
