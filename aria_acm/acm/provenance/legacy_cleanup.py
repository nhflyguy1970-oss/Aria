"""Legacy memory contamination cleanup — one-time D047 migration.

D046 (Trusted Memory Ingestion) rejects untrusted sources before Semantic
Extraction, but it intentionally never rewrites existing semantic memory.
Autobiographical memories encoded *before* D046 therefore may still contain
tool output, diagnostic output, system messages, and other non-user cognitive
artifacts, and those artifacts are still recallable.

This module implements the separately approved remediation:

- Experiences that carry recorded D046 source metadata are re-evaluated under
  the current trust policy and removed fail-closed when the recorded source is
  ineligible (covers imported snapshots with fabricated source metadata).
- Legacy experiences (external encodes that predate D046, identified by
  ``semantic_extraction`` metadata without ``source_actor``) cannot be judged
  by provenance alone — the trust boundary did not exist when they were
  written. They are removed only when their original evidence text bears an
  affirmative non-user artifact signature (tool wrappers, memory-search
  output, diagnostics, reflection traces, system messages, prompt fragments,
  infrastructure logs, implementation metadata). Legacy memories without such
  a signature are presumed legitimate user knowledge and preserved.
- Internal cognition (Reflection organ births, goal completion) is never
  external ingestion and is never touched.

The migration is idempotent: running it on an already-clean graph removes
nothing and mutates nothing.
"""

from __future__ import annotations

import re
from time import time
from typing import Any

from acm.provenance.ingestion import (
    HostOperation,
    IngestionActor,
    IngestionProvenance,
    MessageRole,
    evaluate_ingestion,
)

# Affirmative non-user artifact signatures for legacy (pre-D046) records.
# Conservative by design: ordinary first-person user knowledge must never match.
_ARTIFACT_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "tool_output",
        re.compile(
            r"(?:^\s*tool\s+\w+\s+(?:worked|failed|succeeded|returned|executed|completed)\b)"
            r"|(?:^\s*\[tool\])"
            r"|(?:\btool\s+(?:output|result|execution|call)\s*[:\-])",
            re.IGNORECASE,
        ),
    ),
    (
        "memory_search_output",
        re.compile(
            r"(?:^\s*memory[_ ]search\b)"
            r"|(?:\bmemory[_ ]search\s+(?:output|result|results)\b)"
            r"|(?:\bsearch\s+results?\s*[:\-])"
            r"|(?:\bretrieved\s+\d+\s+(?:memories|results|entries)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "diagnostic_output",
        re.compile(
            r"(?:^\s*diagnostics?\s*[:\-])"
            r"|(?:\bdiagnostic\s+(?:output|report|probe|trace)\b)"
            r"|(?:^\s*(?:trace|probe)\s*[:\-])",
            re.IGNORECASE,
        ),
    ),
    (
        "reflection_output",
        re.compile(
            r"(?:^\s*reflection(?:\s+(?:trace|output|report))?\s*[:\-])",
            re.IGNORECASE,
        ),
    ),
    (
        "system_message",
        re.compile(
            r"(?:^\s*\[system\])|(?:^\s*system(?:\s+message)?\s*[:\-])",
            re.IGNORECASE,
        ),
    ),
    (
        "prompt_fragment",
        re.compile(
            r"(?:^\s*(?:system\s+)?prompt\s*[:\-])|(?:\byou\s+are\s+an?\s+(?:ai|assistant)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "infrastructure_log",
        re.compile(
            r"(?:^\s*\[?(?:info|warn|warning|error|debug|critical)\]?\s*[:\]])"
            r"|(?:^\s*\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"
            r"|(?:\binfrastructure\s+(?:log|message)\s*[:\-]?)",
            re.IGNORECASE,
        ),
    ),
    (
        "implementation_metadata",
        re.compile(
            r"(?:^\s*(?:implementation\s+)?metadata\s*[:\-])|(?:^\s*\{\s*\")",
            re.IGNORECASE,
        ),
    ),
)

# Minimum length before substring payload matching may condemn an attribute
# value — prevents short token values ("favorite", "color") from matching.
_PAYLOAD_SUBSTRING_MIN = 20


def classify_untrusted_artifact(text: str) -> str | None:
    """Return the artifact class if ``text`` bears a non-user signature."""
    t = (text or "").strip()
    if not t:
        return None
    for name, pattern in _ARTIFACT_SIGNATURES:
        if pattern.search(t):
            return name
    return None


def _recorded_provenance(md: dict[str, str]) -> IngestionProvenance:
    """Rebuild the recorded D046 source declaration; bad values fail closed."""

    def _coerce(enum_cls: Any, raw: str) -> Any:
        try:
            return enum_cls(raw)
        except ValueError:
            return enum_cls.UNKNOWN

    return IngestionProvenance(
        actor=_coerce(IngestionActor, md.get("source_actor", "")),
        host_operation=_coerce(HostOperation, md.get("source_host_operation", "")),
        message_role=_coerce(MessageRole, md.get("source_message_role", "")),
    )


def _rejection_reason(exp: Any) -> str | None:
    """Why this Experience would be rejected under the D046 trust policy.

    Returns ``None`` for experiences that are preserved.
    """
    md = exp.meta_dict()
    if "source_actor" in md:
        # D046-era record — re-evaluate the recorded source, fail closed.
        decision = evaluate_ingestion(_recorded_provenance(md))
        if decision.eligible:
            return None
        return f"recorded_source_ineligible:{decision.reason}"
    if "semantic_extraction" not in md:
        # Internal cognition (Reflection organ, goal completion) — not external
        # ingestion; never subject to this cleanup.
        return None
    # Legacy external encode (pre-D046): classify original evidence text.
    for text in (md.get("evidence", ""), exp.summary):
        artifact = classify_untrusted_artifact(text)
        if artifact:
            return f"legacy_untrusted_artifact:{artifact}"
    return None


def _normalize(value: str) -> str:
    return (value or "").strip().rstrip(".").lower()


def _contaminated_fact_pairs(exp: Any) -> set[tuple[str, str]]:
    """(property, value) fact pairs extracted from a contaminated encode."""
    md = exp.meta_dict()
    pairs: set[tuple[str, str]] = set()
    for i in range(12):
        prop = md.get(f"fact_{i}_property")
        value = md.get(f"fact_{i}_value")
        if prop and value:
            pairs.add((prop, _normalize(value)))
    return pairs


def _attribute_contaminated(
    attr: Any,
    *,
    fact_pairs: set[tuple[str, str]],
    payload_texts: list[str],
    contaminated_ids: set[str],
) -> bool:
    if (attr.key, _normalize(attr.value)) in fact_pairs:
        return True
    if attr.evidence_ids and all(eid in contaminated_ids for eid in attr.evidence_ids):
        return True
    value_l = _normalize(attr.value)
    if not value_l:
        return False
    for payload in payload_texts:
        payload_l = _normalize(payload)
        if not payload_l:
            continue
        if value_l == payload_l:
            return True
        if len(value_l) >= _PAYLOAD_SUBSTRING_MIN and value_l in payload_l:
            return True
    return False


def cleanup_legacy_contamination(engine: Any) -> dict[str, Any]:
    """One-time, idempotent removal of autobiographical contamination.

    Removes Experiences whose provenance would be rejected under the D046
    trust policy, the Concepts/attributes derived solely from them, and the
    provenance records of the removed artifacts. Legitimate user memories —
    identity, preferences, relationships — and valid provenance are preserved.
    Attributes that a contaminated encode superseded are reactivated.
    """
    store = engine.store
    reasons: dict[str, str] = {}
    for exp in store.experiences.values():
        reason = _rejection_reason(exp)
        if reason:
            reasons[exp.id] = reason
    contaminated_ids = set(reasons)

    fact_pairs: set[tuple[str, str]] = set()
    payload_texts: list[str] = []
    for exp_id in contaminated_ids:
        exp = store.experiences[exp_id]
        fact_pairs |= _contaminated_fact_pairs(exp)
        payload_texts.append(exp.summary)
        evidence = exp.meta_dict().get("evidence", "")
        if evidence:
            payload_texts.append(evidence)

    removed_concepts: list[str] = []
    removed_attributes = 0
    reactivated_attributes = 0

    for concept in list(store.concepts.values()):
        original_evidence = list(concept.evidence_ids)
        # Concepts born exclusively from contaminated encodes are removed whole.
        if original_evidence and all(eid in contaminated_ids for eid in original_evidence):
            removed_concepts.append(concept.id)
            continue

        # Strip contaminated lineage from surviving concepts.
        concept.evidence_ids[:] = [
            eid for eid in concept.evidence_ids if eid not in contaminated_ids
        ]
        concept.exemplar_ids[:] = [
            eid for eid in concept.exemplar_ids if eid not in contaminated_ids
        ]

        deactivated_keys: set[str] = set()
        kept: list[Any] = []
        for attr in concept.attributes:
            if contaminated_ids and _attribute_contaminated(
                attr,
                fact_pairs=fact_pairs,
                payload_texts=payload_texts,
                contaminated_ids=contaminated_ids,
            ):
                removed_attributes += 1
                if attr.active:
                    deactivated_keys.add(attr.key)
                continue
            attr.evidence_ids[:] = [eid for eid in attr.evidence_ids if eid not in contaminated_ids]
            kept.append(attr)
        concept.attributes[:] = kept

        # A contaminated value may have superseded a legitimate one (D045-era
        # attribute versioning). Restore the newest surviving version.
        for key in deactivated_keys:
            if any(a.key == key and a.active for a in concept.attributes):
                continue
            candidates = [a for a in concept.attributes if a.key == key]
            if candidates:
                restored = max(candidates, key=lambda a: a.version)
                restored.active = True
                reactivated_attributes += 1
                concept.prototype.features[key] = restored.value
            else:
                concept.prototype.features.pop(key, None)
                concept.prototype.feature_weights.pop(key, None)

    removed_concept_ids = set(removed_concepts)
    for cid in removed_concepts:
        store.concepts.pop(cid, None)

    # Repair hierarchy / instance links on surviving concepts.
    if removed_concept_ids:
        for concept in store.concepts.values():
            concept.parent_ids[:] = [i for i in concept.parent_ids if i not in removed_concept_ids]
            concept.child_ids[:] = [i for i in concept.child_ids if i not in removed_concept_ids]
            concept.instance_ids[:] = [
                i for i in concept.instance_ids if i not in removed_concept_ids
            ]

    removed_associations = 0
    for aid, assoc in list(store.associations.items()):
        if assoc.source_id in removed_concept_ids or assoc.target_id in removed_concept_ids:
            del store.associations[aid]
            removed_associations += 1

    # Remove contaminated Experiences and their organ-level state.
    organ = getattr(engine, "experiences", None)
    removed_links = 0
    for exp_id in contaminated_ids:
        exp = store.experiences.pop(exp_id, None)
        if organ is not None:
            organ._state.pop(exp_id, None)
            if exp is not None:
                fp = exp.summary.lower()
                count = organ._summary_counts.get(fp, 0)
                if count <= 1:
                    organ._summary_counts.pop(fp, None)
                else:
                    organ._summary_counts[fp] = count - 1
    if organ is not None:
        for lid, link in list(organ.links.items()):
            if link.source_id in contaminated_ids or link.target_id in contaminated_ids:
                del organ.links[lid]
                removed_links += 1
        # Hierarchy edges are organ-held; drop edges touching removed concepts.
        concepts_organ = getattr(engine, "concepts", None)
        if concepts_organ is not None and removed_concept_ids:
            for hid, edge in list(concepts_organ.hierarchy.items()):
                if edge.child_id in removed_concept_ids or edge.parent_id in removed_concept_ids:
                    del concepts_organ.hierarchy[hid]

    # Working focus must not retain removed artifacts.
    buffer = getattr(engine, "buffer", None)
    if buffer is not None and (removed_concept_ids or contaminated_ids):
        gone = removed_concept_ids | contaminated_ids
        survivors = [item for item in buffer.items() if item.ref_id not in gone]
        buffer.clear()
        for item in reversed(survivors):
            buffer.push(item)

    # Provenance of removed artifacts is removed; valid provenance is preserved.
    removed_artifacts = contaminated_ids | removed_concept_ids
    removed_provenance = 0
    for pid, record in list(store.provenance.items()):
        if record.artifact_id in removed_artifacts:
            del store.provenance[pid]
            removed_provenance += 1

    validation = getattr(engine, "validation", None)
    if validation is not None:
        from acm.validation.harness import LifecycleEvent

        for exp_id, reason in reasons.items():
            validation.record_lifecycle(LifecycleEvent(time(), "legacy_cleanup", exp_id, reason))

    flushed = False
    if reasons and getattr(engine, "durable", None) is not None:
        engine.flush(kind="legacy_cleanup")
        flushed = True

    return {
        "schema": "legacy_memory_cleanup.v1",
        "clean": not reasons,
        "examined_experiences": len(store.experiences) + len(contaminated_ids),
        "removed_experiences": len(contaminated_ids),
        "removed_experience_ids": sorted(contaminated_ids),
        "reasons": dict(sorted(reasons.items())),
        "removed_concepts": len(removed_concepts),
        "removed_concept_ids": sorted(removed_concepts),
        "removed_attributes": removed_attributes,
        "reactivated_attributes": reactivated_attributes,
        "removed_associations": removed_associations,
        "removed_links": removed_links,
        "removed_provenance": removed_provenance,
        "flushed": flushed,
    }


__all__ = [
    "classify_untrusted_artifact",
    "cleanup_legacy_contamination",
]
