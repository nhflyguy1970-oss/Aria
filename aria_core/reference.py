"""Aria Core — Reference (delegates to jarvis.reference_engine)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("reference")


def search_reference(query: str, *, subject: str = "") -> dict[str, Any]:
    from jarvis.reference_engine import search_reference as _search

    return _search(query, subject=subject)
