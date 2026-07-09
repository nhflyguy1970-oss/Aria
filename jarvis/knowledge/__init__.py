"""Unified knowledge — registry, sync, and search across all workstation sources."""

from jarvis.knowledge.registry import KnowledgeSource, get_source, list_sources, registry_snapshot, sync_registry
from jarvis.knowledge.search import format_unified_results, unified_search

__all__ = [
    "KnowledgeSource",
    "format_unified_results",
    "get_source",
    "list_sources",
    "registry_snapshot",
    "sync_registry",
    "unified_search",
]
