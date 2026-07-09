"""Audio behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class AudioSession(Protocol):
    def resolve_audio(self, path: str) -> str: ...

    def note_audio(self, path: str) -> None: ...


@dataclass
class AudioContext:
    """Minimal orchestrator view required by the audio engine."""

    audio: Any
    session: AudioSession

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> AudioContext:
        return cls(audio=orchestrator.audio, session=orchestrator.session)
