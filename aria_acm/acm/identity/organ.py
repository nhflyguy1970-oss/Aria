"""Identity organ — privileged schemas that emerge from lived cognition.

Not personality. Not consciousness. Not a manually maintained profile blob.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from time import time
from typing import TYPE_CHECKING, Any

from acm.identity.policy import IdentityPolicyGate, IdentityProposal
from acm.types import Attribute, ConceptRole, EdgeType

if TYPE_CHECKING:
    from acm.concepts.model import Concept
    from acm.core.store import CognitiveStore
    from acm.validation.harness import ValidationHarness

_SELF_ROLE = re.compile(
    r"\b(i\s+am|i'?m|my\s+name\s+is|i\s+work\s+as|i\s+serve\s+as)\b",
    re.I,
)
_CAPABILITY = re.compile(
    r"\b(i\s+can|i\s+am\s+able\s+to|capable\s+of|my\s+(?:skill|capability))\b",
    re.I,
)
_WHO_QUERY = re.compile(
    r"\b(who\s+am\s+i|who\s+are\s+you|what\s+am\s+i|what\s+do\s+you\s+know"
    r"|what\s+(?:are\s+)?my\s+capabilities|how\s+have\s+i\s+changed)\b",
    re.I,
)
_USER_REFERENT = re.compile(r"\b(you\s+are|user'?s?\s+name|the\s+user\s+is)\b", re.I)


@dataclass
class LineageEntry:
    timestamp: float
    schema_id: str
    attribute_key: str
    previous: str | None
    current: str
    kind: str  # adopt | strengthen | supersede | propose | assent | reject
    concept_id: str = ""
    evidence_id: str = ""
    confidence: float = 0.0


@dataclass
class IdentitySnapshot:
    """Reconstructed identity view — derived, not a editable form."""

    agent_id: str
    schemas: dict[str, dict[str, Any]]
    central_concepts: list[dict[str, Any]]
    active_goals: list[str]
    capabilities: list[str]
    uncertainties: list[str]
    lineage_tail: list[dict[str, Any]]
    confidence: float
    evolution: dict[str, Any]


@dataclass
class IdentityOrgan:
    """Emergent identity over privileged schema concepts."""

    agent_id: str
    store: CognitiveStore
    validation: ValidationHarness
    policy: IdentityPolicyGate = field(default_factory=IdentityPolicyGate)
    lineage: list[LineageEntry] = field(default_factory=list)
    _schema_ids: dict[str, str] = field(default_factory=dict)
    _influence_events: int = 0
    _growth_events: int = 0
    _change_events: int = 0
    _stability_hits: int = 0

    # --- schema anchors (organizational nuclei; content still experience-driven) ----

    def ensure_schemas(self) -> dict[str, str]:
        for role, label in (
            ("agent", f"agent:{self.agent_id}"),
            ("user", "user"),
            ("project", "project"),
        ):
            if role in self._schema_ids and self._schema_ids[role] in self.store.concepts:
                continue
            existing = self.store.find_concepts_by_label(label)
            concept = next((c for c in existing if c.identity), None)
            if concept is None:
                concept = self.store.add_concept(
                    label,
                    role=ConceptRole.IDENTITY,
                    identity=True,
                    provisional=True,
                    importance=0.85,
                    confidence=0.4,
                    strength=0.4,
                    metadata={"identity_role": role, "schema": True},
                )
                self._growth_events += 1
                self.validation.record_identity(
                    action="schema_created",
                    schema_role=role,
                    concept_id=concept.id,
                    growth=1,
                )
            self._schema_ids[role] = concept.id
        return dict(self._schema_ids)

    def schema_concept(self, role: str = "agent") -> Concept:
        ids = self.ensure_schemas()
        return self.store.concepts[ids[role]]

    # --- classification -----------------------------------------------------------

    def is_who_query(self, text: str) -> bool:
        return bool(_WHO_QUERY.search(text or ""))

    def classify_identity_signal(self, text: str, *, kind: str) -> str | None:
        """Return target schema role if text is identity-relevant, else None."""
        if kind == "identity":
            return "user" if _USER_REFERENT.search(text or "") else "agent"
        if _USER_REFERENT.search(text or ""):
            return "user"
        if _SELF_ROLE.search(text or "") or _CAPABILITY.search(text or ""):
            return "agent"
        if kind == "preference" and re.search(r"\bmy\b", text or "", re.I):
            # Preferences can become identity-adjacent, not schema statement content alone
            return "adjacent"
        return None

    # --- integrate experience into identity ---------------------------------------

    def integrate_encode(
        self,
        *,
        text: str,
        kind: str,
        concept: Concept,
        experience_id: str,
        weight: float,
        assent: bool = False,
        proposal_id: str | None = None,
    ) -> dict[str, Any]:
        signal = self.classify_identity_signal(text, kind=kind)
        if signal is None:
            return {"identity": False}

        self.ensure_schemas()
        if signal == "adjacent":
            return self._link_adjacent(concept, weight=weight)

        schema = self.schema_concept("user" if signal == "user" else "agent")
        key, value = self._extract_identity_attribute(text, kind=kind)

        # Capability concepts get OWNED_BY agent schema
        if _CAPABILITY.search(text) or key == "capability":
            concept.identity = True
            concept.role = ConceptRole.IDENTITY
            concept.metadata["identity_role"] = "capability"
            self._associate(schema.id, concept.id, EdgeType.OWNED_BY, weight=0.55 + 0.3 * weight)

        result: dict[str, Any] = {
            "identity": True,
            "schema_id": schema.id,
            "schema_role": schema.metadata.get("identity_role", "agent"),
            "attribute_key": key,
        }

        existing = next((a for a in schema.attributes if a.key == key and a.active), None)
        if existing is None:
            schema.attributes.append(
                Attribute(
                    key=key,
                    value=value,
                    confidence=min(0.92, 0.55 + weight / 2),
                    importance=max(weight, 0.7),
                    evidence_ids=[experience_id],
                )
            )
            self._strengthen_schema(schema, weight)
            self._lineage(
                schema.id,
                key,
                None,
                value,
                "adopt",
                concept_id=concept.id,
                evidence_id=experience_id,
                confidence=schema.confidence,
            )
            self._growth_events += 1
            self.validation.record_identity(
                action="adopt",
                schema_id=schema.id,
                attribute_key=key,
                current=value,
                growth=1,
                confidence=schema.confidence,
                lineage=True,
            )
            result["status"] = "adopted"
            return result

        if existing.value.lower() == value.lower():
            before = existing.confidence
            existing.confidence = min(1.0, existing.confidence + 0.06)
            if experience_id not in existing.evidence_ids:
                existing.evidence_ids.append(experience_id)
            self._strengthen_schema(schema, weight * 0.5)
            self._stability_hits += 1
            self._lineage(
                schema.id,
                key,
                existing.value,
                value,
                "strengthen",
                concept_id=concept.id,
                evidence_id=experience_id,
                confidence=existing.confidence,
            )
            self.validation.record_identity(
                action="strengthen",
                schema_id=schema.id,
                attribute_key=key,
                confidence_before=before,
                confidence_after=existing.confidence,
                stability=1,
                lineage=True,
            )
            result["status"] = "strengthened"
            return result

        # High-impact flip — require assent unless explicitly granted
        if not assent and not (proposal_id and self._assented(proposal_id)):
            prop = self.policy.propose(
                schema_id=schema.id,
                attribute_key=key,
                previous=existing.value,
                proposed=value,
                reason="identity_attribute_conflict",
            )
            self._change_events += 1
            self._lineage(
                schema.id,
                key,
                existing.value,
                value,
                "propose",
                concept_id=concept.id,
                evidence_id=experience_id,
                confidence=existing.confidence,
            )
            self.validation.record_identity(
                action="propose_change",
                schema_id=schema.id,
                attribute_key=key,
                previous=existing.value,
                proposed=value,
                proposal_id=prop.id,
                change=1,
                lineage=True,
            )
            result["status"] = "proposed"
            result["proposal_id"] = prop.id
            return result

        return self._apply_supersede(
            schema=schema,
            existing=existing,
            value=value,
            experience_id=experience_id,
            concept_id=concept.id,
            weight=weight,
            proposal_id=proposal_id,
        )

    def assent(self, proposal_id: str) -> dict[str, Any]:
        prop = self.policy.assent(proposal_id)
        if prop is None:
            return {"assented": False, "reason": "missing_or_not_pending"}
        schema = self.store.concepts.get(prop.schema_id)
        if schema is None:
            return {"assented": False, "reason": "schema_missing"}
        existing = next(
            (a for a in schema.attributes if a.key == prop.attribute_key and a.active),
            None,
        )
        if existing is None:
            schema.attributes.append(
                Attribute(
                    key=prop.attribute_key,
                    value=prop.proposed,
                    confidence=0.75,
                    importance=0.85,
                )
            )
            self._lineage(
                schema.id,
                prop.attribute_key,
                prop.previous,
                prop.proposed,
                "assent",
                confidence=0.75,
            )
        else:
            self._apply_supersede(
                schema=schema,
                existing=existing,
                value=prop.proposed,
                experience_id="",
                concept_id="",
                weight=0.85,
                proposal_id=proposal_id,
            )
        self.validation.record_identity(
            action="assent",
            proposal_id=proposal_id,
            schema_id=prop.schema_id,
            attribute_key=prop.attribute_key,
            previous=prop.previous,
            current=prop.proposed,
            change=1,
            lineage=True,
        )
        return {
            "assented": True,
            "proposal_id": proposal_id,
            "attribute_key": prop.attribute_key,
            "value": prop.proposed,
        }

    def reject(self, proposal_id: str) -> dict[str, Any]:
        prop = self.policy.reject(proposal_id)
        if prop is None:
            return {"rejected": False}
        self._lineage(
            prop.schema_id,
            prop.attribute_key,
            prop.previous,
            prop.proposed,
            "reject",
        )
        self.validation.record_identity(
            action="reject",
            proposal_id=proposal_id,
            schema_id=prop.schema_id,
            lineage=True,
        )
        return {"rejected": True, "proposal_id": proposal_id}

    def pending_proposals(self) -> list[IdentityProposal]:
        return self.policy.pending()

    # --- influence on cognition ---------------------------------------------------

    def attention_boost(self, text: str, *, kind: str) -> float:
        if self.classify_identity_signal(text, kind=kind) in ("agent", "user"):
            self._influence_events += 1
            self.validation.record_identity(action="influence_attention", influence=1)
            return 0.15
        return 0.0

    def rank_bonus(self, concept: Concept, *, query: str) -> float:
        bonus = 0.0
        if concept.identity:
            bonus += 0.6
        if self.is_who_query(query) and concept.identity:
            bonus += 1.5
            self._influence_events += 1
        # Centrality to schema neighborhood
        for role_id in self._schema_ids.values():
            if concept.id == role_id:
                bonus += 1.0
            for edge, other in self.store.neighbors(concept.id):
                if other.id == role_id or edge.target_id == role_id:
                    bonus += 0.35 * edge.weight
        if bonus >= 0.6 and (concept.identity or self.is_who_query(query)):
            self.validation.record_identity(
                action="influence_remember",
                concept_id=concept.id,
                influence=1,
                bonus=round(bonus, 3),
            )
        return bonus

    def mark_concept_formation(self, concept: Concept, *, text: str, kind: str) -> None:
        signal = self.classify_identity_signal(text, kind=kind)
        if signal in ("agent", "user"):
            concept.importance = max(concept.importance, 0.75)
            if kind == "identity" or _SELF_ROLE.search(text):
                concept.identity = True
                concept.role = ConceptRole.IDENTITY

    # --- reconstruction / snapshot -----------------------------------------------

    def snapshot(self) -> IdentitySnapshot:
        self.ensure_schemas()
        schemas: dict[str, dict[str, Any]] = {}
        confidences: list[float] = []
        for role, cid in self._schema_ids.items():
            concept = self.store.concepts[cid]
            attrs = [
                {
                    "key": a.key,
                    "value": a.value,
                    "confidence": a.confidence,
                    "version": a.version,
                    "evidence_count": len(a.evidence_ids),
                }
                for a in concept.attributes
                if a.active
            ]
            confidences.append(concept.confidence)
            schemas[role] = {
                "concept_id": concept.id,
                "label": concept.labels[0],
                "confidence": concept.confidence,
                "strength": concept.strength,
                "provisional": concept.provisional,
                "attributes": attrs,
            }

        central = self._central_concepts(limit=8)
        capabilities = [
            c["label"]
            for c in central
            if c.get("identity_role") == "capability" or "capability" in c.get("label", "")
        ]
        # also from agent schema attrs
        for attr in schemas.get("agent", {}).get("attributes", []):
            if attr["value"] in capabilities:
                continue
            if attr["key"] == "capability" or _CAPABILITY.search(attr["value"]):
                capabilities.append(attr["value"])

        uncertainties = [
            f"{role}:{a['key']}"
            for role, body in schemas.items()
            for a in body.get("attributes", [])
            if a["confidence"] < 0.55
        ]
        schema_labels = {body["label"] for body in schemas.values()}
        for c in central:
            if c["confidence"] < 0.55 and c["label"] not in schema_labels:
                uncertainties.append(c["label"])

        goals = [g.title for g in self.store.active_goals()]
        mean_c = sum(confidences) / len(confidences) if confidences else 0.0
        evolution = {
            "growth_events": self._growth_events,
            "change_events": self._change_events,
            "stability_hits": self._stability_hits,
            "influence_events": self._influence_events,
            "lineage_length": len(self.lineage),
            "pending_proposals": len(self.policy.pending()),
        }
        self.validation.record_identity(
            action="snapshot",
            confidence=mean_c,
            growth=self._growth_events,
            change=self._change_events,
            stability=self._stability_hits,
            influence=self._influence_events,
            lineage_length=len(self.lineage),
            evolution=evolution,
        )
        return IdentitySnapshot(
            agent_id=self.agent_id,
            schemas=schemas,
            central_concepts=central,
            active_goals=goals,
            capabilities=capabilities[:12],
            uncertainties=uncertainties[:12],
            lineage_tail=[self._lineage_dict(e) for e in self.lineage[-40:]],
            confidence=mean_c,
            evolution=evolution,
        )

    def who_am_i(self) -> dict[str, Any]:
        snap = self.snapshot()
        agent = snap.schemas.get("agent", {})
        lines = [f"I am {self.agent_id}."]
        for attr in agent.get("attributes", []):
            if attr["key"] == "role":
                lines.append(f"My role is {attr['value']}.")
            elif attr["key"] == "name":
                lines.append(f"I am known as {attr['value']}.")
            elif attr["key"] == "capability":
                lines.append(f"I can {attr['value']}.")
            elif attr["key"] == "statement":
                lines.append(attr["value"].rstrip(".") + ".")
        if snap.capabilities:
            lines.append("Capabilities: " + "; ".join(snap.capabilities[:5]) + ".")
        if snap.active_goals:
            lines.append("Active goals: " + "; ".join(snap.active_goals[:5]) + ".")
        if snap.uncertainties:
            lines.append(
                "I am less certain about: " + ", ".join(snap.uncertainties[:4]) + "."
            )
        return {
            "answer": " ".join(lines),
            "confidence": snap.confidence,
            "explanation_class": "experience",
            "schemas": {"agent": agent},
            "evolution": snap.evolution,
            "central_concepts": snap.central_concepts[:5],
        }

    def observables(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "growth": snap.evolution["growth_events"],
            "stability": snap.evolution["stability_hits"],
            "change": snap.evolution["change_events"],
            "confidence": snap.confidence,
            "influence": snap.evolution["influence_events"],
            "lineage_length": snap.evolution["lineage_length"],
            "evolution": snap.evolution,
            "pending_proposals": snap.evolution["pending_proposals"],
        }

    # --- internals ----------------------------------------------------------------

    def _extract_identity_attribute(self, text: str, *, kind: str) -> tuple[str, str]:
        t = text.strip()
        m = re.search(r"my\s+name\s+is\s+(.+?)(?:\.|$)", t, re.I)
        if m:
            return "name", m.group(1).strip().rstrip(".")
        m = re.search(r"\b(?:i\s+am|i'?m)\s+(?:a|an)\s+(.+?)(?:\.|$)", t, re.I)
        if m:
            return "role", m.group(1).strip().rstrip(".")
        m = re.search(r"\b(?:i\s+am|i'?m)\s+(.+?)(?:\.|$)", t, re.I)
        if m:
            return "role", m.group(1).strip().rstrip(".")
        m = re.search(
            r"\b(?:i\s+can|i\s+am\s+able\s+to|capable\s+of)\s+(.+?)(?:\.|$)",
            t,
            re.I,
        )
        if m:
            return "capability", m.group(1).strip().rstrip(".")
        if kind == "identity":
            return "statement", t
        return "statement", t

    def _link_adjacent(self, concept: Concept, *, weight: float) -> dict[str, Any]:
        schema = self.schema_concept("agent")
        edge = self._associate(
            schema.id, concept.id, EdgeType.RELATED_TO, weight=0.35 + 0.25 * weight
        )
        self.validation.record_identity(
            action="adjacent_link",
            schema_id=schema.id,
            concept_id=concept.id,
            edge_id=edge.id,
            influence=1,
        )
        return {"identity": True, "status": "adjacent", "schema_id": schema.id}

    def _associate(self, source_id: str, target_id: str, edge_type: EdgeType, *, weight: float):
        # Avoid duplicate active edges of same type
        for edge in self.store.associations.values():
            if not edge.active:
                continue
            if (
                edge.source_id == source_id
                and edge.target_id == target_id
                and edge.edge_type == edge_type
            ):
                edge.weight = min(1.0, max(edge.weight, weight))
                return edge
        return self.store.add_association(
            source_id, target_id, edge_type=edge_type, weight=weight
        )

    def _strengthen_schema(self, schema: Concept, weight: float) -> None:
        schema.strength = min(1.0, schema.strength + 0.06 * weight)
        schema.confidence = min(1.0, schema.confidence + 0.05 * weight)
        schema.importance = max(schema.importance, 0.8)
        schema.provisional = schema.strength < 0.7
        schema.access_count += 1
        schema.last_activated = time()

    def _apply_supersede(
        self,
        *,
        schema: Concept,
        existing: Attribute,
        value: str,
        experience_id: str,
        concept_id: str,
        weight: float,
        proposal_id: str | None,
    ) -> dict[str, Any]:
        previous = existing.value
        existing.active = False
        schema.attributes.append(
            Attribute(
                key=existing.key,
                value=value,
                confidence=min(0.95, existing.confidence + 0.08),
                importance=max(existing.importance, weight),
                evidence_ids=[experience_id] if experience_id else [],
                version=existing.version + 1,
            )
        )
        self._strengthen_schema(schema, weight)
        self._change_events += 1
        self._lineage(
            schema.id,
            existing.key,
            previous,
            value,
            "supersede",
            concept_id=concept_id,
            evidence_id=experience_id,
            confidence=schema.confidence,
        )
        self.validation.record_identity(
            action="supersede",
            schema_id=schema.id,
            attribute_key=existing.key,
            previous=previous,
            current=value,
            proposal_id=proposal_id,
            change=1,
            lineage=True,
            confidence=schema.confidence,
        )
        return {
            "identity": True,
            "status": "superseded",
            "schema_id": schema.id,
            "attribute_key": existing.key,
            "previous": previous,
            "current": value,
            "proposal_id": proposal_id,
        }

    def _assented(self, proposal_id: str) -> bool:
        prop = self.policy.proposals.get(proposal_id)
        return bool(prop and prop.status == "assented")

    def _lineage(
        self,
        schema_id: str,
        key: str,
        previous: str | None,
        current: str,
        kind: str,
        *,
        concept_id: str = "",
        evidence_id: str = "",
        confidence: float = 0.0,
    ) -> None:
        self.lineage.append(
            LineageEntry(
                timestamp=time(),
                schema_id=schema_id,
                attribute_key=key,
                previous=previous,
                current=current,
                kind=kind,
                concept_id=concept_id,
                evidence_id=evidence_id,
                confidence=confidence,
            )
        )
        if len(self.lineage) > 2000:
            del self.lineage[:-2000]

    def _lineage_dict(self, entry: LineageEntry) -> dict[str, Any]:
        return {
            "timestamp": entry.timestamp,
            "schema_id": entry.schema_id,
            "attribute_key": entry.attribute_key,
            "previous": entry.previous,
            "current": entry.current,
            "kind": entry.kind,
            "concept_id": entry.concept_id,
            "evidence_id": entry.evidence_id,
            "confidence": entry.confidence,
        }

    def _central_concepts(self, *, limit: int) -> list[dict[str, Any]]:
        scored: list[tuple[float, Concept]] = []
        schema_ids = set(self._schema_ids.values())
        for concept in self.store.concepts.values():
            if not concept.active:
                continue
            score = concept.strength * concept.importance * (0.5 + 0.5 * concept.confidence)
            score *= 1.0 + 0.1 * concept.access_count
            if concept.identity:
                score *= 1.8
            if concept.id in schema_ids:
                score *= 1.2
            for edge, other in self.store.neighbors(concept.id):
                if other.id in schema_ids or other.identity:
                    score += 0.4 * edge.weight
            if score > 0.2:
                scored.append((score, concept))
        scored.sort(key=lambda x: x[0], reverse=True)
        out: list[dict[str, Any]] = []
        for score, c in scored[:limit]:
            out.append(
                {
                    "concept_id": c.id,
                    "label": c.labels[0],
                    "score": round(score, 3),
                    "confidence": c.confidence,
                    "identity": c.identity,
                    "identity_role": c.metadata.get("identity_role", ""),
                }
            )
        return out
