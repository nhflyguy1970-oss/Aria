"""Unified knowledge — registry, sync, and search across all workstation sources."""

from jarvis.knowledge.registry import KnowledgeSource, get_source, list_sources, registry_snapshot, sync_registry
from jarvis.knowledge.search import format_unified_results, unified_search
from jarvis.knowledge.ingestion import ingest_all, maybe_scheduled_ingest, watch_paths

__all__ = [
    "KnowledgeSource",
    "format_unified_results",
    "get_source",
    "ingest_all",
    "list_sources",
    "maybe_scheduled_ingest",
    "registry_snapshot",
    "sync_registry",
    "unified_search",
    "watch_paths",
]
