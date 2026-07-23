"""Identity organ — privileged schemas that emerge from lived cognition.

Not personality. Not consciousness. Not a manually maintained profile blob.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from time import time
from typing import TYPE_CHECKING, Any

from acm.identity.assistant_profile import AssistantIdentityProfile
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
_MY_NAME = re.compile(r"\bmy\s+name\s+is\b", re.I)
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
_ASSISTANT_ADDRESS = re.compile(
    r"\b(you\s+are|your\s+name\s+is|call\s+yourself)\b",
    re.I,
)
_OPERATIONAL_TAG = "operational"


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
    profile: AssistantIdentityProfile = field(default_factory=AssistantIdentityProfile)
    _operational_applied: bool = False

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
        self.apply_operational_identity()
        return dict(self._schema_ids)

    def apply_operational_identity(self, *, force: bool = False) -> None:
        """Seed assistant schema from configuration (intrinsic operational identity)."""
        if self._operational_applied and not force:
            return
        if "agent" not in self._schema_ids:
            return
        schema = self.store.concepts[self._schema_ids["agent"]]
        profile = self.profile
        name = profile.resolved_name(self.agent_id)
        seeds: list[tuple[str, str]] = [("name", name)]
        if profile.role:
            seeds.append(("role", profile.role))
        if profile.description:
            seeds.append(("description", profile.description))
        if profile.personality:
            seeds.append(("personality", profile.personality))
        for cap in profile.capabilities:
            seeds.append(("capability", cap))
        for key, value in profile.extra.items():
            seeds.append((key, value))
        for key, value in seeds:
            existing = next(
                (a for a in schema.attributes if a.key == key and a.active),
                None,
            )
            if existing is not None:
                if _OPERATIONAL_TAG in existing.context_tags:
                    existing.value = value
                    existing.confidence = max(existing.confidence, 0.95)
                    continue
                # Replace contaminated non-operational name with operational seed
                if key == "name":
                    existing.active = False
                else:
                    continue
            schema.attributes.append(
                Attribute(
                    key=key,
                    value=value,
                    confidence=0.95,
                    importance=0.95,
                    context_tags=(_OPERATIONAL_TAG,),
                    evidence_ids=["operational"],
                )
            )
            schema.confidence = max(schema.confidence, 0.9)
            schema.strength = max(schema.strength, 0.85)
            schema.provisional = False
        self._operational_applied = True
        self.validation.record_identity(
            action="operational_seed",
            schema_id=schema.id,
            name=name,
        )

    def set_assistant_profile(self, profile: AssistantIdentityProfile) -> None:
        self.profile = profile
        self._operational_applied = False
        self.ensure_schemas()

    def schema_concept(self, role: str = "agent") -> Concept:
        ids = self.ensure_schemas()
        return self.store.concepts[ids[role]]

    # --- classification -----------------------------------------------------------

    def is_who_query(self, text: str) -> bool:
        return bool(_WHO_QUERY.search(text or ""))

    def classify_identity_signal(self, text: str, *, kind: str) -> str | None:
        """Return target schema role if text is identity-relevant, else None."""
        try:
            from acm.semantic import extract_semantics

            extracted = extract_semantics(text, kind=kind)
            id_facts = extracted.identity_facts()
            if id_facts:
                subjects = {f.subject.value for f in id_facts}
                if "user" in subjects and "assistant" not in subjects:
                    return "user"
                if "assistant" in subjects and "user" not in subjects:
                    return "agent"
                if "assistant" in subjects:
                    return "agent"
                if "user" in subjects:
                    return "user"
                if any(f.kind.value == "relationship" for f in extracted.facts):
                    return "adjacent"
        except Exception:
            pass
        # Legacy fallback — first-person autobiography is USER (D043).
        # Never map bare "my name is" / "I am" onto the assistant schema.
        if _ASSISTANT_ADDRESS.search(text or "") and not _MY_NAME.search(text or ""):
            return "agent"
        if _USER_REFERENT.search(text or "") or _MY_NAME.search(text or ""):
            return "user"
        if _SELF_ROLE.search(text or ""):
            return "user"
        if kind == "preference" and re.search(r"\bmy\b", text or "", re.I):
            return "adjacent"
        if _CAPABILITY.search(text or "") and kind == "identity":
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
        facts: list | None = None,
    ) -> dict[str, Any]:
        # Prefer structured Semantic Extraction facts when provided
        structured = list(facts or [])
        if structured:
            return self._integrate_facts(
                facts=structured,
                text=text,
                kind=kind,
                concept=concept,
                experience_id=experience_id,
                weight=weight,
                assent=assent,
                proposal_id=proposal_id,
            )

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

        return self._upsert_attribute(
            schema=schema,
            key=key,
            value=value,
            experience_id=experience_id,
            concept_id=concept.id,
            weight=weight,
            assent=assent,
            proposal_id=proposal_id,
            auto_revise=signal == "user" and key in ("name", "preferred_name", "location"),
            result=result,
        )

    def _integrate_facts(
        self,
        *,
        facts: list,
        text: str,
        kind: str,
        concept: Concept,
        experience_id: str,
        weight: float,
        assent: bool,
        proposal_id: str | None,
    ) -> dict[str, Any]:
        from acm.semantic.model import FactKind, PerspectiveSubject

        self.ensure_schemas()
        applied: list[dict[str, Any]] = []
        last: dict[str, Any] = {"identity": False}

        for fact in facts:
            kind_val = getattr(fact.kind, "value", str(fact.kind))
            subject_val = getattr(fact.subject, "value", str(fact.subject))
            prop = str(fact.property)
            value = str(fact.value)

            if kind_val == FactKind.RELATIONSHIP.value or (
                subject_val == PerspectiveSubject.THIRD_PARTY.value
            ):
                # Relationship: adjacent link + attribute on a labeled concept
                concept.metadata["relation_type"] = fact.relation_type or "related"
                concept.metadata["relation_name"] = value
                applied.append(
                    {
                        "kind": "relationship",
                        "relation_type": fact.relation_type,
                        "value": value,
                        "status": "adjacent",
                    }
                )
                last = self._link_adjacent(concept, weight=weight)
                last["relationship"] = {
                    "type": fact.relation_type,
                    "name": value,
                }
                continue

            if kind_val == FactKind.PREFERENCE.value:
                last = self._link_adjacent(concept, weight=weight)
                last["preference"] = {"key": prop, "value": value}
                applied.append(last)
                continue

            if kind_val == FactKind.POSSESSION.value:
                # Possessions live on entity concepts (laptop/desktop/…), not user schema.
                last = self._link_adjacent(concept, weight=weight)
                last["possession"] = {
                    "entity": getattr(fact, "relation_type", None) or "",
                    "key": prop,
                    "value": value,
                }
                applied.append(last)
                continue

            if kind_val in (FactKind.GOAL.value, FactKind.PROJECT.value):
                # Goals/projects handled by engine; mark adjacent identity influence
                last = self._link_adjacent(concept, weight=weight * 0.5)
                last[kind_val] = value
                applied.append(last)
                continue

            if subject_val == PerspectiveSubject.USER.value:
                schema = self.schema_concept("user")
                schema_role = "user"
            elif subject_val == PerspectiveSubject.ASSISTANT.value:
                schema = self.schema_concept("agent")
                schema_role = "agent"
            else:
                continue

            # D043: never write user-name collisions onto assistant schema from
            # conversational/tool text unless operational or explicit assent.
            if schema_role == "agent" and prop == "name":
                user = self.schema_concept("user")
                user_names = {
                    a.value.casefold()
                    for a in user.attributes
                    if a.key == "name" and a.active
                }
                if value.casefold() in user_names and not assent:
                    applied.append(
                        {
                            "identity": True,
                            "schema_role": "agent",
                            "attribute_key": prop,
                            "status": "rejected_user_collision",
                            "value": value,
                        }
                    )
                    continue

            if prop == "capability" or kind_val == FactKind.SKILL.value:
                concept.identity = True
                concept.role = ConceptRole.IDENTITY
                concept.metadata["identity_role"] = "capability"
                self._associate(
                    schema.id, concept.id, EdgeType.OWNED_BY, weight=0.55 + 0.3 * weight
                )
                prop = "capability"

            update_op = getattr(fact.update_op, "value", str(getattr(fact, "update_op", "set")))
            auto_revise = schema_role == "user" and prop in (
                "name",
                "preferred_name",
                "location",
                "role",
            )
            if update_op in ("revise", "set") and auto_revise:
                auto_revise = True

            result: dict[str, Any] = {
                "identity": True,
                "schema_id": schema.id,
                "schema_role": schema_role,
                "attribute_key": prop,
                "fact_summary": fact.canonical_summary()
                if hasattr(fact, "canonical_summary")
                else "",
            }
            last = self._upsert_attribute(
                schema=schema,
                key=prop,
                value=value,
                experience_id=experience_id,
                concept_id=concept.id,
                weight=weight,
                assent=assent or update_op == "revise",
                proposal_id=proposal_id,
                auto_revise=auto_revise or update_op == "revise",
                negate=update_op == "negate" or kind_val == FactKind.NEGATION.value,
                result=result,
            )
            if schema_role == "user" and prop == "name" and last.get("status") in (
                "adopted",
                "strengthened",
                "superseded",
            ):
                self._scrub_assistant_user_name_collision(value)
            applied.append(last)

        if not applied:
            # Fall back to legacy path
            return self.integrate_encode(
                text=text,
                kind=kind,
                concept=concept,
                experience_id=experience_id,
                weight=weight,
                assent=assent,
                proposal_id=proposal_id,
                facts=None,
            )
        out = dict(last)
        out["facts_applied"] = len(applied)
        out["applied"] = applied
        out["identity"] = True
        return out

    def _upsert_attribute(
        self,
        *,
        schema: Concept,
        key: str,
        value: str,
        experience_id: str,
        concept_id: str,
        weight: float,
        assent: bool,
        proposal_id: str | None,
        auto_revise: bool,
        result: dict[str, Any],
        negate: bool = False,
    ) -> dict[str, Any]:
        if negate:
            existing = next((a for a in schema.attributes if a.key == key and a.active), None)
            if existing and existing.value.lower() == value.lower():
                existing.active = False
                self._lineage(
                    schema.id,
                    key,
                    existing.value,
                    value,
                    "reject",
                    concept_id=concept_id,
                    evidence_id=experience_id,
                    confidence=existing.confidence,
                )
                result["status"] = "negated"
                return result
            result["status"] = "negate_noop"
            return result

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
                concept_id=concept_id,
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
                concept_id=concept_id,
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

        # Update semantics: user identity attributes revise in place (no duplicate)
        if auto_revise or assent or (proposal_id and self._assented(proposal_id)):
            return self._apply_supersede(
                schema=schema,
                existing=existing,
                value=value,
                experience_id=experience_id,
                concept_id=concept_id,
                weight=weight,
                proposal_id=proposal_id,
            )

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
                concept_id=concept_id,
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
            concept_id=concept_id,
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
        """Assistant-identity reconstruction — agent schema only (never user)."""
        return self.render_assistant_identity()

    def render_user_identity(self) -> dict[str, Any]:
        """Structured user identity only — never assistant / operational profile."""
        from acm.identity.rendering import (
            IdentityRenderTarget,
            isolate_identity_text,
            user_forbidden_from_assistant,
        )

        self.ensure_schemas()
        user = self.schema_concept("user")
        agent = self.schema_concept("agent")
        speak_keys = ("name", "preferred_name", "role", "location", "capability")
        lines: list[str] = []
        attr_confs: list[float] = []
        for attr in user.attributes:
            if not attr.active:
                continue
            if attr.key not in speak_keys and attr.key != "statement":
                continue
            if attr.key == "name":
                lines.append(f"Your name is {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "preferred_name":
                lines.append(f"You prefer to be called {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "role":
                lines.append(f"You are {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "location":
                lines.append(f"You live in {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "capability":
                lines.append(f"You can {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "statement":
                val = str(attr.value or "").strip()
                low = val.lower()
                if "please remember" in low or low.startswith("you are"):
                    continue
                lines.append(val.rstrip(".") + ".")
                attr_confs.append(float(attr.confidence))

        raw = " ".join(lines).strip() if lines else None
        forbidden = user_forbidden_from_assistant(
            [(a.key, a.value) for a in agent.attributes if a.active],
            self.agent_id,
        )
        text = isolate_identity_text(
            raw, target=IdentityRenderTarget.USER, forbidden_values=forbidden
        )
        conf = max(attr_confs) if text and attr_confs else 0.0
        return {
            "answer": text,
            "confidence": conf if text else 0.0,
            "explanation_class": "experience" if text else "unknown",
            "schemas": {"user": {"concept_id": user.id}},
            "source": "user_identity",
            "isolated": True,
        }

    def render_assistant_identity(self) -> dict[str, Any]:
        """Structured assistant identity only — never user facts or personalization."""
        from acm.identity.rendering import (
            IdentityRenderTarget,
            assistant_forbidden_from_user,
            isolate_identity_text,
        )

        self.ensure_schemas()
        agent = self.schema_concept("agent")
        user = self.schema_concept("user")
        user_names = {
            a.value.casefold()
            for a in user.attributes
            if a.key == "name" and a.active
        }
        # Prefer operational attributes; never speak contaminated user-name copies.
        speak_keys = ("name", "role", "description", "capability", "personality")
        lines: list[str] = []
        attr_confs: list[float] = []
        spoken_name = False
        for attr in agent.attributes:
            if not attr.active or attr.key not in speak_keys:
                continue
            if (
                attr.key == "name"
                and attr.value.casefold() in user_names
                and _OPERATIONAL_TAG not in attr.context_tags
            ):
                continue
            # Skip non-operational statements that could personalize
            if attr.key == "name":
                lines.append(f"My name is {attr.value}.")
                attr_confs.append(float(attr.confidence))
                spoken_name = True
            elif attr.key == "role":
                lines.append(f"My role is {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "description":
                lines.append(str(attr.value).rstrip(".") + ".")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "capability":
                lines.append(f"I can {attr.value}.")
                attr_confs.append(float(attr.confidence))
            elif attr.key == "personality":
                lines.append(str(attr.value).rstrip(".") + ".")
                attr_confs.append(float(attr.confidence))

        if not spoken_name:
            name = self.profile.resolved_name(self.agent_id)
            lines.insert(0, f"My name is {name}.")
            attr_confs.insert(0, 0.95)

        raw = " ".join(lines).strip()
        forbidden = assistant_forbidden_from_user(
            [(a.key, a.value) for a in user.attributes if a.active]
        )
        text = isolate_identity_text(
            raw,
            target=IdentityRenderTarget.ASSISTANT,
            forbidden_values=forbidden,
        )
        reseeded = False
        # Isolation must never erase operational name — re-seed only if empty
        # after true collisions (B45: operational claims are no longer over-filtered).
        if not text:
            name = self.profile.resolved_name(self.agent_id)
            text = f"My name is {name}."
            attr_confs = [0.95]
            reseeded = True

        conf = max(attr_confs) if attr_confs else 0.95
        agent_body = {
            "concept_id": agent.id,
            "label": agent.labels[0] if agent.labels else f"agent:{self.agent_id}",
            "attributes": [
                {
                    "key": a.key,
                    "value": a.value,
                    "confidence": a.confidence,
                    "operational": _OPERATIONAL_TAG in a.context_tags,
                }
                for a in agent.attributes
                if a.active and a.key in speak_keys
            ],
        }
        return {
            "answer": text,
            "confidence": conf,
            "explanation_class": "experience",
            "schemas": {"agent": agent_body},
            "evolution": self.snapshot().evolution,
            "central_concepts": [],
            "source": "assistant_identity",
            "isolated": True,
            "reseeded_operational_name": reseeded,
        }

    def _scrub_assistant_user_name_collision(self, user_name: str) -> None:
        """Deactivate non-operational agent name attrs that equal the user name."""
        agent = self.schema_concept("agent")
        target = user_name.casefold()
        for attr in agent.attributes:
            if (
                attr.active
                and attr.key == "name"
                and attr.value.casefold() == target
                and _OPERATIONAL_TAG not in attr.context_tags
            ):
                attr.active = False
                self.validation.record_identity(
                    action="scrub_user_name_from_agent",
                    schema_id=agent.id,
                    value=attr.value,
                )
                # Re-seed operational name if wiped
                self._operational_applied = False
                self.apply_operational_identity(force=True)

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
        from acm.semantic.strip import strip_instructional

        t, _ = strip_instructional(text.strip())
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
