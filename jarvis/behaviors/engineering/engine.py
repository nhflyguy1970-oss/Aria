"""Engineering engine — coding, git, LSP, and refactor operations."""

from __future__ import annotations

from jarvis.behaviors.engineering._extracted import EngineeringOperations
from jarvis.response import ok


class EngineeringEngine(EngineeringOperations):
    """Isolated engineering domain logic."""

    @classmethod
    def git_status(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import git_util

        return ok(f"```\n{git_util.status()}\n```", module="coding")

    @classmethod
    def git_diff(cls, ctx, params: dict, message: str) -> dict:
        from jarvis import git_util

        file_name = params.get("file", "")
        diff = git_util.diff(file=file_name or None)
        return ok(f"```diff\n{diff[:8000]}\n```", module="coding")
