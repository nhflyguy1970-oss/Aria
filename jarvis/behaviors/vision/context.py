"""Vision behavior context — orchestrator surface without tight coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class VisionSession(Protocol):
    def resolve_image(self, path: str) -> str: ...


class VisionOrchestrator(Protocol):
    _vision_llava_warned: bool

    @property
    def vision(self) -> Any: ...

    @property
    def session(self) -> VisionSession: ...


@dataclass
class VisionContext:
    orchestrator: VisionOrchestrator

    @property
    def vision(self) -> Any:
        return self.orchestrator.vision

    @property
    def session(self) -> VisionSession:
        return self.orchestrator.session

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> VisionContext:
        return cls(orchestrator=orchestrator)
