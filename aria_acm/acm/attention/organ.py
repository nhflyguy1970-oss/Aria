"""Attention & Memory Priority organ — M9."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.attention.field import classify_attention, encode_weight
from acm.attention.model import AttentionAllocation, PriorityEvent, PriorityFactor
from acm.types import AttentionClass

if TYPE_CHECKING:
    from acm.core.store import CognitiveStore
    from acm.validation.harness import ValidationHarness


class AttentionOrgan:
    """Answers: What deserves cognitive attention and continued memory investment?"""

    def __init__(self, store: CognitiveStore, validation: ValidationHarness) -> None:
        self.store = store
        self.validation = validation
        self._allocations = 0
        self._investments = 0

    def what_deserves_attention(self, cue: str = "") -> dict[str, Any]:
        """Cognitive question M9."""
        ranked = self._rank_concepts(cue=cue)[:12]
        if not ranked:
            answer = "Nothing currently stands out for special cognitive investment."
        else:
            bits = [f"{c.labels[0]} (priority={c.importance:.2f})" for c, _ in ranked[:5]]
            answer = "Deserves investment: " + "; ".join(bits)
        return {
            "question": "What deserves cognitive attention and continued memory investment?",
            "answer": answer,
            "priorities": [
                {
                    "concept_id": c.id,
                    "label": c.labels[0] if c.labels else c.id,
                    "priority": c.importance,
                    "accessibility": self.store.accessibility.get(c.id, "accessible"),
                    "score": score,
                }
                for c, score in ranked
            ],
        }

    def allocate(
        self,
        text: str,
        *,
        has_open_goal: bool = False,
        context_tags: tuple[str, ...] = (),
        identity_boost: float = 0.0,
    ) -> AttentionAllocation:
        """Compute attention for encode/remember/reflect — evolving, not hard-coded forever."""
        attention = classify_attention(text, has_open_goal=has_open_goal)
        base = encode_weight(attention)
        factors: dict[str, float] = {}
        concept_ids: list[str] = []

        if attention == AttentionClass.USER_PIN:
            factors[PriorityFactor.USER_PIN.value] = 1.0
        if has_open_goal:
            factors[PriorityFactor.GOAL.value] = 0.15
        if identity_boost:
            factors[PriorityFactor.IDENTITY.value] = min(0.2, identity_boost)

        # Living priority pull from matching concepts (experience-evolved importance)
        matches = self.store.find_concepts_by_label(text) if text else []
        priority_pull = 0.0
        repetition = 0.0
        conflict = 0.0
        for concept in matches[:6]:
            concept_ids.append(concept.id)
            priority_pull = max(priority_pull, max(0.0, concept.importance - 0.5) * 0.35)
            if concept.access_count >= 3:
                repetition = max(repetition, min(0.12, 0.03 * concept.access_count))
            contested = any(a.confidence < 0.45 for a in concept.attributes if a.active)
            if contested:
                conflict = 0.08
        if priority_pull:
            factors[PriorityFactor.IMPORTANCE.value] = priority_pull
        if repetition:
            factors[PriorityFactor.REPETITION.value] = repetition
            if attention == AttentionClass.DEFAULT and repetition >= 0.09:
                attention = AttentionClass.FREQUENCY
                base = encode_weight(attention)
        if conflict:
            factors[PriorityFactor.CONFLICT.value] = conflict
        if context_tags:
            factors[PriorityFactor.CONTEXT.value] = 0.04

        boost = sum(factors.values())
        # Cap boost so living investment, not a secret mega-table, dominates
        boost = min(0.35, boost)
        weight = min(1.0, base + boost)
        self._allocations += 1
        allocation = AttentionAllocation(
            attention_class=attention.value,
            weight=weight,
            base_weight=base,
            priority_boost=boost,
            factors=factors,
            concept_ids=concept_ids,
            summary="Allocated attention from class + living priority factors.",
        )
        self.validation.record_attention(
            action="allocate",
            attention_class=allocation.attention_class,
            weight=weight,
            priority_boost=boost,
            allocate=1,
            factors=dict(factors),
        )
        return allocation

    def invest(
        self,
        concept_id: str,
        *,
        delta: float,
        source: str,
        factors: list[str] | tuple[str, ...] = (),
        summary: str = "",
    ) -> PriorityEvent | None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return None
        before = concept.importance
        capped = max(-0.08, min(0.1, delta))
        if concept.identity:
            capped = max(-0.02, min(0.06, capped))
        concept.importance = max(0.05, min(1.0, concept.importance + capped))
        after = concept.importance
        event = PriorityEvent(
            timestamp=time(),
            concept_id=concept_id,
            before=before,
            after=after,
            delta=after - before,
            source=source,
            factors=tuple(factors),
            summary=summary or f"Priority {source}",
        )
        self.store.priority_events.append(event)
        self._investments += 1
        self.validation.record_attention(
            action="invest",
            concept_id=concept_id,
            priority_before=before,
            priority_after=after,
            source=source,
            invest=1,
            priority_evolution=1,
        )
        return event

    def priority_of(self, concept_id: str) -> float:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return 0.0
        return float(concept.importance)

    def replay_candidates(self, *, limit: int = 8) -> list[str]:
        """Offline Cognition uses priority-ranked hot concepts (not hard-coded order)."""
        ranked = self._rank_concepts()[:limit]
        return [c.id for c, _ in ranked]

    def observables(self) -> dict[str, Any]:
        return {
            "allocations": self._allocations,
            "investments": self._investments,
            "priority_events": len(self.store.priority_events),
        }

    def _rank_concepts(self, cue: str = "") -> list[tuple[Any, float]]:
        q = cue.lower().strip()
        scored: list[tuple[Any, float]] = []
        for c in self.store.concepts.values():
            if not c.labels:
                continue
            if c.stage.value == "retired":
                continue
            score = c.importance * 0.55 + min(1.0, c.access_count / 10.0) * 0.25
            score += c.strength * 0.15 + c.confidence * 0.05
            if c.identity:
                score += 0.1
            if q and any(q in lab.lower() or lab.lower() in q for lab in c.labels):
                score += 0.2
            # Accessibility dampens rank for dormant structures
            access = self.store.accessibility.get(c.id)
            if access:
                score *= {
                    "highly_accessible": 1.05,
                    "accessible": 1.0,
                    "less_accessible": 0.75,
                    "dormant": 0.35,
                    "rarely_activated": 0.2,
                    "archived": 0.1,
                    "prune_eligible": 0.05,
                }.get(access, 1.0)
            scored.append((c, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
