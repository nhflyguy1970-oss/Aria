"""Cognitive observability events — no prompts, no chain-of-thought."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Any


@dataclass
class CognitiveTraceEvent:
    verb: str
    timestamp: float = field(default_factory=time)
    attention_class: str = "default"
    context_tags: list[str] = field(default_factory=list)
    goal_ids: list[str] = field(default_factory=list)
    activated_concept_ids: list[str] = field(default_factory=list)
    association_edge_types: list[str] = field(default_factory=list)
    explanation_class: str = "unknown"
    reconsolidation: str = "null"  # null | light | supersede | contest
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return asdict(self)


class TraceLog:
    def __init__(self, *, max_events: int = 1000) -> None:
        self.max_events = max_events
        self.events: list[CognitiveTraceEvent] = []

    def append(self, event: CognitiveTraceEvent) -> None:
        self.events.append(event)
        overflow = len(self.events) - self.max_events
        if overflow > 0:
            del self.events[:overflow]

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return [e.to_public() for e in self.events[-limit:]]
