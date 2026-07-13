"""Aria Core — Learning public API (Phase 5 Core-owned)."""

from __future__ import annotations

from typing import Any

from aria_core import learning_manager as _mgr
from aria_core.ownership import module_ownership

OWNER = module_ownership("learning")

# Stable Core Learning API
Proposal = _mgr.Proposal
enabled = _mgr.enabled
propose = _mgr.propose
commit = _mgr.commit
propose_learning = _mgr.propose_learning
approve_learning = _mgr.approve_learning
reject_learning = _mgr.reject_learning
commit_learning = _mgr.commit_learning
replay_learning = _mgr.replay_learning
rollback_learning = _mgr.rollback_learning
learning_history = _mgr.learning_history
learning_statistics = _mgr.learning_statistics
recent_audit = _mgr.recent_audit
clear_audit = _mgr.clear_audit
mission_control_panel = _mgr.mission_control_panel


def recent_audit_limit(*, limit: int = 50) -> list[dict[str, Any]]:
    return recent_audit(limit=limit)


__all__ = [
    "OWNER",
    "Proposal",
    "approve_learning",
    "clear_audit",
    "commit",
    "commit_learning",
    "enabled",
    "learning_history",
    "learning_statistics",
    "mission_control_panel",
    "propose",
    "propose_learning",
    "recent_audit",
    "reject_learning",
    "replay_learning",
    "rollback_learning",
]
