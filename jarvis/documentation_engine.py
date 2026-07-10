"""Backward compatibility shim — use Reference Engine."""

from jarvis.reference_engine import search_documentation, search_reference

__all__ = ["search_reference", "search_documentation"]
