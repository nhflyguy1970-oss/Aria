"""Accessibility & Forgetting models — never deletion."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AccessibilityLevel(StrEnum):
    HIGHLY_ACCESSIBLE = "highly_accessible"
    ACCESSIBLE = "accessible"
    LESS_ACCESSIBLE = "less_accessible"
    DORMANT = "dormant"
    RARELY_ACTIVATED = "rarely_activated"
    ARCHIVED = "archived"
    PRUNE_ELIGIBLE = "prune_eligible"


# Activation energy multipliers — functional accessibility, not anatomy
ACCESSIBILITY_FACTOR: dict[AccessibilityLevel, float] = {
    AccessibilityLevel.HIGHLY_ACCESSIBLE: 1.15,
    AccessibilityLevel.ACCESSIBLE: 1.0,
    AccessibilityLevel.LESS_ACCESSIBLE: 0.65,
    AccessibilityLevel.DORMANT: 0.28,
    AccessibilityLevel.RARELY_ACTIVATED: 0.15,
    AccessibilityLevel.ARCHIVED: 0.06,
    AccessibilityLevel.PRUNE_ELIGIBLE: 0.02,
}

_LEVEL_ORDER = list(AccessibilityLevel)


@dataclass
class AccessibilityEvent:
    timestamp: float
    target_kind: str  # concept | association
    target_id: str
    before: str
    after: str
    source: str
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "before": self.before,
            "after": self.after,
            "source": self.source,
            "summary": self.summary,
        }


def next_cooler(level: AccessibilityLevel) -> AccessibilityLevel:
    idx = _LEVEL_ORDER.index(level)
    return _LEVEL_ORDER[min(len(_LEVEL_ORDER) - 1, idx + 1)]


def next_warmer(level: AccessibilityLevel) -> AccessibilityLevel:
    idx = _LEVEL_ORDER.index(level)
    return _LEVEL_ORDER[max(0, idx - 1)]
