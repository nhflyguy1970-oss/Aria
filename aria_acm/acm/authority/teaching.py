"""Teaching Recognition — declarative user statements become memory updates.

The Cognitive Memory Response Pipeline receives every inbound user request
(hosts MUST route user messages through Memory Authority before language-model
generation). A request is a *teaching* when it is a declarative, non-
interrogative statement from which Semantic Extraction yields structured
cognitive facts ("My favorite color is green.", "My name is Jeff.").

Prior to this stage, valid teachings were dispatched as retrieval requests:
"My favorite color is green." classified as intent=preference and terminated
at the Remembering Organ, answering from the *current* store ("blue") while
the new value was never encoded. Teaching Recognition closes that gap without
weakening any protection:

- Interrogatives never teach ("Is my favorite color yellow?" extracts no
  preference fact, and any request that parses as a question is refused here).
- Trusted Memory Ingestion (D046) still gates the encode: the teaching is
  submitted as a user conversational statement, and content-level artifact
  protection still rejects tool/system/infra payloads regardless of declared
  provenance.
- Evidence and retrieval requests carry no declarative facts and therefore
  never mutate memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from acm.semantic import extract_semantics
from acm.semantic.facts import is_interrogative


@dataclass(frozen=True)
class TeachingDetection:
    """Whether a request is a declarative teaching, and the extracted facts."""

    is_teaching: bool
    reason: str
    facts: tuple[Any, ...] = field(default_factory=tuple)

    def to_public(self) -> dict[str, Any]:
        return {
            "is_teaching": self.is_teaching,
            "reason": self.reason,
            "facts": [
                {
                    "kind": f.kind.value,
                    "property": f.property,
                    "value": f.value,
                    "update_op": f.update_op.value,
                }
                for f in self.facts
            ],
            "schema": "teaching_detection.v1",
        }


def detect_teaching(request: str) -> TeachingDetection:
    """Classify a request as declarative teaching vs. retrieval cue.

    Teachings require extracted cognitive facts AND a non-interrogative form.
    This function never mutates memory — the encode (with its trust gates)
    remains the single enforcement point.
    """
    text = (request or "").strip()
    if not text:
        return TeachingDetection(False, "empty_request")
    if is_interrogative(text):
        return TeachingDetection(False, "interrogative_never_teaches")
    extraction = extract_semantics(text)
    if not extraction.facts:
        return TeachingDetection(False, "no_declarative_facts")
    return TeachingDetection(
        True,
        "declarative_facts_extracted",
        facts=tuple(extraction.facts),
    )
