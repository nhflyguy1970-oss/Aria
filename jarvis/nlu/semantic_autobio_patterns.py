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
        FactKind.RELATIONSHIP,
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
    r"what\s+vehicles?\s+do\s+i\s+own\b|"
    # Autobiographical relational reasoning
    r"why\s+(?:did|do|am)\s+i\b|"
    r"why\s+is\s+my\b.+\bbetter\b|"
    r"how\s+are\s+.+\s+and\s+.+\s+related\b|"
    r"how\s+does\s+.+\s+relate\s+to\s+my\s+goal\b|"
    r"how\s+does\s+.+\s+fit\s+into\s+my\s+projects?\b|"
    r"would\s+.+\s+fit\s+my\s+preferences?\b|"
    r"what\s+(?:programming\s+)?language\s+do\s+i\s+prefer\b|"
    r"what\s+is\s+my\s+(?:long[- ]?term\s+)?goal\b|"
    r"how\s+(?:did|do)\s+you\s+know\b|"
    r"which\s+(?:of\s+my\s+)?computers?\s+should\s+i\s+use\b|"
    r"which\s+should\s+i\s+use\s+for\b|"
    # Autobiographical prediction (Memory Authority → Prediction organ)
    r"what\s+am\s+i\s+likely\b|"
    r"when\s+am\s+i\s+likely\b|"
    r"what\s+is\s+likely\b|"
    r"what(?:'s|\s+is)\s+likely\s+to\s+happen\b|"
    r"if\s+i\b.+\bwhat\s+is\s+likely\b|"
    r"why\s+do\s+you\s+think\s+that\s+is\s+likely\b|"
    r"why\s+(?:is|was)\s+that\s+likely\b|"
    r"based\s+upon\s+memory,?\s+what\s+is\s+likely\b|"
    r"how\s+did\s+you\s+(?:make|form|arrive\s+at)\s+(?:that\s+)?prediction\b|"
    r"how\s+did\s+you\s+predict\b|"
    r"explain\s+(?:that\s+|your\s+)?prediction\b|"
    r"how\s+confident\s+are\s+you\s+that\b|"
    r"how\s+sure\s+are\s+you\s+that\b|"
    r"how\s+certain\s+are\s+you\s+that\b|"
    r"when\s+should\s+i\s+(?:work|fish|hike|go)\b|"
    r"what\s+should\s+i\s+(?:do|work)\b|"
    r"will\s+i\s+(?:definitely|certainly|probably|likely)\b|"
    r"am\s+i\s+(?:definitely|certainly|probably)\s+going\s+to\b|"
    r"what\s+will\s+happen\b|"
    r"will\s+(?:it|i|we)\b|"
    r"am\s+i\s+(?:going\s+to|likely\s+to)\b"
    r")",
    re.I,
)

# Habit / predictive teachings that must never fall through to host LLM.
_PREDICTIVE_TEACHING_SURFACE = re.compile(
    r"\b(?:"
    r"every\s+time\s+i\b|"
    r"whenever\s+i\b|"
    r"every\s+(?:saturday|sunday|monday|tuesday|wednesday|thursday|friday|weekend)\b|"
    r"i\s+usually\b|"
    r"it\s+has\s+rained\s+every\s+day\b|"
    r"sometimes\s+\w+\s+helps?\s+me\b|"
    r"\w+\s+sometimes\s+helps?\s+me\b|"
    r"(?:coffee|tea|alcohol)\s+causes?\b"
    r")",
    re.I,
)


def is_semantic_autobio_teaching(text: str) -> bool:
    """Declarative personal facts ACM Teaching Recognition will encode."""
    blob = text or ""
    if _PREDICTIVE_TEACHING_SURFACE.search(blob):
        return True
    detected = detect_teaching(blob)
    if not detected.is_teaching or not detected.facts:
        return False
    if any(f.kind in _SEMANTIC_TEACHING_KINDS for f in detected.facts):
        return True
    # Recurring-experience / habit patterns used by Prediction.
    return any(
        f.kind == FactKind.EXPERIENCE and f.property == "predictive_pattern"
        for f in detected.facts
    )


def is_semantic_autobio_query(text: str) -> bool:
    """Recall / integration questions about learned personal semantic memory."""
    return bool(SEMANTIC_AUTOBIO_QUERY.search(text or ""))


def is_semantic_autobio_utterance(text: str) -> bool:
    return is_semantic_autobio_teaching(text) or is_semantic_autobio_query(text)
