"""M0/M1 Cognitive Memory Validation Harness — development/validation capability."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from time import time
from typing import Any


@dataclass
class ActivationRecord:
    timestamp: float
    cue: str
    concept_ids: list[str]
    concept_labels: list[str]
    why: list[str]  # cue classes — not chain-of-thought
    goal_ids: list[str] = field(default_factory=list)
    attention_class: str = "default"
    context_tags: list[str] = field(default_factory=list)


@dataclass
class ConfidenceDelta:
    timestamp: float
    concept_id: str
    attribute_key: str
    before: float
    after: float
    reason: str


@dataclass
class AssociationChange:
    timestamp: float
    edge_id: str
    change: str  # added | strengthened | weakened | superseded
    source_id: str
    target_id: str
    edge_type: str
    weight: float


@dataclass
class LifecycleEvent:
    timestamp: float
    verb: str
    subject_id: str
    detail: str


@dataclass
class WorkingTransition:
    timestamp: float
    action: str  # enter | displace | clear
    ref_id: str
    label: str


class ValidationHarness:
    """Records observable cognitive state for milestone validation.

    Not a runtime organ. Not host-specific. Safe metadata only.
    """

    def __init__(self, *, max_events: int = 2000) -> None:
        self.max_events = max_events
        self.activations: list[ActivationRecord] = []
        self.confidence_deltas: list[ConfidenceDelta] = []
        self.association_changes: list[AssociationChange] = []
        self.lifecycle: list[LifecycleEvent] = []
        self.working_transitions: list[WorkingTransition] = []
        self.reconsolidations: list[dict[str, Any]] = []
        self.sleep_events: list[dict[str, Any]] = []
        self.identity_touches: list[dict[str, Any]] = []
        self.experience_events: list[dict[str, Any]] = []
        self.concept_events: list[dict[str, Any]] = []
        # Aggregated identity observables (M1)
        self.identity_metrics: dict[str, float | int] = {
            "growth": 0,
            "stability": 0,
            "change": 0,
            "influence": 0,
            "lineage_events": 0,
            "last_confidence": 0.0,
        }
        # Aggregated experience observables (M2)
        self.experience_metrics: dict[str, float | int] = {
            "births": 0,
            "lineage": 0,
            "salience_evolutions": 0,
            "temporal_links": 0,
            "lifecycle": 0,
            "multimodal": 0,
            "identity_influenced": 0,
            "goal_influenced": 0,
        }
        # Aggregated concept observables (M3)
        self.concept_metrics: dict[str, float | int] = {
            "births": 0,
            "nuclei": 0,
            "strengthenings": 0,
            "weakenings": 0,
            "maturity_changes": 0,
            "abstractions": 0,
            "hierarchy": 0,
            "merges": 0,
            "splits": 0,
            "prototypes": 0,
        }
        self.association_events: list[dict[str, Any]] = []
        self.association_metrics: dict[str, float | int] = {
            "births": 0,
            "strengthenings": 0,
            "weakenings": 0,
            "dormancies": 0,
            "reactivations": 0,
            "neighborhoods": 0,
            "clusters": 0,
            "goal_influenced": 0,
            "identity_influenced": 0,
            "temporal": 0,
            "asymmetric_births": 0,
        }
        self.remembering_events: list[dict[str, Any]] = []
        self.remembering_metrics: dict[str, float | int] = {
            "reconstructions": 0,
            "activations": 0,
            "ambiguities": 0,
            "propagations": 0,
            "decays": 0,
            "experience_participants": 0,
            "goal_influenced": 0,
            "identity_influenced": 0,
            "context_influenced": 0,
            "working_influenced": 0,
        }
        self.reflection_events: list[dict[str, Any]] = []
        self.reflection_metrics: dict[str, float | int] = {
            "reflections": 0,
            "contradictions": 0,
            "patterns": 0,
            "questions": 0,
            "hypotheses": 0,
            "insufficient_evidence": 0,
            "activation_reused": 0,
            "reflective_experiences": 0,
        }
        self.learning_events: list[dict[str, Any]] = []
        self.learning_metrics: dict[str, float | int] = {
            "events": 0,
            "applied": 0,
            "proposed": 0,
            "abstained": 0,
            "rollbacks": 0,
            "assents": 0,
            "rejects": 0,
            "concept_evolution": 0,
            "association_evolution": 0,
            "identity_evolution": 0,
            "confidence_evolution": 0,
            "generalization": 0,
            "transfer": 0,
        }
        self.offline_events: list[dict[str, Any]] = []
        self.offline_metrics: dict[str, float | int] = {
            "events": 0,
            "replays": 0,
            "consolidations": 0,
            "abstractions": 0,
            "cools": 0,
            "stabilizations": 0,
            "proposals": 0,
        }
        self.attention_events: list[dict[str, Any]] = []
        self.attention_metrics: dict[str, float | int] = {
            "events": 0,
            "allocations": 0,
            "investments": 0,
            "priority_evolution": 0,
        }
        self.forgetting_events: list[dict[str, Any]] = []
        self.forgetting_metrics: dict[str, float | int] = {
            "events": 0,
            "cools": 0,
            "reactivations": 0,
            "dormancies": 0,
            "accessibility_evolution": 0,
            "proposals": 0,
            "resists": 0,
        }
        self.prediction_events: list[dict[str, Any]] = []
        self.prediction_metrics: dict[str, float | int] = {
            "events": 0,
            "predictions": 0,
            "evaluations": 0,
            "last_confidence": 0.0,
            "last_accuracy": 0.0,
        }
        self.simulation_events: list[dict[str, Any]] = []
        self.simulation_metrics: dict[str, float | int] = {
            "events": 0,
            "simulations": 0,
            "hypothetical_steps": 0,
            "branches": 0,
        }
        self.recombination_events: list[dict[str, Any]] = []
        self.recombination_metrics: dict[str, float | int] = {
            "events": 0,
            "recombinations": 0,
            "last_novelty": 0.0,
        }
        self.analogy_events: list[dict[str, Any]] = []
        self.analogy_metrics: dict[str, float | int] = {
            "events": 0,
            "mappings": 0,
            "transfers": 0,
            "last_confidence": 0.0,
        }
        self.reconciliation_events: list[dict[str, Any]] = []
        self.reconciliation_metrics: dict[str, float | int] = {
            "events": 0,
            "reconciliations": 0,
            "conflicts": 0,
            "corroborations": 0,
            "last_confidence_before": 0.0,
            "last_confidence_after": 0.0,
        }
        self.confidence_organ_events: list[dict[str, Any]] = []
        self.confidence_organ_metrics: dict[str, float | int] = {
            "events": 0,
            "evolutions": 0,
            "recalibrations": 0,
            "last_before": 0.0,
            "last_after": 0.0,
        }
        self.storage_events: list[dict[str, Any]] = []
        self.storage_metrics: dict[str, float | int] = {
            "events": 0,
            "flushes": 0,
            "exports": 0,
            "imports": 0,
            "backups": 0,
            "restores": 0,
            "verifies": 0,
        }
        self.provenance_events: list[dict[str, Any]] = []
        self.provenance_metrics: dict[str, float | int] = {
            "events": 0,
            "stamps": 0,
        }
        self.shadow_events: list[dict[str, Any]] = []
        self.shadow_metrics: dict[str, float | int] = {
            "events": 0,
            "agreements": 0,
            "disagreements": 0,
        }

    def _trim(self, seq: list[Any]) -> None:
        overflow = len(seq) - self.max_events
        if overflow > 0:
            del seq[:overflow]

    def record_activation(self, record: ActivationRecord) -> None:
        self.activations.append(record)
        self._trim(self.activations)

    def record_confidence(self, delta: ConfidenceDelta) -> None:
        self.confidence_deltas.append(delta)
        self._trim(self.confidence_deltas)

    def record_association(self, change: AssociationChange) -> None:
        self.association_changes.append(change)
        self._trim(self.association_changes)

    def record_lifecycle(self, event: LifecycleEvent) -> None:
        self.lifecycle.append(event)
        self._trim(self.lifecycle)

    def record_working(self, transition: WorkingTransition) -> None:
        self.working_transitions.append(transition)
        self._trim(self.working_transitions)

    def record_reconsolidation(self, **payload: Any) -> None:
        self.reconsolidations.append({"timestamp": time(), **payload})
        self._trim(self.reconsolidations)

    def record_sleep(self, **payload: Any) -> None:
        self.sleep_events.append({"timestamp": time(), **payload})
        self._trim(self.sleep_events)

    def record_identity(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.identity_touches.append(event)
        self._trim(self.identity_touches)
        # Roll metrics from observable fields
        for key in ("growth", "stability", "change", "influence"):
            if key in payload and payload[key]:
                self.identity_metrics[key] = int(self.identity_metrics[key]) + int(
                    payload[key]
                )
        if payload.get("lineage") or payload.get("lineage_length") is not None:
            self.identity_metrics["lineage_events"] = int(
                self.identity_metrics["lineage_events"]
            ) + (1 if payload.get("lineage") else 0)
            if payload.get("lineage_length") is not None:
                # keep max observed lineage length as evolution proxy
                self.identity_metrics["lineage_events"] = max(
                    int(self.identity_metrics["lineage_events"]),
                    int(payload["lineage_length"]),
                )
        if "confidence" in payload and payload["confidence"] is not None:
            self.identity_metrics["last_confidence"] = float(payload["confidence"])
        elif "confidence_after" in payload:
            self.identity_metrics["last_confidence"] = float(payload["confidence_after"])

    def record_experience(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.experience_events.append(event)
        self._trim(self.experience_events)
        action = str(payload.get("action", ""))
        if action == "birth":
            self.experience_metrics["births"] = int(self.experience_metrics["births"]) + 1
            if payload.get("lineage"):
                self.experience_metrics["lineage"] = int(self.experience_metrics["lineage"]) + 1
            if payload.get("identity_influenced"):
                self.experience_metrics["identity_influenced"] = (
                    int(self.experience_metrics["identity_influenced"]) + 1
                )
            if int(payload.get("goal_count") or 0) > 0:
                self.experience_metrics["goal_influenced"] = (
                    int(self.experience_metrics["goal_influenced"]) + 1
                )
        elif action == "salience_evolution":
            self.experience_metrics["salience_evolutions"] = (
                int(self.experience_metrics["salience_evolutions"]) + 1
            )
        elif action == "temporal_link":
            self.experience_metrics["temporal_links"] = (
                int(self.experience_metrics["temporal_links"]) + 1
            )
        elif action == "lifecycle":
            self.experience_metrics["lifecycle"] = int(self.experience_metrics["lifecycle"]) + 1
        elif action == "envelope" or payload.get("multimodal"):
            self.experience_metrics["multimodal"] = int(self.experience_metrics["multimodal"]) + 1

    def record_concept(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.concept_events.append(event)
        self._trim(self.concept_events)
        if payload.get("birth") or payload.get("action") == "birth":
            self.concept_metrics["births"] = int(self.concept_metrics["births"]) + 1
        if payload.get("nucleus"):
            self.concept_metrics["nuclei"] = int(self.concept_metrics["nuclei"]) + 1
        if payload.get("strengthening"):
            self.concept_metrics["strengthenings"] = (
                int(self.concept_metrics["strengthenings"]) + 1
            )
        if payload.get("weakening"):
            self.concept_metrics["weakenings"] = int(self.concept_metrics["weakenings"]) + 1
        if payload.get("maturity") or payload.get("lifecycle"):
            self.concept_metrics["maturity_changes"] = (
                int(self.concept_metrics["maturity_changes"]) + 1
            )
        if payload.get("abstraction"):
            self.concept_metrics["abstractions"] = int(self.concept_metrics["abstractions"]) + 1
        if payload.get("hierarchy"):
            self.concept_metrics["hierarchy"] = int(self.concept_metrics["hierarchy"]) + 1
        if payload.get("merge"):
            self.concept_metrics["merges"] = int(self.concept_metrics["merges"]) + 1
        if payload.get("split"):
            self.concept_metrics["splits"] = int(self.concept_metrics["splits"]) + 1
        if payload.get("prototype"):
            self.concept_metrics["prototypes"] = int(self.concept_metrics["prototypes"]) + 1

    def record_association_organ(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.association_events.append(event)
        self._trim(self.association_events)
        if payload.get("birth") or payload.get("action") == "birth":
            self.association_metrics["births"] = int(self.association_metrics["births"]) + 1
            fwd = float(payload.get("strength_forward") or 0)
            back = float(payload.get("strength_backward") or 0)
            if abs(fwd - back) > 0.08:
                self.association_metrics["asymmetric_births"] = (
                    int(self.association_metrics["asymmetric_births"]) + 1
                )
        if payload.get("strengthening"):
            self.association_metrics["strengthenings"] = (
                int(self.association_metrics["strengthenings"]) + 1
            )
        if payload.get("weakening"):
            self.association_metrics["weakenings"] = int(self.association_metrics["weakenings"]) + 1
        if payload.get("action") == "reactivate" or payload.get("reactivation"):
            self.association_metrics["reactivations"] = (
                int(self.association_metrics["reactivations"]) + 1
            )
        if payload.get("distance") == "dormant":
            self.association_metrics["dormancies"] = int(self.association_metrics["dormancies"]) + 1
        if payload.get("neighborhood") or payload.get("clusters"):
            self.association_metrics["neighborhoods"] = (
                int(self.association_metrics["neighborhoods"]) + 1
            )
        if payload.get("clusters"):
            self.association_metrics["clusters"] = int(self.association_metrics["clusters"]) + 1
        if payload.get("goal_influenced"):
            self.association_metrics["goal_influenced"] = (
                int(self.association_metrics["goal_influenced"]) + 1
            )
        if payload.get("identity_influenced"):
            self.association_metrics["identity_influenced"] = (
                int(self.association_metrics["identity_influenced"]) + 1
            )
        if payload.get("temporal"):
            self.association_metrics["temporal"] = int(self.association_metrics["temporal"]) + 1

    def record_remembering(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.remembering_events.append(event)
        self._trim(self.remembering_events)
        action = payload.get("action")
        if action == "activation":
            self.remembering_metrics["activations"] = (
                int(self.remembering_metrics["activations"]) + 1
            )
            steps = int(payload.get("propagation_steps") or 0)
            if steps:
                self.remembering_metrics["propagations"] = (
                    int(self.remembering_metrics["propagations"]) + steps
                )
            decayed = int(payload.get("decayed") or 0)
            if decayed:
                self.remembering_metrics["decays"] = (
                    int(self.remembering_metrics["decays"]) + decayed
                )
        if payload.get("reconstruction") or action == "reconstruction":
            self.remembering_metrics["reconstructions"] = (
                int(self.remembering_metrics["reconstructions"]) + 1
            )
        if payload.get("ambiguity") or payload.get("ambiguous"):
            self.remembering_metrics["ambiguities"] = (
                int(self.remembering_metrics["ambiguities"]) + 1
            )
        participants = int(payload.get("experience_participants") or 0)
        if participants:
            self.remembering_metrics["experience_participants"] = (
                int(self.remembering_metrics["experience_participants"]) + participants
            )
        if payload.get("goal_influenced"):
            self.remembering_metrics["goal_influenced"] = (
                int(self.remembering_metrics["goal_influenced"]) + 1
            )
        if payload.get("identity_influenced"):
            self.remembering_metrics["identity_influenced"] = (
                int(self.remembering_metrics["identity_influenced"]) + 1
            )
        if payload.get("context_influenced"):
            self.remembering_metrics["context_influenced"] = (
                int(self.remembering_metrics["context_influenced"]) + 1
            )
        if payload.get("working_influenced"):
            self.remembering_metrics["working_influenced"] = (
                int(self.remembering_metrics["working_influenced"]) + 1
            )

    def record_reflection(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.reflection_events.append(event)
        self._trim(self.reflection_events)
        if payload.get("reflection") or payload.get("action") == "evaluation":
            self.reflection_metrics["reflections"] = (
                int(self.reflection_metrics["reflections"]) + 1
            )
        if payload.get("contradiction"):
            self.reflection_metrics["contradictions"] = (
                int(self.reflection_metrics["contradictions"]) + 1
            )
        if payload.get("pattern"):
            self.reflection_metrics["patterns"] = int(self.reflection_metrics["patterns"]) + 1
        if payload.get("question"):
            self.reflection_metrics["questions"] = int(self.reflection_metrics["questions"]) + 1
        if payload.get("hypothesis"):
            self.reflection_metrics["hypotheses"] = (
                int(self.reflection_metrics["hypotheses"]) + 1
            )
        if payload.get("insufficient_evidence"):
            self.reflection_metrics["insufficient_evidence"] = (
                int(self.reflection_metrics["insufficient_evidence"]) + 1
            )
        if payload.get("activation_reused"):
            self.reflection_metrics["activation_reused"] = (
                int(self.reflection_metrics["activation_reused"]) + 1
            )
        if payload.get("reflective_experience_id"):
            self.reflection_metrics["reflective_experiences"] = (
                int(self.reflection_metrics["reflective_experiences"]) + 1
            )

    def record_learning(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.learning_events.append(event)
        self._trim(self.learning_events)
        self.learning_metrics["events"] = int(self.learning_metrics["events"]) + 1
        if payload.get("apply"):
            self.learning_metrics["applied"] = int(self.learning_metrics["applied"]) + 1
        if payload.get("propose"):
            self.learning_metrics["proposed"] = int(self.learning_metrics["proposed"]) + 1
        if payload.get("abstain"):
            self.learning_metrics["abstained"] = int(self.learning_metrics["abstained"]) + 1
        if payload.get("rollback"):
            self.learning_metrics["rollbacks"] = int(self.learning_metrics["rollbacks"]) + 1
        if payload.get("assent"):
            self.learning_metrics["assents"] = int(self.learning_metrics["assents"]) + 1
        if payload.get("reject"):
            self.learning_metrics["rejects"] = int(self.learning_metrics["rejects"]) + 1
        if payload.get("concept_evolution"):
            self.learning_metrics["concept_evolution"] = (
                int(self.learning_metrics["concept_evolution"]) + 1
            )
        if payload.get("association_evolution"):
            self.learning_metrics["association_evolution"] = (
                int(self.learning_metrics["association_evolution"]) + 1
            )
        if payload.get("identity_evolution"):
            self.learning_metrics["identity_evolution"] = (
                int(self.learning_metrics["identity_evolution"]) + 1
            )
        if payload.get("confidence_evolution"):
            self.learning_metrics["confidence_evolution"] = (
                int(self.learning_metrics["confidence_evolution"]) + 1
            )
        if payload.get("generalization"):
            self.learning_metrics["generalization"] = (
                int(self.learning_metrics["generalization"]) + 1
            )
        if payload.get("transfer"):
            self.learning_metrics["transfer"] = int(self.learning_metrics["transfer"]) + 1

    def record_offline(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.offline_events.append(event)
        self._trim(self.offline_events)
        self.offline_metrics["events"] = int(self.offline_metrics["events"]) + 1
        if payload.get("replay"):
            self.offline_metrics["replays"] = int(self.offline_metrics["replays"]) + 1
        if payload.get("consolidate"):
            self.offline_metrics["consolidations"] = (
                int(self.offline_metrics["consolidations"]) + 1
            )
        if payload.get("proposal") or payload.get("action") == "abstraction_proposal":
            self.offline_metrics["abstractions"] = int(self.offline_metrics["abstractions"]) + 1
            self.offline_metrics["proposals"] = int(self.offline_metrics["proposals"]) + 1
        if payload.get("cool"):
            self.offline_metrics["cools"] = int(self.offline_metrics["cools"]) + 1
        if payload.get("stabilize"):
            self.offline_metrics["stabilizations"] = (
                int(self.offline_metrics["stabilizations"]) + 1
            )

    def record_attention(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.attention_events.append(event)
        self._trim(self.attention_events)
        self.attention_metrics["events"] = int(self.attention_metrics["events"]) + 1
        if payload.get("allocate"):
            self.attention_metrics["allocations"] = (
                int(self.attention_metrics["allocations"]) + 1
            )
        if payload.get("invest"):
            self.attention_metrics["investments"] = (
                int(self.attention_metrics["investments"]) + 1
            )
        if payload.get("priority_evolution"):
            self.attention_metrics["priority_evolution"] = (
                int(self.attention_metrics["priority_evolution"]) + 1
            )

    def record_forgetting(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.forgetting_events.append(event)
        self._trim(self.forgetting_events)
        self.forgetting_metrics["events"] = int(self.forgetting_metrics["events"]) + 1
        if payload.get("cool"):
            cool_n = int(payload.get("cool") or 1)
            self.forgetting_metrics["cools"] = int(self.forgetting_metrics["cools"]) + cool_n
        if payload.get("reactivate"):
            self.forgetting_metrics["reactivations"] = (
                int(self.forgetting_metrics["reactivations"]) + 1
            )
        if payload.get("dormancy"):
            self.forgetting_metrics["dormancies"] = (
                int(self.forgetting_metrics["dormancies"]) + 1
            )
        if payload.get("accessibility_evolution"):
            self.forgetting_metrics["accessibility_evolution"] = (
                int(self.forgetting_metrics["accessibility_evolution"]) + 1
            )
        if payload.get("proposal"):
            self.forgetting_metrics["proposals"] = (
                int(self.forgetting_metrics["proposals"]) + 1
            )
        if payload.get("resist"):
            self.forgetting_metrics["resists"] = int(self.forgetting_metrics["resists"]) + 1

    def record_prediction(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.prediction_events.append(event)
        self._trim(self.prediction_events)
        self.prediction_metrics["events"] = int(self.prediction_metrics["events"]) + 1
        if payload.get("predict"):
            self.prediction_metrics["predictions"] = (
                int(self.prediction_metrics["predictions"]) + 1
            )
        if payload.get("evaluate"):
            self.prediction_metrics["evaluations"] = (
                int(self.prediction_metrics["evaluations"]) + 1
            )
        if payload.get("confidence") is not None:
            self.prediction_metrics["last_confidence"] = float(payload["confidence"])
        if payload.get("confidence_after") is not None:
            self.prediction_metrics["last_confidence"] = float(payload["confidence_after"])
        if payload.get("accuracy") is not None:
            self.prediction_metrics["last_accuracy"] = float(payload["accuracy"])

    def record_simulation(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.simulation_events.append(event)
        self._trim(self.simulation_events)
        self.simulation_metrics["events"] = int(self.simulation_metrics["events"]) + 1
        if payload.get("simulate"):
            self.simulation_metrics["simulations"] = (
                int(self.simulation_metrics["simulations"]) + 1
            )
            self.simulation_metrics["branches"] = (
                int(self.simulation_metrics["branches"]) + 1
            )
        steps = int(payload.get("steps") or 0)
        if steps:
            self.simulation_metrics["hypothetical_steps"] = (
                int(self.simulation_metrics["hypothetical_steps"]) + steps
            )

    def record_recombination(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.recombination_events.append(event)
        self._trim(self.recombination_events)
        self.recombination_metrics["events"] = int(self.recombination_metrics["events"]) + 1
        if payload.get("recombine"):
            self.recombination_metrics["recombinations"] = (
                int(self.recombination_metrics["recombinations"]) + 1
            )
        if payload.get("novelty") is not None:
            self.recombination_metrics["last_novelty"] = float(payload["novelty"])

    def record_analogy(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.analogy_events.append(event)
        self._trim(self.analogy_events)
        self.analogy_metrics["events"] = int(self.analogy_metrics["events"]) + 1
        if payload.get("analogy"):
            self.analogy_metrics["mappings"] = int(self.analogy_metrics["mappings"]) + 1
        if payload.get("transfer"):
            self.analogy_metrics["transfers"] = int(self.analogy_metrics["transfers"]) + 1
        if payload.get("confidence") is not None:
            self.analogy_metrics["last_confidence"] = float(payload["confidence"])

    def record_storage(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.storage_events.append(event)
        self._trim(self.storage_events)
        self.storage_metrics["events"] = int(self.storage_metrics["events"]) + 1
        action = str(payload.get("action", ""))
        key = {
            "flush": "flushes",
            "export": "exports",
            "import": "imports",
            "backup": "backups",
            "restore": "restores",
            "verify": "verifies",
        }.get(action)
        if key:
            self.storage_metrics[key] = int(self.storage_metrics[key]) + 1

    def record_provenance(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.provenance_events.append(event)
        self._trim(self.provenance_events)
        self.provenance_metrics["events"] = int(self.provenance_metrics["events"]) + 1
        if payload.get("action") == "stamp" or payload.get("stamp"):
            self.provenance_metrics["stamps"] = int(self.provenance_metrics["stamps"]) + int(
                payload.get("count") or 1
            )

    def record_shadow(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.shadow_events.append(event)
        self._trim(self.shadow_events)
        self.shadow_metrics["events"] = int(self.shadow_metrics["events"]) + 1
        if payload.get("agree"):
            self.shadow_metrics["agreements"] = int(self.shadow_metrics["agreements"]) + 1
        if payload.get("disagree"):
            self.shadow_metrics["disagreements"] = (
                int(self.shadow_metrics["disagreements"]) + 1
            )

    def record_reconciliation(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.reconciliation_events.append(event)
        self._trim(self.reconciliation_events)
        self.reconciliation_metrics["events"] = int(self.reconciliation_metrics["events"]) + 1
        if payload.get("reconcile"):
            self.reconciliation_metrics["reconciliations"] = (
                int(self.reconciliation_metrics["reconciliations"]) + 1
            )
        if payload.get("conflict"):
            self.reconciliation_metrics["conflicts"] = (
                int(self.reconciliation_metrics["conflicts"]) + 1
            )
        if payload.get("corroboration"):
            self.reconciliation_metrics["corroborations"] = (
                int(self.reconciliation_metrics["corroborations"]) + 1
            )
        if payload.get("confidence_before") is not None:
            self.reconciliation_metrics["last_confidence_before"] = float(
                payload["confidence_before"]
            )
        if payload.get("confidence_after") is not None:
            self.reconciliation_metrics["last_confidence_after"] = float(
                payload["confidence_after"]
            )

    def record_confidence_organ(self, **payload: Any) -> None:
        event = {"timestamp": time(), **payload}
        self.confidence_organ_events.append(event)
        self._trim(self.confidence_organ_events)
        self.confidence_organ_metrics["events"] = (
            int(self.confidence_organ_metrics["events"]) + 1
        )
        if payload.get("evolve"):
            self.confidence_organ_metrics["evolutions"] = (
                int(self.confidence_organ_metrics["evolutions"]) + 1
            )
            if str(payload.get("source", "")) == "reconciliation":
                self.confidence_organ_metrics["recalibrations"] = (
                    int(self.confidence_organ_metrics["recalibrations"]) + 1
                )
        if payload.get("before") is not None:
            self.confidence_organ_metrics["last_before"] = float(payload["before"])
        if payload.get("after") is not None:
            self.confidence_organ_metrics["last_after"] = float(payload["after"])

    def snapshot(self) -> dict[str, Any]:
        """Public validation snapshot — metadata only, no chain-of-thought."""
        return {
            "schema": "acm.validation/0.13",
            "counts": {
                "activations": len(self.activations),
                "confidence_deltas": len(self.confidence_deltas),
                "association_changes": len(self.association_changes),
                "lifecycle": len(self.lifecycle),
                "working_transitions": len(self.working_transitions),
                "reconsolidations": len(self.reconsolidations),
                "sleep_events": len(self.sleep_events),
                "identity_touches": len(self.identity_touches),
                "experience_events": len(self.experience_events),
                "concept_events": len(self.concept_events),
                "association_events": len(self.association_events),
                "remembering_events": len(self.remembering_events),
                "reflection_events": len(self.reflection_events),
                "learning_events": len(self.learning_events),
                "offline_events": len(self.offline_events),
                "attention_events": len(self.attention_events),
                "forgetting_events": len(self.forgetting_events),
                "prediction_events": len(self.prediction_events),
                "simulation_events": len(self.simulation_events),
                "recombination_events": len(self.recombination_events),
                "analogy_events": len(self.analogy_events),
                "reconciliation_events": len(self.reconciliation_events),
                "confidence_organ_events": len(self.confidence_organ_events),
                "storage_events": len(self.storage_events),
                "provenance_events": len(self.provenance_events),
                "shadow_events": len(self.shadow_events),
            },
            "identity": {
                "growth": self.identity_metrics["growth"],
                "stability": self.identity_metrics["stability"],
                "change": self.identity_metrics["change"],
                "confidence": self.identity_metrics["last_confidence"],
                "influence": self.identity_metrics["influence"],
                "lineage": self.identity_metrics["lineage_events"],
                "evolution": {
                    "touches": len(self.identity_touches),
                    "growth": self.identity_metrics["growth"],
                    "stability": self.identity_metrics["stability"],
                    "change": self.identity_metrics["change"],
                    "influence": self.identity_metrics["influence"],
                },
            },
            "experience": {
                "births": self.experience_metrics["births"],
                "lineage": self.experience_metrics["lineage"],
                "salience_evolutions": self.experience_metrics["salience_evolutions"],
                "temporal_links": self.experience_metrics["temporal_links"],
                "lifecycle": self.experience_metrics["lifecycle"],
                "multimodal": self.experience_metrics["multimodal"],
                "identity_influenced": self.experience_metrics["identity_influenced"],
                "goal_influenced": self.experience_metrics["goal_influenced"],
                "context_events": sum(
                    1 for e in self.experience_events if e.get("context_tags")
                ),
            },
            "concept": {
                "births": self.concept_metrics["births"],
                "nuclei": self.concept_metrics["nuclei"],
                "strengthenings": self.concept_metrics["strengthenings"],
                "weakenings": self.concept_metrics["weakenings"],
                "maturity": self.concept_metrics["maturity_changes"],
                "hierarchy": self.concept_metrics["hierarchy"],
                "abstraction": self.concept_metrics["abstractions"],
                "merge_proposals": self.concept_metrics["merges"],
                "split_proposals": self.concept_metrics["splits"],
                "prototypes": self.concept_metrics["prototypes"],
                "evolution": {
                    "touches": len(self.concept_events),
                    "births": self.concept_metrics["births"],
                    "strengthenings": self.concept_metrics["strengthenings"],
                    "weakenings": self.concept_metrics["weakenings"],
                },
            },
            "association": {
                "births": self.association_metrics["births"],
                "strengthenings": self.association_metrics["strengthenings"],
                "weakenings": self.association_metrics["weakenings"],
                "dormancies": self.association_metrics["dormancies"],
                "reactivations": self.association_metrics["reactivations"],
                "neighborhoods": self.association_metrics["neighborhoods"],
                "clusters": self.association_metrics["clusters"],
                "goal_influenced": self.association_metrics["goal_influenced"],
                "identity_influenced": self.association_metrics["identity_influenced"],
                "temporal": self.association_metrics["temporal"],
                "asymmetric_births": self.association_metrics["asymmetric_births"],
                "evolution": {
                    "touches": len(self.association_events),
                    "births": self.association_metrics["births"],
                    "strengthenings": self.association_metrics["strengthenings"],
                    "weakenings": self.association_metrics["weakenings"],
                },
            },
            "remembering": {
                "reconstructions": self.remembering_metrics["reconstructions"],
                "activations": self.remembering_metrics["activations"],
                "ambiguities": self.remembering_metrics["ambiguities"],
                "propagations": self.remembering_metrics["propagations"],
                "decays": self.remembering_metrics["decays"],
                "experience_participants": self.remembering_metrics["experience_participants"],
                "goal_influenced": self.remembering_metrics["goal_influenced"],
                "identity_influenced": self.remembering_metrics["identity_influenced"],
                "context_influenced": self.remembering_metrics["context_influenced"],
                "working_influenced": self.remembering_metrics["working_influenced"],
                "evolution": {
                    "touches": len(self.remembering_events),
                    "reconstructions": self.remembering_metrics["reconstructions"],
                    "activations": self.remembering_metrics["activations"],
                    "ambiguities": self.remembering_metrics["ambiguities"],
                },
            },
            "activations": [asdict(a) for a in self.activations[-40:]],
            "confidence_deltas": [asdict(c) for c in self.confidence_deltas[-40:]],
            "association_changes": [asdict(a) for a in self.association_changes[-40:]],
            "lifecycle": [asdict(e) for e in self.lifecycle[-40:]],
            "working_transitions": [asdict(w) for w in self.working_transitions[-40:]],
            "reconsolidations": deepcopy(self.reconsolidations[-40:]),
            "sleep_events": deepcopy(self.sleep_events[-40:]),
            "identity_touches": deepcopy(self.identity_touches[-40:]),
            "experience_events": deepcopy(self.experience_events[-40:]),
            "concept_events": deepcopy(self.concept_events[-40:]),
            "association_events": deepcopy(self.association_events[-40:]),
            "remembering_events": deepcopy(self.remembering_events[-40:]),
            "reflection": {
                "reflections": self.reflection_metrics["reflections"],
                "contradictions": self.reflection_metrics["contradictions"],
                "patterns": self.reflection_metrics["patterns"],
                "questions": self.reflection_metrics["questions"],
                "hypotheses": self.reflection_metrics["hypotheses"],
                "insufficient_evidence": self.reflection_metrics["insufficient_evidence"],
                "activation_reused": self.reflection_metrics["activation_reused"],
                "reflective_experiences": self.reflection_metrics["reflective_experiences"],
                "evolution": {
                    "touches": len(self.reflection_events),
                    "reflections": self.reflection_metrics["reflections"],
                    "contradictions": self.reflection_metrics["contradictions"],
                    "questions": self.reflection_metrics["questions"],
                },
            },
            "reflection_events": deepcopy(self.reflection_events[-40:]),
            "learning": {
                "events": self.learning_metrics["events"],
                "applied": self.learning_metrics["applied"],
                "proposed": self.learning_metrics["proposed"],
                "abstained": self.learning_metrics["abstained"],
                "rollbacks": self.learning_metrics["rollbacks"],
                "assents": self.learning_metrics["assents"],
                "rejects": self.learning_metrics["rejects"],
                "concept_evolution": self.learning_metrics["concept_evolution"],
                "association_evolution": self.learning_metrics["association_evolution"],
                "identity_evolution": self.learning_metrics["identity_evolution"],
                "confidence_evolution": self.learning_metrics["confidence_evolution"],
                "generalization": self.learning_metrics["generalization"],
                "transfer": self.learning_metrics["transfer"],
                "evolution": {
                    "touches": len(self.learning_events),
                    "applied": self.learning_metrics["applied"],
                    "proposed": self.learning_metrics["proposed"],
                    "abstained": self.learning_metrics["abstained"],
                },
            },
            "learning_events": deepcopy(self.learning_events[-40:]),
            "offline": {
                "events": self.offline_metrics["events"],
                "replays": self.offline_metrics["replays"],
                "consolidations": self.offline_metrics["consolidations"],
                "abstractions": self.offline_metrics["abstractions"],
                "cools": self.offline_metrics["cools"],
                "stabilizations": self.offline_metrics["stabilizations"],
                "proposals": self.offline_metrics["proposals"],
                "evolution": {
                    "touches": len(self.offline_events),
                    "replays": self.offline_metrics["replays"],
                    "consolidations": self.offline_metrics["consolidations"],
                },
            },
            "offline_events": deepcopy(self.offline_events[-40:]),
            "attention": {
                "events": self.attention_metrics["events"],
                "allocations": self.attention_metrics["allocations"],
                "investments": self.attention_metrics["investments"],
                "priority_evolution": self.attention_metrics["priority_evolution"],
                "evolution": {
                    "touches": len(self.attention_events),
                    "allocations": self.attention_metrics["allocations"],
                    "investments": self.attention_metrics["investments"],
                },
            },
            "attention_events": deepcopy(self.attention_events[-40:]),
            "forgetting": {
                "events": self.forgetting_metrics["events"],
                "cools": self.forgetting_metrics["cools"],
                "reactivations": self.forgetting_metrics["reactivations"],
                "dormancies": self.forgetting_metrics["dormancies"],
                "accessibility_evolution": self.forgetting_metrics["accessibility_evolution"],
                "proposals": self.forgetting_metrics["proposals"],
                "resists": self.forgetting_metrics["resists"],
                "evolution": {
                    "touches": len(self.forgetting_events),
                    "cools": self.forgetting_metrics["cools"],
                    "reactivations": self.forgetting_metrics["reactivations"],
                },
            },
            "forgetting_events": deepcopy(self.forgetting_events[-40:]),
            "prediction": {
                "events": self.prediction_metrics["events"],
                "predictions": self.prediction_metrics["predictions"],
                "evaluations": self.prediction_metrics["evaluations"],
                "confidence": self.prediction_metrics["last_confidence"],
                "accuracy": self.prediction_metrics["last_accuracy"],
                "evolution": {
                    "touches": len(self.prediction_events),
                    "predictions": self.prediction_metrics["predictions"],
                    "evaluations": self.prediction_metrics["evaluations"],
                },
            },
            "prediction_events": deepcopy(self.prediction_events[-40:]),
            "simulation": {
                "events": self.simulation_metrics["events"],
                "simulations": self.simulation_metrics["simulations"],
                "hypothetical_steps": self.simulation_metrics["hypothetical_steps"],
                "branches": self.simulation_metrics["branches"],
                "evolution": {
                    "touches": len(self.simulation_events),
                    "simulations": self.simulation_metrics["simulations"],
                },
            },
            "simulation_events": deepcopy(self.simulation_events[-40:]),
            "recombination": {
                "events": self.recombination_metrics["events"],
                "recombinations": self.recombination_metrics["recombinations"],
                "novelty": self.recombination_metrics["last_novelty"],
                "evolution": {
                    "touches": len(self.recombination_events),
                    "recombinations": self.recombination_metrics["recombinations"],
                },
            },
            "recombination_events": deepcopy(self.recombination_events[-40:]),
            "analogy": {
                "events": self.analogy_metrics["events"],
                "mappings": self.analogy_metrics["mappings"],
                "transfers": self.analogy_metrics["transfers"],
                "confidence": self.analogy_metrics["last_confidence"],
                "evolution": {
                    "touches": len(self.analogy_events),
                    "mappings": self.analogy_metrics["mappings"],
                },
            },
            "analogy_events": deepcopy(self.analogy_events[-40:]),
            "reconciliation": {
                "events": self.reconciliation_metrics["events"],
                "reconciliations": self.reconciliation_metrics["reconciliations"],
                "conflicts": self.reconciliation_metrics["conflicts"],
                "corroborations": self.reconciliation_metrics["corroborations"],
                "confidence_before": self.reconciliation_metrics["last_confidence_before"],
                "confidence_after": self.reconciliation_metrics["last_confidence_after"],
                "evolution": {
                    "touches": len(self.reconciliation_events),
                    "reconciliations": self.reconciliation_metrics["reconciliations"],
                    "conflicts": self.reconciliation_metrics["conflicts"],
                },
            },
            "reconciliation_events": deepcopy(self.reconciliation_events[-40:]),
            "confidence": {
                "events": self.confidence_organ_metrics["events"],
                "evolutions": self.confidence_organ_metrics["evolutions"],
                "recalibrations": self.confidence_organ_metrics["recalibrations"],
                "before": self.confidence_organ_metrics["last_before"],
                "after": self.confidence_organ_metrics["last_after"],
                "evolution": {
                    "touches": len(self.confidence_organ_events),
                    "evolutions": self.confidence_organ_metrics["evolutions"],
                    "recalibrations": self.confidence_organ_metrics["recalibrations"],
                },
            },
            "confidence_organ_events": deepcopy(self.confidence_organ_events[-40:]),
            "storage": {
                "events": self.storage_metrics["events"],
                "flushes": self.storage_metrics["flushes"],
                "exports": self.storage_metrics["exports"],
                "imports": self.storage_metrics["imports"],
                "backups": self.storage_metrics["backups"],
                "restores": self.storage_metrics["restores"],
                "verifies": self.storage_metrics["verifies"],
            },
            "storage_events": deepcopy(self.storage_events[-40:]),
            "provenance": {
                "events": self.provenance_metrics["events"],
                "stamps": self.provenance_metrics["stamps"],
            },
            "provenance_events": deepcopy(self.provenance_events[-40:]),
            "shadow": {
                "events": self.shadow_metrics["events"],
                "agreements": self.shadow_metrics["agreements"],
                "disagreements": self.shadow_metrics["disagreements"],
            },
            "shadow_events": deepcopy(self.shadow_events[-40:]),
        }

    def reset(self) -> None:
        self.activations.clear()
        self.confidence_deltas.clear()
        self.association_changes.clear()
        self.lifecycle.clear()
        self.working_transitions.clear()
        self.reconsolidations.clear()
        self.sleep_events.clear()
        self.identity_touches.clear()
        self.experience_events.clear()
        self.concept_events.clear()
        self.association_events.clear()
        self.remembering_events.clear()
        self.reflection_events.clear()
        self.learning_events.clear()
        self.offline_events.clear()
        self.attention_events.clear()
        self.forgetting_events.clear()
        self.prediction_events.clear()
        self.simulation_events.clear()
        self.recombination_events.clear()
        self.analogy_events.clear()
        self.reconciliation_events.clear()
        self.confidence_organ_events.clear()
        self.storage_events.clear()
        self.provenance_events.clear()
        self.shadow_events.clear()
        self.identity_metrics = {
            "growth": 0,
            "stability": 0,
            "change": 0,
            "influence": 0,
            "lineage_events": 0,
            "last_confidence": 0.0,
        }
        self.experience_metrics = {
            "births": 0,
            "lineage": 0,
            "salience_evolutions": 0,
            "temporal_links": 0,
            "lifecycle": 0,
            "multimodal": 0,
            "identity_influenced": 0,
            "goal_influenced": 0,
        }
        self.concept_metrics = {
            "births": 0,
            "nuclei": 0,
            "strengthenings": 0,
            "weakenings": 0,
            "maturity_changes": 0,
            "abstractions": 0,
            "hierarchy": 0,
            "merges": 0,
            "splits": 0,
            "prototypes": 0,
        }
        self.association_metrics = {
            "births": 0,
            "strengthenings": 0,
            "weakenings": 0,
            "dormancies": 0,
            "reactivations": 0,
            "neighborhoods": 0,
            "clusters": 0,
            "goal_influenced": 0,
            "identity_influenced": 0,
            "temporal": 0,
            "asymmetric_births": 0,
        }
        self.remembering_metrics = {
            "reconstructions": 0,
            "activations": 0,
            "ambiguities": 0,
            "propagations": 0,
            "decays": 0,
            "experience_participants": 0,
            "goal_influenced": 0,
            "identity_influenced": 0,
            "context_influenced": 0,
            "working_influenced": 0,
        }
        self.reflection_metrics = {
            "reflections": 0,
            "contradictions": 0,
            "patterns": 0,
            "questions": 0,
            "hypotheses": 0,
            "insufficient_evidence": 0,
            "activation_reused": 0,
            "reflective_experiences": 0,
        }
        self.learning_metrics = {
            "events": 0,
            "applied": 0,
            "proposed": 0,
            "abstained": 0,
            "rollbacks": 0,
            "assents": 0,
            "rejects": 0,
            "concept_evolution": 0,
            "association_evolution": 0,
            "identity_evolution": 0,
            "confidence_evolution": 0,
            "generalization": 0,
            "transfer": 0,
        }
        self.offline_metrics = {
            "events": 0,
            "replays": 0,
            "consolidations": 0,
            "abstractions": 0,
            "cools": 0,
            "stabilizations": 0,
            "proposals": 0,
        }
        self.attention_metrics = {
            "events": 0,
            "allocations": 0,
            "investments": 0,
            "priority_evolution": 0,
        }
        self.forgetting_metrics = {
            "events": 0,
            "cools": 0,
            "reactivations": 0,
            "dormancies": 0,
            "accessibility_evolution": 0,
            "proposals": 0,
            "resists": 0,
        }
        self.prediction_metrics = {
            "events": 0,
            "predictions": 0,
            "evaluations": 0,
            "last_confidence": 0.0,
            "last_accuracy": 0.0,
        }
        self.simulation_metrics = {
            "events": 0,
            "simulations": 0,
            "hypothetical_steps": 0,
            "branches": 0,
        }
        self.recombination_metrics = {
            "events": 0,
            "recombinations": 0,
            "last_novelty": 0.0,
        }
        self.analogy_metrics = {
            "events": 0,
            "mappings": 0,
            "transfers": 0,
            "last_confidence": 0.0,
        }
        self.reconciliation_metrics = {
            "events": 0,
            "reconciliations": 0,
            "conflicts": 0,
            "corroborations": 0,
            "last_confidence_before": 0.0,
            "last_confidence_after": 0.0,
        }
        self.confidence_organ_metrics = {
            "events": 0,
            "evolutions": 0,
            "recalibrations": 0,
            "last_before": 0.0,
            "last_after": 0.0,
        }
        self.storage_metrics = {
            "events": 0,
            "flushes": 0,
            "exports": 0,
            "imports": 0,
            "backups": 0,
            "restores": 0,
            "verifies": 0,
        }
        self.provenance_metrics = {
            "events": 0,
            "stamps": 0,
        }
        self.shadow_metrics = {
            "events": 0,
            "agreements": 0,
            "disagreements": 0,
        }
