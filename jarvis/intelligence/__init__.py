"""Aria next-generation intelligence platform — modular capability layer.

Reuses existing memory, RAG, agents, graph, HA, vision, voice, and coding systems.
Adds production gaps: hybrid RAG, reasoning traces, multi-agent scratchpad,
automation/workflows, knowledge-graph API, plugins, and connectors.
"""

from __future__ import annotations

__all__ = [
    "hybrid_search",
    "reason",
    "run_multi_agent",
    "platform_status",
]

from jarvis.intelligence.hybrid_rag import hybrid_search
from jarvis.intelligence.platform_bus import platform_status
from jarvis.intelligence.reasoning import reason
from jarvis.intelligence.multi_agent import run_multi_agent
