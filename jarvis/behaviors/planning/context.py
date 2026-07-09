"""Planning behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class JournalScheduling(Protocol):
    def match_open_task(
        self,
        message: str,
        *,
        bullet_id: str | None = None,
        task_query: str | None = None,
    ) -> tuple[dict | None, list[dict], str]: ...

    def bullet_schedule(self, bullet_id: str, month: str) -> dict | None: ...

    def bullet_thread_to_daily(self, bullet_id: str, day: str, *, duplicate: bool = False) -> dict | None: ...

    def format_open_tasks(self, limit: int = 8) -> str: ...


@dataclass
class PlanningContext:
    """Minimal orchestrator view required by the planning engine."""

    journal: JournalScheduling

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> PlanningContext:
        return cls(journal=orchestrator.journal)
