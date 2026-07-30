"""Latency observability — explain every millisecond without changing execution behavior."""

from __future__ import annotations

from jarvis.latency_observability.trace import (
    LatencyTrace,
    active_trace,
    begin_trace,
    complete_trace,
    current_trace_id,
    get_trace,
    note_stage,
)

__all__ = [
    "LatencyTrace",
    "active_trace",
    "begin_trace",
    "complete_trace",
    "current_trace_id",
    "get_trace",
    "note_stage",
]
