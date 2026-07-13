"""Aria Core — Reflex public API (Phase 8)."""

from __future__ import annotations

from aria_core import reflex_engine as _eng
from aria_core.ownership import module_ownership

OWNER = module_ownership("reflex")

REFLEX_VERSION = _eng.REFLEX_VERSION
extract_features = _eng.extract_features
evaluate = _eng.evaluate
try_reflex = _eng.try_reflex
is_reflex = _eng.is_reflex
reflex_history = _eng.reflex_history
reflex_statistics = _eng.reflex_statistics
mission_control_panel = _eng.mission_control_panel
mark_false_positive = _eng.mark_false_positive
mark_false_negative = _eng.mark_false_negative
reset_for_tests = _eng.reset_for_tests

__all__ = [
    "OWNER",
    "REFLEX_VERSION",
    "evaluate",
    "extract_features",
    "is_reflex",
    "mark_false_negative",
    "mark_false_positive",
    "mission_control_panel",
    "reflex_history",
    "reflex_statistics",
    "reset_for_tests",
    "try_reflex",
]
