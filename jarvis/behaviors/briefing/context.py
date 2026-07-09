"""Briefing behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class BriefingSession(Protocol):
    last_briefing_headlines: list[dict] | None

    def note_briefing_headlines(self, headlines: list[dict]) -> None: ...


@dataclass
class BriefingContext:
    """Minimal orchestrator view required by the briefing engine."""

    journal: Any
    memory_store: Any
    session: BriefingSession

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> BriefingContext:
        return cls(
            journal=orchestrator.journal,
            memory_store=orchestrator.memory,
            session=orchestrator.session,
        )
