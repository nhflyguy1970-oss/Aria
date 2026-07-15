"""Reflection organ — answers: What do I think about what I remember?"""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.experiences.kinds import CognitiveKind
from acm.reflection.model import ReflectionEvaluation, ReflectionOutcome
from acm.working.buffer import BufferItem

if TYPE_CHECKING:
    from acm.core.store import CognitiveStore
    from acm.experiences.organ import ExperienceOrgan
    from acm.remembering.model import Reconstruction
    from acm.remembering.organ import RememberingOrgan
    from acm.validation.harness import ValidationHarness
    from acm.working.buffer import WorkingBuffer


class ReflectionOrgan:
    """Evaluates reconstructions; births Reflective Experiences. Never rewrites history."""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        remembering: RememberingOrgan,
        experiences: ExperienceOrgan,
        *,
        buffer: WorkingBuffer | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.remembering = remembering
        self.experiences = experiences
        self.buffer = buffer
        self._reflections = 0
        self._contradictions = 0
        self._questions = 0
        self._hypotheses = 0
        self._patterns = 0
        self._uncertain = 0

    def bind(
        self,
        *,
        remembering: RememberingOrgan | None = None,
        experiences: ExperienceOrgan | None = None,
        buffer: WorkingBuffer | None = None,
    ) -> None:
        if remembering is not None:
            self.remembering = remembering
        if experiences is not None:
            self.experiences = experiences
        if buffer is not None:
            self.buffer = buffer

    def what_do_i_think(
        self,
        cue: str,
        *,
        context_tags: tuple[str, ...] | list[str] = (),
        attention_weight: float = 0.5,
        attention_class: str = "default",
    ) -> ReflectionEvaluation:
        """Cognitive question M6: What do I think about what I remember?"""
        tags = tuple(context_tags)
        reconstruction = self.remembering.what_do_i_remember(
            cue,
            context_tags=tags,
            attention_weight=attention_weight,
            attention_class=attention_class,
        )
        evaluation = self._evaluate(cue, reconstruction)
        reflective = self._birth_reflective_experience(evaluation, reconstruction)
        evaluation.reflective_experience_id = reflective.id if reflective else ""
        if reflective and reflective.reflects_on_id:
            evaluation.reflects_on_id = reflective.reflects_on_id
        self._enter_working(evaluation)
        self._observe(evaluation, attention_class=attention_class)
        return evaluation

    def evaluate_reconstruction(
        self, reconstruction: Reconstruction, *, cue: str = ""
    ) -> ReflectionEvaluation:
        """Evaluate an existing reconstruction without re-running Remembering."""
        q = cue or reconstruction.cue
        evaluation = self._evaluate(q, reconstruction)
        reflective = self._birth_reflective_experience(evaluation, reconstruction)
        evaluation.reflective_experience_id = reflective.id if reflective else ""
        if reflective and reflective.reflects_on_id:
            evaluation.reflects_on_id = reflective.reflects_on_id
        self._observe(evaluation, attention_class="default")
        return evaluation

    # --- evaluation -----------------------------------------------------------

    def _evaluate(self, cue: str, reconstruction: Reconstruction) -> ReflectionEvaluation:
        outcomes: list[ReflectionOutcome] = []
        contradictions: list[str] = []
        consistencies: list[str] = []
        patterns: list[str] = []
        questions: list[str] = []
        hypotheses: list[str] = []

        conf = float(reconstruction.confidence)
        evidence_n = len(reconstruction.experience_ids)
        assoc_n = len(reconstruction.association_ids)
        unknown = reconstruction.explanation_class == "unknown" or not reconstruction.answer
        insufficient = evidence_n == 0 or conf < 0.35 or unknown
        ambiguous = bool(reconstruction.ambiguous) or bool(reconstruction.competing)

        if unknown or conf <= 0.0:
            outcomes.append(ReflectionOutcome.UNKNOWN)
            outcomes.append(ReflectionOutcome.UNCERTAINTY)
            questions.append(f"What evidence would ground a recollection for '{cue}'?")
            self._uncertain += 1
            self._questions += 1
        elif insufficient:
            outcomes.append(ReflectionOutcome.INSUFFICIENT_EVIDENCE)
            outcomes.append(ReflectionOutcome.UNCERTAINTY)
            questions.append("Do I need more experience before trusting this recollection?")
            self._uncertain += 1
            self._questions += 1
        else:
            outcomes.append(ReflectionOutcome.SUFFICIENT)

        if ambiguous:
            outcomes.append(ReflectionOutcome.CONTRADICTION)
            for rival in reconstruction.competing[:4]:
                contradictions.append(
                    f"Competing recollection: {rival.label} ≈ {rival.answer_preview[:80]}"
                )
            questions.append("Which competing recollection best fits current context and goals?")
            hypotheses.append("Multiple interpretations remain viable until more evidence arrives.")
            self._contradictions += 1
            self._questions += 1
            self._hypotheses += 1
        elif not unknown and conf >= 0.55:
            outcomes.append(ReflectionOutcome.CONSISTENCY)
            consistencies.append("Single dominant reconstruction without near competitors.")

        # Pattern observation from activation neighborhood (not reasoning)
        act = reconstruction.activation or {}
        steps = int(act.get("propagation_steps") or 0)
        concept_hits = act.get("concept_activations") or []
        if steps >= 2 and len(concept_hits) >= 2:
            outcomes.append(ReflectionOutcome.PATTERN)
            labels = [c.get("label", "") for c in concept_hits[:4] if c.get("label")]
            if labels:
                patterns.append("Activation neighborhood: " + ", ".join(labels))
            else:
                patterns.append(
                    f"Activation spread across {len(concept_hits)} concepts "
                    f"({steps} hops)."
                )
            self._patterns += 1

        if assoc_n >= 2 and ReflectionOutcome.PATTERN not in outcomes:
            outcomes.append(ReflectionOutcome.PATTERN)
            patterns.append(f"Related through {assoc_n} associations.")
            self._patterns += 1

        if conf < 0.55 and ReflectionOutcome.UNCERTAINTY not in outcomes:
            outcomes.append(ReflectionOutcome.UNCERTAINTY)
            self._uncertain += 1

        # Confidence assessment — evaluative, not a silent overwrite of Concept confidence
        assessment = conf
        if insufficient:
            assessment = min(assessment, 0.35)
        if ambiguous:
            assessment = min(assessment, 0.5)
        if evidence_n >= 3 and not ambiguous:
            assessment = min(1.0, assessment + 0.05)

        if ReflectionOutcome.QUESTION not in outcomes and questions:
            outcomes.append(ReflectionOutcome.QUESTION)
        if ReflectionOutcome.HYPOTHESIS not in outcomes and hypotheses:
            outcomes.append(ReflectionOutcome.HYPOTHESIS)

        outcomes.append(ReflectionOutcome.INSIGHT)
        summary = self._summary(
            cue=cue,
            reconstruction=reconstruction,
            outcomes=outcomes,
            assessment=assessment,
            insufficient=insufficient,
            ambiguous=ambiguous,
        )

        # Dedupe outcomes preserving order
        seen: set[str] = set()
        ordered: list[ReflectionOutcome] = []
        for o in outcomes:
            if o.value not in seen:
                seen.add(o.value)
                ordered.append(o)

        return ReflectionEvaluation(
            cue=cue,
            remembered_answer=reconstruction.answer,
            remembered_confidence=conf,
            confidence_assessment=assessment,
            outcomes=ordered,
            contradictions=contradictions,
            consistencies=consistencies,
            patterns=patterns,
            questions=questions,
            hypotheses=hypotheses,
            insufficient_evidence=insufficient,
            ambiguous=ambiguous,
            evaluation_summary=summary,
            activated_concept_ids=list(reconstruction.activated_concept_ids),
            association_ids=list(reconstruction.association_ids),
            experience_ids=list(reconstruction.experience_ids),
            reconstruction=reconstruction.to_public(),
            activation_reused=True,
        )

    def _summary(
        self,
        *,
        cue: str,
        reconstruction: Reconstruction,
        outcomes: list[ReflectionOutcome],
        assessment: float,
        insufficient: bool,
        ambiguous: bool,
    ) -> str:
        # Template-class evaluative language — not chain-of-thought
        if reconstruction.explanation_class == "unknown" or reconstruction.confidence <= 0:
            return (
                f"I don't know enough about '{cue}'. "
                "I should gather more experience before trusting a recollection."
            )
        if ambiguous:
            return (
                f"I remember something about this, but evidence conflicts "
                f"(assessment={assessment:.2f}). Multiple interpretations remain plausible."
            )
        if insufficient:
            return (
                f"I have a tentative recollection, but evidence is insufficient "
                f"(assessment={assessment:.2f}). I should gather more experience."
            )
        if assessment >= 0.7 and ReflectionOutcome.CONSISTENCY in outcomes:
            return (
                f"My recollection appears consistent and adequately grounded "
                f"(assessment={assessment:.2f}): {reconstruction.answer}"
            )
        return (
            f"I evaluated my recollection with moderate confidence "
            f"(assessment={assessment:.2f}): {reconstruction.answer}"
        )

    # --- Reflective Experience birth -----------------------------------------

    def _birth_reflective_experience(
        self, evaluation: ReflectionEvaluation, reconstruction: Reconstruction
    ):
        reflects_on = ""
        if reconstruction.experience_ids:
            reflects_on = reconstruction.experience_ids[0]
        elif reconstruction.primary_concept_id:
            concept = self.store.concepts.get(reconstruction.primary_concept_id)
            if concept and concept.evidence_ids:
                reflects_on = concept.evidence_ids[-1]

        # If nothing to reflect on yet, still birth a Reflective Experience (anchors itself)
        # without revising anything — parent/reflects_on optional.
        outcome_bits = ",".join(o.value for o in evaluation.outcomes[:6])
        summary = evaluation.evaluation_summary
        metadata = {
            "reflection_outcomes": outcome_bits,
            "confidence_assessment": f"{evaluation.confidence_assessment:.4f}",
            "remembered_confidence": f"{evaluation.remembered_confidence:.4f}",
            "cue": evaluation.cue[:120],
        }
        if evaluation.questions:
            metadata["questions"] = " | ".join(evaluation.questions[:3])
        if evaluation.hypotheses:
            metadata["hypotheses"] = " | ".join(evaluation.hypotheses[:3])

        kwargs: dict[str, Any] = {
            "attention_class": "default",
            "attention_weight": 0.85,
            "concept_ids": tuple(evaluation.activated_concept_ids[:8]),
            "metadata": metadata,
        }
        if reflects_on and reflects_on in self.store.experiences:
            return self.experiences.reflect(reflects_on, summary, **kwargs)
        return self.experiences.birth(
            summary,
            encode_kind="experience",
            cognitive_kind=CognitiveKind.REFLECTION,
            **kwargs,
        )

    def _enter_working(self, evaluation: ReflectionEvaluation) -> None:
        if self.buffer is None or not evaluation.activated_concept_ids:
            return
        cid = evaluation.activated_concept_ids[0]
        concept = self.store.concepts.get(cid)
        if concept is None:
            return
        self.buffer.push(
            BufferItem(
                kind="hypothesis",
                ref_id=concept.id,
                label=f"reflect:{concept.labels[0] if concept.labels else cid}",
                attention=0.65,
                importance=0.55,
            )
        )

    def _observe(self, evaluation: ReflectionEvaluation, *, attention_class: str) -> None:
        self._reflections += 1
        self.validation.record_reflection(
            action="evaluation",
            cue=evaluation.cue[:120],
            outcomes=[o.value for o in evaluation.outcomes],
            confidence_assessment=evaluation.confidence_assessment,
            remembered_confidence=evaluation.remembered_confidence,
            contradiction=1 if evaluation.contradictions else 0,
            pattern=1 if evaluation.patterns else 0,
            question=1 if evaluation.questions else 0,
            hypothesis=1 if evaluation.hypotheses else 0,
            insufficient_evidence=1 if evaluation.insufficient_evidence else 0,
            reflective_experience_id=evaluation.reflective_experience_id,
            reflects_on_id=evaluation.reflects_on_id,
            activation_reused=1 if evaluation.activation_reused else 0,
            reflection=1,
            attention_class=attention_class,
            timestamp_hint=time(),
        )

    def observables(self) -> dict[str, Any]:
        return {
            "reflections": self._reflections,
            "contradictions": self._contradictions,
            "questions": self._questions,
            "hypotheses": self._hypotheses,
            "patterns": self._patterns,
            "uncertain": self._uncertain,
        }
