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

# D045: attribute keys that exist only to support cueing / indexing / emergence.
# They carry lexical metadata (surface forms), not semantic memory content, and
# must never be rendered as cognitive answers or admit a concept into
# ambiguity scoring.
LEXICAL_SUPPORT_KEYS: frozenset[str] = frozenset(
    {
        "mentioned",
        "cue",
        "token",
        "surface",
        "surface_form",
        "lexeme",
        "index",
        "stem",
    }
)

# Values that merely restate an interrogative cue are not independently
# answerable semantic content (e.g. preference='What is my favorite color?').
_INTERROGATIVE_VALUE = re.compile(
    r"^\s*(?:what|who|when|where|why|how)\b|\?\s*$",
    re.I,
)

# Generic preference tokens — matching these alone must not collapse distinct
# favorite_* domains (color vs food vs fish) into one another.
_GENERIC_PREF_TOKENS: frozenset[str] = frozenset(
    {"favorite", "favourite", "prefer", "preference", "preferences", "like", "likes"}
)

# "favorite <domain>" in a cue (color, food, fish, …). Stop before "is"/punctuation
# so "My favorite food is pizza." yields domain=food, not food_is.
_FAVORITE_DOMAIN = re.compile(
    r"(?:favorite|favourite)\s+(\w+)\b",
    re.I,
)

# Evidence / lineage introspection — reconstruct attribute history, do not answer
# as if the cue were a preference question.
_EVIDENCE_REQUEST = re.compile(
    r"\b((?:show|tell|give|list|what(?:'s|\s+is))\s+(?:me\s+)?(?:the\s+)?evidence|"
    r"evidence\s+for|supporting\s+evidence|what\s+supports)\b",
    re.I,
)

# Memory explanation — why active / why retired / what replaced.
_WHY_FAVORITE = re.compile(
    r"\bwhy\s+is\s+(.+?)\s+my\s+(?:favorite|favourite)\s+(\w+)\b",
    re.I,
)
_WHY_NOT_ACTIVE = re.compile(
    r"\bwhy\s+(?:isn'?t|is\s+not|isn\s+t)\s+(.+?)\s+active\b",
    re.I,
)
_WHY_ACTIVE = re.compile(
    r"\bwhy\s+is\s+(.+?)\s+active\b",
    re.I,
)
_WHAT_REPLACED = re.compile(
    r"\bwhat\s+replaced\s+(.+?)(?:\?|$)",
    re.I,
)
_PERSONAL_SUMMARY = re.compile(
    r"\b(what\s+do\s+you\s+know\s+about\s+me|tell\s+me\s+about\s+(?:me|myself)|"
    r"about\s+myself|what\s+do\s+you\s+remember\s+about\s+me)\b",
    re.I,
)


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
        # Evidence / lineage / summary introspection is read-only — never
        # reconsolidate or otherwise mutate living memory.
        if not (
            _is_evidence_request(cue)
            or _is_explanation_request(cue)
            or _is_personal_summary_request(cue)
        ):
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
        low = (cue or "").lower()
        # User identity questions must never reconstruct via assistant who_am_i.
        user_cue = re.search(
            r"\bwho\s+am\s+i\b|\bwhat\s+am\s+i\b|\bmy\s+name\b|\babout\s+(?:me|the\s+user)\b",
            low,
        )
        if user_cue:
            field = self.activation.activate(
                cue,
                context_tags=context_tags,
                attention_weight=attention_weight,
                identity_query=True,
            )
            # Defer to general reconstruction over user-cued activation — handlers
            # own structured user identity; this path is a safety net only.
            ranked = field.ranked_concepts(limit=6)
            reconstruction = self._reconstruct(cue, field, ranked)
            self._observe(
                reconstruction,
                attention_class=attention_class,
                context_tags=tuple(context_tags),
            )
            return reconstruction

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
            activated_concept_ids=activated
            or [n.target_id for n in field.ranked_concepts(limit=5)],
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
        tokens = _cue_tokens(cue)
        # Lineage / summary introspection can succeed from the store even when
        # activation ranking is empty — check before the empty-rank early exit.
        if _is_evidence_request(cue):
            return self._reconstruct_evidence(cue, field, ranked, tokens)
        if _is_explanation_request(cue):
            return self._reconstruct_explanation(cue, field, ranked)
        if _is_personal_summary_request(cue):
            return self._reconstruct_personal_summary(cue, field, ranked)

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

        domain = _preference_domain(cue)
        # D045: only answerable concepts may serve as the primary recollection
        # or as competing recollections. Lexical support concepts remain in the
        # activation field (supporting retrieval) but never answer or compete.
        # M0K: when the cue names a favorite <domain>, only that domain's
        # favorite_* concept may answer — never a sibling preference domain.
        answerable_ranked = [
            node
            for node in ranked
            if (c := self.store.concepts.get(node.target_id)) is not None
            and _answerable(c, tokens, domain=domain)
        ]
        if domain:
            domain_only = [
                node
                for node in answerable_ranked
                if _concept_matches_preference_domain(
                    self.store.concepts[node.target_id], domain
                )
            ]
            answerable_ranked = domain_only

        if not answerable_ranked:
            exp_nodes = sorted(field.experiences.values(), key=lambda n: -n.energy)[:6]
            return Reconstruction(
                cue=cue,
                answer="I don't have anything solid about that yet.",
                explanation_class=ExplanationClass.UNKNOWN.value,
                confidence=0.0,
                activated_concept_ids=[n.target_id for n in ranked],
                association_ids=list(field.associations.keys())[:16],
                experience_ids=[n.target_id for n in exp_nodes],
                experience_summaries=[n.label for n in exp_nodes],
                activation=field.to_public(),
                cue_classes=list(field.cue_classes),
                goal_influenced=field.goal_influenced,
                identity_influenced=field.identity_influenced,
                context_influenced=field.context_influenced,
                working_influenced=field.working_influenced,
            )

        top = answerable_ranked[0]
        concept = self.store.concepts[top.target_id]
        answer, expl, conf = self._format_from_concept(cue, concept, top.energy)

        if expl == ExplanationClass.UNKNOWN or not (answer or "").strip():
            exp_nodes = sorted(field.experiences.values(), key=lambda n: -n.energy)[:6]
            return Reconstruction(
                cue=cue,
                answer="I don't have anything solid about that yet.",
                explanation_class=ExplanationClass.UNKNOWN.value,
                confidence=0.0,
                activated_concept_ids=[n.target_id for n in ranked],
                association_ids=list(field.associations.keys())[:16],
                experience_ids=[n.target_id for n in exp_nodes],
                experience_summaries=[n.label for n in exp_nodes],
                activation=field.to_public(),
                cue_classes=list(field.cue_classes),
                goal_influenced=field.goal_influenced,
                identity_influenced=field.identity_influenced,
                context_influenced=field.context_influenced,
                working_influenced=field.working_influenced,
            )

        competing: list[CompetingRecollection] = []
        ambiguous = False
        for rival in answerable_ranked[1:4]:
            if rival.energy < top.energy * COMPETE_RATIO:
                continue
            r_concept = self.store.concepts.get(rival.target_id)
            if r_concept is None:
                continue
            # Cue relevance still required among answerable rivals
            if not _cue_relevant(r_concept, tokens, domain=domain):
                continue
            preview, _, rconf = self._format_from_concept(cue, r_concept, rival.energy)
            if not preview.strip():
                continue
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
        tokens = _cue_tokens(cue)
        domain = _preference_domain(cue)
        best_attr = None
        candidates: list[Any] = []
        for attr in concept.attributes:
            if not _is_semantic_attr(attr):
                continue
            if _attr_grounds_in_cue(attr, tokens, domain=domain):
                candidates.append(attr)
        if candidates:
            # Prefer structured favorite_* attributes over a generic "preference"
            # dump — the live blocker rendered the preference key when a tool
            # wrapper had been stored as its value.
            keyed = [a for a in candidates if a.key.startswith("favorite_")]
            if domain:
                domain_n = _normalize_domain(domain)
                domain_keyed = [
                    a
                    for a in keyed
                    if (_attr_domain(a.key) or "") == domain_n
                    or (_attr_domain(a.key) or "").startswith(domain_n + "_")
                ]
                if domain_keyed:
                    keyed = domain_keyed
            best_attr = keyed[0] if keyed else candidates[0]
        if best_attr is None:
            # D045: concepts whose only content is lexical support metadata must
            # not fall through to a bare-label answer ("favorite.").
            active = [a for a in concept.attributes if a.active]
            if active and all(not _is_semantic_attr(a) for a in active):
                return ("", ExplanationClass.UNKNOWN, 0.0)
            # Memory Authority: do not confabulate from an unrelated first attribute
            # or bare concept label when the cue does not ground in attributes.
            label_hit = False
            for lab in concept.labels or ():
                if any(tok in lab.lower() for tok in tokens if tok not in _GENERIC_PREF_TOKENS):
                    label_hit = True
                    break
                if domain and domain.replace("_", " ") in lab.lower():
                    label_hit = True
                    break
            if label_hit and concept.labels:
                conf = min(1.0, concept.confidence * (0.45 + 0.4 * min(1.0, energy)))
                answer = concept.labels[0]
                if not answer.endswith("."):
                    answer += "."
                return answer, ExplanationClass.STALE, conf
            return ("", ExplanationClass.UNKNOWN, 0.0)

        conf = min(
            1.0,
            0.55 * best_attr.confidence + 0.25 * concept.confidence + 0.2 * min(1.0, energy),
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

    def _reconstruct_evidence(
        self,
        cue: str,
        field: ActivationField,
        ranked: list[Any],
        tokens: list[str],
    ) -> Reconstruction:
        """Lineage introspection: active/retired attribute versions + experiences.

        Read-only. Does not invent values. Domains stay independent.
        """
        domain = _preference_domain(cue)
        lines: list[str] = []
        experience_ids: list[str] = []
        experience_summaries: list[str] = []
        concept_ids: list[str] = []

        # Prefer preference concepts with favorite_* attributes (all versions).
        pref_concepts: list[Concept] = []
        seen: set[str] = set()
        for node in ranked:
            concept = self.store.concepts.get(node.target_id)
            if concept is None or concept.id in seen:
                continue
            attrs = [a for a in concept.attributes if a.key.startswith("favorite_")]
            if not attrs:
                continue
            if domain and not _concept_matches_preference_domain(concept, domain):
                continue
            seen.add(concept.id)
            pref_concepts.append(concept)

        # Also scan the full store so evidence is complete even when activation
        # ranking missed an older domain (e.g. bare "Show me the evidence.").
        if not domain:
            for concept in self.store.concepts.values():
                if concept.id in seen:
                    continue
                if any(a.key.startswith("favorite_") for a in concept.attributes):
                    seen.add(concept.id)
                    pref_concepts.append(concept)
        elif not pref_concepts:
            for concept in self.store.concepts.values():
                if _concept_matches_preference_domain(concept, domain):
                    pref_concepts.append(concept)

        for concept in pref_concepts:
            concept_ids.append(concept.id)
            keyed: dict[str, list[Any]] = {}
            for attr in concept.attributes:
                if not attr.key.startswith("favorite_"):
                    continue
                if domain and not (
                    (_attr_domain(attr.key) or "") == _normalize_domain(domain)
                    or (_attr_domain(attr.key) or "").startswith(_normalize_domain(domain) + "_")
                ):
                    continue
                keyed.setdefault(attr.key, []).append(attr)
            for key, versions in keyed.items():
                pretty = key.replace("favorite_", "favorite ").replace("_", " ")
                lines.append(f"{pretty}:")
                for attr in sorted(versions, key=lambda a: a.version):
                    state = "active" if attr.active else "retired"
                    evidence_bits: list[str] = []
                    for eid in attr.evidence_ids:
                        exp = self.store.experiences.get(eid)
                        if exp is None:
                            continue
                        if eid not in experience_ids:
                            experience_ids.append(eid)
                            experience_summaries.append(exp.summary)
                        meta = exp.metadata
                        if isinstance(meta, dict):
                            raw = meta.get("evidence") or exp.summary
                        else:
                            raw = exp.summary
                        if raw and raw not in evidence_bits:
                            evidence_bits.append(str(raw)[:160])
                    teaching = f" — {evidence_bits[0]}" if evidence_bits else ""
                    lines.append(f"  v{attr.version} {attr.value} ({state}){teaching}")

        if not lines:
            exp_nodes = sorted(field.experiences.values(), key=lambda n: -n.energy)[:8]
            if exp_nodes:
                lines.append("Supporting experiences:")
                for n in exp_nodes:
                    lines.append(f"  - {n.label}")
                    experience_ids.append(n.target_id)
                    experience_summaries.append(n.label)
                answer = "\n".join(lines)
                return Reconstruction(
                    cue=cue,
                    answer=answer,
                    explanation_class=ExplanationClass.EXPERIENCE.value,
                    confidence=0.7,
                    activated_concept_ids=[n.target_id for n in ranked],
                    experience_ids=experience_ids,
                    experience_summaries=experience_summaries,
                    activation=field.to_public(),
                    cue_classes=list(field.cue_classes),
                    goal_influenced=field.goal_influenced,
                    identity_influenced=field.identity_influenced,
                    context_influenced=field.context_influenced,
                    working_influenced=field.working_influenced,
                )
            return Reconstruction(
                cue=cue,
                answer="I don't currently know.",
                explanation_class=ExplanationClass.UNKNOWN.value,
                confidence=0.0,
                activation=field.to_public(),
                cue_classes=list(field.cue_classes),
            )

        header = "Evidence (preference lineage):"
        answer = header + "\n" + "\n".join(lines)
        return Reconstruction(
            cue=cue,
            answer=answer,
            explanation_class=ExplanationClass.EXPERIENCE.value,
            confidence=0.9,
            primary_concept_id=concept_ids[0] if concept_ids else "",
            primary_label=(
                self.store.concepts[concept_ids[0]].labels[0]
                if concept_ids and self.store.concepts[concept_ids[0]].labels
                else ""
            ),
            activated_concept_ids=concept_ids or [n.target_id for n in ranked],
            experience_ids=experience_ids[:12],
            experience_summaries=experience_summaries[:12],
            activation=field.to_public(),
            cue_classes=list(field.cue_classes),
            goal_influenced=field.goal_influenced,
            identity_influenced=field.identity_influenced,
            context_influenced=field.context_influenced,
            working_influenced=field.working_influenced,
        )

    def _reconstruct_explanation(
        self,
        cue: str,
        field: ActivationField,
        ranked: list[Any],
    ) -> Reconstruction:
        """Evidence-backed lineage explanation — active/retired/replaced.

        Read-only. Reconstructs only from certified attribute versions.
        """
        answer = self._format_explanation(cue)
        if not (answer or "").strip():
            return Reconstruction(
                cue=cue,
                answer="I don't currently know.",
                explanation_class=ExplanationClass.UNKNOWN.value,
                confidence=0.0,
                activation=field.to_public(),
                cue_classes=list(field.cue_classes),
            )
        concept_ids = [
            n.target_id for n in ranked if self.store.concepts.get(n.target_id) is not None
        ]
        return Reconstruction(
            cue=cue,
            answer=answer,
            explanation_class=ExplanationClass.EXPERIENCE.value,
            confidence=0.9,
            primary_concept_id=concept_ids[0] if concept_ids else "",
            activated_concept_ids=concept_ids,
            activation=field.to_public(),
            cue_classes=list(field.cue_classes),
            goal_influenced=field.goal_influenced,
            identity_influenced=field.identity_influenced,
            context_influenced=field.context_influenced,
            working_influenced=field.working_influenced,
        )

    def _format_explanation(self, cue: str) -> str:
        """Derive a lineage explanation from preference attribute versions."""
        cue_l = (cue or "").strip()

        m = _WHY_NOT_ACTIVE.search(cue_l)
        if m:
            value = _clean_value(m.group(1))
            return self._explain_why_not_active(value)

        m = _WHAT_REPLACED.search(cue_l)
        if m:
            value = _clean_value(m.group(1))
            return self._explain_what_replaced(value)

        m = _WHY_FAVORITE.search(cue_l)
        if m:
            value = _clean_value(m.group(1))
            domain = _normalize_domain(m.group(2))
            return self._explain_why_favorite(value, domain)

        m = _WHY_ACTIVE.search(cue_l)
        if m:
            value = _clean_value(m.group(1))
            return self._explain_why_active(value)

        return ""

    def _iter_preference_attrs(self) -> list[tuple[Any, Any]]:
        """All favorite_* attributes across concepts (active and retired)."""
        pairs: list[tuple[Any, Any]] = []
        for concept in self.store.concepts.values():
            for attr in concept.attributes:
                if attr.key.startswith("favorite_"):
                    pairs.append((concept, attr))
        return pairs

    def _find_attr_by_value(
        self, value: str, *, active: bool | None = None
    ) -> tuple[Any, Any] | None:
        needle = (value or "").strip().lower()
        if not needle:
            return None
        best: tuple[Any, Any] | None = None
        for concept, attr in self._iter_preference_attrs():
            if active is not None and bool(attr.active) != active:
                continue
            aval = (attr.value or "").strip().lower()
            if aval == needle or needle in aval or aval in needle:
                if best is None or attr.version > best[1].version:
                    best = (concept, attr)
        return best

    def _active_successor(self, key: str, concept: Any) -> Any | None:
        for attr in concept.attributes:
            if attr.key == key and attr.active:
                return attr
        # Sibling concepts may hold the same favorite_* key after updates.
        for other in self.store.concepts.values():
            for attr in other.attributes:
                if attr.key == key and attr.active:
                    return attr
        return None

    def _explain_why_not_active(self, value: str) -> str:
        hit = self._find_attr_by_value(value, active=False)
        if hit is None:
            # Value might still be active — say so from evidence.
            active_hit = self._find_attr_by_value(value, active=True)
            if active_hit is not None:
                return _lead_cap(
                    f"{active_hit[1].value} is currently active in your memory — "
                    "it has not been retired."
                )
            return ""
        concept, retired = hit
        successor = self._active_successor(retired.key, concept)
        pretty = retired.key.replace("favorite_", "favorite ").replace("_", " ")
        if successor is not None:
            return _lead_cap(
                f"{retired.value} was replaced when you later taught that your "
                f"{pretty} is {successor.value}. {retired.value} remains in your "
                "evidence as a retired memory."
            )
        return _lead_cap(
            f"{retired.value} is retired in your evidence for {pretty}. "
            "No active replacement is currently recorded."
        )

    def _explain_what_replaced(self, value: str) -> str:
        hit = self._find_attr_by_value(value, active=False)
        if hit is None:
            return ""
        concept, retired = hit
        successor = self._active_successor(retired.key, concept)
        if successor is None:
            return ""
        return _lead_cap(
            f"{successor.value} replaced {retired.value}. "
            f"{retired.value} remains in your evidence as a retired memory."
        )

    def _explain_why_favorite(self, value: str, domain: str) -> str:
        domain = _normalize_domain(domain)
        # Prefer active attr matching value+domain; fall back to any matching key.
        active_match: tuple[Any, Any] | None = None
        for concept, attr in self._iter_preference_attrs():
            if not attr.active:
                continue
            ad = _attr_domain(attr.key) or ""
            if ad != domain and not ad.startswith(domain + "_"):
                continue
            aval = (attr.value or "").strip().lower()
            if aval == value.lower() or value.lower() in aval or aval in value.lower():
                active_match = (concept, attr)
                break
        if active_match is None:
            for concept, attr in self._iter_preference_attrs():
                if not attr.active:
                    continue
                ad = _attr_domain(attr.key) or ""
                if ad == domain or ad.startswith(domain + "_"):
                    active_match = (concept, attr)
                    break
        if active_match is None:
            return ""
        concept, active = active_match
        pretty = active.key.replace("favorite_", "favorite ").replace("_", " ")
        retired_prior = [
            a
            for a in concept.attributes
            if a.key == active.key and not a.active and a.version < active.version
        ]
        if not retired_prior:
            # Scan other concepts for earlier retired versions of same key.
            for other in self.store.concepts.values():
                for a in other.attributes:
                    if a.key == active.key and not a.active and a.version < active.version:
                        retired_prior.append(a)
        if retired_prior:
            prior = max(retired_prior, key=lambda a: a.version)
            return _lead_cap(
                f"{active.value} is your current {pretty} because you later taught "
                f"that after {prior.value}. {prior.value} remains in your evidence "
                "as a retired memory."
            )
        return _lead_cap(
            f"{active.value} is your current {pretty} because you taught that "
            "preference, and it is the active value in your evidence."
        )

    def _explain_why_active(self, value: str) -> str:
        hit = self._find_attr_by_value(value, active=True)
        if hit is None:
            return ""
        concept, active = hit
        pretty = active.key.replace("favorite_", "favorite ").replace("_", " ")
        retired_prior = [
            a
            for a in concept.attributes
            if a.key == active.key and not a.active and a.version < active.version
        ]
        for other in self.store.concepts.values():
            for a in other.attributes:
                if a.key == active.key and not a.active and a.version < active.version:
                    if a not in retired_prior:
                        retired_prior.append(a)
        if retired_prior:
            prior = max(retired_prior, key=lambda a: a.version)
            return _lead_cap(
                f"{active.value} is active because you later taught that your "
                f"{pretty} is {active.value}, replacing {prior.value}. "
                f"{prior.value} remains retired in your evidence."
            )
        return _lead_cap(
            f"{active.value} is active because you taught that your {pretty} "
            "is that value, and no later teaching has superseded it."
        )

    def _reconstruct_personal_summary(
        self,
        cue: str,
        field: ActivationField,
        ranked: list[Any],
    ) -> Reconstruction:
        """Active-only personal summary from identity + preference memories."""
        lines: list[str] = []
        concept_ids: list[str] = []

        # Identity (user schema) — active only.
        if self.identity is not None:
            try:
                rendered = self.identity.render_user_identity()
                text = (rendered or {}).get("answer") or ""
                if text.strip():
                    for part in re.split(r"(?<=\.)\s+", text.strip()):
                        if part.strip():
                            lines.append(part.strip())
                    uid = ((rendered or {}).get("schemas") or {}).get("user", {}).get(
                        "concept_id"
                    )
                    if uid:
                        concept_ids.append(uid)
            except Exception:
                pass

        # Active favorite_* across all preference concepts.
        seen_keys: set[str] = set()
        favorites: list[tuple[str, str, str]] = []  # (sort, pretty, value)
        for concept in self.store.concepts.values():
            for attr in concept.attributes:
                if not attr.active or not attr.key.startswith("favorite_"):
                    continue
                if attr.key in seen_keys:
                    continue
                if not _is_semantic_attr(attr):
                    continue
                seen_keys.add(attr.key)
                pretty = attr.key.replace("favorite_", "favorite ").replace("_", " ")
                favorites.append((attr.key, pretty, str(attr.value)))
                if concept.id not in concept_ids:
                    concept_ids.append(concept.id)

        for _, pretty, value in sorted(favorites, key=lambda t: t[0]):
            lines.append(f"Your {pretty} is {value}.")

        if not lines:
            return Reconstruction(
                cue=cue,
                answer="I don't currently know.",
                explanation_class=ExplanationClass.UNKNOWN.value,
                confidence=0.0,
                activation=field.to_public(),
                cue_classes=list(field.cue_classes),
            )

        answer = "\n".join(lines)
        return Reconstruction(
            cue=cue,
            answer=answer,
            explanation_class=ExplanationClass.EXPERIENCE.value,
            confidence=0.9,
            primary_concept_id=concept_ids[0] if concept_ids else "",
            activated_concept_ids=concept_ids
            or [n.target_id for n in ranked],
            activation=field.to_public(),
            cue_classes=list(field.cue_classes),
            goal_influenced=field.goal_influenced,
            identity_influenced=field.identity_influenced,
            context_influenced=field.context_influenced,
            working_influenced=field.working_influenced,
        )

    # --- side effects on cognition (not history) -------------------------------

    def _reconsolidate(self, reconstruction: Reconstruction, cue: str) -> None:
        cid = reconstruction.primary_concept_id
        if not cid:
            return
        # Memory Authority: do not reinforce confidence on unknown / weak recall
        if reconstruction.explanation_class == ExplanationClass.UNKNOWN.value:
            return
        if float(reconstruction.confidence or 0.0) < 0.45:
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
        self.validation.record_reconsolidation(concept_id=concept.id, kind="light", query=cue[:80])
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
            ExplanationClass.EXPERIENCE: ("I remembered this from something you shared with me."),
            ExplanationClass.REPEATED: ("This strengthened because it has appeared repeatedly."),
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


def _cue_tokens(cue: str) -> list[str]:
    """Normalize cue tokens — strip punctuation so 'color?' matches 'color'."""
    out: list[str] = []
    for raw in (cue or "").lower().split():
        tok = re.sub(r"[^\w]+", "", raw)
        if len(tok) > 2:
            out.append(tok)
    return out


def _normalize_domain(domain: str) -> str:
    """Collapse spelling variants so color/colour compete as one domain."""
    d = (domain or "").strip().lower().replace(" ", "_")
    return d.replace("colour", "color")


def _preference_domain(cue: str) -> str | None:
    """Return favorite-<domain> named by the cue, or None if unspecified."""
    m = _FAVORITE_DOMAIN.search(cue or "")
    if not m:
        return None
    domain = re.sub(r"[^\w\s]+", "", m.group(1)).strip().lower()
    if not domain or domain in _GENERIC_PREF_TOKENS or domain in {"is", "are", "was", "my"}:
        return None
    return _normalize_domain(domain)


def _attr_domain(attr_key: str) -> str | None:
    if not attr_key.startswith("favorite_"):
        return None
    return _normalize_domain(attr_key[len("favorite_") :])


def _concept_matches_preference_domain(concept: Concept, domain: str) -> bool:
    domain = _normalize_domain(domain)
    for a in concept.attributes:
        ad = _attr_domain(a.key)
        if ad and (ad == domain or ad.startswith(domain + "_")):
            return True
    needle = domain.replace("_", " ")
    return any(
        needle in (lab or "").lower().replace("colour", "color")
        for lab in (concept.labels or ())
    )


def _attr_grounds_in_cue(
    attr: Any, tokens: list[str], *, domain: str | None = None
) -> bool:
    """Whether an attribute is a legitimate grounding for this cue."""
    if attr.key.startswith("favorite_"):
        attr_domain = _attr_domain(attr.key) or ""
        if domain:
            domain = _normalize_domain(domain)
            return attr_domain == domain or attr_domain.startswith(domain + "_")
        # No named domain: require a non-generic cue token in key or value so
        # "favorite" alone cannot make every favorite_* answerable.
        specific = [t for t in tokens if t not in _GENERIC_PREF_TOKENS]
        if not specific:
            return True
        return any(t in attr.key or t in (attr.value or "").lower() for t in specific)
    return any(tok in attr.key or tok in (attr.value or "").lower() for tok in tokens)


def _is_evidence_request(cue: str) -> bool:
    return bool(_EVIDENCE_REQUEST.search(cue or ""))


def _is_explanation_request(cue: str) -> bool:
    cue = cue or ""
    return bool(
        _WHY_FAVORITE.search(cue)
        or _WHY_NOT_ACTIVE.search(cue)
        or _WHY_ACTIVE.search(cue)
        or _WHAT_REPLACED.search(cue)
    )


def _is_personal_summary_request(cue: str) -> bool:
    return bool(_PERSONAL_SUMMARY.search(cue or ""))


def _clean_value(raw: str) -> str:
    return re.sub(r"[^\w\s\-']+", "", (raw or "").strip()).strip()


def _lead_cap(text: str) -> str:
    """Capitalize the first alphabetic character for spoken explanations."""
    s = (text or "").strip()
    if not s:
        return s
    for i, ch in enumerate(s):
        if ch.isalpha():
            return s[:i] + ch.upper() + s[i + 1 :]
    return s


def _cue_relevant(
    concept: Concept, tokens: list[str], *, domain: str | None = None
) -> bool:
    if not tokens and not domain:
        return False
    if domain and _concept_matches_preference_domain(concept, domain):
        return True
    specific = [t for t in tokens if t not in _GENERIC_PREF_TOKENS]
    blob = " ".join(concept.labels).lower()
    if specific and any(tok in blob for tok in specific):
        return True
    for attr in concept.attributes:
        if not attr.active:
            continue
        if _attr_grounds_in_cue(attr, tokens, domain=domain):
            return True
    # Fall back to generic token label match only when no preference domain
    # was named (avoids every 'favorite *' label matching on 'favorite').
    if domain is None and any(tok in blob for tok in tokens):
        return True
    return False


def _is_semantic_attr(attr: Any) -> bool:
    """True when an attribute carries independently answerable semantic content."""
    if not getattr(attr, "active", False):
        return False
    if attr.key in LEXICAL_SUPPORT_KEYS:
        return False
    if _INTERROGATIVE_VALUE.search(attr.value or ""):
        return False
    # Non-user artifacts must never render as preferences/identity, even if a
    # contaminated attribute somehow remains after cleanup.
    from acm.provenance.legacy_cleanup import classify_untrusted_artifact

    if classify_untrusted_artifact(str(attr.value or "")):
        return False
    return True


def _answerable(
    concept: Concept, tokens: list[str], *, domain: str | None = None
) -> bool:
    """D045 + M0K: can this concept satisfy the reconstruction request itself?

    True only when the concept holds at least one active *semantic* attribute
    that grounds in the cue. When the cue names a favorite <domain>, only that
    domain's favorite_* attributes count — sibling preference domains never
    answer or compete.
    """
    if not tokens and not domain:
        return False
    for attr in concept.attributes:
        if not _is_semantic_attr(attr):
            continue
        if _attr_grounds_in_cue(attr, tokens, domain=domain):
            return True
    return False
