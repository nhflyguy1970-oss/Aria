"""Analogical Reasoning organ — M14."""

from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Any

from acm.analogy.model import AnalogyAlignment, AnalogyMapping
from acm.associations.model import RelationKind
from acm.types import new_id

if TYPE_CHECKING:
    from acm.activation.engine import ActivationEngine
    from acm.associations.organ import AssociationOrgan
    from acm.attention.organ import AttentionOrgan
    from acm.core.store import CognitiveStore
    from acm.forgetting.organ import ForgettingOrgan
    from acm.validation.harness import ValidationHarness


class AnalogyOrgan:
    """Answers: What existing memories are analogous even when they appear different?"""

    def __init__(
        self,
        store: CognitiveStore,
        validation: ValidationHarness,
        *,
        activation: ActivationEngine | None = None,
        associations: AssociationOrgan | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        self.store = store
        self.validation = validation
        self.activation = activation
        self.associations = associations
        self.attention = attention
        self.forgetting = forgetting
        self._mappings = 0

    def bind(
        self,
        *,
        activation: ActivationEngine | None = None,
        associations: AssociationOrgan | None = None,
        attention: AttentionOrgan | None = None,
        forgetting: ForgettingOrgan | None = None,
    ) -> None:
        if activation is not None:
            self.activation = activation
        if associations is not None:
            self.associations = associations
        if attention is not None:
            self.attention = attention
        if forgetting is not None:
            self.forgetting = forgetting

    def what_is_analogous(
        self,
        cue: str,
        *,
        other: str = "",
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.55,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Cognitive question M14."""
        maps = self.find_analogies(
            cue,
            other=other,
            context_tags=context_tags,
            attention_weight=attention_weight,
            limit=limit,
        )
        if not maps:
            answer = "No clear analogical mappings emerge from current memory yet."
        else:
            bits = [
                f"{m.source_label} ↔ {m.target_label} (~{m.confidence:.0%})"
                for m in maps[:3]
            ]
            answer = "Analogous memories: " + "; ".join(bits)
        return {
            "question": "What existing memories are analogous even when they appear different?",
            "answer": answer,
            "analogies": [m.to_public() for m in maps],
            "plans": False,
            "decides": False,
            "executive": False,
        }

    def find_analogies(
        self,
        cue: str,
        *,
        other: str = "",
        context_tags: tuple[str, ...] = (),
        attention_weight: float = 0.55,
        limit: int = 5,
    ) -> list[AnalogyMapping]:
        if self.activation is None:
            raise RuntimeError("Analogy requires ActivationEngine")
        field_a = self.activation.activate(
            cue, context_tags=context_tags, attention_weight=attention_weight
        )
        seeds_a = [n.target_id for n in field_a.ranked_concepts(limit=6)]
        if other:
            field_b = self.activation.activate(
                other, context_tags=context_tags, attention_weight=attention_weight
            )
            seeds_b = [n.target_id for n in field_b.ranked_concepts(limit=6)]
        else:
            # Cross-domain: use far neighbors / clusters as candidate targets
            seeds_b = self._distant_candidates(seeds_a)
        mappings: list[AnalogyMapping] = []
        for sid in seeds_a[:4]:
            source = self.store.concepts.get(sid)
            if source is None:
                continue
            for tid in seeds_b[:8]:
                if tid == sid:
                    continue
                target = self.store.concepts.get(tid)
                if target is None:
                    continue
                mapping = self._map_pair(cue, source, target)
                if mapping and mapping.confidence >= 0.18:
                    mappings.append(mapping)
        mappings.sort(key=lambda m: m.confidence, reverse=True)
        kept: list[AnalogyMapping] = []
        seen_pairs: set[tuple[str, str]] = set()
        for m in mappings:
            key = tuple(sorted((m.source_id, m.target_id)))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            self.store.analogies[m.id] = m
            kept.append(m)
            self._mappings += 1
            self.validation.record_analogy(
                action="map",
                analogy_id=m.id,
                confidence=m.confidence,
                alignment_count=len(m.alignments),
                analogy=1,
                transfer=1 if m.alignments else 0,
            )
            if len(kept) >= limit:
                break
        return kept

    def observables(self) -> dict[str, Any]:
        return {
            "mappings": self._mappings,
            "stored": len(self.store.analogies),
            "avg_confidence": (
                sum(a.confidence for a in self.store.analogies.values())
                / max(1, len(self.store.analogies))
            ),
        }

    def _distant_candidates(self, seed_ids: list[str]) -> list[str]:
        out: list[str] = []
        for cid in seed_ids:
            for edge, neighbor in self.store.neighbors(cid):
                if neighbor.id in seed_ids:
                    continue
                # Prefer resembles / far / unexpected style links
                if edge.relation == RelationKind.RESEMBLES:
                    out.append(neighbor.id)
                elif max(edge.strength_forward, edge.strength_backward) < 0.35:
                    out.append(neighbor.id)
                else:
                    # Second hop
                    for _e2, n2 in self.store.neighbors(neighbor.id):
                        if n2.id not in seed_ids and n2.id != cid:
                            out.append(n2.id)
        # Also sibling resembles via shared parents
        for cid in seed_ids:
            c = self.store.concepts.get(cid)
            if not c:
                continue
            for pid in c.parent_ids:
                p = self.store.concepts.get(pid)
                if not p:
                    continue
                for child in p.child_ids:
                    if child not in seed_ids:
                        out.append(child)
        return list(dict.fromkeys(out))[:16]

    def _map_pair(self, cue: str, source: Any, target: Any) -> AnalogyMapping | None:
        why: list[str] = []
        alignments: list[AnalogyAlignment] = []
        score = 0.0

        # Shared parents → structural family
        shared_parents = set(source.parent_ids) & set(target.parent_ids)
        if shared_parents:
            score += 0.25
            why.append("shared_parent")
            for pid in list(shared_parents)[:2]:
                p = self.store.concepts.get(pid)
                alignments.append(
                    AnalogyAlignment(
                        source_concept_id=source.id,
                        target_concept_id=target.id,
                        source_label=source.labels[0] if source.labels else source.id,
                        target_label=target.labels[0] if target.labels else target.id,
                        relation="shared_parent",
                        strength=0.55,
                        why=["hierarchy"],
                    )
                )
                if p and p.labels:
                    alignments[-1].why.append(f"parent:{p.labels[0]}")

        # Direct resembles
        for edge in self.store.associations.values():
            if not edge.active:
                continue
            pair = {edge.source_id, edge.target_id}
            if pair != {source.id, target.id}:
                continue
            if edge.relation == RelationKind.RESEMBLES:
                score += 0.35 * max(edge.strength_forward, edge.strength_backward)
                why.append("resembles")
                alignments.append(
                    AnalogyAlignment(
                        source_concept_id=source.id,
                        target_concept_id=target.id,
                        source_label=source.labels[0] if source.labels else source.id,
                        target_label=target.labels[0] if target.labels else target.id,
                        relation="resembles",
                        strength=max(edge.strength_forward, edge.strength_backward),
                        why=["direct_resemblance"],
                    )
                )

        # Relational pattern: same relation kinds to neighbors
        rels_s = self._relation_signature(source.id)
        rels_t = self._relation_signature(target.id)
        shared_rels = set(rels_s) & set(rels_t)
        if shared_rels:
            score += 0.08 * len(shared_rels)
            why.append("relation_pattern")
            for rel in list(shared_rels)[:3]:
                alignments.append(
                    AnalogyAlignment(
                        source_concept_id=source.id,
                        target_concept_id=target.id,
                        source_label=source.labels[0] if source.labels else source.id,
                        target_label=target.labels[0] if target.labels else target.id,
                        relation=rel,
                        strength=0.4,
                        why=["structural_correspondence", rel],
                    )
                )

        # Role / attribute soft overlap
        if source.role == target.role and source.role.value != "other":
            score += 0.1
            why.append("same_role")
        src_keys = {a.key for a in source.attributes if a.active}
        tgt_keys = {a.key for a in target.attributes if a.active}
        if src_keys & tgt_keys:
            score += 0.12
            why.append("attribute_overlap")

        if self.attention is not None:
            score *= 0.85 + 0.15 * (
                (
                    self.attention.priority_of(source.id)
                    + self.attention.priority_of(target.id)
                )
                / 2
            )
        if self.forgetting is not None:
            score *= 0.5 * (
                self.forgetting.factor(source.id) + self.forgetting.factor(target.id)
            )

        # Learning residue improves confidence modestly
        score = min(0.92, score + min(0.1, len(self.store.adaptations) * 0.008))
        # Offline / accessibility events as consolidation aid
        score = min(0.95, score + min(0.06, len(self.store.accessibility_events) * 0.001))

        if score < 0.18:
            return None
        src_lab = source.labels[0] if source.labels else source.id
        tgt_lab = target.labels[0] if target.labels else target.id
        transfer = (
            f"Structure of '{src_lab}' aligns with '{tgt_lab}' "
            f"via {', '.join(dict.fromkeys(why) or ['pattern'])}."
        )
        return AnalogyMapping(
            id=new_id("anl"),
            cue=cue[:160],
            source_id=source.id,
            target_id=target.id,
            source_label=src_lab,
            target_label=tgt_lab,
            confidence=score,
            alignments=alignments[:8],
            created=time(),
            transfer_summary=transfer,
            why=list(dict.fromkeys(why)),
        )

    def _relation_signature(self, concept_id: str) -> list[str]:
        kinds: list[str] = []
        for edge in self.store.associations.values():
            if not edge.active:
                continue
            if edge.source_id == concept_id or edge.target_id == concept_id:
                kinds.append(edge.relation.value)
        return list(dict.fromkeys(kinds))
