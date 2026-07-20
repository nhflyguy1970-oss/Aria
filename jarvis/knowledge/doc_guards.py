"""Guardrails — keep internal implementation docs out of normal user retrieval."""

from __future__ import annotations

import re

_INTERNAL_DOC_MARKERS: tuple[str, ...] = (
    "docs/adr/",
    "docs/acm_integration/",
    "memory_design_principles",
    "decision_log",
    "problem_report",
    "blueprint",
    "integration_test_plan",
    "memory_replacement",
    "aria_acm_architecture",
    "aria_cognitive_memory",
    "cognitive_memory_test_strategy",
    "architecture_boundaries",
    "phase_roadmap",
    "project_history",
)

_DEVELOPER_DOC_REQUEST = re.compile(
    r"\b("
    r"adr|architecture doc(?:ument)?s?|design doc(?:ument)?s?|developer doc(?:ument)?s?|"
    r"internal doc(?:ument)?s?|implementation doc(?:ument)?s?|"
    r"acm integration|memory design principles|decision log|"
    r"show (?:me )?(?:the )?(?:adr|architecture|design doc)"
    r")\b",
    re.I,
)


def is_internal_doc(path: str) -> bool:
    """True for ADRs, ACM integration blueprints, and other operator-only docs."""
    normalized = str(path or "").replace("\\", "/").lower()
    if not normalized:
        return False
    return any(marker in normalized for marker in _INTERNAL_DOC_MARKERS)


def is_developer_doc_request(query: str) -> bool:
    """True when the user explicitly asked for internal/developer documentation."""
    return bool(_DEVELOPER_DOC_REQUEST.search((query or "").strip()))


_PLANNING_REQUEST = re.compile(
    r"\b(?:help me plan|help us plan|plan (?:a|an|the|my|our)\b|make (?:a|an) plan\b|"
    r"create (?:a|an) plan\b|plan my (?:day|week))\b",
    re.I,
)


def is_planning_request(query: str) -> bool:
    """True when the user asked for a plan — must not fall through to docs."""
    return bool(_PLANNING_REQUEST.search((query or "").strip()))


def filter_user_facing_paths(paths: list[str], *, query: str = "") -> list[str]:
    """Drop internal docs unless the user explicitly requested developer material."""
    if is_developer_doc_request(query):
        return paths
    filtered = [p for p in paths if not is_internal_doc(p)]
    # Planning requests must never surface application catalog docs.
    if is_planning_request(query):
        filtered = [
            p
            for p in filtered
            if "applications.md" not in str(p).replace("\\", "/").lower()
        ]
    return filtered
