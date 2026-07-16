"""Public Semantic Extraction API."""

from __future__ import annotations

from acm.semantic.extract import extract_semantics
from acm.semantic.model import (
    CognitiveFact,
    ExtractionResult,
    FactKind,
    PerspectiveResolution,
    PerspectiveSubject,
    UpdateOp,
)
from acm.semantic.perspective import resolve_perspective
from acm.semantic.strip import has_remember_instruction, strip_instructional

__all__ = [
    "CognitiveFact",
    "ExtractionResult",
    "FactKind",
    "PerspectiveResolution",
    "PerspectiveSubject",
    "UpdateOp",
    "extract_semantics",
    "resolve_perspective",
    "strip_instructional",
    "has_remember_instruction",
]
