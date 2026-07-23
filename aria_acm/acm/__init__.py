"""ACM — Aria Cognitive Memory: host-agnostic cognitive memory engine."""

from __future__ import annotations

# Aria nested-vendor shim: allow `import acm` to resolve to this package.
import sys as _acm_sys

_acm_sys.modules.setdefault("acm", _acm_sys.modules[__name__])

from acm._version import __version__
from acm.api.engine import CognitiveEngine, RememberResult
from acm.authority import (
    CognitiveIntent,
    CognitiveMemoryResult,
    MemoryStatus,
    classify_memory_request,
    speak_cognitive_result,
)
from acm.observability.trace import CognitiveTraceEvent
from acm.plugins import BaseExtension, ExtensionRegistry
from acm.provenance import (
    TRUSTED_USER_CORRECTION,
    TRUSTED_USER_STATEMENT,
    TRUSTED_USER_TEACHING,
    HostOperation,
    IngestionActor,
    IngestionDecision,
    IngestionProvenance,
    MessageRole,
)
from acm.validation.harness import ValidationHarness

__all__ = [
    "CognitiveEngine",
    "CognitiveIntent",
    "CognitiveMemoryResult",
    "MemoryStatus",
    "RememberResult",
    "CognitiveTraceEvent",
    "ValidationHarness",
    "BaseExtension",
    "ExtensionRegistry",
    "HostOperation",
    "IngestionActor",
    "IngestionDecision",
    "IngestionProvenance",
    "MessageRole",
    "TRUSTED_USER_CORRECTION",
    "TRUSTED_USER_STATEMENT",
    "TRUSTED_USER_TEACHING",
    "classify_memory_request",
    "speak_cognitive_result",
    "__version__",
]
