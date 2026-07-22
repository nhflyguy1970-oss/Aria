"""Public ACM engine API — plug-and-play for any agent host."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter, time
from typing import Any

from acm._version import __version__ as acm_version
from acm.activation import ActivationEngine
from acm.analogy import AnalogyOrgan
from acm.associations import AssociationOrgan
from acm.attention import AttentionOrgan
from acm.concepts import ConceptOrgan
from acm.confidence import ConfidenceOrgan
from acm.context.frame import ContextFrame, infer_context
from acm.core.store import CognitiveStore
from acm.experiences import ExperienceOrgan
from acm.forgetting import ForgettingOrgan
from acm.identity import IdentityOrgan
from acm.learning import LearningOrgan
from acm.observability.trace import CognitiveTraceEvent, TraceLog
from acm.plugins import ExtensionRegistry
from acm.prediction import PredictionOrgan
from acm.provenance import IngestionProvenance, evaluate_ingestion
from acm.recombination import RecombinationOrgan
from acm.reconciliation import ReconciliationOrgan
from acm.reflection import ReflectionOrgan
from acm.remembering import RememberingOrgan
from acm.simulation import SimulationOrgan
from acm.sleep import OfflineCognitionOrgan
from acm.types import (
    AttentionClass,
    EdgeType,
    ExplanationClass,
    MemoryVerb,
)
from acm.validation.harness import (
    AssociationChange,
    LifecycleEvent,
    ValidationHarness,
    WorkingTransition,
)
from acm.working.buffer import BufferItem, WorkingBuffer


@dataclass
class RememberResult:
    answer: str
    explanation: str
    explanation_class: ExplanationClass
    activated_concept_ids: list[str]
    confidence: float
    trace: dict[str, Any]
    ambiguous: bool = False
    reconstruction: dict[str, Any] | None = None


class CognitiveEngine:
    """Host-agnostic cognitive memory engine.

    Adapters for Aria / FlyTying / robotics belong *outside* this package.
    """

    def __init__(
        self,
        *,
        agent_id: str = "agent",
        buffer_capacity: int = 7,
        persist_path: str | None = None,
        auto_persist: bool = False,
        assistant_identity: dict[str, Any] | None = None,
    ) -> None:
        from acm.identity.assistant_profile import AssistantIdentityProfile

        self.agent_id = agent_id
        self.auto_persist = auto_persist
        self.durable = None
        if persist_path:
            from acm.persistence import DurableCognitiveStore

            self.durable = DurableCognitiveStore(persist_path)
            self.store = self.durable.store
        else:
            self.store = CognitiveStore()
        self.buffer = WorkingBuffer(capacity=buffer_capacity)
        self.context = ContextFrame()
        self.validation = ValidationHarness()
        self.trace = TraceLog()
        self.experiences = ExperienceOrgan(store=self.store, validation=self.validation)
        self.concepts = ConceptOrgan(store=self.store, validation=self.validation)
        self.associations = AssociationOrgan(
            store=self.store, validation=self.validation, concepts=self.concepts
        )
        self.concepts.bind_associations(self.associations)
        profile = AssistantIdentityProfile.from_mapping(assistant_identity, agent_id=agent_id)
        self.identity = IdentityOrgan(
            agent_id=agent_id,
            store=self.store,
            validation=self.validation,
            profile=profile,
        )
        self.identity.ensure_schemas()
        self.attention = AttentionOrgan(store=self.store, validation=self.validation)
        self.forgetting = ForgettingOrgan(
            store=self.store, validation=self.validation, attention=self.attention
        )
        self.activation = ActivationEngine(
            store=self.store,
            validation=self.validation,
            associations=self.associations,
            identity=self.identity,
            buffer=self.buffer,
            attention=self.attention,
            forgetting=self.forgetting,
        )
        self.remembering = RememberingOrgan(
            store=self.store,
            validation=self.validation,
            activation=self.activation,
            identity=self.identity,
            associations=self.associations,
            buffer=self.buffer,
            attention=self.attention,
            forgetting=self.forgetting,
        )
        self.reflection = ReflectionOrgan(
            store=self.store,
            validation=self.validation,
            remembering=self.remembering,
            experiences=self.experiences,
            buffer=self.buffer,
        )
        self.learning = LearningOrgan(
            store=self.store,
            validation=self.validation,
            concepts=self.concepts,
            associations=self.associations,
            identity=self.identity,
        )
        self.offline = OfflineCognitionOrgan(
            store=self.store,
            validation=self.validation,
            learning=self.learning,
            activation=self.activation,
            attention=self.attention,
            forgetting=self.forgetting,
        )
        self.prediction = PredictionOrgan(
            store=self.store,
            validation=self.validation,
            activation=self.activation,
            attention=self.attention,
            forgetting=self.forgetting,
        )
        self.simulation = SimulationOrgan(
            store=self.store,
            validation=self.validation,
            activation=self.activation,
            attention=self.attention,
            prediction=self.prediction,
        )
        self.recombination = RecombinationOrgan(
            store=self.store,
            validation=self.validation,
            activation=self.activation,
            attention=self.attention,
            prediction=self.prediction,
            simulation=self.simulation,
        )
        self.analogy = AnalogyOrgan(
            store=self.store,
            validation=self.validation,
            activation=self.activation,
            associations=self.associations,
            attention=self.attention,
            forgetting=self.forgetting,
        )
        self.confidence = ConfidenceOrgan(store=self.store, validation=self.validation)
        self.reconciliation = ReconciliationOrgan(
            store=self.store,
            validation=self.validation,
            activation=self.activation,
            confidence=self.confidence,
        )
        self.extensions = ExtensionRegistry(core_version=acm_version)
        self.extensions.bind_engine(self)
        # Metacognitive sketches — emerge from state; not scripted “consciousness”
        self._encode_count = 0
        self._remember_count = 0
        self._reflect_count = 0
        self._learn_count = 0
        self._sleep_count = 0
        self._predict_count = 0
        self._simulate_count = 0
        self._recombine_count = 0
        self._analogy_count = 0
        self._reconcile_count = 0
        self._assess_count = 0
        # Nuclei exist as organizational anchors; content still arrives via experience
        self.identity.ensure_schemas()
        for cid in self.identity._schema_ids.values():
            concept = self.store.concepts.get(cid)
            if concept is not None:
                self.concepts.register_existing(concept)
                self.forgetting.ensure(cid)
        if self.durable is not None and self.auto_persist:
            self.flush(kind="boot")

    def flush(self, *, kind: str = "checkpoint") -> dict[str, Any]:
        if self.durable is None:
            return {"ok": False, "reason": "no_persist_path"}
        result = self.durable.flush(kind=kind)
        self.validation.record_storage(action="flush", kind=kind, ok=1)
        return result

    def export_snapshot(self, dest: str) -> dict[str, Any]:
        if self.durable is None:
            import json
            from pathlib import Path

            from acm.persistence.codec import export_store

            payload_path = Path(dest)
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            snap = export_store(self.store)
            payload_path.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
            self.validation.record_storage(action="export", ok=1)
            return {"ok": True, "path": str(payload_path), "checksum": snap["checksum"]}
        result = self.durable.export(dest)
        self.validation.record_storage(action="export", ok=1)
        return result

    def import_snapshot(self, src: str) -> dict[str, Any]:
        if self.durable is None:
            import json
            from pathlib import Path

            from acm.persistence.codec import import_store

            payload = json.loads(Path(src).read_text(encoding="utf-8"))
            import_store(payload, store=self.store)
            self.validation.record_storage(action="import", ok=1)
            return {"ok": True, "experiences": len(self.store.experiences)}
        result = self.durable.import_snapshot(src)
        self.validation.record_storage(action="import", ok=1)
        return result

    def backup(self, dest: str) -> dict[str, Any]:
        if self.durable is None:
            return {"ok": False, "reason": "no_persist_path"}
        result = self.durable.backup(dest)
        self.validation.record_storage(action="backup", ok=1)
        return result

    def restore(self, src: str) -> dict[str, Any]:
        if self.durable is None:
            return {"ok": False, "reason": "no_persist_path"}
        result = self.durable.restore(src)
        self.validation.record_storage(action="restore", ok=1)
        return result

    def verify_persistence(self) -> dict[str, Any]:
        if self.durable is None:
            from acm.persistence.codec import export_store, verify_snapshot

            snap = export_store(self.store)
            errors = verify_snapshot(snap)
            return {"ok": not errors, "snapshot_errors": errors, "checksum": snap.get("checksum")}
        result = self.durable.verify()
        self.validation.record_storage(action="verify", ok=1 if result.get("ok") else 0)
        return result

    def provenance_of(self, artifact_id: str) -> list[dict[str, Any]]:
        return [p.to_public() for p in self.store.provenance_for(artifact_id)]

    def cleanup_legacy_contamination(self) -> dict[str, Any]:
        """One-time D047 migration — remove pre-D046 untrusted-source memories.

        Idempotent maintenance operation; see ``acm.provenance.legacy_cleanup``.
        """
        from acm.provenance.legacy_cleanup import cleanup_legacy_contamination

        return cleanup_legacy_contamination(self)

    # --- public cognitive verbs -------------------------------------------------

    def set_context(self, *tags: str, activity: str = "", place: str = "") -> ContextFrame:
        self.context = ContextFrame(tags=tuple(tags), activity=activity, place=place)
        return self.context

    def open_goal(self, title: str, *, importance: float = 0.6) -> str:
        normalized = _normalize_goal_title(title)
        for existing in self.store.active_goals():
            if _normalize_goal_title(existing.title) == normalized:
                existing.importance = max(float(existing.importance or 0.0), importance)
                return existing.id

        goal = self.store.add_goal(title, importance=importance)
        displaced = self.buffer.push(
            BufferItem(
                kind="goal",
                ref_id=goal.id,
                label=title,
                attention=0.8,
                importance=importance,
            )
        )
        self._note_displace(displaced)
        self.validation.record_lifecycle(
            LifecycleEvent(time(), MemoryVerb.ENCODE.value, goal.id, f"goal_open:{title}")
        )
        # Goals bias identity reconstruction (active pursuits are part of “who”)
        agent = self.identity.schema_concept("agent")
        self.store.add_association(
            agent.id, goal.id, edge_type=EdgeType.RELATED_TO, weight=0.45 + 0.2 * importance
        )
        self.validation.record_identity(
            action="goal_bind",
            schema_id=agent.id,
            goal_id=goal.id,
            influence=1,
        )
        return goal.id

    def complete_goal(self, goal_id: str) -> None:
        goal = self.store.goals.get(goal_id)
        if not goal:
            return
        goal.status = "completed"
        goal.completed = time()
        self.validation.record_lifecycle(
            LifecycleEvent(time(), "goal_complete", goal_id, goal.title)
        )
        # Goal completion is itself an Experience — nothing bypasses Experience
        self.experiences.birth(
            f"Goal completed: {goal.title}",
            encode_kind="experience",
            attention_class=AttentionClass.GOAL.value,
            attention_weight=0.85,
            goal_ids=(goal_id,),
            goal_completed=True,
            context_tags=self.context.tags,
            metadata={"goal_id": goal_id},
        )

    def encode(
        self,
        text: str,
        *,
        kind: str = "experience",
        pin: bool = False,
        context_tags: tuple[str, ...] | None = None,
        assent: bool = False,
        proposal_id: str | None = None,
        external_kind: str = "text",
        envelope_ids: tuple[str, ...] | None = None,
        revises_id: str | None = None,
        reflects_on_id: str | None = None,
        t_start: float | None = None,
        t_end: float | None = None,
        speaker: str | None = None,
        provenance: IngestionProvenance | None = None,
    ) -> dict[str, Any]:
        from acm.authority.protection import reject_speech_contamination
        from acm.semantic import extract_semantics

        ingestion = evaluate_ingestion(provenance)
        if not ingestion.eligible:
            return {
                "encoded": False,
                "reason": "memory_trust",
                "detail": ingestion.reason,
                "ingestion": ingestion.to_public(),
            }
        assert provenance is not None

        blocked = reject_speech_contamination(
            text=text,
            context_tags=context_tags,
            external_kind=external_kind,
        )
        if blocked is not None:
            return blocked

        t0 = perf_counter()
        self.context = infer_context(text, self.context)
        if context_tags:
            tags = tuple(dict.fromkeys(list(self.context.tags) + list(context_tags)))
            self.context = ContextFrame(
                tags=tags, activity=self.context.activity, place=self.context.place
            )

        # Semantic Extraction — language → cognitive facts before any organ storage
        extraction = extract_semantics(text, kind=kind, speaker=speaker)
        cognitive_text = extraction.primary_summary or text.strip()
        evidence_text = extraction.evidence or text.strip()

        episodic_facts = [
            f for f in extraction.facts if f.kind.value == "experience" and f.relation_type
        ]
        # Autobiographical events: resolve relative time into Experience.t_start
        if t_start is None and episodic_facts:
            from acm.semantic.temporal import resolve_temporal_window

            window = resolve_temporal_window(episodic_facts[0].relation_type or "")
            if window is not None:
                t_start = window.midpoint

        has_goal = bool(self.store.active_goals())
        identity_boost = self.identity.attention_boost(text, kind=kind)
        allocation = self.attention.allocate(
            text,
            has_open_goal=has_goal,
            context_tags=self.context.tags,
            identity_boost=identity_boost,
        )
        try:
            attention = AttentionClass(allocation.attention_class)
        except ValueError:
            attention = AttentionClass.DEFAULT
        if pin:
            attention = AttentionClass.USER_PIN
            allocation.attention_class = attention.value
            allocation.weight = max(allocation.weight, 1.0)
        elif kind == "preference" and attention == AttentionClass.DEFAULT:
            attention = AttentionClass.NOVELTY
            allocation.attention_class = attention.value
            allocation.weight = max(allocation.weight, 0.75)
        elif kind == "identity" and attention == AttentionClass.DEFAULT:
            attention = AttentionClass.STAKES
            allocation.attention_class = attention.value
            allocation.weight = max(allocation.weight, 0.9)
        elif self.identity.classify_identity_signal(text, kind=kind) in ("agent", "user"):
            if attention == AttentionClass.DEFAULT:
                attention = AttentionClass.STAKES
                allocation.attention_class = attention.value
                allocation.weight = max(allocation.weight, 0.85)
        # Extracted identity/preference facts are always durable
        if extraction.facts and attention == AttentionClass.DEFAULT:
            attention = AttentionClass.STAKES
            allocation.attention_class = attention.value
            allocation.weight = max(allocation.weight, 0.85)
        weight = min(1.0, allocation.weight + identity_boost * 0.1)

        # Low default attention may still encode lightly — pin/preference/identity durable
        durable = (
            weight >= 0.5
            or kind in ("preference", "identity")
            or bool(revises_id)
            or bool(extraction.facts)
        )
        if not durable:
            self.validation.record_lifecycle(
                LifecycleEvent(time(), MemoryVerb.ENCODE.value, "", "skipped_low_attention")
            )
            return {"encoded": False, "reason": "low_attention", "attention": attention.value}

        # M3 Concept organ — meaning emerges from cognitive cues (not instructional noise)
        concept, concept_ids = self.concepts.ingest_from_encode(
            cognitive_text,
            encode_kind=kind,
            weight=weight,
            context_tags=self.context.tags,
        )
        self.identity.mark_concept_formation(concept, text=cognitive_text, kind=kind)
        identity_signal = self.identity.classify_identity_signal(text, kind=kind)
        identity_influenced = identity_signal in ("agent", "user", "adjacent") or bool(
            extraction.identity_facts()
        )

        goal_ids = tuple(g.id for g in self.store.active_goals())
        exp_metadata: dict[str, str] = {
            "evidence": evidence_text[:2000],
            "semantic_extraction": "1",
            "source_actor": provenance.actor.value,
            "source_host_operation": provenance.host_operation.value,
            "source_message_role": provenance.message_role.value,
            "source_eligibility_reason": ingestion.reason,
        }
        if extraction.instructional_stripped:
            exp_metadata["instructional_stripped"] = "1"
        if extraction.perspective is not None:
            exp_metadata["perspective_first"] = extraction.perspective.first_person.value
        for i, fact in enumerate(extraction.facts[:12]):
            exp_metadata[f"fact_{i}_kind"] = fact.kind.value
            exp_metadata[f"fact_{i}_subject"] = fact.subject.value
            exp_metadata[f"fact_{i}_property"] = fact.property
            exp_metadata[f"fact_{i}_value"] = fact.value[:200]
            exp_metadata[f"fact_{i}_update_op"] = fact.update_op.value
            if fact.relation_type:
                # Experiences use relation_type as temporal; possessions use it as entity.
                if fact.kind.value == "experience":
                    exp_metadata[f"fact_{i}_temporal"] = fact.relation_type[:80]
                else:
                    exp_metadata[f"fact_{i}_relation"] = fact.relation_type[:80]
                    exp_metadata[f"fact_{i}_temporal"] = fact.relation_type[:80]

        if episodic_facts:
            ef = episodic_facts[0]
            exp_metadata["episodic"] = "1"
            exp_metadata["temporal_cue"] = (ef.relation_type or "")[:80]
            exp_metadata["event_action"] = (ef.property or "")[:80]
            exp_metadata["event_object"] = (ef.value or "")[:200]
            if ef.relation_type:
                from acm.semantic.temporal import resolve_temporal_window

                win = resolve_temporal_window(ef.relation_type)
                if win is not None:
                    exp_metadata["temporal_label"] = win.label

        exp = self.experiences.birth(
            cognitive_text,
            external_kind=external_kind,
            encode_kind=kind,
            attention_class=attention.value,
            attention_weight=weight,
            context_tags=self.context.tags,
            goal_ids=goal_ids,
            envelope_ids=tuple(envelope_ids or ()),
            concept_ids=tuple(concept_ids),
            t_start=t_start,
            t_end=t_end,
            revises_id=revises_id,
            reflects_on_id=reflects_on_id,
            identity_influenced=identity_influenced,
            metadata=exp_metadata,
        )
        if episodic_facts:
            self._link_episodic_neighbors(exp)
        self.concepts.bind_experience(exp, concept_ids=concept_ids)
        self.associations.absorb_experience(
            exp, concept_ids, identity_influenced=identity_influenced
        )
        self.forgetting.ensure(concept.id)
        self.attention.invest(
            concept.id,
            delta=0.04 + 0.05 * weight,
            source="encode",
            factors=["novelty", "salience"],
            summary="Encoding invested memory priority.",
        )
        self.confidence.evolve_from_encode(concept.id, success=True)
        # Prediction accuracy loop — memory outcome feedback, not reward for actions
        recent = sorted(self.store.predictions.values(), key=lambda p: p.created, reverse=True)
        for pred in recent[:3]:
            if pred.evaluated:
                continue
            if any(
                tok in (pred.cue or "").lower()
                for tok in cognitive_text.lower().split()
                if len(tok) > 3
            ):
                self.prediction.evaluate(pred.id, concept.id)
                break

        for attr in concept.attributes:
            if exp.id not in attr.evidence_ids:
                attr.evidence_ids.append(exp.id)

        # Open goals / project schema from extracted facts (additive)
        for fact in extraction.facts:
            if fact.kind.value == "goal" and fact.value:
                try:
                    self.open_goal(fact.value, importance=0.7)
                except Exception:
                    pass
            if fact.kind.value == "project" and fact.property == "project" and fact.value:
                try:
                    project = self.identity.schema_concept("project")
                    from acm.types import Attribute as _Attr

                    if not any(
                        a.key == "title" and a.value.lower() == fact.value.lower() and a.active
                        for a in project.attributes
                    ):
                        project.attributes.append(
                            _Attr(
                                key="title",
                                value=fact.value,
                                confidence=0.8,
                                importance=0.7,
                                evidence_ids=[exp.id],
                            )
                        )
                except Exception:
                    pass

        # Memory evolution — retire finished projects / unused entities (history preserved).
        self._apply_lifecycle_facts(extraction.facts, experience_id=exp.id)
        # Autobiographical relational reasoning — explicit, evidence-linked
        # Concept relationships only (never inferred from world knowledge).
        self._apply_relational_facts(extraction.facts, experience_id=exp.id)

        identity_result = self.identity.integrate_encode(
            text=text,
            kind=kind,
            concept=concept,
            experience_id=exp.id,
            weight=weight,
            assent=assent,
            proposal_id=proposal_id,
            facts=extraction.facts or None,
        )

        displaced = self.buffer.push(
            BufferItem(
                kind="concept",
                ref_id=concept.id,
                label=concept.labels[0],
                attention=weight,
                importance=concept.importance,
            )
        )
        self._note_displace(displaced)
        self.validation.record_working(
            WorkingTransition(time(), "enter", concept.id, concept.labels[0])
        )
        self.validation.record_lifecycle(
            LifecycleEvent(time(), MemoryVerb.ENCODE.value, concept.id, kind)
        )

        # Goal bias residue: keep legacy concept↔goal edge for compatibility
        for goal in self.store.active_goals():
            g_edge = self.store.add_association(
                concept.id, goal.id, edge_type=EdgeType.RELATED_TO, weight=0.4 + 0.2 * weight
            )
            self.validation.record_association(
                AssociationChange(
                    time(),
                    g_edge.id,
                    "added",
                    concept.id,
                    goal.id,
                    g_edge.relation.value,
                    g_edge.weight,
                )
            )

        latency = (perf_counter() - t0) * 1000
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.ENCODE.value,
                attention_class=attention.value,
                context_tags=list(self.context.tags),
                goal_ids=list(goal_ids),
                activated_concept_ids=[concept.id],
                explanation_class=ExplanationClass.EXPERIENCE.value,
                latency_ms=latency,
                metadata={
                    "identity": identity_result,
                    "experience": {
                        "id": exp.id,
                        "cognitive_kind": exp.cognitive_kind.value,
                        "external_kind": exp.external_kind.value,
                        "sequence": exp.sequence,
                    },
                    "concept_ids": concept_ids,
                    "concept_stage": concept.stage.value,
                    "semantic_extraction": extraction.to_public(),
                    "ingestion": ingestion.to_public(),
                },
            )
        )
        self._encode_count += 1
        payload = {
            "encoded": True,
            "experience_id": exp.id,
            "concept_id": concept.id,
            "concept_ids": concept_ids,
            "concept": concept.to_public(),
            "attention": attention.value,
            "importance": weight,
            "identity": identity_result,
            "experience": self.experiences.public_view(exp),
            "semantic_extraction": extraction.to_public(),
            "ingestion": ingestion.to_public(),
        }
        from acm.provenance import ProvenanceSource, stamp_provenance

        prov = stamp_provenance(
            self.store,
            artifact_kind="experience",
            artifact_id=exp.id,
            origin=ProvenanceSource.ENCODE,
            experience_ids=[exp.id],
            contributor_ids=list(concept_ids),
            explain="Encoded Experience with observed concept contributors.",
            source_actor=provenance.actor.value,
            host_operation=provenance.host_operation.value,
            message_role=provenance.message_role.value,
            eligibility_reason=ingestion.reason,
        )
        stamp_provenance(
            self.store,
            artifact_kind="concept",
            artifact_id=concept.id,
            origin=ProvenanceSource.ENCODE,
            experience_ids=[exp.id],
            contributor_ids=[concept.id],
            parent_provenance_ids=[prov.id],
            explain="Concept updated from encode evidence.",
            source_actor=provenance.actor.value,
            host_operation=provenance.host_operation.value,
            message_role=provenance.message_role.value,
            eligibility_reason=ingestion.reason,
        )
        payload["provenance_id"] = prov.id
        self.validation.record_provenance(action="stamp", count=2)
        if self.auto_persist and self.durable is not None:
            self.flush(kind="encode")
        self.extensions.emit("after_encode", dict(payload))
        return payload

    def what_happened(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Cognitive question M2: What happened?"""
        return self.experiences.what_happened(**kwargs)

    def what_is_this(self, cue: str) -> dict[str, Any]:
        """Cognitive question M3: What is this?"""
        return self.concepts.what_is_this(cue)

    def how_related(self, left: str, right: str) -> dict[str, Any]:
        """Cognitive question M4: How is this related?"""
        return self.associations.how_related(left, right)

    def what_do_i_remember(self, cue: str) -> dict[str, Any]:
        """Cognitive question M5: What do I remember?"""
        result = self.remember(cue)
        public = result.reconstruction or {
            "question": "What do I remember?",
            "answer": result.answer,
            "confidence": result.confidence,
            "ambiguous": result.ambiguous,
            "activated_concept_ids": result.activated_concept_ids,
        }
        return public

    def what_do_i_think(self, cue: str) -> dict[str, Any]:
        """Cognitive question M6: What do I think about what I remember?"""
        self.context = infer_context(cue, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            cue, has_open_goal=has_goal, context_tags=self.context.tags
        )
        weight = allocation.weight
        evaluation = self.reflection.what_do_i_think(
            cue,
            context_tags=self.context.tags,
            attention_weight=weight,
            attention_class=allocation.attention_class,
        )
        self._reflect_count += 1
        for cid in evaluation.activated_concept_ids[:4]:
            self.attention.invest(
                cid,
                delta=0.02,
                source="reflection",
                factors=["reflection"],
                summary="Reflection invested priority.",
            )
        return evaluation.to_public()

    def what_have_i_learned(self, cue: str = "") -> dict[str, Any]:
        """Cognitive question M7: What have I learned?"""
        return self.learning.what_have_i_learned(cue)

    def what_deserves_attention(self, cue: str = "") -> dict[str, Any]:
        """M9: What deserves cognitive attention and continued memory investment?"""
        return self.attention.what_deserves_attention(cue)

    def what_should_be_harder_to_remember(self, cue: str = "") -> dict[str, Any]:
        """Cognitive question M10: What should become harder to remember?"""
        return self.forgetting.what_should_be_harder_to_remember(cue)

    def what_is_likely(self, cue: str) -> dict[str, Any]:
        """Cognitive question M11: Based upon memory, what is likely?"""
        self.context = infer_context(cue, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            cue, has_open_goal=has_goal, context_tags=self.context.tags
        )
        result = self.prediction.what_is_likely(
            cue,
            context_tags=self.context.tags,
            attention_weight=allocation.weight,
        )
        self._predict_count += 1
        self.validation.record_lifecycle(
            LifecycleEvent(
                time(),
                MemoryVerb.PREDICT.value,
                result.get("id", ""),
                f"outcomes:{len(result.get('outcomes') or [])}",
            )
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.PREDICT.value,
                attention_class=allocation.attention_class,
                context_tags=list(self.context.tags),
                metadata={
                    "prediction_id": result.get("id"),
                    "confidence": result.get("confidence"),
                    "plans": False,
                },
            )
        )
        self.extensions.emit("after_predict", dict(result))
        return result

    def what_futures_can_memory_imagine(self, cue: str, *, branches: int = 3) -> dict[str, Any]:
        """Cognitive question M12: What possible futures can memory imagine?"""
        self.context = infer_context(cue, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            cue, has_open_goal=has_goal, context_tags=self.context.tags
        )
        before = len(self.store.experiences)
        result = self.simulation.what_futures_can_memory_imagine(
            cue,
            branches=branches,
            context_tags=self.context.tags,
            attention_weight=allocation.weight,
        )
        self._simulate_count += 1
        result["experiences_unchanged"] = len(self.store.experiences) == before
        self.validation.record_lifecycle(
            LifecycleEvent(
                time(),
                MemoryVerb.SIMULATE.value,
                "",
                f"branches:{len(result.get('simulations') or [])}",
            )
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.SIMULATE.value,
                attention_class=allocation.attention_class,
                metadata={
                    "branch_count": len(result.get("simulations") or []),
                    "hypothetical": True,
                    "historical_experiences_created": 0,
                    "plans": False,
                },
            )
        )
        self.extensions.emit("after_simulate", dict(result))
        return result

    def what_new_memories_can_emerge(self, cue: str, *, blends: int = 3) -> dict[str, Any]:
        """Cognitive question M13: What new memories can emerge by recombining existing memories?"""
        self.context = infer_context(cue, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            cue, has_open_goal=has_goal, context_tags=self.context.tags
        )
        before = len(self.store.experiences)
        result = self.recombination.what_new_memories_can_emerge(
            cue,
            blends=blends,
            context_tags=self.context.tags,
            attention_weight=allocation.weight,
        )
        self._recombine_count += 1
        result["experiences_unchanged"] = len(self.store.experiences) == before
        self.validation.record_lifecycle(
            LifecycleEvent(
                time(),
                MemoryVerb.RECOMBINE.value,
                "",
                f"blends:{len(result.get('recombinations') or [])}",
            )
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.RECOMBINE.value,
                attention_class=allocation.attention_class,
                metadata={
                    "count": len(result.get("recombinations") or []),
                    "historical": False,
                    "plans": False,
                },
            )
        )
        self.extensions.emit("after_recombine", dict(result))
        return result

    def what_is_analogous(self, cue: str, other: str = "") -> dict[str, Any]:
        """Cognitive question M14: What existing memories are analogous even when different?"""
        self.context = infer_context(cue, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            cue, has_open_goal=has_goal, context_tags=self.context.tags
        )
        result = self.analogy.what_is_analogous(
            cue,
            other=other,
            context_tags=self.context.tags,
            attention_weight=allocation.weight,
        )
        self._analogy_count += 1
        self.validation.record_lifecycle(
            LifecycleEvent(
                time(),
                MemoryVerb.ANALOGIZE.value,
                "",
                f"maps:{len(result.get('analogies') or [])}",
            )
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.ANALOGIZE.value,
                attention_class=allocation.attention_class,
                metadata={
                    "count": len(result.get("analogies") or []),
                    "executive": False,
                    "plans": False,
                },
            )
        )
        self.extensions.emit("after_analogy", dict(result))
        return result

    def how_should_memory_reconcile(self, cue: str) -> dict[str, Any]:
        """Cognitive question M15: When memories disagree, how should memory reconcile them?"""
        self.context = infer_context(cue, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            cue, has_open_goal=has_goal, context_tags=self.context.tags
        )
        before = len(self.store.experiences)
        before_ids = set(self.store.experiences)
        result = self.reconciliation.how_should_memory_reconcile(
            cue,
            context_tags=self.context.tags,
            attention_weight=allocation.weight,
        )
        self._reconcile_count += 1
        result["experiences_unchanged"] = len(self.store.experiences) == before
        result["experience_ids_unchanged"] = set(self.store.experiences) == before_ids
        rid = ""
        if isinstance(result.get("reconciliation"), dict):
            rid = str(result["reconciliation"].get("id") or "")
        self.validation.record_lifecycle(
            LifecycleEvent(
                time(),
                MemoryVerb.RECONCILE.value,
                rid,
                f"status:{(result.get('reconciliation') or {}).get('status', '')}",
            )
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.RECONCILE.value,
                attention_class=allocation.attention_class,
                metadata={
                    "reconciliation_id": rid,
                    "status": (result.get("reconciliation") or {}).get("status"),
                    "historical_rewrite": False,
                    "deleted": False,
                    "plans": False,
                },
            )
        )
        self.extensions.emit("after_reconcile", dict(result))
        return result

    def how_certain_am_i(self, cue: str = "", *, concept_id: str = "") -> dict[str, Any]:
        """Cognitive question M16: How certain am I that this memory is accurate?"""
        if cue:
            self.context = infer_context(cue, self.context)
        result = self.confidence.how_certain_am_i(cue, concept_id=concept_id)
        self._assess_count += 1
        self.validation.record_lifecycle(
            LifecycleEvent(
                time(),
                MemoryVerb.ASSESS.value,
                concept_id or "",
                f"overall:{result.get('overall_confidence', 0)}",
            )
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.ASSESS.value,
                metadata={
                    "overall_confidence": result.get("overall_confidence"),
                    "snapshot_count": len(result.get("snapshots") or []),
                    "plans": False,
                    "decides": False,
                },
            )
        )
        self.extensions.emit("after_assess", dict(result))
        return result

    def evaluate_prediction(self, prediction_id: str, realized_concept_id: str) -> dict[str, Any]:
        return self.prediction.evaluate(prediction_id, realized_concept_id)

    def cool_memory(self, concept_id: str, *, steps: int = 1) -> dict[str, Any]:
        """Soft forget — accessibility down; never deletes Experiences."""
        before_count = len(self.store.experiences)
        # Host-requested cool is intentional (not silent); still never deletes.
        event = self.forgetting.cool(concept_id, source="host", steps=steps, force=True)
        self.validation.record_lifecycle(
            LifecycleEvent(time(), MemoryVerb.FORGET.value, concept_id, "cool")
        )
        return {
            "cooled": event is not None,
            "event": event.to_public() if event else None,
            "experiences_unchanged": len(self.store.experiences) == before_count,
            "deleted": False,
        }

    def reactivate_memory(self, concept_id: str, *, steps: int = 1) -> dict[str, Any]:
        event = self.forgetting.reactivate(concept_id, source="host", steps=steps)
        return {
            "reactivated": event is not None,
            "event": event.to_public() if event else None,
        }

    def learn(
        self,
        *,
        reflective_experience_id: str = "",
        cue: str = "",
    ) -> dict[str, Any]:
        """Apply Learning from a Reflective Experience (explicit online adaptation)."""
        rid = reflective_experience_id
        if not rid and cue:
            thought = self.what_do_i_think(cue)
            rid = str(thought.get("reflective_experience_id") or "")
        if not rid:
            return {
                "question": "What have I learned?",
                "answer": "No Reflective Experience available to learn from.",
                "adaptations": [],
            }
        adaptations = self.learning.learn_from_reflection(rid)
        self._learn_count += 1
        for a in adaptations:
            if a.applied and a.target_kind.value == "concept" and a.target_id:
                self.attention.invest(
                    a.target_id,
                    delta=0.03,
                    source="learning",
                    factors=["learning"],
                    summary="Learning invested priority.",
                )
                self.forgetting.reactivate(a.target_id, source="learning", steps=1)
                self.confidence.evolve_from_learning(a.target_id, reinforce=True)
        self.validation.record_lifecycle(
            LifecycleEvent(time(), MemoryVerb.LEARN.value, rid, f"adaptations:{len(adaptations)}")
        )
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.LEARN.value,
                activated_concept_ids=[],
                metadata={
                    "reflective_experience_id": rid,
                    "adaptation_count": len(adaptations),
                    "applied": sum(1 for a in adaptations if a.applied),
                },
            )
        )
        payload = {
            "question": "What have I learned?",
            "reflective_experience_id": rid,
            "adaptations": [a.to_public() for a in adaptations],
            "applied": sum(1 for a in adaptations if a.applied),
            "proposed": sum(1 for a in adaptations if a.governance.value == "proposed"),
            "abstained": sum(1 for a in adaptations if a.governance.value == "abstained"),
            "lessons": self.learning.what_have_i_learned().get("lessons", [])[:10],
        }
        self.extensions.emit("after_learn", dict(payload))
        return payload

    def assent_adaptation(self, adaptation_id: str) -> dict[str, Any]:
        return self.learning.assent_adaptation(adaptation_id)

    def reject_adaptation(self, adaptation_id: str) -> dict[str, Any]:
        return self.learning.reject_adaptation(adaptation_id)

    def rollback_adaptation(self, adaptation_id: str) -> dict[str, Any]:
        rolled = self.learning.rollback_adaptation(adaptation_id)
        if rolled is None:
            return {"status": "missing"}
        return {"status": "rolled_back", "adaptation": rolled.to_public()}

    def timeline(self, **kwargs: Any) -> dict[str, Any]:
        return self.experiences.timeline(**kwargs)

    def revise_experience(
        self,
        experience_id: str,
        text: str,
        *,
        provenance: IngestionProvenance | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Correction path — always births a new immutable Experience."""
        return self.encode(
            text,
            revises_id=experience_id,
            provenance=provenance,
            **kwargs,
        )

    def reflect_on(
        self,
        experience_id: str,
        text: str,
        *,
        provenance: IngestionProvenance | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Host-supplied Reflective Experience lineage helper.

        Prefer `what_do_i_think` for organ evaluation.
        """
        return self.encode(
            text,
            reflects_on_id=experience_id,
            pin=True,
            provenance=provenance,
            **kwargs,
        )

    def remember(self, query: str) -> RememberResult:
        """Active Remembering — reconstructs via shared Cognitive Activation Architecture."""
        t0 = perf_counter()
        self.context = infer_context(query, self.context)
        has_goal = bool(self.store.active_goals())
        allocation = self.attention.allocate(
            query, has_open_goal=has_goal, context_tags=self.context.tags
        )
        attention = AttentionClass(allocation.attention_class)
        weight = allocation.weight

        reconstruction = self.remembering.what_do_i_remember(
            query,
            context_tags=self.context.tags,
            attention_weight=weight,
            attention_class=attention.value,
        )
        # Working-memory displacement observability
        for item in reconstruction.activation.get("working_displaced") or []:
            self.validation.record_working(
                WorkingTransition(time(), "displace", item["ref_id"], item["label"])
            )

        try:
            expl_class = ExplanationClass(reconstruction.explanation_class)
        except ValueError:
            expl_class = ExplanationClass.UNKNOWN
        explanation = self.remembering.explanation_text(expl_class, reconstruction.confidence)

        latency = (perf_counter() - t0) * 1000
        assoc_types: list[str] = []
        for aid in reconstruction.association_ids[:8]:
            edge = self.store.associations.get(aid)
            if edge is not None:
                assoc_types.append(edge.relation.value)

        reconsolidation = "null"
        if reconstruction.primary_concept_id:
            reconsolidation = "light"
            if any(
                r.get("kind") == "contest_signal" for r in self.validation.reconsolidations[-3:]
            ):
                reconsolidation = "contest"

        event = CognitiveTraceEvent(
            verb=MemoryVerb.REMEMBER.value,
            attention_class=attention.value,
            context_tags=list(self.context.tags),
            goal_ids=[g.id for g in self.store.active_goals()],
            activated_concept_ids=list(reconstruction.activated_concept_ids),
            association_edge_types=assoc_types,
            explanation_class=expl_class.value,
            reconsolidation=reconsolidation,
            latency_ms=latency,
            metadata={
                "ambiguous": reconstruction.ambiguous,
                "identity_query": reconstruction.identity_influenced
                and self.identity.is_who_query(query),
                "activation_steps": reconstruction.activation.get("propagation_steps", 0),
                "experience_participants": len(reconstruction.experience_ids),
            },
        )
        self.trace.append(event)
        self._remember_count += 1
        result = RememberResult(
            answer=reconstruction.answer,
            explanation=explanation,
            explanation_class=expl_class,
            activated_concept_ids=list(reconstruction.activated_concept_ids),
            confidence=reconstruction.confidence,
            trace=event.to_public(),
            ambiguous=reconstruction.ambiguous,
            reconstruction=reconstruction.to_public(),
        )
        self.extensions.emit(
            "after_remember",
            {
                "query": query,
                "answer": result.answer,
                "identity_query": bool(event.metadata.get("identity_query")),
                "ambiguous": result.ambiguous,
            },
        )
        return result

    def sleep(self, *, apply_low_impact: bool = True) -> dict[str, Any]:
        """M8 Offline Cognition — functional consolidation (replay + stabilize)."""
        payload = self.offline.consolidate(apply_low_impact=apply_low_impact)
        self._sleep_count += 1
        self.trace.append(
            CognitiveTraceEvent(
                verb=MemoryVerb.SLEEP.value,
                reconsolidation="sleep",
                metadata={
                    "sleep_batch_id": payload.get("sleep_batch_id"),
                    "replay_count": payload.get("replay_count", 0),
                    "pruned_edges": payload.get("pruned_edges", 0),
                    "proposal_count": len(payload.get("proposals") or []),
                    "adaptations_applied": payload.get("adaptations_applied", 0),
                },
            )
        )
        self.extensions.emit("after_sleep", dict(payload))
        return payload

    def who_am_i(self) -> dict[str, Any]:
        """Reconstruct agent identity from schemas + lived structure."""
        return self.identity.who_am_i()

    def classify_request(self, text: str) -> dict[str, Any]:
        """Cognitive Intent Classification — ownership before speech (D039)."""
        from acm.authority.classification import classify_memory_request

        return classify_memory_request(text).to_public()

    def route_request(self, text: str) -> dict[str, Any]:
        """Classify + determine cognitive organ ownership (no reconstruction yet)."""
        from acm.authority.routing import CognitiveRoutingEngine

        return CognitiveRoutingEngine(self).decide(text).to_public()

    def dispatch_request(self, text: str) -> dict[str, Any]:
        """End-to-end cognitive dispatch (ownership + organ execution) without speak."""
        from acm.authority.dispatch import CognitiveDispatchEngine

        return CognitiveDispatchEngine(self).dispatch(text).to_public()

    def cognitive_respond(self, request: str) -> dict[str, Any]:
        """Memory Authority: classify → route → dispatch → organ → CognitiveMemoryResult.

        Returns ``CognitiveMemoryResult.to_public()``. Hosts MUST invoke this (or
        equivalent organ verbs) for memory requests **before** language-model
        generation. Language models must only speak via ``speak_cognitive_result``.
        The language model never chooses which organ answers. Infrastructure never
        terminates a cognitive request (D040).
        """
        from acm.authority.pipeline import CognitiveResponsePipeline

        result = CognitiveResponsePipeline(self).respond(request)
        return result.to_public()

    def speak_cognitive_result(self, result: dict[str, Any] | Any) -> str:
        """Faithful speech for a Cognitive Memory Result — never invents memory."""
        from acm.authority.result import CognitiveMemoryResult, MemoryStatus
        from acm.authority.speak import speak_cognitive_result

        if isinstance(result, CognitiveMemoryResult):
            return speak_cognitive_result(result)
        if not isinstance(result, dict):
            return ""
        status_raw = result.get("status") or "unknown"
        try:
            status = MemoryStatus(status_raw)
        except ValueError:
            status = MemoryStatus.UNKNOWN
        obj = CognitiveMemoryResult(
            status=status,
            is_memory_request=bool(result.get("is_memory_request")),
            intent=str(result.get("intent") or ""),
            memory=result.get("memory"),
            confidence=float(result.get("confidence") or 0.0),
            uncertainty=result.get("uncertainty"),
            explanation_class=str(result.get("explanation_class") or "unknown"),
            ambiguous=bool(result.get("ambiguous")),
            language_may_speak=bool(result.get("language_may_speak", True)),
        )
        return speak_cognitive_result(obj)

    def identity_snapshot(self) -> dict[str, Any]:
        snap = self.identity.snapshot()
        return {
            "agent_id": snap.agent_id,
            "schemas": snap.schemas,
            "central_concepts": snap.central_concepts,
            "active_goals": snap.active_goals,
            "capabilities": snap.capabilities,
            "uncertainties": snap.uncertainties,
            "lineage_tail": snap.lineage_tail,
            "confidence": snap.confidence,
            "evolution": snap.evolution,
        }

    def assent_identity(self, proposal_id: str) -> dict[str, Any]:
        return self.identity.assent(proposal_id)

    def reject_identity(self, proposal_id: str) -> dict[str, Any]:
        return self.identity.reject(proposal_id)

    def metacognitive_sketch(self) -> dict[str, Any]:
        """Foundations for self-modeling — not consciousness."""
        active_concepts = [c for c in self.store.concepts.values() if c.active]
        uncertain = [
            c
            for c in active_concepts
            if c.confidence < 0.55 or any(a.confidence < 0.55 for a in c.attributes if a.active)
        ]
        ident = self.identity.observables()
        exobs = self.experiences.observables()
        cob = self.concepts.observables()
        aobs = self.associations.observables()
        robs = self.remembering.observables()
        fobs = self.reflection.observables()
        lobs = self.learning.observables()
        oobs = self.offline.observables()
        atobs = self.attention.observables()
        fobs_forget = self.forgetting.observables()
        preds = self.prediction.observables()
        sims = self.simulation.observables()
        rcobs = self.recombination.observables()
        anobs = self.analogy.observables()
        rclobs = self.reconciliation.observables()
        cfobs = self.confidence.observables()
        return {
            "agent_id": self.agent_id,
            "what_i_know_count": len(active_concepts),
            "what_i_do_not_know_well_count": len(uncertain),
            "experiences": len(self.store.experiences),
            "what_happened_count": exobs["experience_count"],
            "active_goals": [g.title for g in self.store.active_goals()],
            "identity_concepts": [c.labels[0] for c in active_concepts if c.identity],
            "identity": ident,
            "experience": exobs,
            "concept": cob,
            "association": aobs,
            "remembering": robs,
            "reflection": fobs,
            "learning": lobs,
            "offline": oobs,
            "attention": atobs,
            "forgetting": fobs_forget,
            "prediction": preds,
            "simulation": sims,
            "recombination": rcobs,
            "analogy": anobs,
            "reconciliation": rclobs,
            "confidence": cfobs,
            "encode_count": self._encode_count,
            "remember_count": self._remember_count,
            "reflect_count": self._reflect_count,
            "learn_count": self._learn_count,
            "sleep_count": self._sleep_count,
            "predict_count": self._predict_count,
            "simulate_count": self._simulate_count,
            "recombine_count": self._recombine_count,
            "analogy_count": self._analogy_count,
            "reconcile_count": self._reconcile_count,
            "assess_count": self._assess_count,
            "buffer_occupancy": len(self.buffer),
            "context_tags": list(self.context.tags),
            "extensions": self.extensions.names(),
        }

    # --- internals --------------------------------------------------------------

    def _apply_relational_facts(self, facts: list[Any], *, experience_id: str) -> None:
        """Birth first-class typed associations from explicit relational teachings."""
        from acm.associations.model import RelationKind

        relation_map = {
            "motivated_by": RelationKind.CAUSED_BY,
            "supports_goal": RelationKind.SUPPORTS,
            "part_of": RelationKind.PART_OF,
            "uses": RelationKind.DEPENDS_ON,
            "supports": RelationKind.SUPPORTS,
        }
        for fact in facts or []:
            kind = getattr(fact, "kind", None)
            kind_v = kind.value if hasattr(kind, "value") else str(kind or "")
            if kind_v != "relationship":
                continue
            relation_name = (getattr(fact, "property", "") or "").lower()
            if relation_name not in relation_map:
                continue
            source_label = (getattr(fact, "relation_type", "") or "").strip()
            target_label = (getattr(fact, "value", "") or "").strip()
            if target_label == "current_goal":
                goals = sorted(
                    self.store.active_goals(),
                    key=lambda g: getattr(g, "created", 0.0),
                )
                target_label = goals[-1].title if goals else ""
            if not source_label or not target_label:
                continue
            source = self._ensure_relational_concept(
                source_label, evidence_id=experience_id
            )
            target = self._ensure_relational_concept(
                target_label, evidence_id=experience_id
            )
            assoc = self.associations.relate(
                source.id,
                target.id,
                relation_map[relation_name],
                strength_forward=0.72,
                strength_backward=0.42,
                confidence=float(getattr(fact, "confidence", 0.85) or 0.85),
                evidence_id=experience_id,
                context_tags=self.context.tags,
                goal_influenced=relation_name == "supports_goal",
                identity_influenced=True,
            )
            if assoc is not None:
                assoc.metadata["autobiographical"] = True
                assoc.metadata["learned_relation"] = relation_name

    def _ensure_relational_concept(self, label: str, *, evidence_id: str) -> Any:
        """Resolve or create one Concept endpoint for an explicit learned entity."""
        clean = " ".join((label or "").strip().split())
        candidates = self.store.find_concepts_by_label(clean)
        for concept in candidates:
            if any(lab.casefold() == clean.casefold() for lab in concept.labels):
                if evidence_id and evidence_id not in concept.evidence_ids:
                    concept.evidence_ids.append(evidence_id)
                concept.metadata["autobiographical_entity"] = True
                return concept
            if any(
                attr.active and str(attr.value).casefold() == clean.casefold()
                for attr in concept.attributes
            ):
                if clean.casefold() not in {lab.casefold() for lab in concept.labels}:
                    concept.labels.append(clean)
                if evidence_id and evidence_id not in concept.evidence_ids:
                    concept.evidence_ids.append(evidence_id)
                concept.metadata["autobiographical_entity"] = True
                return concept
        from acm.types import ConceptRole

        concept = self.store.add_concept(
            clean,
            role=ConceptRole.ENTITY,
            confidence=0.78,
            importance=0.7,
            provisional=False,
            evidence_ids=[evidence_id] if evidence_id else [],
            metadata={"autobiographical_entity": True},
        )
        return concept

    def _apply_lifecycle_facts(self, facts: list[Any], *, experience_id: str) -> None:
        """Retire finished projects / unused entities while preserving attribute history."""
        for fact in facts or []:
            kind = getattr(fact, "kind", None)
            kind_v = kind.value if hasattr(kind, "value") else str(kind or "")
            prop = (getattr(fact, "property", "") or "").lower()
            value = (getattr(fact, "value", "") or "").strip().lower()
            relation = (getattr(fact, "relation_type", "") or "").strip()

            if kind_v == "project" and prop == "status" and value in (
                "finished",
                "complete",
                "completed",
                "retired",
                "done",
            ):
                title = relation or getattr(fact, "value", "") or ""
                self._retire_project(title, experience_id=experience_id)
            elif kind_v == "possession" and prop == "status" and value == "retired":
                self._retire_entity(relation, experience_id=experience_id)

    def _retire_project(self, title: str, *, experience_id: str) -> None:
        name = (title or "").strip()
        if not name:
            return
        needle = name.casefold()
        try:
            project = self.identity.schema_concept("project")
            for attr in project.attributes:
                if not attr.active:
                    continue
                if attr.key in ("title", "project") and attr.value.casefold() == needle:
                    attr.active = False
                    if experience_id and experience_id not in attr.evidence_ids:
                        attr.evidence_ids.append(experience_id)
        except Exception:
            pass
        for concept in self.store.concepts.values():
            labels = " ".join(getattr(concept, "labels", []) or []).lower()
            if needle not in labels and f"project {needle}" not in labels:
                # Also match attributes by value
                pass
            for attr in list(getattr(concept, "attributes", []) or []):
                if not getattr(attr, "active", False):
                    continue
                if attr.key in ("title", "project") and str(attr.value).casefold() == needle:
                    attr.active = False
                    if experience_id and experience_id not in attr.evidence_ids:
                        attr.evidence_ids.append(experience_id)
                if attr.key == "status" and "project" in labels and needle in labels:
                    # leave status updates to _apply_attribute supersede
                    pass
            # Ensure finished status is recorded on the project concept
            if needle in labels or any(
                a.key in ("title", "project") and str(a.value).casefold() == needle
                for a in getattr(concept, "attributes", []) or []
            ):
                from acm.types import Attribute as _Attr

                for attr in concept.attributes:
                    if attr.key == "status" and attr.active and attr.value.lower() != "finished":
                        attr.active = False
                if not any(
                    a.key == "status" and a.active and a.value.lower() == "finished"
                    for a in concept.attributes
                ):
                    concept.attributes.append(
                        _Attr(
                            key="status",
                            value="finished",
                            confidence=0.9,
                            importance=0.7,
                            evidence_ids=[experience_id] if experience_id else [],
                        )
                    )

    def _retire_entity(self, entity: str, *, experience_id: str) -> None:
        name = (entity or "").strip().lower()
        if not name:
            return
        for concept in self.store.concepts.values():
            labels = " ".join(getattr(concept, "labels", []) or []).lower()
            if name not in labels.split() and not labels.startswith(name):
                continue
            from acm.types import Attribute as _Attr

            for attr in concept.attributes:
                if not attr.active:
                    continue
                if attr.key == "status":
                    continue
                attr.active = False
                if experience_id and experience_id not in attr.evidence_ids:
                    attr.evidence_ids.append(experience_id)
            if not any(
                a.key == "status" and a.active and a.value.lower() == "retired"
                for a in concept.attributes
            ):
                # Retire any prior status first
                for attr in concept.attributes:
                    if attr.key == "status" and attr.active:
                        attr.active = False
                concept.attributes.append(
                    _Attr(
                        key="status",
                        value="retired",
                        confidence=0.92,
                        importance=0.8,
                        evidence_ids=[experience_id] if experience_id else [],
                    )
                )

    def _link_episodic_neighbors(self, exp: Any) -> None:
        """Link a new episodic experience to nearest earlier/later episodic events."""
        from acm.experiences.model import TemporalRelation

        def _is_episodic(e: Any) -> bool:
            meta = e.meta_dict() if hasattr(e, "meta_dict") else dict(getattr(e, "metadata", ()) or ())
            return meta.get("episodic") == "1"

        others = [
            e
            for e in self.store.experiences.values()
            if e.id != exp.id and _is_episodic(e)
        ]
        earlier = [e for e in others if e.t_start < exp.t_start]
        later = [e for e in others if e.t_start > exp.t_start]
        if earlier:
            prev = max(earlier, key=lambda e: (e.t_start, e.sequence))
            self.experiences.link(prev.id, exp.id, TemporalRelation.PRECEDES, weight=0.9)
            self.experiences.link(exp.id, prev.id, TemporalRelation.FOLLOWS, weight=0.9)
        if later:
            nxt = min(later, key=lambda e: (e.t_start, e.sequence))
            self.experiences.link(exp.id, nxt.id, TemporalRelation.PRECEDES, weight=0.9)
            self.experiences.link(nxt.id, exp.id, TemporalRelation.FOLLOWS, weight=0.9)

    def _note_displace(self, displaced: list[BufferItem]) -> None:
        for item in displaced:
            self.validation.record_working(
                WorkingTransition(time(), "displace", item.ref_id, item.label)
            )


def _normalize_goal_title(title: str) -> str:
    """Canonicalize goal titles so repeated identical teachings reuse one active goal."""
    text = " ".join((title or "").strip().lower().split())
    if text.startswith("to "):
        text = text[3:].strip()
    return text
