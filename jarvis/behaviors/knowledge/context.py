"""Knowledge behavior context — orchestrator surface without JarvisAssistant coupling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class KnowledgeContext:
    """Minimal orchestrator view required by the knowledge engine."""

    memory: Any
    session: Any
    _orchestrator: Any

    def refresh_system_prompt(self) -> None:
        self._orchestrator.refresh_system_prompt()

    def resolve_document_path(self, params: dict) -> str:
        from jarvis.config import DATA_DIR, PROJECT_ROOT, UPLOAD_DIR
        from jarvis.document_pipeline import documents_dir

        raw = (params.get("path") or "").strip()
        if not raw:
            return self.session.resolve_document("")
        path = Path(raw)
        if path.is_absolute() and path.exists():
            return str(path)
        for base in (PROJECT_ROOT, DATA_DIR, UPLOAD_DIR, documents_dir()):
            candidate = (base / raw).resolve()
            if candidate.exists():
                return str(candidate)
        resolved = path.expanduser()
        return str(resolved) if resolved.exists() else raw

    def __getattr__(self, name: str) -> Any:
        return getattr(self._orchestrator, name)

    @classmethod
    def from_orchestrator(cls, orchestrator: Any) -> KnowledgeContext:
        return cls(
            memory=orchestrator.memory,
            session=orchestrator.session,
            _orchestrator=orchestrator,
        )
