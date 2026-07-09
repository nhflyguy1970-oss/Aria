"""Data behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class DataSession(Protocol):
    last_data_path: str

    def resolve_data(self, path: str) -> str: ...

    def note_data(self, path: str) -> None: ...

    def note_module(self, module: str) -> None: ...


@dataclass
class DataContext:
    """Minimal orchestrator view required by the data engine."""

    data: Any
    session: DataSession

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> DataContext:
        return cls(data=orchestrator.data, session=orchestrator.session)
