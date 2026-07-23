"""Learning organ — durable adaptation."""

from acm.learning.model import (
    Adaptation,
    AdaptationKind,
    AdaptationTarget,
    GovernanceClass,
)
from acm.learning.organ import LearningOrgan
from acm.learning.stability import LearningStabilityLimits
from acm.learning.temporal_pattern import PatternKind, PatternStatus, TemporalPattern

__all__ = [
    "Adaptation",
    "AdaptationKind",
    "AdaptationTarget",
    "GovernanceClass",
    "LearningOrgan",
    "LearningStabilityLimits",
    "PatternKind",
    "PatternStatus",
    "TemporalPattern",
]
