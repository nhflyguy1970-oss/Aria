"""Serialize / deserialize CognitiveStore state — technology-agnostic codec."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from hashlib import sha256
from typing import Any

from acm.analogy.model import AnalogyAlignment, AnalogyMapping
from acm.associations.model import Association, AssociationStage, RelationKind
from acm.attention.model import PriorityEvent
from acm.concepts.model import Concept, ConceptStage, Prototype
from acm.confidence.model import ConfidenceEvent
from acm.core.store import CognitiveStore, Goal
from acm.experiences.kinds import CognitiveKind, ExternalKind
from acm.experiences.model import Experience
from acm.experiences.salience import SalienceVector
from acm.forgetting.model import AccessibilityEvent
from acm.learning.model import Adaptation, AdaptationKind, AdaptationTarget, GovernanceClass
from acm.persistence.schema import CHECKSUM_ALGO, SCHEMA_VERSION, SNAPSHOT_FORMAT
from acm.prediction.model import PredictedOutcome, Prediction
from acm.provenance.model import ProvenanceRecord
from acm.recombination.model import RecombinedFragment, RecombinedMemory
from acm.reconciliation.model import ReconciliationRecord, ReconciliationStatus
from acm.simulation.model import HypotheticalStep, Simulation
from acm.types import Attribute, ConceptRole, EnvelopeRef


def _jsonable(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if is_dataclass(obj):
        return {k: _jsonable(v) for k, v in asdict(obj).items()}
    return str(obj)


def checksum_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def export_store(store: CognitiveStore) -> dict[str, Any]:
    """Export living store state to a versioned snapshot dict."""
    body = {
        "experiences": {k: _jsonable(v) for k, v in store.experiences.items()},
        "concepts": {k: _jsonable(v) for k, v in store.concepts.items()},
        "associations": {k: _jsonable(v) for k, v in store.associations.items()},
        "goals": {k: _jsonable(v) for k, v in store.goals.items()},
        "envelopes": {k: _jsonable(v) for k, v in store.envelopes.items()},
        "adaptations": {k: _jsonable(v) for k, v in store.adaptations.items()},
        "accessibility": dict(store.accessibility),
        "priority_events": [_jsonable(e) for e in store.priority_events],
        "accessibility_events": [_jsonable(e) for e in store.accessibility_events],
        "predictions": {k: _jsonable(v) for k, v in store.predictions.items()},
        "simulations": {k: _jsonable(v) for k, v in store.simulations.items()},
        "recombinations": {k: _jsonable(v) for k, v in store.recombinations.items()},
        "analogies": {k: _jsonable(v) for k, v in store.analogies.items()},
        "reconciliations": {k: _jsonable(v) for k, v in store.reconciliations.items()},
        "confidence_events": [_jsonable(e) for e in store.confidence_events],
        "provenance": {k: _jsonable(v) for k, v in store.provenance.items()},
    }
    payload = {
        "format": SNAPSHOT_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "checksum_algo": CHECKSUM_ALGO,
        "body": body,
    }
    payload["checksum"] = checksum_payload(body)
    return payload


def verify_snapshot(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("format") != SNAPSHOT_FORMAT:
        errors.append(f"unexpected format: {payload.get('format')}")
    if int(payload.get("schema_version") or 0) > SCHEMA_VERSION:
        errors.append("snapshot schema newer than runtime")
    body = payload.get("body")
    if not isinstance(body, dict):
        errors.append("missing body")
        return errors
    expected = payload.get("checksum")
    actual = checksum_payload(body)
    if expected and expected != actual:
        errors.append("checksum mismatch")
    return errors


def _attr(d: dict[str, Any]) -> Attribute:
    return Attribute(
        key=str(d.get("key", "")),
        value=str(d.get("value", "")),
        confidence=float(d.get("confidence", 0.7)),
        importance=float(d.get("importance", 0.5)),
        context_tags=tuple(d.get("context_tags") or ()),
        evidence_ids=list(d.get("evidence_ids") or []),
        active=bool(d.get("active", True)),
        version=int(d.get("version", 1)),
    )


def _experience(d: dict[str, Any]) -> Experience:
    sal = d.get("salience_birth") or {}
    if "composite" in sal:
        sal = {k: v for k, v in sal.items() if k != "composite"}
    meta = d.get("metadata") or ()
    if isinstance(meta, dict):
        meta = tuple((str(k), str(v)) for k, v in meta.items())
    return Experience(
        id=str(d["id"]),
        summary=str(d.get("summary", "")),
        sequence=int(d.get("sequence", 0)),
        t_start=float(d.get("t_start", 0.0)),
        t_encoded=float(d.get("t_encoded", d.get("t_start", 0.0))),
        external_kind=ExternalKind(d.get("external_kind", "text")),
        cognitive_kind=CognitiveKind(d.get("cognitive_kind", "observation")),
        salience_birth=SalienceVector(**{k: float(v) for k, v in sal.items()}),
        t_end=None if d.get("t_end") is None else float(d["t_end"]),
        context_tags=tuple(d.get("context_tags") or ()),
        goal_ids=tuple(d.get("goal_ids") or ()),
        envelope_ids=tuple(d.get("envelope_ids") or ()),
        concept_ids=tuple(d.get("concept_ids") or ()),
        parent_id=d.get("parent_id"),
        revises_id=d.get("revises_id"),
        reflects_on_id=d.get("reflects_on_id"),
        identity_influenced=bool(d.get("identity_influenced", False)),
        attention_class=str(d.get("attention_class", "default")),
        metadata=tuple(meta),
    )


def _concept(d: dict[str, Any]) -> Concept:
    proto = d.get("prototype") or {}
    return Concept(
        id=str(d["id"]),
        labels=list(d.get("labels") or []),
        role=ConceptRole(d.get("role", "entity")),
        attributes=[_attr(a) for a in (d.get("attributes") or [])],
        envelope_ids=list(d.get("envelope_ids") or []),
        strength=float(d.get("strength", 0.35)),
        importance=float(d.get("importance", 0.5)),
        confidence=float(d.get("confidence", 0.45)),
        access_count=int(d.get("access_count", 0)),
        first_seen=float(d.get("first_seen", 0.0)),
        last_activated=float(d.get("last_activated", 0.0)),
        provisional=bool(d.get("provisional", True)),
        active=bool(d.get("active", True)),
        identity=bool(d.get("identity", False)),
        stage=ConceptStage(d.get("stage", "nucleus")),
        evidence_ids=list(d.get("evidence_ids") or []),
        exemplar_ids=list(d.get("exemplar_ids") or []),
        instance_ids=list(d.get("instance_ids") or []),
        parent_ids=list(d.get("parent_ids") or []),
        child_ids=list(d.get("child_ids") or []),
        prototype=Prototype(
            features=dict(proto.get("features") or {}),
            feature_weights={k: float(v) for k, v in (proto.get("feature_weights") or {}).items()},
        ),
        metadata=dict(d.get("metadata") or {}),
    )


def import_store(payload: dict[str, Any], *, store: CognitiveStore | None = None) -> CognitiveStore:
    errors = verify_snapshot(payload)
    if errors:
        raise ValueError("; ".join(errors))
    # migrate older schemas if needed
    ver = int(payload.get("schema_version") or 1)
    body = payload["body"]
    if ver < SCHEMA_VERSION:
        body = migrate_body(body, from_version=ver, to_version=SCHEMA_VERSION)

    target = store or CognitiveStore()
    target.experiences.clear()
    target.concepts.clear()
    target.associations.clear()
    target.goals.clear()
    target.envelopes.clear()
    target.adaptations.clear()
    target.accessibility.clear()
    target.priority_events.clear()
    target.accessibility_events.clear()
    target.predictions.clear()
    target.simulations.clear()
    target.recombinations.clear()
    target.analogies.clear()
    target.reconciliations.clear()
    target.confidence_events.clear()
    target.provenance.clear()

    for eid, d in (body.get("experiences") or {}).items():
        target.experiences[str(eid)] = _experience(d)
    for cid, d in (body.get("concepts") or {}).items():
        target.concepts[str(cid)] = _concept(d)
    for aid, d in (body.get("associations") or {}).items():
        target.associations[str(aid)] = Association(
            id=str(d["id"]),
            source_id=str(d["source_id"]),
            target_id=str(d["target_id"]),
            relation=RelationKind(d.get("relation", "related_to")),
            strength_forward=float(d.get("strength_forward", 0.4)),
            strength_backward=float(d.get("strength_backward", 0.25)),
            confidence=float(d.get("confidence", 0.5)),
            stage=AssociationStage(d.get("stage", "nascent")),
            evidence_ids=list(d.get("evidence_ids") or []),
            context_tags=tuple(d.get("context_tags") or ()),
            goal_influenced=bool(d.get("goal_influenced", False)),
            identity_influenced=bool(d.get("identity_influenced", False)),
            temporal_weight=float(d.get("temporal_weight", 0.0)),
            access_count=int(d.get("access_count", 0)),
            first_seen=float(d.get("first_seen", 0.0)),
            last_activated=float(d.get("last_activated", 0.0)),
            metadata=dict(d.get("metadata") or {}),
        )
    for gid, d in (body.get("goals") or {}).items():
        target.goals[str(gid)] = Goal(
            id=str(d["id"]),
            title=str(d.get("title", "")),
            status=str(d.get("status", "active")),
            importance=float(d.get("importance", 0.6)),
            created=float(d.get("created", 0.0)),
            completed=float(d.get("completed", 0.0)),
            metadata=dict(d.get("metadata") or {}),
        )
    for eid, d in (body.get("envelopes") or {}).items():
        target.envelopes[str(eid)] = EnvelopeRef(
            content_hash=str(d.get("content_hash", "")),
            kind=str(d.get("kind", "text")),
            mime=str(d.get("mime", "")),
            metadata=dict(d.get("metadata") or {}),
        )
    for adid, d in (body.get("adaptations") or {}).items():
        target.adaptations[str(adid)] = Adaptation(
            id=str(d["id"]),
            kind=AdaptationKind(d.get("kind", "reinforce")),
            target_kind=AdaptationTarget(d.get("target_kind", "concept")),
            target_id=str(d.get("target_id", "")),
            governance=GovernanceClass(d.get("governance", "automatic")),
            before=dict(d.get("before") or {}),
            after=dict(d.get("after") or {}),
            reflective_experience_ids=list(d.get("reflective_experience_ids") or []),
            evidence_experience_ids=list(d.get("evidence_experience_ids") or []),
            sleep_batch_id=str(d.get("sleep_batch_id", "")),
            summary=str(d.get("summary", "")),
            attribute_key=str(d.get("attribute_key", "")),
            created=float(d.get("created", 0.0)),
            applied=bool(d.get("applied", False)),
            metadata=dict(d.get("metadata") or {}),
        )
    target.accessibility.update(
        {str(k): str(v) for k, v in (body.get("accessibility") or {}).items()}
    )
    for e in body.get("priority_events") or []:
        before = float(e.get("before", 0.0))
        after = float(e.get("after", 0.0))
        factors = e.get("factors") or ()
        target.priority_events.append(
            PriorityEvent(
                timestamp=float(e.get("timestamp", 0.0)),
                concept_id=str(e.get("concept_id", "")),
                before=before,
                after=after,
                delta=float(e.get("delta", after - before)),
                source=str(e.get("source", "")),
                factors=tuple(factors),
                summary=str(e.get("summary", "")),
            )
        )
    for e in body.get("accessibility_events") or []:
        target.accessibility_events.append(
            AccessibilityEvent(
                timestamp=float(e.get("timestamp", 0.0)),
                target_kind=str(e.get("target_kind", "concept")),
                target_id=str(e.get("target_id", e.get("concept_id", ""))),
                before=str(e.get("before", "")),
                after=str(e.get("after", "")),
                source=str(e.get("source", "")),
                summary=str(e.get("summary", "")),
                metadata=dict(e.get("metadata") or {}),
            )
        )
    for pid, d in (body.get("predictions") or {}).items():
        outcomes = [
            PredictedOutcome(
                concept_id=str(o.get("concept_id", "")),
                label=str(o.get("label", "")),
                probability=float(o.get("probability", 0.0)),
                support=list(o.get("support") or []),
                why=list(o.get("why") or []),
            )
            for o in (d.get("outcomes") or [])
        ]
        target.predictions[str(pid)] = Prediction(
            id=str(d["id"]),
            cue=str(d.get("cue", "")),
            outcomes=outcomes,
            confidence=float(d.get("confidence", 0.0)),
            created=float(d.get("created", 0.0)),
            evaluated=bool(d.get("evaluated", False)),
            accuracy=None if d.get("accuracy") is None else float(d["accuracy"]),
            hypothetical=bool(d.get("hypothetical", False)),
            source_concept_ids=list(d.get("source_concept_ids") or []),
            metadata=dict(d.get("metadata") or {}),
        )
    for sid, d in (body.get("simulations") or {}).items():
        steps = [
            HypotheticalStep(
                index=int(s.get("index", 0)),
                concept_id=str(s.get("concept_id", "")),
                label=str(s.get("label", "")),
                summary=str(s.get("summary", s.get("description", ""))),
                source_experience_ids=list(s.get("source_experience_ids") or []),
                hypothetical=True,
            )
            for s in (d.get("steps") or [])
        ]
        target.simulations[str(sid)] = Simulation(
            id=str(d["id"]),
            cue=str(d.get("cue", "")),
            branch=int(d.get("branch", 0)),
            steps=steps,
            confidence=float(d.get("confidence", 0.0)),
            created=float(d.get("created", 0.0)),
            source_concept_ids=list(d.get("source_concept_ids") or []),
            prediction_id=str(d.get("prediction_id", "")),
            hypothetical=True,
            metadata=dict(d.get("metadata") or {}),
        )
    for rid, d in (body.get("recombinations") or {}).items():
        fragments = []
        for f in d.get("fragments") or []:
            if isinstance(f, dict):
                fragments.append(
                    RecombinedFragment(
                        concept_id=str(f.get("concept_id", "")),
                        label=str(f.get("label", "")),
                        role=str(f.get("role", "blend")),
                        source_experience_ids=list(f.get("source_experience_ids") or []),
                    )
                )
        target.recombinations[str(rid)] = RecombinedMemory(
            id=str(d["id"]),
            cue=str(d.get("cue", "")),
            fragments=fragments,
            novelty=float(d.get("novelty", 0.0)),
            confidence=float(d.get("confidence", 0.0)),
            created=float(d.get("created", 0.0)),
            summary=str(d.get("summary", "")),
            domains=list(d.get("domains") or []),
            simulation_id=str(d.get("simulation_id", "")),
            prediction_id=str(d.get("prediction_id", "")),
            recombined=True,
            historical=False,
            metadata=dict(d.get("metadata") or {}),
        )
    for aid, d in (body.get("analogies") or {}).items():
        alignments = [
            AnalogyAlignment(
                source_concept_id=str(a.get("source_concept_id", "")),
                target_concept_id=str(a.get("target_concept_id", "")),
                source_label=str(a.get("source_label", "")),
                target_label=str(a.get("target_label", "")),
                relation=str(a.get("relation", "")),
                strength=float(a.get("strength", 0.0)),
                why=list(a.get("why") or []),
            )
            for a in (d.get("alignments") or [])
            if isinstance(a, dict)
        ]
        target.analogies[str(aid)] = AnalogyMapping(
            id=str(d["id"]),
            cue=str(d.get("cue", "")),
            source_id=str(d.get("source_id", "")),
            target_id=str(d.get("target_id", "")),
            source_label=str(d.get("source_label", "")),
            target_label=str(d.get("target_label", "")),
            confidence=float(d.get("confidence", 0.0)),
            alignments=alignments,
            created=float(d.get("created", 0.0)),
            transfer_summary=str(d.get("transfer_summary", "")),
            why=list(d.get("why") or []),
            metadata=dict(d.get("metadata") or {}),
        )
    for rid, d in (body.get("reconciliations") or {}).items():
        target.reconciliations[str(rid)] = ReconciliationRecord(
            id=str(d["id"]),
            cue=str(d.get("cue", "")),
            status=ReconciliationStatus(d.get("status", "unresolved")),
            subject_ids=list(d.get("subject_ids") or []),
            evidence_ids=list(d.get("evidence_ids") or []),
            conflicting_ids=list(d.get("conflicting_ids") or []),
            supporting_ids=list(d.get("supporting_ids") or []),
            confidence_before=float(d.get("confidence_before", 0.0)),
            confidence_after=float(d.get("confidence_after", 0.0)),
            summary=str(d.get("summary", "")),
            created=float(d.get("created", 0.0)),
            context_tags=tuple(d.get("context_tags") or ()),
            factors=list(d.get("factors") or []),
            metadata=dict(d.get("metadata") or {}),
        )
    for e in body.get("confidence_events") or []:
        target.confidence_events.append(
            ConfidenceEvent(
                timestamp=float(e.get("timestamp", 0.0)),
                target_kind=str(e.get("target_kind", "")),
                target_id=str(e.get("target_id", "")),
                before=float(e.get("before", 0.0)),
                after=float(e.get("after", 0.0)),
                source=str(e.get("source", "")),
                factors=list(e.get("factors") or []),
                summary=str(e.get("summary", "")),
            )
        )
    for pid, d in (body.get("provenance") or {}).items():
        target.provenance[str(pid)] = ProvenanceRecord.from_public(d)
    return target


def migrate_body(body: dict[str, Any], *, from_version: int, to_version: int) -> dict[str, Any]:
    """Forward-only schema migration of snapshot body."""
    out = dict(body)
    version = from_version
    while version < to_version:
        out.setdefault("provenance", {})
        version += 1
    out.setdefault("provenance", {})
    return out
