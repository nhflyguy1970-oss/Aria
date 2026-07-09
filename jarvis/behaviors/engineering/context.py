"""Engineering behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EngineeringContext:
    """Orchestrator facade for coding, git, and LSP operations."""

    _orchestrator: Any

    def __getattr__(self, name: str) -> Any:
        return getattr(self._orchestrator, name)

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> EngineeringContext:
        return cls(_orchestrator=orchestrator)
