"""Aria Core — sovereign API surface (Phase 2).

Phase 2 rule: wrap and delegate. Do not move implementations.
Existing jarvis / aiplatform modules remain the organs.
"""

from __future__ import annotations

from aria_core.ownership import OWNERSHIP, module_ownership

__version__ = "2.0.0-phase2"

__all__ = [
    "OWNERSHIP",
    "module_ownership",
    "__version__",
]
