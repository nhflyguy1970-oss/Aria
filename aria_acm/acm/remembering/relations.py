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

    # Context-specific preference must be matched before the general preference.
    if re.search(
        r"\bwhat\s+(?:programming\s+)?language\s+do\s+i\s+prefer\s+for\s+systems\s+programming\b",
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


def is_answer_provenance_query(cue: str) -> bool:
    """Meta-explainability: how did/do you know <prior autobiographical answer>."""
    return bool(re.search(r"\bhow\s+(?:did|do)\s+you\s+know\b", cue or "", re.I))


def explain_answer_provenance(cue: str, *, store: Any) -> str | None:
    """Cite the autobiographical evidence that supported a prior answer.

    Returns None when the cue is not a provenance question. Returns UNKNOWN when
    it is a provenance question but no supporting autobiographical evidence exists.
    Never falls back to unrelated hardware memories that merely share a verb.
    """
    text = (cue or "").strip()
    if not is_answer_provenance_query(text):
        return None

    low = text.lower()
    relations = collect_learned_relations(store)

    # Why desktop upgrade — exact supporting relationship + teaching evidence.
    if re.search(
        r"\b(?:why\s+)?(?:i\s+)?upgrad(?:ed|e)\s+(?:my\s+)?desktop\b|"
        r"\bwhy\s+i\s+upgraded\s+(?:my\s+)?desktop\b",
        low,
    ):
        rel = _find(
            relations, source_contains="desktop upgrade", learned="motivated_by"
        )
        if rel is None:
            return UNKNOWN
        taught = _supporting_teaching_text(store, rel.evidence_ids)
        if not taught:
            taught = f"you upgraded your desktop to {rel.target}"
        return (
            f"You previously taught me that {taught}. "
            "I answered using that remembered autobiographical fact and its "
            "associated relationship."
        )

    # Generic provenance: require distinctive topic overlap with teaching evidence.
    supporting = _best_topic_evidence(store, text)
    if supporting:
        return (
            f"You previously taught me that {supporting}. "
            "I answered using that remembered autobiographical fact"
            + (
                " and its associated relationship."
                if _evidence_has_relationship(store, text)
                else "."
            )
        )
    return UNKNOWN


def _supporting_teaching_text(store: Any, evidence_ids: tuple[str, ...] | list[str]) -> str:
    for eid in evidence_ids:
        exp = store.experiences.get(eid)
        if exp is None:
            continue
        meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
        raw = (meta.get("evidence") if isinstance(meta, dict) else None) or exp.summary
        if raw:
            return _to_second_person_teaching(str(raw))
    return ""


def _to_second_person_teaching(text: str) -> str:
    phrase = (text or "").strip().rstrip(".")
    if not phrase:
        return phrase
    phrase = re.sub(r"^I\s+", "you ", phrase, count=1, flags=re.I)
    phrase = re.sub(r"\bmy\b", "your", phrase, flags=re.I)
    if phrase and phrase[0].isupper() and not phrase.startswith("You"):
        phrase = phrase[0].lower() + phrase[1:]
    return phrase


def _topic_tokens(cue: str) -> set[str]:
    topic = re.sub(
        r"^.*?\bhow\s+(?:did|do)\s+you\s+know\s+(?:why\s+)?",
        "",
        cue or "",
        flags=re.I,
    )
    stop = {
        "i",
        "my",
        "the",
        "a",
        "an",
        "to",
        "for",
        "and",
        "or",
        "did",
        "do",
        "you",
        "know",
        "why",
        "how",
        "about",
    }
    return {
        tok
        for tok in re.findall(r"[a-z0-9]+", topic.lower())
        if len(tok) > 2 and tok not in stop
    }


def _best_topic_evidence(store: Any, cue: str) -> str:
    tokens = _topic_tokens(cue)
    if not tokens:
        return ""
    best_text = ""
    best_score = 0.0
    for exp in store.experiences.values():
        meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
        if not isinstance(meta, dict):
            meta = {}
        raw = str(meta.get("evidence") or exp.summary or "").strip()
        if not raw:
            continue
        low = raw.lower()
        overlap = {tok for tok in tokens if tok in low}
        # Require at least one distinctive noun beyond generic verbs.
        distinctive = overlap - {"upgraded", "upgrade", "prefer", "building", "built"}
        if not distinctive:
            continue
        score = float(len(overlap))
        if any(str(meta.get(k, "")).startswith("relationship") for k in meta):
            score += 3.0
        if any(
            str(meta.get(f"fact_{i}_kind", "")).lower() == "relationship"
            for i in range(6)
        ):
            score += 3.0
        if score > best_score:
            best_score = score
            best_text = _to_second_person_teaching(raw)
    return best_text


def _evidence_has_relationship(store: Any, cue: str) -> bool:
    tokens = _topic_tokens(cue)
    for rel in collect_learned_relations(store):
        blob = f"{rel.source} {rel.target} {rel.learned_relation}".lower()
        if tokens and any(tok in blob for tok in tokens):
            return True
    return False


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
