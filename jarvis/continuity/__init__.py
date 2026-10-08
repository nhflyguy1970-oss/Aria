"""Conversation continuity — source history linked to ACM.

ACM remains ARIA's cognitive memory. This package is the source-history layer
beside it: what was actually said and done, indexed for retrieval, with user
statements linked into ACM by provenance. See store, ingest and retrieve.
"""

from jarvis.continuity.ingest import (
    drain_outbox,
    record_tool_outcome,
    status,
    sync_all,
    sync_archives,
    sync_missions,
)
from jarvis.continuity.retrieve import (
    HITS,
    NO_RECORD,
    PARTIAL,
    UNAVAILABLE,
    ContinuityResult,
    answer,
    is_continuity_query,
    retrieve,
)

__all__ = [
    "HITS",
    "NO_RECORD",
    "PARTIAL",
    "UNAVAILABLE",
    "ContinuityResult",
    "answer",
    "drain_outbox",
    "is_continuity_query",
    "record_tool_outcome",
    "retrieve",
    "status",
    "sync_all",
    "sync_archives",
    "sync_missions",
]
