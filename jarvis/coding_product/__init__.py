"""Coding product — propose → review → apply → undo → verify.

Owns coding workflow surfaces. Does not own Projects, Job Center,
Activity Center, Mission Control, or Models configuration.
"""

from __future__ import annotations

from jarvis.coding_product.home import coding_home_snapshot
from jarvis.coding_product.terminology import TERMINOLOGY, BOUNDARIES

__all__ = [
    "coding_home_snapshot",
    "TERMINOLOGY",
    "BOUNDARIES",
]
