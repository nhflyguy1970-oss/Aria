"""What a task needs from a model.

Requirements split in two. Hard requirements are things that make a result
invalid if missing — vision for an image, tools for a tool call, enough context
for the prompt — and are never traded away by scoring. Preferences shape the
ranking and nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis.model_routing import capabilities as caps

# Latency/quality preference.
FAST = "fast"
BALANCED = "balanced"
QUALITY = "quality"
PREFERENCES = (FAST, BALANCED, QUALITY)

DEFAULT_OUTPUT_RESERVE = 1024
DEFAULT_MAX_FALLBACKS = 2


@dataclass(frozen=True)
class RoutingRequest:
    """A task's model requirements. Every field has a deterministic default."""

    task_type: str = "general"
    role: str = ""
    required_capabilities: tuple[str, ...] = ()
    preferred_capabilities: tuple[str, ...] = ()
    min_context_tokens: int = 0
    output_reserve_tokens: int = DEFAULT_OUTPUT_RESERVE
    require_tools: bool = False
    require_vision: bool = False
    require_structured_output: bool = False
    local_only: bool = True
    preferred_model: str = ""
    preferred_provider: str = ""
    excluded_models: tuple[str, ...] = ()
    latency_preference: str = BALANCED
    max_fallbacks: int = DEFAULT_MAX_FALLBACKS
    timeout_s: float = 120.0
    agent_id: str = ""
    skill_id: str = ""
    mission_id: str = ""
    requester: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def hard_capabilities(self) -> tuple[str, ...]:
        """Everything that must genuinely be supported, from all sources."""
        needed = set(self.required_capabilities)
        if self.require_tools:
            needed.add(caps.TOOL_USE)
        if self.require_vision:
            needed.add(caps.VISION)
        if self.require_structured_output:
            needed.add(caps.STRUCTURED_OUTPUT)
        return tuple(sorted(needed))

    def total_context_needed(self) -> int:
        """Prompt plus reserved output space: both have to fit."""
        return max(0, int(self.min_context_tokens)) + max(0, int(self.output_reserve_tokens))

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "role": self.role,
            "required_capabilities": list(self.required_capabilities),
            "hard_capabilities": list(self.hard_capabilities()),
            "preferred_capabilities": list(self.preferred_capabilities),
            "min_context_tokens": self.min_context_tokens,
            "output_reserve_tokens": self.output_reserve_tokens,
            "total_context_needed": self.total_context_needed(),
            "require_tools": self.require_tools,
            "require_vision": self.require_vision,
            "require_structured_output": self.require_structured_output,
            "local_only": self.local_only,
            "preferred_model": self.preferred_model,
            "preferred_provider": self.preferred_provider,
            "excluded_models": list(self.excluded_models),
            "latency_preference": self.latency_preference,
            "max_fallbacks": self.max_fallbacks,
            "timeout_s": self.timeout_s,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "mission_id": self.mission_id,
            "requester": self.requester,
            "metadata": dict(self.metadata),
        }


def validate(request: RoutingRequest) -> RoutingRequest:
    for capability in (*request.required_capabilities, *request.preferred_capabilities):
        caps.normalise(capability)
    if request.latency_preference not in PREFERENCES:
        raise ValueError(f"Unknown latency preference: {request.latency_preference!r}")
    if request.max_fallbacks < 0:
        raise ValueError("max_fallbacks cannot be negative")
    if request.timeout_s <= 0:
        raise ValueError("timeout_s must be positive")
    return request
