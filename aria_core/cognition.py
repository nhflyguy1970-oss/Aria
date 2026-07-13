"""Aria Core — Cognition public API (Phase 6 Cognitive Orchestrator)."""

from __future__ import annotations

from aria_core.cognitive_orchestrator import (
    COGNITION_VERSION,
    COGNITIVE_ORGANS,
    VERB_POLICY,
    cognition_statistics,
    mission_control_panel,
    participation_for,
    recent_pipelines,
    run,
)
from aria_core.ownership import module_ownership

OWNER = module_ownership("cognition")

orchestrate = run

__all__ = [
    "COGNITION_VERSION",
    "COGNITIVE_ORGANS",
    "OWNER",
    "VERB_POLICY",
    "cognition_statistics",
    "mission_control_panel",
    "orchestrate",
    "participation_for",
    "recent_pipelines",
    "run",
]
