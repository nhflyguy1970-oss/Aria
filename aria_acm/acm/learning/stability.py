"""Learning stability limits — M5 Cap7 (never invent Experiences)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningStabilityLimits:
    """Hard bounds for long-duration learning stability."""

    min_confidence: float = 0.05
    max_confidence: float = 0.98
    max_adaptations_per_target: int = 48
    max_temporal_patterns: int = 500
    max_abstractions: int = 500
    max_hypotheses: int = 800
    max_prediction_audits: int = 2000
    max_concepts: int = 5000
    max_adaptations_total: int = 8000
    oscillation_epsilon: float = 0.02
    max_oscillation_flips: int = 8
