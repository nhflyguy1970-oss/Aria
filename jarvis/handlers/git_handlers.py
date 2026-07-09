"""Git status / diff handlers — re-exported from extracted Git behavior."""

from jarvis.behaviors.git import GitBehavior

_git = GitBehavior()
git_status = _git.git_status
git_diff = _git.git_diff

__all__ = ["git_status", "git_diff"]
