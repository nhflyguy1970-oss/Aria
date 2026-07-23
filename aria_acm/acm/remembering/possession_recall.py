"""Adjacent possession / relationship fact recall (B47).

Answers cues like "What's my dog's name?" from stored relationship facts
without polluting Who am I / Who are you identity speech.
"""

from __future__ import annotations

import re
from typing import Any

from acm.authority.mode import read_only

SCHEMA = "acm.possession.recall.v1"

_RELATION_NAME_Q = re.compile(
    r"\b(?:what(?:'s|\s+is)|whats)\s+my\s+"
    r"(?P<rel>dog|cat|pet|wife|husband|partner|friend|son|daughter|mom|dad|"
    r"mother|father|brother|sister|child)"
    r"(?:'s)?\s+name\b",
    re.I,
)
_RELATION_WHO = re.compile(
    r"\b(?:who\s+is\s+my|what(?:'s|\s+is)\s+the\s+name\s+of\s+my)\s+"
    r"(?P<rel>dog|cat|pet|wife|husband|partner|friend|son|daughter)\b",
    re.I,
)

_REL_TYPES = (
    "dog",
    "cat",
    "pet",
    "wife",
    "husband",
    "partner",
    "friend",
    "son",
    "daughter",
    "mom",
    "dad",
    "mother",
    "father",
    "brother",
    "sister",
    "child",
)


def is_possession_relationship_query(cue: str) -> bool:
    text = (cue or "").strip()
    if not text:
        return False
    if _RELATION_NAME_Q.search(text) or _RELATION_WHO.search(text):
        return True
    low = text.lower()
    return bool(
        re.search(
            r"\bmy\s+(?:" + "|".join(_REL_TYPES) + r")(?:'s)?\s+name\b",
            low,
        )
        and re.search(r"\b(?:what|who|whats)\b", low)
    )


def _requested_relation(cue: str) -> str | None:
    m = _RELATION_NAME_Q.search(cue or "")
    if m:
        return m.group("rel").lower().strip()
    m = _RELATION_WHO.search(cue or "")
    if m:
        return m.group("rel").lower().strip()
    m = re.search(
        r"\bmy\s+(" + "|".join(_REL_TYPES) + r")(?:'s)?\s+name\b",
        cue or "",
        re.I,
    )
    if m:
        return m.group(1).lower()
    return None


def collect_relationship_name_facts(store: Any) -> list[dict[str, str]]:
    """Active relationship name facts from experience metadata + concept metadata."""
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for exp in sorted(
        store.experiences.values(),
        key=lambda e: (getattr(e, "t_start", 0.0), getattr(e, "sequence", 0)),
    ):
        meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
        for i in range(12):
            kind = meta.get(f"fact_{i}_kind")
            if kind != "relationship":
                continue
            prop = meta.get(f"fact_{i}_property") or ""
            value = meta.get(f"fact_{i}_value") or ""
            rel = (meta.get(f"fact_{i}_relation") or "").lower()
            if prop != "name" or not value or not rel:
                continue
            key = (rel, value.casefold())
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "relation_type": rel,
                    "name": value,
                    "experience_id": str(getattr(exp, "id", "") or ""),
                }
            )

    for concept in store.concepts.values():
        meta = getattr(concept, "metadata", {}) or {}
        rel = str(meta.get("relation_type") or "").lower()
        name = str(meta.get("relation_name") or "")
        if rel and name:
            key = (rel, name.casefold())
            if key in seen:
                continue
            seen.add(key)
            out.append({"relation_type": rel, "name": name, "experience_id": ""})

    return out


def answer_possession_relationship_query(cue: str, *, store: Any) -> str | None:
    """Return spoken answer or None if not a possession/relationship name cue."""
    if not is_possession_relationship_query(cue):
        return None
    rel = _requested_relation(cue)
    facts = collect_relationship_name_facts(store)
    if not facts:
        return None
    if rel:
        matches = [f for f in facts if f["relation_type"] == rel]
        # pet → dog/cat
        if not matches and rel == "pet":
            matches = [f for f in facts if f["relation_type"] in {"dog", "cat", "pet"}]
    else:
        matches = facts
    if not matches:
        return None
    fact = matches[-1]  # most recent experience order; list is chronological
    return f"Your {fact['relation_type']}'s name is {fact['name']}."


def present_possession_recall(engine: Any, request: str) -> dict[str, Any]:
    """Public read-only possession/relationship recall."""
    with read_only():
        if not is_possession_relationship_query(request):
            return {
                "schema": SCHEMA,
                "status": "not_possession_query",
                "memory": None,
                "invents_experiences": False,
                "store_write": False,
            }
        answer = answer_possession_relationship_query(request, store=engine.store)
        if not answer:
            return {
                "schema": SCHEMA,
                "status": "unknown",
                "memory": None,
                "invents_experiences": False,
                "store_write": False,
                "confidence": 0.0,
            }
        return {
            "schema": SCHEMA,
            "status": "known",
            "memory": answer,
            "invents_experiences": False,
            "store_write": False,
            "confidence": 0.9,
            "explanation_class": "experience",
            "pollutes_identity_speech": False,
        }
