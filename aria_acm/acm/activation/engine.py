"""Cognitive Activation Engine — shared by Remembering and future active organs."""

from __future__ import annotations

from collections import deque
from time import time
from typing import TYPE_CHECKING, Any

from acm.activation.model import (
    ActivatedNode,
    ActivationField,
    ActivationSeed,
    ActivationTarget,
    CueClass,
    PropagationStep,
)
from acm.associations.model import AssociationStage

if TYPE_CHECKING:
    from acm.associations.organ import AssociationOrgan
    from acm.attention.organ import AttentionOrgan
    from acm.core.store import CognitiveStore
    from acm.forgetting.organ import ForgettingOrgan
    from acm.identity.organ import IdentityOrgan
    from acm.validation.harness import ValidationHarness
    from acm.working.buffer import WorkingBuffer


class ActivationEngine:
    """Canonical cue → field propagation (D018).

    Parameters are cognitive constants for M5. Structural policy changes later
    require explicit user authorization — continuous Learning may tune strengths
    without rewriting this architecture silently.

    Attention & Accessibility modulate energy; they do not fork this architecture.
    """

    SEED_THRESHOLD = 0.18
    SPREAD_THRESHOLD = 0.08
    DECAY = 0.62
    MAX_HOPS = 3
    MAX_FANOUT = 6
    LATERAL_INHIBITION = 0.12

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        associations: AssociationOrgan | None = None,
        identity: IdentityOrgan | None = None,
        buffer: WorkingBuffer | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.associations = associations
        self.identity = identity
        self.buffer = buffer
        self.attention = attention
        self.forgetting = forgetting

    def bind(
        self,
        *,
        associations: AssociationOrgan | None = None,
        identity: IdentityOrgan | None = None,
        buffer: WorkingBuffer | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        if associations is not None:
            self.associations = associations
        if identity is not None:
            self.identity = identity
        if buffer is not None:
            self.buffer = buffer
        if attention is not None:
            self.attention = attention
        if forgetting is not None:
            self.forgetting = forgetting

    def activate(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] | list[str] = (),
        attention_weight: float = 0.5,
        identity_query: bool = False,
    ) -> ActivationField:
        tags = tuple(context_tags)
        field = ActivationField(cue=cue)
        cue_classes = self._classify_cue(cue, identity_query=identity_query, tags=tags)
        field.cue_classes = list(cue_classes)

        seeds = self._collect_seeds(
            cue,
            tags=tags,
            attention_weight=attention_weight,
            identity_query=identity_query,
            cue_classes=cue_classes,
            field=field,
        )
        field.seeds = seeds

        queue: deque[tuple[str, float, int, str]] = deque()
        for seed in seeds:
            if seed.target_kind != ActivationTarget.CONCEPT:
                continue
            if seed.energy < self.SEED_THRESHOLD:
                continue
            self._credit_concept(field, seed.target_id, seed.energy, depth=0, source="seed")
            queue.append((seed.target_id, seed.energy, 0, "seed"))

        while queue:
            concept_id, energy, depth, _src = queue.popleft()
            if depth >= self.MAX_HOPS:
                field.decayed += 1
                continue
            transmitted = 0
            for assoc, neighbor_id, direction, strength in self._outgoing(concept_id):
                if transmitted >= self.MAX_FANOUT:
                    break
                residual = energy * strength * self.DECAY
                if residual < self.SPREAD_THRESHOLD:
                    field.decayed += 1
                    continue
                field.associations[assoc.id] = max(field.associations.get(assoc.id, 0.0), residual)
                field.steps.append(
                    PropagationStep(
                        from_id=concept_id,
                        to_id=neighbor_id,
                        association_id=assoc.id,
                        relation=assoc.relation.value,
                        energy_in=energy,
                        energy_out=residual,
                        direction=direction,
                    )
                )
                before = field.concepts.get(neighbor_id)
                self._credit_concept(
                    field, neighbor_id, residual, depth=depth + 1, source=concept_id
                )
                after = field.concepts.get(neighbor_id)
                if after is None:
                    continue
                if before is None or after.energy > (before.energy + 1e-9):
                    queue.append((neighbor_id, residual, depth + 1, concept_id))
                transmitted += 1

        self._lateral_inhibition(field)
        self._attach_experiences(field, tags=tags)
        field.max_energy = max((n.energy for n in field.concepts.values()), default=0.0)

        self.validation.record_remembering(
            action="activation",
            cue=cue[:120],
            cue_classes=list(field.cue_classes),
            seed_count=len(field.seeds),
            concept_activations=len(field.concepts),
            association_activations=len(field.associations),
            experience_participants=len(field.experiences),
            propagation_steps=len(field.steps),
            decayed=field.decayed,
            inhibited=field.inhibited,
            goal_influenced=field.goal_influenced,
            identity_influenced=field.identity_influenced,
            context_influenced=field.context_influenced,
            working_influenced=field.working_influenced,
            max_energy=field.max_energy,
        )
        return field

    # --- seeding ----------------------------------------------------------------

    def _collect_seeds(
        self,
        cue: str,
        *,
        tags: tuple[str, ...],
        attention_weight: float,
        identity_query: bool,
        cue_classes: list[str],
        field: ActivationField,
    ) -> list[ActivationSeed]:
        q = cue.lower()
        tokens = [t for t in q.split() if len(t) > 2]
        seeds: list[ActivationSeed] = []
        active_goals = list(self.store.active_goals())
        if active_goals:
            field.goal_influenced = True
        if tags:
            field.context_influenced = True

        wm_ids: set[str] = set()
        if self.buffer is not None:
            wm_ids = {item.ref_id for item in self.buffer.items()}

        for concept in self.store.concepts.values():
            stage = getattr(concept, "stage", None)
            if stage and stage.value == "retired":
                continue
            dormant = not concept.active or (stage and stage.value == "dormant")
            energy = 0.0
            classes: list[str] = []

            blob = " ".join(concept.labels).lower()
            lexical_hit = any(tok in blob for tok in tokens) or (
                len(q) >= 3 and q in blob
            )
            if lexical_hit:
                energy += 0.55
                classes.append(CueClass.LEXICAL.value)

            for attr in concept.attributes:
                if not attr.active:
                    continue
                if attr.value.lower() in q or any(
                    tok in attr.value.lower() or tok in attr.key for tok in tokens
                ):
                    energy += 0.85 * attr.confidence
                    classes.append(CueClass.QUESTION.value)
                ctx_boost = _tag_overlap(tags, attr.context_tags)
                if ctx_boost:
                    energy += 0.35 * ctx_boost
                    classes.append(CueClass.CONTEXT.value)

            # Dormant / inactive only enter via strong cue match (reactivation path)
            if dormant and energy < 0.55:
                continue

            if concept.id in wm_ids and not dormant:
                energy += 0.4
                classes.append(CueClass.WORKING.value)
                field.working_influenced = True

            if active_goals and not dormant:
                for goal in active_goals:
                    gtoks = [t for t in goal.title.lower().split() if len(t) > 2]
                    if any(t in blob for t in gtoks):
                        energy += 0.35 * goal.importance
                        classes.append(CueClass.GOAL.value)
                for edge, other in self.store.neighbors(concept.id):
                    if other.id in {g.id for g in active_goals} or edge.target_id in {
                        g.id for g in active_goals
                    }:
                        energy += 0.3 * edge.weight
                        classes.append(CueClass.GOAL.value)

            if self.identity is not None:
                bonus = self.identity.rank_bonus(concept, query=cue)
                if bonus > 0 and (energy > 0 or identity_query):
                    energy += min(0.5, bonus * 0.15)
                    classes.append(CueClass.IDENTITY.value)
                    field.identity_influenced = True

            if identity_query and concept.identity:
                energy += 0.7
                classes.append(CueClass.IDENTITY.value)
                field.identity_influenced = True

            energy *= 0.45 + 0.55 * attention_weight
            energy *= 0.5 + 0.5 * concept.strength
            # Living priority & accessibility modulate the singular Activation Architecture
            if self.attention is not None:
                energy *= 0.75 + 0.25 * self.attention.priority_of(concept.id)
            access_factor = 1.0
            if self.forgetting is not None:
                access_factor = self.forgetting.factor(concept.id)
            elif concept.id in self.store.accessibility:
                from acm.forgetting.model import ACCESSIBILITY_FACTOR, AccessibilityLevel

                try:
                    access_factor = ACCESSIBILITY_FACTOR[
                        AccessibilityLevel(self.store.accessibility[concept.id])
                    ]
                except ValueError:
                    access_factor = 1.0
            # Strong lexical cues pierce dormancy (reactivation) without a second activation model
            if dormant and lexical_hit:
                access_factor = max(access_factor, 0.85)
            energy *= access_factor

            threshold = self.SEED_THRESHOLD * (1.15 if dormant else 1.0)
            if energy >= threshold:
                seeds.append(
                    ActivationSeed(
                        target_kind=ActivationTarget.CONCEPT,
                        target_id=concept.id,
                        energy=min(1.5, energy),
                        cue_classes=tuple(dict.fromkeys(classes or cue_classes)),
                        label=concept.labels[0] if concept.labels else concept.id,
                    )
                )

        seeds.sort(key=lambda s: s.energy, reverse=True)
        return seeds[:24]

    def _classify_cue(
        self, cue: str, *, identity_query: bool, tags: tuple[str, ...]
    ) -> list[str]:
        classes: list[str] = [CueClass.QUESTION.value]
        if identity_query:
            classes.append(CueClass.IDENTITY.value)
        if tags:
            classes.append(CueClass.CONTEXT.value)
        if self.store.active_goals():
            classes.append(CueClass.GOAL.value)
        if "?" in cue or cue.lower().startswith(("what", "who", "where", "when", "how")):
            classes.append(CueClass.QUESTION.value)
        return list(dict.fromkeys(classes))

    # --- graph walk -------------------------------------------------------------

    def _outgoing(self, concept_id: str) -> list[tuple[Any, str, str, float]]:
        out: list[tuple[Any, str, str, float]] = []
        for assoc in self.store.associations.values():
            if assoc.stage in (AssociationStage.RETIRED, AssociationStage.DORMANT):
                continue
            if assoc.source_id == concept_id:
                strength = assoc.strength_forward * (0.5 + 0.5 * assoc.confidence)
                out.append((assoc, assoc.target_id, "forward", strength))
            elif assoc.target_id == concept_id:
                strength = assoc.strength_backward * (0.5 + 0.5 * assoc.confidence)
                out.append((assoc, assoc.source_id, "backward", strength))
        out.sort(key=lambda x: x[3], reverse=True)
        return out

    def _credit_concept(
        self,
        field: ActivationField,
        concept_id: str,
        energy: float,
        *,
        depth: int,
        source: str,
    ) -> None:
        concept = self.store.concepts.get(concept_id)
        if concept is None:
            return
        # Allow dormant targets that already seeded (reactivation path)
        if not concept.active and concept_id not in {s.target_id for s in field.seeds}:
            return
        existing = field.concepts.get(concept_id)
        if existing is None:
            field.concepts[concept_id] = ActivatedNode(
                target_kind=ActivationTarget.CONCEPT,
                target_id=concept_id,
                energy=energy,
                confidence=concept.confidence,
                label=concept.labels[0] if concept.labels else concept_id,
                path_depth=depth,
                sources=(source,),
            )
        else:
            # Parallel waves merge with diminishing returns
            merged = existing.energy + energy * (1.0 - min(0.85, existing.energy))
            existing.energy = merged
            existing.path_depth = min(existing.path_depth, depth)
            if source not in existing.sources:
                existing.sources = existing.sources + (source,)

    def _lateral_inhibition(self, field: ActivationField) -> None:
        ranked = field.ranked_concepts(limit=20)
        if len(ranked) < 2:
            return
        top = ranked[0].energy
        for node in ranked[1:]:
            if node.energy < top * self.LATERAL_INHIBITION:
                # drop very weak relatives from reconstruction consideration
                del field.concepts[node.target_id]
                field.inhibited += 1

    def _attach_experiences(self, field: ActivationField, *, tags: tuple[str, ...]) -> None:
        now = time()
        for node in field.ranked_concepts(limit=8):
            concept = self.store.concepts.get(node.target_id)
            if concept is None:
                continue
            for eid in list(concept.evidence_ids)[-8:] + list(concept.exemplar_ids)[-4:]:
                exp = self.store.experiences.get(eid)
                if exp is None:
                    continue
                # Salience / temporal bias — never mutate Experience
                age_bonus = 1.0 / (1.0 + max(0.0, now - exp.t_start) / 86400.0)
                ctx = _tag_overlap(tags, exp.context_tags)
                energy = node.energy * (0.35 + 0.4 * exp.importance + 0.15 * age_bonus + 0.2 * ctx)
                prior = field.experiences.get(eid)
                if prior is None or energy > prior.energy:
                    field.experiences[eid] = ActivatedNode(
                        target_kind=ActivationTarget.EXPERIENCE,
                        target_id=eid,
                        energy=energy,
                        confidence=node.confidence,
                        label=exp.summary[:80],
                        path_depth=node.path_depth + 1,
                        sources=(node.target_id,),
                    )


def _tag_overlap(a: tuple[str, ...] | list[str], b: tuple[str, ...] | list[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = {t.lower() for t in a}, {t.lower() for t in b}
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / max(1, len(sa | sb))
