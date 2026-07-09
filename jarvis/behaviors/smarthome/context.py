"""Smart home behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class SessionNotes(Protocol):
    def note_module(self, module: str) -> None: ...


@dataclass
class SmartHomeContext:
    """Minimal orchestrator view required by the smart home engine."""

    session: SessionNotes

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> SmartHomeContext:
        return cls(session=orchestrator.session)
