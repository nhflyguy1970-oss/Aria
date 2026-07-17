"""Memory protection — language-model output must never become cognitive memory."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# Tags / origin markers that identify speech or generative contamination.
MEMORY_PROTECTION_TAGS: frozenset[str] = frozenset(
    {
        "llm_generated",
        "language_model",
        "speech_output",
        "host_generation",
        "assistant_utterance",
        "confabulation",
        "generated_response",
        "chat_completion",
    }
)

_FORBIDDEN_EXTERNAL_KINDS = frozenset(
    {
        "llm",
        "language_model",
        "speech",
        "generated",
        "completion",
    }
)


def reject_speech_contamination(
    *,
    text: str = "",
    context_tags: Iterable[str] | None = None,
    external_kind: str = "",
    provenance_origin: str = "",
) -> dict[str, Any] | None:
    """Return a reject dict if encode would contaminate memory from speech/LM.

    Returns ``None`` when encode is allowed.
    """
    tags = {str(t).strip().lower() for t in (context_tags or ()) if t}
    kind = (external_kind or "").strip().lower()
    origin = (provenance_origin or "").strip().lower()

    hit_tags = sorted(tags & MEMORY_PROTECTION_TAGS)
    if hit_tags:
        return {
            "encoded": False,
            "reason": "memory_protection",
            "detail": "language_model_or_speech_tags_forbidden",
            "tags": hit_tags,
        }
    if kind in _FORBIDDEN_EXTERNAL_KINDS:
        return {
            "encoded": False,
            "reason": "memory_protection",
            "detail": "external_kind_forbidden",
            "external_kind": kind,
        }
    if origin in MEMORY_PROTECTION_TAGS or origin in _FORBIDDEN_EXTERNAL_KINDS:
        return {
            "encoded": False,
            "reason": "memory_protection",
            "detail": "provenance_origin_forbidden",
            "origin": origin,
        }
    # Heuristic: block obvious "As an AI I made up..." self-reports tagged as memory
    lower = (text or "").lower()
    if "i hallucinated" in lower or "i invented that" in lower:
        return {
            "encoded": False,
            "reason": "memory_protection",
            "detail": "self_identified_fabrication",
        }
    # Content-level trust: tool/system/infra wrappers must never enter memory,
    # even when a host mislabels them as trusted user speech. Provenance alone
    # is insufficient when the payload itself is a non-user artifact.
    from acm.provenance.legacy_cleanup import classify_untrusted_artifact

    artifact = classify_untrusted_artifact(text)
    if artifact:
        return {
            "encoded": False,
            "reason": "memory_trust",
            "detail": f"content_artifact:{artifact}",
            "artifact": artifact,
        }
    return None
