"""Evidence / confidence gates that convert soft activation into honest unknown."""

from __future__ import annotations

from acm.authority.result import MemoryStatus
from acm.types import ExplanationClass

# Below this blended confidence, do not claim known memory.
MIN_KNOWN_CONFIDENCE = 0.42
# Below this, refuse reconsolidation reinforcement (handled in remembering organ).
MIN_RECONSOLIDATION_CONFIDENCE = 0.45


def gate_status(
    *,
    explanation_class: str,
    confidence: float,
    ambiguous: bool,
    has_memory_text: bool,
    supporting_experience_count: int,
    cue_matched: bool,
) -> MemoryStatus:
    """Map reconstruction fields onto Memory Authority status."""
    try:
        expl = ExplanationClass(explanation_class)
    except ValueError:
        expl = ExplanationClass.UNKNOWN

    if expl == ExplanationClass.UNKNOWN or not has_memory_text:
        return MemoryStatus.UNKNOWN

    if expl == ExplanationClass.CONTESTED or ambiguous:
        return MemoryStatus.CONFLICTING

    if not cue_matched and supporting_experience_count == 0:
        return MemoryStatus.INSUFFICIENT_EVIDENCE

    if confidence < MIN_KNOWN_CONFIDENCE:
        return MemoryStatus.LOW_CONFIDENCE

    if expl == ExplanationClass.STALE and confidence < 0.55:
        return MemoryStatus.LOW_CONFIDENCE

    return MemoryStatus.KNOWN


def uncertainty_label(status: MemoryStatus, confidence: float) -> str | None:
    if status == MemoryStatus.UNKNOWN:
        return "no_reliable_reconstruction"
    if status == MemoryStatus.INSUFFICIENT_EVIDENCE:
        return "activation_without_cue_grounding"
    if status == MemoryStatus.LOW_CONFIDENCE:
        return f"confidence_{confidence:.2f}_below_threshold"
    if status == MemoryStatus.CONFLICTING:
        return "competing_recollections"
    return None
