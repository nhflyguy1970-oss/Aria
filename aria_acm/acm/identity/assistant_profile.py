"""Operational (intrinsic) assistant identity — configuration, not autobiography."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AssistantIdentityProfile:
    """Host-configured assistant identity exposed by the Identity organ.

    Source of truth is configuration (or agent_id), not conversational memory.
    Autobiographical user facts must never populate these fields.
    """

    name: str | None = None
    role: str | None = None
    description: str | None = None
    capabilities: tuple[str, ...] = ()
    personality: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls, data: dict[str, Any] | None, *, agent_id: str
    ) -> AssistantIdentityProfile:
        if not data:
            return cls(name=agent_id)
        caps = data.get("capabilities") or ()
        if isinstance(caps, str):
            caps = (caps,)
        extra = {
            str(k): str(v)
            for k, v in (data.get("extra") or {}).items()
            if k not in ("name", "role", "description", "capabilities", "personality")
        }
        return cls(
            name=str(data["name"]) if data.get("name") else agent_id,
            role=str(data["role"]) if data.get("role") else None,
            description=str(data["description"]) if data.get("description") else None,
            capabilities=tuple(str(c) for c in caps),
            personality=str(data["personality"]) if data.get("personality") else None,
            extra=extra,
        )

    def resolved_name(self, agent_id: str) -> str:
        return (self.name or agent_id or "assistant").strip() or "assistant"
