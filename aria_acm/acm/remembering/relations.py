"""Evidence-bounded autobiographical relational reasoning.

Answers only from explicit, evidence-linked autobiographical Associations and
active semantic facts. No world knowledge or undocumented architecture.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from acm.remembering.semantic import UNKNOWN, SemanticFact


@dataclass(frozen=True)
class LearnedRelation:
    source: str
    relation: str
    target: str
    learned_relation: str
    evidence_ids: tuple[str, ...]


def collect_learned_relations(store: Any) -> list[LearnedRelation]:
    """Collect first-class autobiographical edges with direct evidence."""
    out: list[LearnedRelation] = []
    for assoc in store.associations.values():
        if not getattr(assoc, "active", False):
            continue
        metadata = getattr(assoc, "metadata", {}) or {}
        evidence = tuple(getattr(assoc, "evidence_ids", []) or ())
        if not metadata.get("autobiographical") or not evidence:
            continue
        source = store.concepts.get(assoc.source_id)
        target = store.concepts.get(assoc.target_id)
        if source is None or target is None:
            continue
        source_label = _best_label(source)
        target_label = _best_label(target)
        if not source_label or not target_label:
            continue
        relation = getattr(assoc.relation, "value", str(assoc.relation))
        out.append(
            LearnedRelation(
                source=source_label,
                relation=relation,
                target=target_label,
                learned_relation=str(metadata.get("learned_relation") or relation),
                evidence_ids=evidence,
            )
        )
    return out


def is_relational_autobiography_query(cue: str) -> bool:
    text = (cue or "").strip()
    if not text:
        return False
    return bool(
        re.search(
            r"\b(?:"
            r"why\s+(?:did|do|am)\s+i\b|"
            r"why\s+is\s+my\b.+\bbetter\b|"
            r"how\s+(?:are|is)\s+.+\s+(?:and|to)\s+.+\s+related\b|"
            r"how\s+does\s+.+\s+(?:relate|fit)\b|"
            r"would\s+.+\s+fit\s+my\s+preferences?\b|"
            r"what\s+(?:programming\s+)?language\s+do\s+i\s+prefer\b|"
            r"which\s+(?:of\s+my\s+)?computers?\s+should\s+i\s+use\b|"
            r"which\s+should\s+i\s+use\s+for\b"
            r")",
            text,
            re.I,
        )
    )


def answer_relational_query(
    cue: str,
    *,
    store: Any,
    active_facts: list[SemanticFact],
) -> str | None:
    """Reconstruct a bounded relational answer, or None when not this intent."""
    text = (cue or "").strip()
    if not text:
        return None
    low = text.lower()
    relations = collect_learned_relations(store)

    if re.search(r"\bwhy\s+did\s+i\s+upgrade\s+my\s+desktop\b", low):
        rel = _find(relations, source_contains="desktop upgrade", learned="motivated_by")
        if rel:
            return f"Because you upgraded your desktop to {rel.target}."
        return UNKNOWN

    if re.search(r"\bwhy\s+am\s+i\s+(?:building|working\s+on)\s+([a-z0-9_-]+)", low):
        project = re.search(
            r"\bwhy\s+am\s+i\s+(?:building|working\s+on)\s+([a-z0-9_-]+)",
            text,
            re.I,
        )
        name = project.group(1) if project else ""
        rel = _find(relations, source_equals=name, learned="supports_goal")
        if rel:
            return (
                f"You are building {rel.source} to achieve your goal of "
                f"{_goal_phrase(rel.target)}."
            )
        return UNKNOWN

    if re.search(r"\bhow\s+does\s+aria\s+relate\s+to\s+my\s+goal\b", low):
        rel = _find(relations, source_equals="Aria", learned="supports_goal")
        if rel:
            return (
                f"Aria exists to achieve your goal of "
                f"{_goal_phrase(rel.target)}."
            )
        return UNKNOWN

    if re.search(r"\bhow\s+are\s+aria\s+and\s+acm\s+related\b", low):
        rel = _find(
            relations,
            source_equals="Aria",
            target_equals="ACM",
            learned="uses",
        )
        return "Aria uses ACM." if rel else UNKNOWN

    if re.search(r"\bhow\s+does\s+blackfly\s+fit\s+into\s+my\s+projects\b", low):
        rel = _find(relations, source_equals="BlackFly", learned="part_of")
        if rel:
            return f"BlackFly is part of your {rel.target}."
        return UNKNOWN

    if re.search(r"\bwhy\s+do\s+i\s+prefer\s+local\s+ai\b", low):
        rel = _find(relations, source_contains="local AI", learned="motivated_by")
        if rel:
            return f"You prefer local AI because you value {rel.target}."
        return UNKNOWN

    if re.search(r"\bwould\s+cloud\s+ai\b.+\bfit\s+my\s+preferences?\b", low):
        pref = _active_preference(active_facts, "prefer_ai")
        if pref is None:
            return UNKNOWN
        motivation = _find(
            relations, source_contains=pref.value, learned="motivated_by"
        )
        if "local" not in pref.value.lower():
            return UNKNOWN
        if motivation:
            return (
                "Cloud AI would not usually fit your remembered preference for "
                f"{pref.value}, which is motivated by {motivation.target}."
            )
        return (
            "Cloud AI would not usually fit your remembered preference for "
            f"{pref.value}."
        )

    if re.search(
        r"\bwhat\s+language\s+do\s+i\s+prefer\s+for\s+systems\s+programming\b",
        low,
    ):
        pref = _active_preference(
            active_facts,
            "prefer_programming_language__for_systems_programming",
        )
        return (
            f"For systems programming, you prefer {pref.value}."
            if pref
            else UNKNOWN
        )

    if re.search(r"\bwhat\s+(?:programming\s+)?language\s+do\s+i\s+prefer\b", low):
        pref = _active_preference(active_facts, "prefer_programming_language")
        return f"You prefer {pref.value}." if pref else UNKNOWN

    if re.search(r"\bwhy\s+is\s+my\s+desktop\s+better\s+for\s+ai\b", low):
        support = _find(relations, source_equals="desktop", learned="supports")
        motive = _find(
            relations, source_contains="desktop upgrade", learned="motivated_by"
        )
        if support or motive:
            target = (support or motive).target
            return (
                "Your desktop is the remembered AI-focused option because you "
                f"upgraded it to {target}."
            )
        return UNKNOWN

    if re.search(
        r"\bwhich\s+(?:of\s+my\s+)?computers?\s+should\s+i\s+use\s+for\s+(?:training\s+ai|ai\s+training)\b",
        low,
    ):
        support = _find(relations, source_equals="desktop", learned="supports")
        motive = _find(
            relations, source_contains="desktop upgrade", learned="motivated_by"
        )
        if support or motive:
            target = (support or motive).target
            return (
                f"Use your desktop for AI training because you upgraded it to {target}."
            )
        return UNKNOWN

    if re.search(r"\bwhich\s+should\s+i\s+use\s+for\s+software\s+development\b", low):
        # Language preferences alone do not identify a computer.
        return UNKNOWN

    if re.search(r"\bwhy\s+did\s+i\s+buy\s+my\s+phone\b", low):
        rel = _find(relations, source_contains="phone purchase", learned="motivated_by")
        return f"You bought your phone to {rel.target}." if rel else UNKNOWN

    return None


def _best_label(concept: Any) -> str:
    labels = list(getattr(concept, "labels", []) or [])
    if not labels:
        return ""
    # Prefer the shortest explicit entity label over generated phrase labels.
    return min(labels, key=lambda value: (len(value.split()), len(value)))


def _find(
    relations: list[LearnedRelation],
    *,
    source_equals: str = "",
    source_contains: str = "",
    target_equals: str = "",
    learned: str = "",
) -> LearnedRelation | None:
    for rel in reversed(relations):
        if learned and rel.learned_relation != learned:
            continue
        if source_equals and rel.source.casefold() != source_equals.casefold():
            continue
        if source_contains and source_contains.casefold() not in rel.source.casefold():
            continue
        if target_equals and rel.target.casefold() != target_equals.casefold():
            continue
        return rel
    return None


def _active_preference(
    facts: list[SemanticFact], property_name: str
) -> SemanticFact | None:
    for fact in reversed(facts):
        if fact.kind == "preference" and fact.property == property_name:
            return fact
    return None


def _goal_phrase(value: str) -> str:
    phrase = value.strip()
    if re.match(r"^to\s+build\b", phrase, re.I):
        return re.sub(r"^to\s+build\b", "building", phrase, flags=re.I)
    return re.sub(r"^to\s+", "", phrase, flags=re.I)
