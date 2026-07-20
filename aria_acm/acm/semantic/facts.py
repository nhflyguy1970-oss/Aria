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
from acm.semantic.temporal import normalize_temporal_cue

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
    r"\b(?:my\s+project\s+is|"
    r"(?:i'?m|i\s+am)\s+working\s+on(?:\s+project)?|"
    r"(?:i'?m|i\s+am)\s+building|"
    r"(?:i'?m|i\s+am)\s+developing)\s+(.+?)(?:\.|$)",
    re.I,
)
_LIKE = re.compile(r"\bi\s+like\s+(.+?)(?:\.|$)", re.I)

# Semantic autobiographical possessions / device attributes.
_OWNED_ENTITIES = (
    r"laptop|desktop|computer|pc|workstation|machine|phone|tablet|"
    r"server|nas|gpu|editor|keyboard|mouse|monitor"
)
_POSSESSION_RUNS = re.compile(
    rf"\bmy\s+({_OWNED_ENTITIES})\s+(?:runs|running|uses|using)\s+(.+?)(?:\.|$)",
    re.I,
)
_POSSESSION_HAS = re.compile(
    rf"\bmy\s+({_OWNED_ENTITIES})\s+has\s+(?:an?\s+)?(.+?)(?:\.|$)",
    re.I,
)
_POSSESSION_IS = re.compile(
    rf"\bmy\s+({_OWNED_ENTITIES})(?:'s)?\s+(?:os|operating\s+system|graphics\s+card|"
    rf"gpu|ram|memory|editor)\s+is\s+(.+?)(?:\.|$)",
    re.I,
)
_I_USE = re.compile(r"\bi\s+use\s+(.+?)(?:\.|$)", re.I)

_OS_HINTS = {
    "zorin",
    "linux",
    "ubuntu",
    "windows",
    "macos",
    "mac os",
    "fedora",
    "debian",
    "arch",
    "mint",
    "chromeos",
}
_GPU_HINTS = ("rtx", "gtx", "radeon", "rx ", "nvidia", "amd", "gpu", "graphics")
_RAM_HINTS = ("gb ram", "gb of ram", "memory")
_EDITOR_HINTS = ("vs code", "vscode", "vim", "neovim", "emacs", "cursor", "sublime", "jetbrains")


def _possession_property(value: str, *, hinted: str | None = None) -> str:
    if hinted:
        h = hinted.lower().replace(" ", "_")
        if h in ("os", "operating_system"):
            return "os"
        if h in ("graphics_card", "gpu"):
            return "gpu"
        if h in ("ram", "memory"):
            return "ram"
        if h == "editor":
            return "editor"
        return h
    low = (value or "").lower()
    if any(h in low for h in _OS_HINTS) or low.strip() in _OS_HINTS:
        return "os"
    if any(h in low for h in _GPU_HINTS):
        return "gpu"
    if any(h in low for h in _RAM_HINTS) or re.search(r"\b\d+\s*gb\b", low):
        return "ram"
    if any(h in low for h in _EDITOR_HINTS):
        return "editor"
    return "attribute"


def _extract_possession(
    text: str,
    *,
    subject: PerspectiveSubject,
) -> list[CognitiveFact]:
    """Extract owned-entity attribute facts (OS, GPU, RAM, editor, …)."""
    t = (text or "").strip()
    if not t or _INTERROGATIVE.search(t):
        return []
    out: list[CognitiveFact] = []

    m = _POSSESSION_RUNS.search(t)
    if m:
        entity = _clean_value(m.group(1)).lower()
        value = _clean_value(m.group(2))
        if entity and value:
            out.append(
                CognitiveFact(
                    kind=FactKind.POSSESSION,
                    subject=subject,
                    property=_possession_property(value, hinted="os"),
                    value=value,
                    relation_type=entity,
                    confidence=0.9,
                    labels=(entity,),
                )
            )

    m = _POSSESSION_HAS.search(t)
    if m:
        entity = _clean_value(m.group(1)).lower()
        value = _clean_value(m.group(2))
        if entity and value:
            out.append(
                CognitiveFact(
                    kind=FactKind.POSSESSION,
                    subject=subject,
                    property=_possession_property(value),
                    value=value,
                    relation_type=entity,
                    confidence=0.88,
                    labels=(entity,),
                )
            )

    m = _POSSESSION_IS.search(t)
    if m:
        entity = _clean_value(m.group(1)).lower()
        # pattern groups: entity, then value — property inferred from wording
        value = _clean_value(m.group(2))
        prop_m = re.search(
            r"\b(os|operating\s+system|graphics\s+card|gpu|ram|memory|editor)\b",
            t,
            re.I,
        )
        hinted = prop_m.group(1) if prop_m else None
        if entity and value:
            out.append(
                CognitiveFact(
                    kind=FactKind.POSSESSION,
                    subject=subject,
                    property=_possession_property(value, hinted=hinted),
                    value=value,
                    relation_type=entity,
                    confidence=0.9,
                    labels=(entity,),
                )
            )

    m = _I_USE.search(t)
    if m and not out:
        value = _clean_value(m.group(1))
        prop = _possession_property(value)
        if value and prop in ("os", "editor"):
            out.append(
                CognitiveFact(
                    kind=FactKind.POSSESSION,
                    subject=subject,
                    property=prop,
                    value=value,
                    relation_type="computer" if prop == "os" else "editor",
                    confidence=0.8,
                    labels=("computer" if prop == "os" else "editor",),
                )
            )
    return out


# Autobiographical episodic events — first-person past with a temporal cue.
# "Yesterday I bought a kayak." / "I cleaned my garage yesterday."
_TEMPORAL_PHRASE = (
    r"(?:yesterday|today|this\s+morning|this\s+afternoon|this\s+evening|"
    r"last\s+night|last\s+week|last\s+month|"
    r"last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))"
)
_EPISODIC_ACTION = (
    r"(bought|cleaned|went|installed|visited|built|finished|started|"
    r"drove|flew|walked|called|met|watched|read|wrote|cooked|fixed|"
    r"moved|painted|planted|hiked|ran|swam|played|taught|learned|"
    r"attended|joined|left|opened|closed|replaced|upgraded|"
    r"purchased|ordered|picked\s+up|dropped\s+off|"
    r"caught|fished|hooked|landed|harvested|observed|released|cast)"
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


def _prefer_domain_from_value(value: str) -> str | None:
    """Derive a preference domain noun from 'barbless hooks' → hooks."""
    tokens = re.findall(r"[a-zA-Z][\w'-]*", value or "")
    if not tokens:
        return None
    # Prefer the last content noun (hooks, coffee, …).
    domain = tokens[-1].lower()
    if domain in {"a", "an", "the", "my", "to", "for", "with", "and", "or"}:
        return None
    return domain


def _extract_episodic(
    text: str,
    *,
    subject: PerspectiveSubject,
) -> CognitiveFact | None:
    """Extract one autobiographical episodic event fact, if present."""
    t = (text or "").strip()
    m = re.match(
        rf"^\s*({_TEMPORAL_PHRASE})\s+i\s+{_EPISODIC_ACTION}\s+(.+?)(?:\.|$)",
        t,
        re.I,
    )
    if m:
        temporal = normalize_temporal_cue(m.group(1))
        action = re.sub(r"\s+", " ", m.group(2).strip().lower())
        obj = _clean_value(m.group(3))
        if obj:
            return CognitiveFact(
                kind=FactKind.EXPERIENCE,
                subject=subject,
                property=action.replace(" ", "_"),
                value=obj,
                relation_type=temporal,
                confidence=0.9,
                labels=(temporal, action),
            )
    m = re.match(
        rf"^\s*i\s+{_EPISODIC_ACTION}\s+(.+?)\s+({_TEMPORAL_PHRASE})\s*[.!?]?\s*$",
        t,
        re.I,
    )
    if m:
        action = re.sub(r"\s+", " ", m.group(1).strip().lower())
        obj = _clean_value(m.group(2))
        temporal = normalize_temporal_cue(m.group(3))
        if obj:
            return CognitiveFact(
                kind=FactKind.EXPERIENCE,
                subject=subject,
                property=action.replace(" ", "_"),
                value=obj,
                relation_type=temporal,
                confidence=0.9,
                labels=(temporal, action),
            )
    return None


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
        m = _PREFER.search(t) or _LIKE.search(t)
        if m:
            value = _clean_value(m.group(1))
            domain = _prefer_domain_from_value(value)
            # Special-case common preference domains from phrasing.
            low = value.lower()
            if re.search(r"\b(local|cloud)\b.+\bai\b|\bai\b.+\b(local|cloud|model)", low):
                domain = "ai"
            elif re.search(r"\bdebug", low) or "step-by-step" in low or "step by step" in low:
                domain = "debugging"
            prop = f"prefer_{domain}" if domain else "preference"
            facts.append(
                CognitiveFact(
                    kind=FactKind.PREFERENCE,
                    subject=fp,
                    property=prop,
                    value=value,
                    confidence=0.82,
                    labels=(domain,) if domain else (),
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

    # Semantic autobiographical possessions (OS / hardware / tools)
    if not _INTERROGATIVE.search(t):
        facts.extend(_extract_possession(t, subject=fp))

    # Episodic autobiographical events (never from interrogatives)
    if not _INTERROGATIVE.search(t):
        ep = _extract_episodic(t, subject=fp)
        if ep is not None:
            facts.append(ep)

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
