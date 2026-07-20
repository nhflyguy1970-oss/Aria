"""Lightweight label / hierarchy cue extraction — emergence aids, not hand taxonomies."""

from __future__ import annotations

import re
from dataclasses import dataclass

from acm.types import ConceptRole

_STOP = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "for",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "i",
    "my",
    "me",
    "we",
    "you",
    "it",
    "this",
    "that",
    "with",
    "from",
    "as",
    "at",
    "by",
    "about",
}


@dataclass(frozen=True)
class ConceptCue:
    label: str
    role: ConceptRole
    attr_key: str
    attr_value: str
    parent_label: str | None = None
    identity: bool = False
    is_instance: bool = False


_IS_A = re.compile(
    r"\b([A-Za-z][\w\s-]{0,40}?)\s+is\s+a(?:n)?\s+([A-Za-z][\w\s-]{0,40})",
    re.I,
)
_FAV = re.compile(
    r"(?:favorite|favourite)\s+(\w+(?:\s+\w+)?)\s+is\s+(.+?)(?:\.|$)",
    re.I,
)
_PREF_SUMMARY = re.compile(
    r"\bpreferred\s+(\w+(?:\s+\w+)?)\s+is\s+(.+?)(?:\.|$)",
    re.I,
)
_PREF_GENERIC = re.compile(
    r"\bpreference\s+is\s+(.+?)(?:\.|$)",
    re.I,
)
_PREFER_VERB = re.compile(
    r"\bprefer\s+(.+?)(?:\.|$)",
    re.I,
)
_LIKE_VERB = re.compile(
    r"\blike\s+(.+?)(?:\.|$)",
    re.I,
)
_INTERROGATIVE = re.compile(
    r"(?:\?|(?:^\s*(?:what|why|how|when|where|who|which|do|does|did|is|are|"
    r"was|were|can|could|would|should|show|tell|explain)\b))",
    re.I,
)
_POSSESSION_SUMMARY = re.compile(
    r"\b(?:user|assistant)\s+(\w+)\s+(?:runs|has(?:\s+gpu)?|os|gpu|ram|editor)\s+(.+?)(?:\.|;|$)",
    re.I,
)
_POSSESSION_RUNS = re.compile(
    r"\b(?:user|assistant)\s+(\w+)\s+runs\s+(.+?)(?:\.|;|$)",
    re.I,
)
_POSSESSION_HAS_GPU = re.compile(
    r"\b(?:user|assistant)\s+(\w+)\s+has\s+GPU\s+(.+?)(?:\.|;|$)",
    re.I,
)
_POSSESSION_HAS_RAM = re.compile(
    r"\b(?:user|assistant)\s+(\w+)\s+has\s+(.+?)\s+RAM(?:\.|;|$)",
    re.I,
)
_PROJECT_SUMMARY = re.compile(
    r"\bproject:\s*(.+?)(?:\.|;|$)",
    re.I,
)


def extract_cues(text: str, *, encode_kind: str = "experience") -> list[ConceptCue]:
    t = (text or "").strip()
    if not t:
        return []
    cues: list[ConceptCue] = []

    if encode_kind == "identity":
        cues.append(
            ConceptCue(
                label="identity",
                role=ConceptRole.IDENTITY,
                attr_key="statement",
                attr_value=t,
                identity=True,
            )
        )

    if encode_kind == "preference" or re.search(
        r"\b(prefer(?:red|ence|s)?|favorite|favourite)\b", t, re.I
    ):
        # Questions about preferences are retrieval cues — never mint preference
        # attributes from them (live blocker: "Your preference is Tool …").
        if not _INTERROGATIVE.search(t):
            m = _FAV.search(t)
            if m:
                key = f"favorite_{m.group(1).strip().lower().replace(' ', '_')}"
                cues.append(
                    ConceptCue(
                        label=key.replace("_", " "),
                        role=ConceptRole.PREFERENCE,
                        attr_key=key,
                        attr_value=m.group(2).strip().rstrip("."),
                    )
                )
            else:
                m2 = _PREF_SUMMARY.search(t)
                if m2:
                    domain = m2.group(1).strip().lower().replace(" ", "_")
                    key = f"prefer_{domain}"
                    cues.append(
                        ConceptCue(
                            label=f"preferred {domain.replace('_', ' ')}",
                            role=ConceptRole.PREFERENCE,
                            attr_key=key,
                            attr_value=m2.group(2).strip().rstrip("."),
                        )
                    )
                else:
                    m3 = _PREF_GENERIC.search(t) or _PREFER_VERB.search(t) or _LIKE_VERB.search(t)
                    if m3:
                        value = m3.group(1).strip().rstrip(".")
                        tokens = re.findall(r"[a-zA-Z][\w'-]*", value)
                        domain = tokens[-1].lower() if tokens else ""
                        low = value.lower()
                        if re.search(r"\b(local|cloud)\b.+\bai\b|\bai\b.+\b(local|cloud|model)", low):
                            domain = "ai"
                        elif "debug" in low or "step-by-step" in low or "step by step" in low:
                            domain = "debugging"
                        key = f"prefer_{domain}" if domain else "preference"
                        label = (
                            f"preferred {domain}" if domain else "preference"
                        )
                        cues.append(
                            ConceptCue(
                                label=label,
                                role=ConceptRole.PREFERENCE,
                                attr_key=key,
                                attr_value=value,
                            )
                        )

    # Possession / device attributes from cognitive summaries
    for m in _POSSESSION_RUNS.finditer(t):
        entity = _clean_label(m.group(1))
        value = m.group(2).strip().rstrip(".")
        if entity and value:
            cues.append(
                ConceptCue(
                    label=entity,
                    role=ConceptRole.ENTITY,
                    attr_key="os",
                    attr_value=value,
                )
            )
    for m in _POSSESSION_HAS_GPU.finditer(t):
        entity = _clean_label(m.group(1))
        value = m.group(2).strip().rstrip(".")
        if entity and value:
            cues.append(
                ConceptCue(
                    label=entity,
                    role=ConceptRole.ENTITY,
                    attr_key="gpu",
                    attr_value=value,
                )
            )
    for m in _POSSESSION_HAS_RAM.finditer(t):
        entity = _clean_label(m.group(1))
        value = m.group(2).strip().rstrip(".")
        if entity and value:
            cues.append(
                ConceptCue(
                    label=entity,
                    role=ConceptRole.ENTITY,
                    attr_key="ram",
                    attr_value=value,
                )
            )
    for m in _PROJECT_SUMMARY.finditer(t):
        title = m.group(1).strip().rstrip(".")
        if title:
            cues.append(
                ConceptCue(
                    label=f"project {title}",
                    role=ConceptRole.ENTITY,
                    attr_key="project",
                    attr_value=title,
                )
            )

    for m in _IS_A.finditer(t):
        child = _clean_label(m.group(1))
        parent = _clean_label(m.group(2))
        if child and parent and child != parent:
            cues.append(
                ConceptCue(
                    label=child,
                    role=ConceptRole.ENTITY,
                    attr_key="instance_of",
                    attr_value=parent,
                    parent_label=parent,
                    is_instance=True,
                )
            )
            cues.append(
                ConceptCue(
                    label=parent,
                    role=ConceptRole.TOPIC,
                    attr_key="category",
                    attr_value=parent,
                )
            )

    # Token nuclei from content words (emergence fuel)
    for tok in _tokens(t):
        if len(tok) < 4:
            continue
        if any(c.label == tok for c in cues):
            continue
        cues.append(
            ConceptCue(
                label=tok,
                role=ConceptRole.ENTITY,
                attr_key="mentioned",
                attr_value=tok,
            )
        )

    if not cues:
        cues.append(
            ConceptCue(
                label=t[:80],
                role=ConceptRole.ENTITY,
                attr_key="statement",
                attr_value=t,
            )
        )
    return cues


def _clean_label(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip().lower())
    s = re.sub(r"^(the|a|an)\s+", "", s)
    return s[:60]


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text.lower())
    out: list[str] = []
    for w in words:
        if w in _STOP:
            continue
        if w not in out:
            out.append(w)
    return out[:8]
