"""ACM Memory Authority — sole authority for cognitive memory reconstruction.

Hosts MUST call ``CognitiveEngine.cognitive_respond`` (or classify + remember)
before any language-model generation for memory requests. Language models may
only *speak* ``CognitiveMemoryResult`` via ``speak_cognitive_result`` — never
invent, fill, or become memory.
"""

from __future__ import annotations

from acm.authority.classification import (
    MemoryIntent,
    MemoryRequestClassification,
    classify_memory_request,
)
from acm.authority.pipeline import CognitiveResponsePipeline
from acm.authority.protection import (
    MEMORY_PROTECTION_TAGS,
    reject_speech_contamination,
)
from acm.authority.result import CognitiveMemoryResult, MemoryStatus
from acm.authority.speak import speak_cognitive_result

__all__ = [
    "CognitiveMemoryResult",
    "CognitiveResponsePipeline",
    "MEMORY_PROTECTION_TAGS",
    "MemoryIntent",
    "MemoryRequestClassification",
    "MemoryStatus",
    "classify_memory_request",
    "reject_speech_contamination",
    "speak_cognitive_result",
]
