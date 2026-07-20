"""Semantic autobiographical patterns for Aria routing guards.

Cognition lives in ACM; these patterns only prevent Mission Control / chat
mis-routes and steer personal semantic teachings/recalls to Memory Authority.
"""

from __future__ import annotations

import re

from aria_acm.acm.authority.teaching import detect_teaching
from aria_acm.acm.semantic.model import FactKind

_SEMANTIC_TEACHING_KINDS = frozenset(
    {
        FactKind.POSSESSION,
        FactKind.PROJECT,
        FactKind.PREFERENCE,
        FactKind.IDENTITY,
        FactKind.LOCATION,
        FactKind.SKILL,
        FactKind.GOAL,
    }
)

SEMANTIC_AUTOBIO_QUERY = re.compile(
    r"\b(?:"
    r"what\s+operating\s+system\b|"
    r"what\s+operating\s+systems?\s+has\s+my\b|"
    r"what\s+(?:os|gpu|graphics\s+card|ram|editor)\b.+\b(?:laptop|desktop|computer|machine)\b|"
    r"what\s+(?:graphics\s+card|gpu)\s+is\s+in\s+my\b|"
    r"what\s+projects?\s+am\s+i\s+(?:work(?:ing)?\s+on|building)\b|"
    r"what\s+projects?\s+have\s+i\s+worked\s+on\b|"
    r"what\s+ai\s+projects?\b|"
    r"what\s+projects?\s+have\s+i\s+been\s+building\b|"
    r"tell\s+me\s+what\s+you\s+know\s+about\s+my\s+(?:computer|laptop|desktop|ai\s+setup|setup)\b|"
    r"what\s+do\s+you\s+know\s+about\s+my\s+(?:computer|laptop|desktop|ai\s+setup|setup)\b|"
    r"tell\s+me\s+about\s+my\s+computers?\b|"
    r"do\s+i\s+prefer\s+(?:local|cloud)\b|"
    r"what\s+kind\s+of\s+responses?\s+do\s+i\s+like\b|"
    r"what\s+do\s+i\s+(?:prefer|like)\b|"
    r"have\s+my\s+(?:ai\s+)?preferences?\s+changed\b|"
    r"has\s+my\s+(?:desktop|laptop|computer|hardware|gpu)\b.+\bchanged\b|"
    r"how\s+has\s+my\s+(?:ai\s+setup|computer|computers?)\s+changed\b|"
    r"summarize\s+what\s+you\s+know\s+about\s+me\b|"
    r"which\s+computer\b.+\b(?:better|training|ai\s+models?)\b|"
    r"which\s+(?:machine|computer|laptop|desktop)\b.+\bbetter\b|"
    r"what\s+(?:phone|printer|truck|vehicle|kayak|car)\s+do\s+i\s+(?:own|have)\b|"
    r"what\s+vehicles?\s+do\s+i\s+own\b"
    r")\b",
    re.I,
)


def is_semantic_autobio_teaching(text: str) -> bool:
    """Declarative personal facts ACM Teaching Recognition will encode."""
    detected = detect_teaching(text or "")
    if not detected.is_teaching or not detected.facts:
        return False
    return any(f.kind in _SEMANTIC_TEACHING_KINDS for f in detected.facts)


def is_semantic_autobio_query(text: str) -> bool:
    """Recall / integration questions about learned personal semantic memory."""
    return bool(SEMANTIC_AUTOBIO_QUERY.search(text or ""))


def is_semantic_autobio_utterance(text: str) -> bool:
    return is_semantic_autobio_teaching(text) or is_semantic_autobio_query(text)
