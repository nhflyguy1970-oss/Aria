"""Git status / diff handlers."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import ok


@register_action("git_status", module="coding", description="Git working tree status")
def git_status(assistant, params: dict, message: str) -> dict:
    from jarvis import git_util

    return ok(f"```\n{git_util.status()}\n```", module="coding")


@register_action("git_diff", module="coding", description="Git diff for file or repo")
def git_diff(assistant, params: dict, message: str) -> dict:
    from jarvis import git_util

    f = params.get("file", "")
    d = git_util.diff(file=f or None)
    return ok(f"```diff\n{d[:8000]}\n```", module="coding")
