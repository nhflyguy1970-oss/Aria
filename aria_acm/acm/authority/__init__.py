"""ACM Memory Authority — sole authority for cognitive memory reconstruction.

Hosts MUST call ``CognitiveEngine.cognitive_respond`` (or classify + remember)
before any language-model generation for memory requests. Language models may
only *speak* ``CognitiveMemoryResult`` via ``speak_cognitive_result`` — never
invent, fill, or become memory.

Pipeline (D038 · D039 · D040):
  classify → route/ownership → dispatch → organ terminate → CognitiveMemoryResult
"""

from __future__ import annotations

from acm.authority.classification import (
    MemoryIntent,
    MemoryRequestClassification,
    classify_memory_request,
    classify_request,
)
from acm.authority.dispatch import CognitiveDispatchEngine, DispatchOutcome, DispatchRecord
from acm.authority.mode import ExecutionMode, current_execution_mode, is_read_only, read_only
from acm.authority.pipeline import CognitiveResponsePipeline
from acm.authority.protection import (
    MEMORY_PROTECTION_TAGS,
    reject_speech_contamination,
)
from acm.authority.result import CognitiveMemoryResult, MemoryStatus
from acm.authority.routing import (
    CognitiveOwnership,
    CognitiveRoutingEngine,
    RoutingDecision,
    ownership_for_intent,
)
from acm.authority.speak import speak_cognitive_result
from acm.authority.taxonomy import CognitiveIntent

__all__ = [
    "CognitiveDispatchEngine",
    "CognitiveIntent",
    "CognitiveMemoryResult",
    "CognitiveOwnership",
    "CognitiveResponsePipeline",
    "CognitiveRoutingEngine",
    "DispatchOutcome",
    "DispatchRecord",
    "ExecutionMode",
    "MEMORY_PROTECTION_TAGS",
    "MemoryIntent",
    "MemoryRequestClassification",
    "MemoryStatus",
    "RoutingDecision",
    "classify_memory_request",
    "classify_request",
    "current_execution_mode",
    "is_read_only",
    "ownership_for_intent",
    "read_only",
    "reject_speech_contamination",
    "speak_cognitive_result",
]
