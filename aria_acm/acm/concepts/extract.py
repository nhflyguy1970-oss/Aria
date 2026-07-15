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

    if encode_kind == "preference" or re.search(r"\b(prefer|favorite|favourite)\b", t, re.I):
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
            m2 = re.search(r"prefer\s+(.+?)(?:\.|$)", t, re.I)
            val = m2.group(1).strip().rstrip(".") if m2 else t
            cues.append(
                ConceptCue(
                    label="preference",
                    role=ConceptRole.PREFERENCE,
                    attr_key="preference",
                    attr_value=val,
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
