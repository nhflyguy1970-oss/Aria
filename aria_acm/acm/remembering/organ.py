"""Remembering organ — answers: What do I remember?"""

from __future__ import annotations

import re
from time import time
from typing import TYPE_CHECKING, Any

from acm.activation.engine import ActivationEngine
from acm.activation.model import ActivationField
from acm.remembering.model import CompetingRecollection, Reconstruction
from acm.types import ConceptRole, ExplanationClass
from acm.validation.harness import ConfidenceDelta
from acm.working.buffer import BufferItem

if TYPE_CHECKING:
    from acm.associations.organ import AssociationOrgan
    from acm.attention.organ import AttentionOrgan
    from acm.concepts.model import Concept
    from acm.core.store import CognitiveStore
    from acm.forgetting.organ import ForgettingOrgan
    from acm.identity.organ import IdentityOrgan
    from acm.validation.harness import ValidationHarness
    from acm.working.buffer import WorkingBuffer


# Close competitors within this energy ratio → ambiguity (only strong rivals)
COMPETE_RATIO = 0.88


class RememberingOrgan:
    """Cue-driven reconstruction via shared Activation Architecture."""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        activation: ActivationEngine,
        *,
        identity: IdentityOrgan | None = None,
        associations: AssociationOrgan | None = None,
        buffer: WorkingBuffer | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.identity = identity
        self.associations = associations
        self.buffer = buffer
        self.attention = attention
        self.forgetting = forgetting
        self._reconstructions = 0
        self._ambiguous = 0

    def bind(
        self,
        *,
        identity: IdentityOrgan | None = None,
        associations: AssociationOrgan | None = None,
        buffer: WorkingBuffer | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        if identity is not None:
            self.identity = identity
        if associations is not None:
            self.associations = associations
        if buffer is not None:
            self.buffer = buffer
        if attention is not None:
            self.attention = attention
        if forgetting is not None:
            self.forgetting = forgetting
        self.activation.bind(
            associations=self.associations,
            identity=self.identity,
            buffer=self.buffer,
            attention=self.attention,
            forgetting=self.forgetting,
        )

    def what_do_i_remember(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] | list[str] = (),
        attention_weight: float = 0.5,
        attention_class: str = "default",
    ) -> Reconstruction:
        """Cognitive question M5: What do I remember?"""
        tags = tuple(context_tags)
        identity_query = bool(self.identity and self.identity.is_who_query(cue))

        if identity_query and self.identity is not None:
            return self._remember_identity(
                cue,
                context_tags=tags,
                attention_weight=attention_weight,
                attention_class=attention_class,
            )

        field = self.activation.activate(
            cue,
            context_tags=tags,
            attention_weight=attention_weight,
            identity_query=False,
        )
        # Reactivate dormant seeds that made it into the field (strong-cue recovery)
        if self.forgetting is not None:
            for seed in field.seeds:
                concept = self.store.concepts.get(seed.target_id)
                if concept is not None and not concept.active:
                    self.forgetting.reactivate(seed.target_id, source="strong_cue", steps=2)
        ranked = field.ranked_concepts(limit=6)
        reconstruction = self._reconstruct(cue, field, ranked)
        self._reconsolidate(reconstruction, cue)
        displaced = self._enter_working(reconstruction)
        self._observe(
            reconstruction,
            attention_class=attention_class,
            context_tags=tags,
        )
        reconstruction.activation["working_displaced"] = [
            {"ref_id": d.ref_id, "label": d.label} for d in displaced
        ]
        return reconstruction

    # --- identity special path -------------------------------------------------

    def _remember_identity(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] | list[str],
        attention_weight: float,
        attention_class: str,
    ) -> Reconstruction:
        assert self.identity is not None
        who = self.identity.who_am_i()
        field = self.activation.activate(
            cue,
            context_tags=context_tags,
            attention_weight=attention_weight,
            identity_query=True,
        )
        activated = [c["concept_id"] for c in who.get("central_concepts", [])]
        reconstruction = Reconstruction(
            cue=cue,
            answer=who["answer"],
            explanation_class=ExplanationClass.EXPERIENCE.value,
            confidence=float(who["confidence"]),
            primary_concept_id=activated[0] if activated else "",
            primary_label=(
                who["central_concepts"][0]["label"] if who.get("central_concepts") else ""
            ),
            activated_concept_ids=activated or [n.target_id for n in field.ranked_concepts(5)],
            association_ids=list(field.associations.keys())[:12],
            experience_ids=list(field.experiences.keys())[:8],
            experience_summaries=[
                n.label for n in sorted(field.experiences.values(), key=lambda x: -x.energy)[:5]
            ],
            ambiguous=False,
            goal_influenced=field.goal_influenced,
            identity_influenced=True,
            context_influenced=field.context_influenced,
            working_influenced=field.working_influenced,
            activation=field.to_public(),
            cue_classes=list(field.cue_classes),
        )
        self._observe(
            reconstruction,
            attention_class=attention_class,
            context_tags=tuple(context_tags),
        )
        return reconstruction

    # --- reconstruction --------------------------------------------------------

    def _reconstruct(
        self,
        cue: str,
        field: ActivationField,
        ranked: list[Any],
    ) -> Reconstruction:
        if not ranked:
            return Reconstruction(
                cue=cue,
                answer="I don't have anything solid about that yet.",
                explanation_class=ExplanationClass.UNKNOWN.value,
                confidence=0.0,
                activation=field.to_public(),
                cue_classes=list(field.cue_classes),
                goal_influenced=field.goal_influenced,
                identity_influenced=field.identity_influenced,
                context_influenced=field.context_influenced,
                working_influenced=field.working_influenced,
            )

        top = ranked[0]
        concept = self.store.concepts[top.target_id]
        answer, expl, conf = self._format_from_concept(cue, concept, top.energy)

        competing: list[CompetingRecollection] = []
        ambiguous = False
        tokens = [tok for tok in cue.lower().split() if len(tok) > 2]
        for rival in ranked[1:4]:
            if rival.energy < top.energy * COMPETE_RATIO:
                continue
            r_concept = self.store.concepts.get(rival.target_id)
            if r_concept is None:
                continue
            # Only count competitors that also answer the cue (not mere neighborhood bleed)
            if not _cue_relevant(r_concept, tokens):
                continue
            preview, _, rconf = self._format_from_concept(cue, r_concept, rival.energy)
            if preview.strip().lower() == answer.strip().lower():
                continue
            competing.append(
                CompetingRecollection(
                    concept_id=rival.target_id,
                    label=rival.label,
                    energy=rival.energy,
                    confidence=rconf,
                    answer_preview=preview,
                )
            )
        if competing:
            ambiguous = True
            conf = min(conf, 0.55 + 0.2 * max(0.0, top.energy - competing[0].energy))
            self._ambiguous += 1

        # Experience participation (read-only)
        exp_nodes = sorted(field.experiences.values(), key=lambda n: n.energy, reverse=True)[:6]
        # Prefer experiences anchored on top concept
        primary_exps = [n for n in exp_nodes if top.target_id in n.sources] or exp_nodes

        return Reconstruction(
            cue=cue,
            answer=answer,
            explanation_class=expl.value,
            confidence=conf,
            primary_concept_id=concept.id,
            primary_label=concept.labels[0] if concept.labels else concept.id,
            activated_concept_ids=[n.target_id for n in ranked],
            association_ids=list(field.associations.keys())[:16],
            experience_ids=[n.target_id for n in primary_exps],
            experience_summaries=[n.label for n in primary_exps],
            competing=competing,
            ambiguous=ambiguous,
            goal_influenced=field.goal_influenced,
            identity_influenced=field.identity_influenced,
            context_influenced=field.context_influenced,
            working_influenced=field.working_influenced,
            activation=field.to_public(),
            cue_classes=list(field.cue_classes),
        )

    def _format_from_concept(
        self, cue: str, concept: Concept, energy: float
    ) -> tuple[str, ExplanationClass, float]:
        q = cue.lower()
        tokens = [tok for tok in q.split() if len(tok) > 2]
        best_attr = None
        for attr in concept.attributes:
            if not attr.active:
                continue
            if any(tok in attr.key or tok in attr.value.lower() for tok in tokens):
                best_attr = attr
                break
        if best_attr is None:
            active_attrs = [a for a in concept.attributes if a.active]
            best_attr = active_attrs[0] if active_attrs else None
        if best_attr is None:
            return (
                concept.labels[0] if concept.labels else "something related",
                ExplanationClass.EXPERIENCE,
                min(1.0, concept.confidence * (0.5 + 0.5 * min(1.0, energy))),
            )

        conf = min(
            1.0,
            0.55 * best_attr.confidence
            + 0.25 * concept.confidence
            + 0.2 * min(1.0, energy),
        )
        if concept.role == ConceptRole.PREFERENCE or best_attr.key.startswith("favorite_"):
            pretty = best_attr.key.replace("favorite_", "favorite ").replace("_", " ")
            answer = f"Your {pretty} is {best_attr.value}."
            return answer, ExplanationClass.PREFERENCE, conf
        answer = best_attr.value
        if not answer.endswith("."):
            answer += "."
        cls = ExplanationClass.EXPERIENCE
        if conf < 0.55:
            cls = ExplanationClass.STALE
        return answer, cls, conf

    # --- side effects on cognition (not history) -------------------------------

    def _reconsolidate(self, reconstruction: Reconstruction, cue: str) -> None:
        cid = reconstruction.primary_concept_id
        if not cid:
            return
        concept = self.store.concepts.get(cid)
        if concept is None:
            return
        before = concept.confidence
        concept.access_count += 1
        concept.last_activated = time()
        concept.strength = min(1.0, concept.strength + 0.03)
        if re.search(r"\b(actually|instead|correct|update)\b", cue, re.I):
            self.validation.record_reconsolidation(
                concept_id=concept.id, kind="contest_signal", query=cue[:80]
            )
            return
        concept.confidence = min(1.0, concept.confidence + 0.01)
        self.validation.record_confidence(
            ConfidenceDelta(time(), concept.id, "concept", before, concept.confidence, "recall")
        )
        self.validation.record_reconsolidation(
            concept_id=concept.id, kind="light", query=cue[:80]
        )
        # Strengthen associations used in the activation path (accessibility)
        if self.associations is not None:
            for aid in reconstruction.association_ids[:5]:
                self.associations.reinforce(aid, forward_delta=0.015, backward_delta=0.01)
        # Accessibility recovery + priority investment (M9/M10)
        if self.forgetting is not None:
            self.forgetting.reactivate(concept.id, source="remembering", steps=1)
        if self.attention is not None:
            self.attention.invest(
                concept.id,
                delta=0.03,
                source="remembering",
                factors=["repetition", "salience"],
                summary="Successful recall invested priority.",
            )

    def _enter_working(self, reconstruction: Reconstruction) -> list[BufferItem]:
        if self.buffer is None or not reconstruction.primary_concept_id:
            return []
        concept = self.store.concepts.get(reconstruction.primary_concept_id)
        if concept is None:
            return []
        return self.buffer.push(
            BufferItem(
                kind="concept",
                ref_id=concept.id,
                label=concept.labels[0],
                attention=0.7,
                importance=concept.importance,
            )
        )

    def _observe(
        self,
        reconstruction: Reconstruction,
        *,
        attention_class: str,
        context_tags: tuple[str, ...] = (),
    ) -> None:
        self._reconstructions += 1
        self.validation.record_remembering(
            action="reconstruction",
            cue=reconstruction.cue[:120],
            confidence=reconstruction.confidence,
            ambiguous=reconstruction.ambiguous,
            competing=len(reconstruction.competing),
            concept_id=reconstruction.primary_concept_id,
            experience_participants=len(reconstruction.experience_ids),
            association_activations=len(reconstruction.association_ids),
            goal_influenced=reconstruction.goal_influenced,
            identity_influenced=reconstruction.identity_influenced,
            context_influenced=reconstruction.context_influenced,
            working_influenced=reconstruction.working_influenced,
            attention_class=attention_class,
            reconstruction=1,
            ambiguity=1 if reconstruction.ambiguous else 0,
        )
        from acm.validation.harness import ActivationRecord

        self.validation.record_activation(
            ActivationRecord(
                time(),
                reconstruction.cue,
                list(reconstruction.activated_concept_ids),
                [
                    self.store.concepts[c].labels[0]
                    for c in reconstruction.activated_concept_ids
                    if c in self.store.concepts and self.store.concepts[c].labels
                ],
                list(reconstruction.cue_classes) or ["activation", "reconstruction"],
                goal_ids=[g.id for g in self.store.active_goals()],
                attention_class=attention_class,
                context_tags=list(context_tags),
            )
        )

    def observables(self) -> dict[str, Any]:
        return {
            "reconstructions": self._reconstructions,
            "ambiguous": self._ambiguous,
        }

    def explanation_text(self, cls: ExplanationClass | str, confidence: float) -> str:
        if isinstance(cls, str):
            try:
                cls = ExplanationClass(cls)
            except ValueError:
                cls = ExplanationClass.UNKNOWN
        mapping = {
            ExplanationClass.PREFERENCE: (
                "I remembered this because it is one of your preferences."
            ),
            ExplanationClass.EXPERIENCE: (
                "I remembered this from something you shared with me."
            ),
            ExplanationClass.REPEATED: (
                "This strengthened because it has appeared repeatedly."
            ),
            ExplanationClass.STALE: (
                "This information is uncertain because it has not been confirmed strongly."
            ),
            ExplanationClass.CONTESTED: "This is contested; I may need confirmation.",
            ExplanationClass.CONTEXT: "This depends on the current context.",
            ExplanationClass.GOAL: "This came up because of an active goal.",
            ExplanationClass.PROCEDURE: "This is part of a practiced procedure.",
            ExplanationClass.ADOPTED_KNOWLEDGE: (
                "This was adopted into memory from knowledge you accepted."
            ),
            ExplanationClass.UNKNOWN: "I don't have a reliable memory for that yet.",
        }
        text = mapping.get(cls, mapping[ExplanationClass.UNKNOWN])
        if confidence and confidence < 0.55 and cls != ExplanationClass.UNKNOWN:
            text += " Confidence is still developing."
        return text


def _cue_relevant(concept: Concept, tokens: list[str]) -> bool:
    if not tokens:
        return False
    blob = " ".join(concept.labels).lower()
    if any(tok in blob for tok in tokens):
        return True
    for attr in concept.attributes:
        if not attr.active:
            continue
        if any(tok in attr.key or tok in attr.value.lower() for tok in tokens):
            return True
    return False
