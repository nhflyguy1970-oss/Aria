"""ACM — Aria Cognitive Memory: host-agnostic cognitive memory engine."""

from __future__ import annotations

# Aria M0: nested vendored package must resolve absolute `acm.*` imports.
import sys as _acm_sys

_acm_sys.modules.setdefault("acm", _acm_sys.modules[__name__])

from acm._version import __version__
from acm.api.engine import CognitiveEngine, RememberResult
from acm.observability.trace import CognitiveTraceEvent
from acm.plugins import BaseExtension, ExtensionRegistry
from acm.validation.harness import ValidationHarness

__all__ = [
    "CognitiveEngine",
    "RememberResult",
    "CognitiveTraceEvent",
    "ValidationHarness",
    "BaseExtension",
    "ExtensionRegistry",
    "__version__",
]
