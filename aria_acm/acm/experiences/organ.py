"""Experience organ — answers: What happened?"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import TYPE_CHECKING, Any

from acm.experiences.kinds import (
    CognitiveKind,
    ExternalKind,
    classify_cognitive_kind,
    normalize_external_kind,
)
from acm.experiences.model import Experience, ExperienceLifecycle, TemporalLink, TemporalRelation
from acm.experiences.salience import SalienceOverlay, SalienceVector
from acm.types import EnvelopeRef, new_id

if TYPE_CHECKING:
    from acm.core.store import CognitiveStore
    from acm.validation.harness import ValidationHarness


@dataclass
class ExperienceRuntimeState:
    """Mutable circulation / relevance — never mutates the Experience record."""

    lifecycle: ExperienceLifecycle = ExperienceLifecycle.ACTIVE
    salience: SalienceOverlay = field(default_factory=lambda: SalienceOverlay(
        current=SalienceVector(), last_touched=time()
    ))


class ExperienceOrgan:
    """Immutable cognitive events, runtime overlays, and temporal links."""

    def __init__(self, store: CognitiveStore, validation: ValidationHarness) -> None:
        self.store = store
        self.validation = validation
        self._sequence = 0
        self._state: dict[str, ExperienceRuntimeState] = {}
        self.links: dict[str, TemporalLink] = {}
        self._summary_counts: dict[str, int] = {}

    def birth(
        self,
        summary: str,
        *,
        external_kind: str | ExternalKind = ExternalKind.TEXT,
        encode_kind: str = "experience",
        attention_class: str = "default",
        attention_weight: float = 0.5,
        context_tags: tuple[str, ...] = (),
        goal_ids: tuple[str, ...] = (),
        envelope_ids: tuple[str, ...] = (),
        concept_ids: tuple[str, ...] = (),
        t_start: float | None = None,
        t_end: float | None = None,
        revises_id: str | None = None,
        reflects_on_id: str | None = None,
        parent_id: str | None = None,
        identity_influenced: bool = False,
        cognitive_kind: CognitiveKind | None = None,
        goal_completed: bool = False,
        metadata: dict[str, str] | None = None,
        salience: SalienceVector | None = None,
    ) -> Experience:
        now = time()
        start = t_start if t_start is not None else now
        text = (summary or "").strip()
        if not text:
            raise ValueError("experience summary required")

        kind_c = cognitive_kind or classify_cognitive_kind(
            text,
            encode_kind=encode_kind,
            revises_id=revises_id,
            reflects_on_id=reflects_on_id,
            goal_completed=goal_completed,
        )
        fp = text.lower()
        prior_count = self._summary_counts.get(fp, 0)
        self._summary_counts[fp] = prior_count + 1

        if salience is None:
            salience = self._compute_birth_salience(
                attention_weight=attention_weight,
                goal_ids=goal_ids,
                context_tags=context_tags,
                identity_influenced=identity_influenced,
                cognitive_kind=kind_c,
                prior_count=prior_count,
            )

        self._sequence += 1
        exp = Experience(
            id=new_id("exp"),
            summary=text,
            sequence=self._sequence,
            t_start=start,
            t_end=t_end,
            t_encoded=now,
            external_kind=normalize_external_kind(external_kind),
            cognitive_kind=kind_c,
            salience_birth=salience.clamp(),
            context_tags=tuple(context_tags),
            goal_ids=tuple(goal_ids),
            envelope_ids=tuple(envelope_ids),
            concept_ids=tuple(concept_ids),
            parent_id=parent_id,
            revises_id=revises_id,
            reflects_on_id=reflects_on_id,
            identity_influenced=identity_influenced,
            attention_class=attention_class,
            metadata=tuple(sorted((metadata or {}).items())),
        )
        self.store.experiences[exp.id] = exp
        self._state[exp.id] = ExperienceRuntimeState(
            lifecycle=ExperienceLifecycle.ACTIVE,
            salience=SalienceOverlay(current=exp.salience_birth, last_touched=now),
        )

        if revises_id and revises_id in self.store.experiences:
            self.link(exp.id, revises_id, TemporalRelation.REVISES)
            self._set_lifecycle(revises_id, ExperienceLifecycle.DORMANT, reason="revised")
        if reflects_on_id and reflects_on_id in self.store.experiences:
            self.link(exp.id, reflects_on_id, TemporalRelation.REFLECTS_ON)
        if parent_id and parent_id in self.store.experiences:
            self.link(exp.id, parent_id, TemporalRelation.PART_OF_EPISODE, weight=0.7)

        prev = self._previous_experience(excluding=exp.id)
        if prev is not None and abs(exp.t_start - prev.t_start) < 300:
            self.link(exp.id, prev.id, TemporalRelation.NEAR, weight=0.5)
            if abs(exp.t_start - prev.t_start) < 1.0:
                self.link(exp.id, prev.id, TemporalRelation.CONCURRENT, weight=0.8)

        self.validation.record_experience(
            action="birth",
            experience_id=exp.id,
            cognitive_kind=exp.cognitive_kind.value,
            external_kind=exp.external_kind.value,
            sequence=exp.sequence,
            salience=exp.salience_birth.composite(),
            lifecycle=ExperienceLifecycle.ACTIVE.value,
            revises_id=revises_id or "",
            identity_influenced=identity_influenced,
            goal_count=len(goal_ids),
            context_tags=list(context_tags),
            lineage=bool(revises_id or reflects_on_id or parent_id),
        )
        return exp

    def revise(self, revises_id: str, summary: str, **kwargs: Any) -> Experience:
        if revises_id not in self.store.experiences:
            raise KeyError(f"unknown experience: {revises_id}")
        kwargs.pop("revises_id", None)
        return self.birth(summary, revises_id=revises_id, encode_kind="experience", **kwargs)

    def reflect(self, reflects_on_id: str, summary: str, **kwargs: Any) -> Experience:
        if reflects_on_id not in self.store.experiences:
            raise KeyError(f"unknown experience: {reflects_on_id}")
        kwargs.pop("reflects_on_id", None)
        return self.birth(
            summary,
            reflects_on_id=reflects_on_id,
            encode_kind="experience",
            cognitive_kind=CognitiveKind.REFLECTION,
            **kwargs,
        )

    def attach_envelope(
        self,
        *,
        content_hash: str,
        kind: str,
        mime: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        env = EnvelopeRef(
            content_hash=content_hash,
            kind=kind,
            mime=mime,
            metadata=metadata or {},
        )
        eid = new_id("env")
        self.store.envelopes[eid] = env
        self.validation.record_experience(
            action="envelope",
            envelope_id=eid,
            external_kind=normalize_external_kind(kind).value,
            multimodal=1,
        )
        return eid

    def lifecycle_of(self, experience_id: str) -> ExperienceLifecycle:
        state = self._state.get(experience_id)
        return state.lifecycle if state else ExperienceLifecycle.ACTIVE

    def current_salience(self, experience_id: str) -> SalienceVector | None:
        state = self._state.get(experience_id)
        if state is None:
            return None
        state.salience.decay_recency()
        return state.salience.current

    def touch(self, experience_id: str, *, boost: float = 0.05) -> SalienceVector | None:
        state = self._state.get(experience_id)
        if state is None:
            return None
        before = state.salience.current.composite()
        current = state.salience.touch(boost=boost)
        self.validation.record_experience(
            action="salience_evolution",
            experience_id=experience_id,
            salience_before=before,
            salience_after=current.composite(),
            salience=current.composite(),
        )
        if current.composite() < 0.12:
            self._set_lifecycle(experience_id, ExperienceLifecycle.DORMANT, reason="low_salience")
        return current

    def retire(self, experience_id: str) -> bool:
        return self._set_lifecycle(experience_id, ExperienceLifecycle.RETIRED, reason="retire")

    def awaken(self, experience_id: str) -> bool:
        return self._set_lifecycle(experience_id, ExperienceLifecycle.ACTIVE, reason="awaken")

    def link(
        self,
        source_id: str,
        target_id: str,
        relation: TemporalRelation | str,
        *,
        weight: float = 1.0,
    ) -> TemporalLink:
        rel = (
            relation
            if isinstance(relation, TemporalRelation)
            else TemporalRelation(str(relation))
        )
        link = TemporalLink(
            id=new_id("tlink"),
            source_id=source_id,
            target_id=target_id,
            relation=rel,
            weight=weight,
        )
        self.links[link.id] = link
        self.validation.record_experience(
            action="temporal_link",
            link_id=link.id,
            source_id=source_id,
            target_id=target_id,
            relation=rel.value,
            temporal=1,
        )
        return link

    def lineage_chain(self, experience_id: str) -> list[str]:
        chain: list[str] = []
        seen: set[str] = set()
        cur: str | None = experience_id
        while cur and cur not in seen:
            seen.add(cur)
            chain.append(cur)
            exp = self.store.experiences.get(cur)
            if exp is None:
                break
            cur = exp.revises_id or exp.reflects_on_id or exp.parent_id
        chain.reverse()
        return chain

    def public_view(self, exp: Experience) -> dict[str, Any]:
        state = self._state.get(exp.id)
        lifecycle = state.lifecycle.value if state else ExperienceLifecycle.ACTIVE.value
        cur = self.current_salience(exp.id)
        return exp.to_public(
            lifecycle=lifecycle,
            salience_current=cur.to_dict() if cur else None,
        )

    def what_happened(
        self,
        *,
        limit: int = 20,
        cognitive_kind: str | None = None,
        include_dormant: bool = False,
        since: float | None = None,
        until: float | None = None,
    ) -> list[dict[str, Any]]:
        items = sorted(self.store.experiences.values(), key=lambda e: (e.t_start, e.sequence))
        out: list[dict[str, Any]] = []
        for exp in items:
            life = self.lifecycle_of(exp.id)
            if not include_dormant and life != ExperienceLifecycle.ACTIVE:
                continue
            if cognitive_kind and exp.cognitive_kind.value != cognitive_kind:
                continue
            if since is not None and exp.t_start < since:
                continue
            if until is not None and exp.t_start > until:
                continue
            out.append(self.public_view(exp))
        return out[-limit:]

    def timeline(self, *, limit: int = 50) -> dict[str, Any]:
        events = self.what_happened(limit=limit, include_dormant=True)
        return {
            "question": "What happened?",
            "count": len(events),
            "events": events,
            "links": [lnk.to_public() for lnk in list(self.links.values())[-100:]],
            "observables": self.observables(),
        }

    def observables(self) -> dict[str, Any]:
        by_kind: dict[str, int] = {}
        by_life: dict[str, int] = {}
        for exp in self.store.experiences.values():
            by_kind[exp.cognitive_kind.value] = by_kind.get(exp.cognitive_kind.value, 0) + 1
            life = self.lifecycle_of(exp.id).value
            by_life[life] = by_life.get(life, 0) + 1
        return {
            "experience_count": len(self.store.experiences),
            "link_count": len(self.links),
            "envelope_count": len(self.store.envelopes),
            "by_cognitive_kind": by_kind,
            "by_lifecycle": by_life,
            "sequence_high": self._sequence,
        }

    def _compute_birth_salience(
        self,
        *,
        attention_weight: float,
        goal_ids: tuple[str, ...],
        context_tags: tuple[str, ...],
        identity_influenced: bool,
        cognitive_kind: CognitiveKind,
        prior_count: int,
    ) -> SalienceVector:
        novelty = 1.0 if prior_count == 0 else max(0.15, 0.85 / (1 + prior_count))
        unexpected = (
            0.85
            if cognitive_kind == CognitiveKind.UNEXPECTED
            else (0.7 if cognitive_kind == CognitiveKind.CORRECTION else 0.2)
        )
        importance = attention_weight
        if cognitive_kind in (
            CognitiveKind.IDENTITY_CHANGE,
            CognitiveKind.GOAL_COMPLETION,
            CognitiveKind.CORRECTION,
        ):
            importance = max(importance, 0.8)
        if identity_influenced:
            importance = min(1.0, importance + 0.1)
        goal_rel = min(1.0, 0.35 * len(goal_ids) + (0.4 if goal_ids else 0.0))
        context = 0.7 if context_tags else 0.45
        confidence = 0.75 if cognitive_kind != CognitiveKind.QUESTION else 0.45
        return SalienceVector(
            attention=attention_weight,
            novelty=novelty,
            importance=importance,
            goal_relevance=goal_rel,
            confidence=confidence,
            frequency=min(1.0, prior_count / 10.0),
            recency=1.0,
            unexpectedness=unexpected,
            context=context,
        ).clamp()

    def _previous_experience(self, *, excluding: str) -> Experience | None:
        best: Experience | None = None
        for exp in self.store.experiences.values():
            if exp.id == excluding:
                continue
            if best is None or exp.sequence > best.sequence:
                best = exp
        return best

    def _set_lifecycle(
        self, experience_id: str, lifecycle: ExperienceLifecycle, *, reason: str
    ) -> bool:
        state = self._state.get(experience_id)
        if state is None:
            return False
        if state.lifecycle == lifecycle:
            return True
        state.lifecycle = lifecycle
        self.validation.record_experience(
            action="lifecycle",
            experience_id=experience_id,
            lifecycle=lifecycle.value,
            reason=reason,
        )
        return True
