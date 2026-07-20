"""Shared episodic autobiographical patterns for Aria routing guards.

Cognition lives in ACM; these patterns only prevent Mission Control / search
mis-routes and steer declarative events to Memory Authority.
"""

from __future__ import annotations

import re

_TEMPORAL = (
    r"(?:yesterday|today|this\s+morning|this\s+afternoon|this\s+evening|"
    r"last\s+night|last\s+week|last\s+month|"
    r"last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))"
)
_ACTION = (
    r"(?:bought|cleaned|went|installed|visited|built|finished|started|"
    r"drove|flew|walked|called|met|watched|read|wrote|cooked|fixed|"
    r"moved|painted|planted|hiked|ran|swam|played|taught|learned|"
    r"attended|joined|left|opened|closed|replaced|upgraded|"
    r"purchased|ordered|picked\s+up|dropped\s+off)"
)

EPISODIC_TEACHING = re.compile(
    rf"(?:^\s*{_TEMPORAL}\s+i\s+{_ACTION}\s+.+\.?\s*$|"
    rf"^\s*i\s+{_ACTION}\s+.+\s+{_TEMPORAL}\s*[.!?]?\s*$)",
    re.I,
)

EPISODIC_MEMORY_QUERY = re.compile(
    rf"\b(?:"
    rf"what\s+happened(?:\s+{_TEMPORAL})?|"
    rf"what\s+did\s+i\s+\w+(?:\s+{_TEMPORAL})?|"
    rf"what\s+happened\s+(?:before|after)|"
    rf"explain\s+what\s+happened|"
    rf"tell\s+me\s+about\s+(?:buying|cleaning|installing|visiting|going)"
    rf")\b",
    re.I,
)


def is_episodic_teaching(text: str) -> bool:
    return bool(EPISODIC_TEACHING.search((text or "").strip()))


def is_episodic_memory_query(text: str) -> bool:
    return bool(EPISODIC_MEMORY_QUERY.search(text or ""))


def is_episodic_memory_utterance(text: str) -> bool:
    """Teaching or recall — must stay on Memory Authority, not Mission Control."""
    return is_episodic_teaching(text) or is_episodic_memory_query(text)
