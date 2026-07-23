"""Accessibility & Forgetting organ — M10. Never deletes Experiences."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.associations.model import AssociationStage
from acm.concepts.model import ConceptStage
from acm.forgetting.model import (
    ACCESSIBILITY_FACTOR,
    AccessibilityEvent,
    AccessibilityLevel,
    next_cooler,
    next_warmer,
)

if TYPE_CHECKING:
    from acm.attention.organ import AttentionOrgan
    from acm.core.store import CognitiveStore
    from acm.validation.harness import ValidationHarness


class ForgettingOrgan:
    """Answers: What should become harder to remember?"""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        attention: AttentionOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.attention = attention
        self._cools = 0
        self._reactivations = 0

    def bind(self, *, attention: AttentionOrgan | None = None) -> None:
        if attention is not None:
            self.attention = attention

    def what_should_be_harder_to_remember(self, cue: str = "") -> dict[str, Any]:
        """Cognitive question M10."""
        items: list[dict[str, Any]] = []
        for cid, level in self.store.accessibility.items():
            concept = self.store.concepts.get(cid)
            if concept is None:
                continue
            if level in (
                AccessibilityLevel.ACCESSIBLE.value,
                AccessibilityLevel.HIGHLY_ACCESSIBLE.value,
            ):
                continue
            if cue and cue.lower() not in " ".join(concept.labels).lower():
                continue
            items.append(
                {
                    "concept_id": cid,
                    "label": concept.labels[0] if concept.labels else cid,
                    "accessibility": level,
                    "priority": concept.importance,
                }
            )
        items.sort(key=lambda x: ACCESSIBILITY_FACTOR.get(
            AccessibilityLevel(x["accessibility"]), 1.0
        ))
        if not items:
            answer = "No structures are currently marked harder to remember."
        else:
            bits = [f"{i['label']} ({i['accessibility']})" for i in items[:5]]
            answer = "Harder to remember: " + "; ".join(bits)
        return {
            "question": "What should become harder to remember?",
            "answer": answer,
            "less_accessible": items[:20],
        }

    def ensure(self, concept_id: str) -> AccessibilityLevel:
        raw = self.store.accessibility.get(concept_id)
        if raw:
            try:
                return AccessibilityLevel(raw)
            except ValueError:
                pass
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            level = AccessibilityLevel.ACCESSIBLE
        elif concept.identity:
            level = AccessibilityLevel.HIGHLY_ACCESSIBLE
        elif concept.stage == ConceptStage.DORMANT:
            level = AccessibilityLevel.DORMANT
        elif concept.importance >= 0.75 or concept.access_count >= 5:
            level = AccessibilityLevel.HIGHLY_ACCESSIBLE
        else:
            level = AccessibilityLevel.ACCESSIBLE
        from acm.authority.mode import is_read_only

        # Diagnostic mode may compute accessibility for activation without
        # materializing new accessibility map entries (B07).
        if not is_read_only():
            self.store.accessibility[concept_id] = level.value
        return level

    def factor(self, concept_id: str) -> float:
        return ACCESSIBILITY_FACTOR[self.ensure(concept_id)]

    def cool(
        self,
        concept_id: str,
        *,
        source: str = "forgetting",
        steps: int = 1,
        force: bool = False,
    ) -> AccessibilityEvent | None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return None
        if concept.identity:
            return None  # identity accessibility is assent-tier; never silent cool
        level = self.ensure(concept_id)
        # High priority resists ambient cool (host force still allowed)
        priority = concept.importance
        if not force and priority >= 0.85 and level in (
            AccessibilityLevel.HIGHLY_ACCESSIBLE,
            AccessibilityLevel.ACCESSIBLE,
        ):
            self.validation.record_forgetting(
                action="cool_resisted",
                concept_id=concept_id,
                priority=priority,
                resist=1,
            )
            return None
        before = level
        after = level
        for _ in range(max(1, steps)):
            after = next_cooler(after)
        self.store.accessibility[concept_id] = after.value
        self._apply_concept_stage(concept_id, after)
        event = self._record(concept_id, "concept", before, after, source, "Cool accessibility")
        self._cools += 1
        self.validation.record_forgetting(
            action="cool",
            concept_id=concept_id,
            before=before.value,
            after=after.value,
            cool=1,
            accessibility_evolution=1,
            source=source,
        )
        return event

    def reactivate(
        self,
        concept_id: str,
        *,
        source: str = "cue",
        steps: int = 1,
    ) -> AccessibilityEvent | None:
        from acm.authority.mode import is_read_only

        if is_read_only():
            return None
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return None
        before = self.ensure(concept_id)
        after = before
        for _ in range(max(1, steps)):
            after = next_warmer(after)
        # Strong recovery bump when coming from dormant+
        if before in (
            AccessibilityLevel.DORMANT,
            AccessibilityLevel.RARELY_ACTIVATED,
            AccessibilityLevel.ARCHIVED,
        ):
            after = next_warmer(after)
        self.store.accessibility[concept_id] = after.value
        self._apply_concept_stage(concept_id, after)
        if concept.stage == ConceptStage.DORMANT and after in (
            AccessibilityLevel.ACCESSIBLE,
            AccessibilityLevel.HIGHLY_ACCESSIBLE,
            AccessibilityLevel.LESS_ACCESSIBLE,
        ):
            concept.stage = (
                ConceptStage.STABLE if concept.strength >= 0.4 else ConceptStage.GROWING
            )
            concept.active = True
        event = self._record(
            concept_id, "concept", before, after, source, "Reactivate accessibility"
        )
        self._reactivations += 1
        self.validation.record_forgetting(
            action="reactivate",
            concept_id=concept_id,
            before=before.value,
            after=after.value,
            reactivate=1,
            accessibility_evolution=1,
            source=source,
        )
        if self.attention is not None:
            self.attention.invest(
                concept_id,
                delta=0.04,
                source="reactivation",
                factors=["salience", "cue"],
                summary="Reactivation invited priority investment.",
            )
        return event

    def cool_weak_associations(self, *, threshold: float = 0.12) -> list[str]:
        """Called by Offline Cognition — Forgetting owns the cool application."""
        cooled: list[str] = []
        for edge in list(self.store.associations.values()):
            if not edge.active:
                continue
            if max(edge.strength_forward, edge.strength_backward) < threshold:
                edge.stage = AssociationStage.DORMANT
                self.store.accessibility[f"asc:{edge.id}"] = AccessibilityLevel.DORMANT.value
                cooled.append(edge.id)
                self._cools += 1
                self.validation.record_forgetting(
                    action="cool_association",
                    association_id=edge.id,
                    cool=1,
                    dormancy=1,
                    source="offline_request",
                )
                self.store.accessibility_events.append(
                    AccessibilityEvent(
                        timestamp=time(),
                        target_kind="association",
                        target_id=edge.id,
                        before=AccessibilityLevel.ACCESSIBLE.value,
                        after=AccessibilityLevel.DORMANT.value,
                        source="offline_request",
                        summary="Weak association cooled to dormant.",
                    )
                )
        return cooled

    def neglect_pass(self, *, max_items: int = 12) -> list[str]:
        """Cool neglected non-identity concepts (long-running evolution)."""
        now = time()
        candidates = []
        for c in self.store.concepts.values():
            if c.identity or not c.labels:
                continue
            if c.stage == ConceptStage.RETIRED:
                continue
            idle = now - (c.last_activated or c.first_seen or now)
            if idle < 1.0 and c.access_count > 0:
                # In-process tests: also cool very low strength with no access
                continue
            level = self.ensure(c.id)
            if level in (AccessibilityLevel.PRUNE_ELIGIBLE, AccessibilityLevel.ARCHIVED):
                continue
            # Prefer low priority + low access
            score = (1.0 - c.importance) * 0.6 + (1.0 / (1 + c.access_count)) * 0.4
            candidates.append((score, c.id))
        candidates.sort(reverse=True)
        cooled: list[str] = []
        for _, cid in candidates[:max_items]:
            # Cool low-strength / low-access first
            c = self.store.concepts[cid]
            if c.access_count <= 1 and c.strength < 0.45:
                ev = self.cool(cid, source="neglect")
                if ev:
                    cooled.append(cid)
        return cooled

    def mark_prune_eligible(self, concept_id: str) -> dict[str, Any]:
        """Proposal only — never deletes."""
        level = self.ensure(concept_id)
        if level not in (AccessibilityLevel.ARCHIVED, AccessibilityLevel.RARELY_ACTIVATED):
            return {"status": "not_archived", "accessibility": level.value}
        before = level
        after = AccessibilityLevel.PRUNE_ELIGIBLE
        self.store.accessibility[concept_id] = after.value
        self._record(
            concept_id,
            "concept",
            before,
            after,
            "proposal",
            "Eligible for user-approved pruning (not deleted).",
        )
        self.validation.record_forgetting(
            action="prune_eligible",
            concept_id=concept_id,
            proposal=1,
            after=after.value,
        )
        return {"status": "proposed", "accessibility": after.value, "deleted": False}

    def observables(self) -> dict[str, Any]:
        levels: dict[str, int] = {}
        for v in self.store.accessibility.values():
            levels[v] = levels.get(v, 0) + 1
        return {
            "cools": self._cools,
            "reactivations": self._reactivations,
            "tracked": len(self.store.accessibility),
            "levels": levels,
            "events": len(self.store.accessibility_events),
        }

    def _apply_concept_stage(self, concept_id: str, level: AccessibilityLevel) -> None:
        concept = self.store.concepts.get(concept_id)
        if concept is None or concept.identity:
            return
        if level in (
            AccessibilityLevel.DORMANT,
            AccessibilityLevel.RARELY_ACTIVATED,
            AccessibilityLevel.ARCHIVED,
            AccessibilityLevel.PRUNE_ELIGIBLE,
        ):
            if concept.stage != ConceptStage.RETIRED:
                concept.stage = ConceptStage.DORMANT
                concept.active = False
        elif level in (
            AccessibilityLevel.HIGHLY_ACCESSIBLE,
            AccessibilityLevel.ACCESSIBLE,
            AccessibilityLevel.LESS_ACCESSIBLE,
        ):
            if concept.stage == ConceptStage.DORMANT:
                concept.stage = (
                    ConceptStage.STABLE if concept.strength >= 0.4 else ConceptStage.GROWING
                )
                concept.active = True

    def _record(
        self,
        target_id: str,
        kind: str,
        before: AccessibilityLevel,
        after: AccessibilityLevel,
        source: str,
        summary: str,
    ) -> AccessibilityEvent:
        event = AccessibilityEvent(
            timestamp=time(),
            target_kind=kind,
            target_id=target_id,
            before=before.value,
            after=after.value,
            source=source,
            summary=summary,
        )
        self.store.accessibility_events.append(event)
        return event
