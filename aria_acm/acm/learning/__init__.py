"""Learning organ — durable adaptation."""

from acm.learning.model import (
    Adaptation,
    AdaptationKind,
    AdaptationTarget,
    GovernanceClass,
)
from acm.learning.organ import LearningOrgan
from acm.learning.temporal_pattern import PatternKind, PatternStatus, TemporalPattern

__all__ = [
    "Adaptation",
    "AdaptationKind",
    "AdaptationTarget",
    "GovernanceClass",
    "LearningOrgan",
    "PatternKind",
    "PatternStatus",
    "TemporalPattern",
]
