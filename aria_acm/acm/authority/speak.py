"""Faithful speech templates — express ACM results only; never invent memory."""

from __future__ import annotations

from acm.authority.result import CognitiveMemoryResult, MemoryStatus

_UNKNOWN_PHRASES = {
    MemoryStatus.UNKNOWN: "I don't currently know.",
    MemoryStatus.INSUFFICIENT_EVIDENCE: "I don't yet have enough experiences to answer that.",
    MemoryStatus.LOW_CONFIDENCE: "I am not confident enough to answer from memory.",
    MemoryStatus.CONFLICTING: (
        "I have conflicting memories and cannot settle on a single answer yet."
    ),
}


def speak_cognitive_result(result: CognitiveMemoryResult) -> str:
    """Render speech that *only* expresses the ACM Cognitive Memory Result.

    Rules:
    - NEVER invent facts, identities, goals, or experiences.
    - NEVER fill gaps when status is unknown / insufficient / low confidence.
    - NEVER speak raw storage / adaptation dumps.
    - When known, speak the ACM ``memory`` field verbatim (ACM-owned text).
    - Identity intents: never blend the other identity (D044).
    - When not a memory request, return empty — host may use LM for non-memory tasks.
    """
    if not result.is_memory_request or result.status == MemoryStatus.NOT_MEMORY:
        return ""

    if result.status in _UNKNOWN_PHRASES:
        # Prefer organ-authored conflict / insufficiency text when present
        # (Prediction conflict explanations, contested reconstructions).
        if result.status == MemoryStatus.CONFLICTING:
            text = (result.memory or "").strip()
            if text and not text.startswith("{") and not text.startswith("["):
                return text
        base = _UNKNOWN_PHRASES[result.status]
        if result.uncertainty:
            return f"{base} ({result.uncertainty})"
        return base

    if result.status == MemoryStatus.KNOWN:
        text = (result.memory or "").strip()
        if not text or text.startswith("{") or text.startswith("["):
            return _UNKNOWN_PHRASES[MemoryStatus.UNKNOWN]
        if "'id':" in text and "'kind':" in text:
            return _UNKNOWN_PHRASES[MemoryStatus.UNKNOWN]
        # Final isolation pass for identity intents (defense in depth)
        intent = (result.intent or "").lower()
        if intent in ("user_identity", "assistant_identity"):
            from acm.identity.rendering import IdentityRenderTarget, isolate_identity_text

            target = (
                IdentityRenderTarget.USER
                if intent == "user_identity"
                else IdentityRenderTarget.ASSISTANT
            )
            text = isolate_identity_text(text, target=target) or text
        if result.ambiguous:
            return f"{text} (competing memories; confidence {result.confidence:.2f})"
        if result.confidence < 0.7:
            return f"{text} (confidence {result.confidence:.2f})"
        return text

    return _UNKNOWN_PHRASES[MemoryStatus.UNKNOWN]
