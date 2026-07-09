"""Memory behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class VisionOcr(Protocol):
    def ocr(self, path: str) -> str: ...

    def analyze(self, prompt: str, path: str, *, task: str = "") -> str: ...


class JournalRemember(Protocol):
    def bullet_remember_text(self, bullet_id: str) -> str: ...

    def daily_get(self) -> dict: ...


@dataclass
class MemoryContext:
    """Minimal orchestrator view required by the memory engine."""

    memory: Any
    session: Any
    conversation: Any
    journal: JournalRemember
    vision: VisionOcr
    task_manager: Any
    _orchestrator: Any

    def refresh_system_prompt(self) -> None:
        self._orchestrator.refresh_system_prompt()

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> MemoryContext:
        return cls(
            memory=orchestrator.memory,
            session=orchestrator.session,
            conversation=orchestrator.conversation,
            journal=orchestrator.journal,
            vision=orchestrator.vision,
            task_manager=orchestrator.task_manager,
            _orchestrator=orchestrator,
        )
