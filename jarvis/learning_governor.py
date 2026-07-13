"""Learning Governor — compat shim.

Phase 5: Learning is owned by Aria Core (`aria_core.learning_manager`).
This module re-exports the Core Learning Manager so existing jarvis call sites
remain bit-identical without application changes.
"""

from __future__ import annotations

from aria_core.learning_manager import (  # noqa: F401
    Proposal,
    clear_audit,
    clear_history,
    commit,
    enabled,
    learning_history,
    learning_statistics,
    propose,
    recent_audit,
    reset_for_tests,
)

__all__ = [
    "Proposal",
    "clear_audit",
    "clear_history",
    "commit",
    "enabled",
    "learning_history",
    "learning_statistics",
    "propose",
    "recent_audit",
    "reset_for_tests",
]
