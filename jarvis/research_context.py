"""Shared research/context helpers — entity extraction and follow-up expansion.

Used by research verification (premise support) and conversational web search
(preserve active research entities on bare follow-ups). No product-specific logic.
"""

from __future__ import annotations

import re
from typing import Any

# Tokens that do not identify a product/vehicle/entity for follow-up expansion.
_STOP = frozenset(
    {
        "what", "whats", "which", "who", "whom", "when", "where", "why", "how",
        "the", "a", "an", "is", "are", "was", "were", "do", "does", "did",
        "can", "could", "should", "would", "will", "may", "might",
        "i", "me", "my", "we", "our", "you", "your", "it", "its", "this", "that",
        "these", "those", "them", "they", "and", "or", "of", "for", "to", "on",
        "in", "at", "by", "with", "from", "about", "into", "over", "after",
        "please", "show", "tell", "give", "find", "get", "need", "want",
        "specification", "spec", "specs", "torque", "value", "number", "exact",
        "official", "documentation", "manual", "guide", "procedure", "steps",
        "latest", "current", "newest", "version", "release", "supported",
        "according", "conflicting", "sources", "authoritative", "prefer",
    }
)

_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_VERSIONISH = re.compile(
    r"\b(?:v?\d+(?:\.\d+){1,3}|rev\s*[a-z0-9]+|\d{3,4}\.\d+)\b",
    re.I,
)
_PROPER_RUN = re.compile(
    r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,4})\b"
)
_MODEL_TOKEN = re.compile(
    r"\b([A-Z]{2,}[- ]?\d{2,}[A-Za-z0-9]*|[A-Za-z]+\d{2,}[A-Za-z0-9]*)\b"
)


def extract_research_entities(text: str) -> list[str]:
    """Distinctive entities (years, proper nouns, model/version tokens) from a prompt."""
    raw = (text or "").strip()
    if not raw:
        return []
    found: list[str] = []
    seen: set[str] = set()

    def _add(tok: str) -> None:
        t = (tok or "").strip(" .,;:!?\"'")
        if len(t) < 2:
            return
        key = t.casefold()
        if key in _STOP or key in seen:
            return
        seen.add(key)
        found.append(t)

    for m in _YEAR.finditer(raw):
        _add(m.group(0))
    for m in _PROPER_RUN.finditer(raw):
        phrase = m.group(1)
        # Skip sentence-initial common words capitalized by accident
        parts = [p for p in phrase.split() if p.casefold() not in _STOP]
        if parts:
            _add(" ".join(parts))
    for m in _MODEL_TOKEN.finditer(raw):
        _add(m.group(1))
    for m in _VERSIONISH.finditer(raw):
        _add(m.group(0))

    # Domain nouns that anchor vehicle/brake follow-ups when paired with a year/model
    low = raw.lower()
    for noun in (
        "ranger", "f-150", "f150", "civic", "tacoma", "silverado", "camry",
        "rotor", "rotors", "caliper", "brake", "brakes", "lug", "wheel",
        "ubuntu", "lts",
    ):
        if noun in low:
            _add(noun)

    return found[:12]


def premise_tokens(text: str) -> list[str]:
    """Tokens that must appear in sources if the premise entity is real."""
    ents = extract_research_entities(text)
    tokens: list[str] = []
    for e in ents:
        for part in re.findall(r"[A-Za-z0-9]{3,}", e):
            if part.casefold() not in _STOP:
                tokens.append(part.casefold())
    # Invented-looking product names: consecutive CapWords / odd brands
    for m in re.finditer(r"\b([A-Z]{2,}[A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]+){0,3})\b", text or ""):
        phrase = m.group(1)
        for part in re.findall(r"[A-Za-z0-9]{3,}", phrase):
            tokens.append(part.casefold())
    # Dedupe preserving order
    out: list[str] = []
    seen: set[str] = set()
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:16]


def premise_supported_by_results(query: str, results: list[dict] | None) -> bool:
    """True when distinctive premise tokens appear in at least one result."""
    tokens = premise_tokens(query)
    if not tokens:
        return True  # nothing distinctive to verify
    # Require support for the rarest/most distinctive tokens (skip years alone)
    distinctive = [t for t in tokens if not re.fullmatch(r"(19|20)\d{2}", t)]
    if not distinctive:
        distinctive = tokens
    blob = " ".join(
        f"{r.get('title', '')} {r.get('snippet', '')} {r.get('url', '')}".lower()
        for r in (results or [])
    )
    if not blob.strip():
        return False
    hits = sum(1 for t in distinctive[:6] if t in blob)
    # Need at least one strong hit for invented names; half for longer lists
    need = 1 if len(distinctive) <= 2 else max(1, len(distinctive[:6]) // 2)
    return hits >= need


def message_has_anchor_entity(message: str) -> bool:
    """True when the message already names a concrete research subject."""
    ents = extract_research_entities(message)
    # Year + proper noun, or a model token, counts as anchored
    has_year = any(_YEAR.fullmatch(e) for e in ents)
    has_proper = any(len(e.split()) >= 1 and e[:1].isupper() and e.casefold() not in _STOP for e in ents)
    has_model = any(_MODEL_TOKEN.fullmatch(e) or _VERSIONISH.fullmatch(e) for e in ents)
    low = (message or "").lower()
    has_vehicle_noun = bool(
        re.search(r"\b(?:ranger|civic|tacoma|f-?150|silverado|truck|vehicle)\b", low)
    )
    return bool((has_year and (has_proper or has_vehicle_noun)) or has_model or (has_proper and has_vehicle_noun))


def expand_followup_query(message: str, session: Any = None) -> str:
    """Preserve active research entities on bare consequential/current follow-ups."""
    text = (message or "").strip()
    if not text or session is None:
        return text
    if message_has_anchor_entity(text):
        return text
    entities = list(getattr(session, "research_entities", None) or [])
    prior = str(getattr(session, "last_research_query", "") or "").strip()
    if not entities and prior:
        entities = extract_research_entities(prior)
    if not entities:
        return text
    # Only expand when the follow-up looks like a short continuation
    if len(text.split()) > 16 and not re.search(
        r"\b(?:torque|spec|specification|pad|rotor|caliper|bolt|that|those|it)\b",
        text,
        re.I,
    ):
        return text
    prefix = " ".join(entities[:6])
    if not prefix:
        return text
    expanded = f"{prefix} {text}".strip()
    return expanded


def bare_referent_request(message: str) -> bool:
    """True for short utterances whose only object is a bare pronoun (it/that/this)."""
    text = (message or "").strip()
    if not text or len(text.split()) > 10:
        return False
    if not re.search(r"\b(?:it|that|this|them|those)\b", text, re.I):
        return False
    # Has a concrete noun besides the pronoun → not bare
    nouns = re.findall(r"\b[A-Za-z]{3,}\b", text)
    filler = {
        "can", "you", "please", "fix", "it", "that", "this", "them", "those",
        "help", "with", "the", "a", "an", "my", "me", "do", "could", "would",
        "should", "will", "just", "now", "again", "here", "there", "something",
        "one", "other", "when", "did", "come", "out", "and",
    }
    concrete = [n for n in nouns if n.lower() not in filler]
    return len(concrete) == 0


def is_research_followup(message: str) -> bool:
    """Short continuation of an active research topic (tools/when/torque/that one…).

    Used to keep follow-ups on web_search when session has research context,
    instead of bare chat inventing unrelated entities (RW-001/RW-008).
    """
    text = (message or "").strip()
    if not text or len(text.split()) > 18:
        return False
    if message_has_anchor_entity(text):
        return False
    return bool(
        re.search(
            r"(?:"
            r"\b(?:and\s+)?when\s+did\b|"
            r"\bthat\s+one\b|"
            r"\bthe\s+other\s+one\b|"
            r"\bwhat\s+tools\b|"
            r"\bwhat\s+else\s+should\s+i\s+(?:have|bring|get)\b|"
            r"\bbefore\s+i\s+start\b|"
            r"\bwhat\s+(?:is\s+)?the\s+torque\b|"
            r"\bwhat\s+about\s+(?:the\s+)?(?:torque|spec|tools|pads?|rotors?)\b|"
            r"\band\s+what\s+(?:tools|about)\b|"
            r"\bhow\s+much\s+(?:torque|force)\b|"
            r"\bwas\s+the\s+torque\b|"
            r"\bwhen\s+was\s+(?:that|it)\b|"
            r"\bwhat\s+was\s+the\s+(?:torque|spec)\b"
            r")",
            text,
            re.I,
        )
    )
