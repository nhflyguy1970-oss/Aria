"""Multidimensional salience — birth vector frozen; current may evolve."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import time


@dataclass(frozen=True)
class SalienceVector:
    attention: float = 0.5
    novelty: float = 0.5
    importance: float = 0.5
    goal_relevance: float = 0.0
    confidence: float = 0.6
    frequency: float = 0.0
    recency: float = 1.0
    unexpectedness: float = 0.0
    context: float = 0.5

    def clamp(self) -> SalienceVector:
        def c(x: float) -> float:
            return max(0.0, min(1.0, float(x)))

        return SalienceVector(
            attention=c(self.attention),
            novelty=c(self.novelty),
            importance=c(self.importance),
            goal_relevance=c(self.goal_relevance),
            confidence=c(self.confidence),
            frequency=c(self.frequency),
            recency=c(self.recency),
            unexpectedness=c(self.unexpectedness),
            context=c(self.context),
        )

    def composite(self) -> float:
        """Informative scalar — cognition still owns the vector."""
        v = self.clamp()
        return round(
            0.18 * v.attention
            + 0.12 * v.novelty
            + 0.16 * v.importance
            + 0.14 * v.goal_relevance
            + 0.10 * v.confidence
            + 0.06 * v.frequency
            + 0.10 * v.recency
            + 0.08 * v.unexpectedness
            + 0.06 * v.context,
            4,
        )

    def to_dict(self) -> dict[str, float]:
        d = asdict(self.clamp())
        d["composite"] = self.composite()
        return d


@dataclass
class SalienceOverlay:
    """Mutable relevance over time — does not rewrite Experience history."""

    current: SalienceVector
    last_touched: float
    touch_count: int = 0

    def decay_recency(self, now: float | None = None) -> None:
        now = now or time()
        age = max(0.0, now - self.last_touched)
        # Soft half-life ~1 day of idle (process-local approximation)
        factor = 0.5 ** (age / 86400.0) if age else 1.0
        cur = self.current
        self.current = SalienceVector(
            attention=cur.attention,
            novelty=cur.novelty * 0.99,
            importance=cur.importance,
            goal_relevance=cur.goal_relevance,
            confidence=cur.confidence,
            frequency=cur.frequency,
            recency=max(0.05, cur.recency * factor),
            unexpectedness=cur.unexpectedness * 0.995,
            context=cur.context,
        ).clamp()

    def touch(self, *, boost: float = 0.05) -> SalienceVector:
        self.decay_recency()
        cur = self.current
        self.touch_count += 1
        self.last_touched = time()
        self.current = SalienceVector(
            attention=cur.attention,
            novelty=cur.novelty,
            importance=cur.importance,
            goal_relevance=cur.goal_relevance,
            confidence=min(1.0, cur.confidence + boost * 0.25),
            frequency=min(1.0, cur.frequency + boost),
            recency=1.0,
            unexpectedness=cur.unexpectedness,
            context=cur.context,
        ).clamp()
        return self.current
