"""Pattern-based fact extractors — LM-independent, host-independent."""

from __future__ import annotations

import re

from acm.semantic.model import (
    CognitiveFact,
    FactKind,
    PerspectiveResolution,
    PerspectiveSubject,
    UpdateOp,
)
from acm.semantic.perspective import subject_for_first_person, subject_for_second_person

_NAME_VALUE = r"([A-Za-z][\w'’-]*(?:\s+[A-Za-z][\w'’-]*){0,3})"

_MY_NAME = re.compile(rf"\bmy\s+name\s+is\s+{_NAME_VALUE}", re.I)
_IM_NAME = re.compile(rf"\b(?:i'?m|i\s+am)\s+{_NAME_VALUE}(?:\s*[.!?]|$)", re.I)
_CALL_ME = re.compile(rf"\b(?:call\s+me|please\s+call\s+me)\s+{_NAME_VALUE}", re.I)
_YOU_ARE = re.compile(rf"\byou\s+are\s+{_NAME_VALUE}", re.I)
_YOUR_NAME = re.compile(rf"\byour\s+name\s+is\s+{_NAME_VALUE}", re.I)
_USER_NAME = re.compile(rf"\b(?:user'?s?\s+name\s+is|the\s+user\s+is)\s+{_NAME_VALUE}", re.I)

_I_AM_A = re.compile(r"\b(?:i\s+am|i'?m)\s+(?:a|an)\s+(.+?)(?:\.|$)", re.I)
_I_CAN = re.compile(r"\b(?:i\s+can|i\s+am\s+able\s+to)\s+(.+?)(?:\.|$)", re.I)

_DOG_NAME = re.compile(
    rf"\bmy\s+(dog|cat|pet|wife|husband|partner|friend|son|daughter|mom|dad|"
    rf"mother|father|brother|sister|child)'?s?\s+name\s+is\s+{_NAME_VALUE}",
    re.I,
)
_LIVE_IN = re.compile(r"\bi\s+live\s+in\s+(.+?)(?:\.|$)", re.I)
_LOCATED = re.compile(r"\bi\s+(?:am\s+)?(?:from|based\s+in)\s+(.+?)(?:\.|$)", re.I)

_PREFER = re.compile(r"\bi\s+prefer\s+(.+?)(?:\.|$)", re.I)
_FAVORITE = re.compile(
    r"(?:my\s+)?(?:favorite|favourite)\s+(\w+(?:\s+\w+)?)\s+is\s+(.+?)(?:\.|$)",
    re.I,
)

# Interrogatives must never mint preference facts — questions about preferences
# are retrieval cues, not teachings. Matching "favorite color is conflicting?"
# was the live Preference certification blocker.
_INTERROGATIVE = re.compile(
    r"(?:\?|(?:^\s*(?:what|why|how|when|where|who|which|do|does|did|is|are|"
    r"was|were|can|could|would|should|show|tell|explain)\b))",
    re.I,
)


def is_interrogative(text: str) -> bool:
    """True when the text is a question / retrieval cue rather than a teaching."""
    return bool(_INTERROGATIVE.search((text or "").strip()))

_GOAL = re.compile(
    r"\b(?:my\s+(?:long[- ]?term\s+)?goal\s+is|i\s+want\s+to|our\s+goal\s+is)\s+(.+?)(?:\.|$)",
    re.I,
)
_PROJECT = re.compile(
    r"\b(?:my\s+project\s+is|(?:i'?m|i\s+am)\s+working\s+on(?:\s+project)?)\s+(.+?)(?:\.|$)",
    re.I,
)

_NOT_NAME = re.compile(rf"\bmy\s+name\s+is\s+not\s+{_NAME_VALUE}", re.I)
_ACTUALLY_NAME = re.compile(
    rf"\b(?:actually|rather|instead),?\s+my\s+name\s+is\s+{_NAME_VALUE}",
    re.I,
)
_NAME_NOW = re.compile(rf"\b(?:now\s+)?my\s+name\s+is\s+{_NAME_VALUE}", re.I)

# Role-like words that should not be treated as personal names after "I'm"
_ROLEISH = {
    "a",
    "an",
    "the",
    "not",
    "here",
    "there",
    "ready",
    "sure",
    "fine",
    "good",
    "ok",
    "okay",
    "sorry",
    "happy",
    "glad",
    "able",
}


def _clean_value(value: str) -> str:
    v = (value or "").strip().rstrip(".,;:!")
    v = re.sub(r"\s+", " ", v)
    return v


def _looks_like_name(value: str) -> bool:
    v = _clean_value(value)
    if not v or " " in v and len(v.split()) > 4:
        return False
    first = v.split()[0].casefold()
    if first in _ROLEISH:
        return False
    # Prefer capitalized tokens for bare "I'm X" name detection
    return bool(re.match(r"^[A-ZÁÉÍÓÚÄÖÜÑ]", v))


def extract_fact_patterns(
    text: str,
    *,
    perspective: PerspectiveResolution,
) -> list[CognitiveFact]:
    """Extract structured facts from cleaned natural language."""
    t = (text or "").strip()
    if not t:
        return []
    facts: list[CognitiveFact] = []
    fp = subject_for_first_person(perspective)
    sp = subject_for_second_person(perspective)

    # Negation / correction first
    m = _NOT_NAME.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.NEGATION,
                subject=fp,
                property="name",
                value=_clean_value(m.group(1)),
                update_op=UpdateOp.NEGATE,
                confidence=0.9,
            )
        )

    m = _ACTUALLY_NAME.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.CORRECTION,
                subject=fp,
                property="name",
                value=_clean_value(m.group(1)),
                update_op=UpdateOp.REVISE,
                confidence=0.92,
            )
        )

    # Relationships before generic my-name (dog's name ≠ user name)
    m = _DOG_NAME.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.RELATIONSHIP,
                subject=PerspectiveSubject.THIRD_PARTY,
                property="name",
                value=_clean_value(m.group(2)),
                relation_type=m.group(1).lower(),
                confidence=0.9,
            )
        )

    # Identity names (skip when the only "my … name" is a relationship possessives)
    m = _MY_NAME.search(t)
    if m and not _DOG_NAME.search(t[max(0, m.start() - 40) : m.end() + 5]):
        # Reject if this match is nested inside a relationship phrase
        window = t[max(0, m.start() - 24) : m.end()]
        if not re.search(
            r"\b(?:dog|cat|pet|wife|husband|partner|friend|son|daughter|mom|dad|"
            r"mother|father|brother|sister|child)'?s?\s+name\s+is\b",
            window,
            re.I,
        ):
            op = UpdateOp.REVISE if _ACTUALLY_NAME.search(t) else UpdateOp.SET
            if re.search(r"\bnow\b", t, re.I):
                op = UpdateOp.REVISE
            facts.append(
                CognitiveFact(
                    kind=FactKind.IDENTITY,
                    subject=fp,
                    property="name",
                    value=_clean_value(m.group(1)),
                    update_op=op,
                    confidence=0.93,
                )
            )

    m = _CALL_ME.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.IDENTITY,
                subject=fp,
                property="preferred_name",
                value=_clean_value(m.group(1)),
                confidence=0.9,
            )
        )

    m = _USER_NAME.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.IDENTITY,
                subject=PerspectiveSubject.USER,
                property="name",
                value=_clean_value(m.group(1)),
                confidence=0.95,
            )
        )

    m = _YOU_ARE.search(t) or _YOUR_NAME.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.IDENTITY,
                subject=sp,  # usually assistant
                property="name",
                value=_clean_value(m.group(1)),
                confidence=0.92,
            )
        )

    # "I'm Jeff" as name only when looks like a proper name and no "I am a/an"
    if not _I_AM_A.search(t):
        m = _IM_NAME.search(t)
        if m and _looks_like_name(m.group(1)):
            # Avoid duplicating if my name already captured same value
            val = _clean_value(m.group(1))
            if not any(
                f.property == "name" and f.value.casefold() == val.casefold() for f in facts
            ):
                facts.append(
                    CognitiveFact(
                        kind=FactKind.IDENTITY,
                        subject=fp,
                        property="name",
                        value=val,
                        confidence=0.88,
                    )
                )

    m = _I_AM_A.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.IDENTITY,
                subject=fp,
                property="role",
                value=_clean_value(m.group(1)),
                confidence=0.9,
            )
        )

    m = _I_CAN.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.SKILL,
                subject=fp,
                property="capability",
                value=_clean_value(m.group(1)),
                confidence=0.85,
            )
        )

    m = _LIVE_IN.search(t) or _LOCATED.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.LOCATION,
                subject=fp,
                property="location",
                value=_clean_value(m.group(1)),
                confidence=0.88,
            )
        )

    m = _FAVORITE.search(t)
    if m and not _INTERROGATIVE.search(t):
        key = f"favorite_{m.group(1).strip().lower().replace(' ', '_')}"
        facts.append(
            CognitiveFact(
                kind=FactKind.PREFERENCE,
                subject=fp,
                property=key,
                value=_clean_value(m.group(2)),
                confidence=0.85,
            )
        )
    elif not _INTERROGATIVE.search(t):
        m = _PREFER.search(t)
        if m:
            facts.append(
                CognitiveFact(
                    kind=FactKind.PREFERENCE,
                    subject=fp,
                    property="preference",
                    value=_clean_value(m.group(1)),
                    confidence=0.82,
                )
            )

    m = _GOAL.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.GOAL,
                subject=fp,
                property="goal",
                value=_clean_value(m.group(1)),
                confidence=0.8,
            )
        )

    m = _PROJECT.search(t)
    if m:
        facts.append(
            CognitiveFact(
                kind=FactKind.PROJECT,
                subject=fp,
                property="project",
                value=_clean_value(m.group(1)),
                confidence=0.8,
            )
        )

    # Deduplicate by (subject, property, value)
    seen: set[tuple[str, str, str]] = set()
    unique: list[CognitiveFact] = []
    for f in facts:
        key = (f.subject.value, f.property, f.value.casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    return unique
