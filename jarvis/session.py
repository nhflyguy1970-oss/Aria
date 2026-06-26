from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionContext:
    """Tracks conversation context for natural follow-ups."""

    last_file: str = ""
    last_image: str = ""
    last_audio: str = ""
    last_data_path: str = ""
    last_document_path: str = ""
    last_knowledge_slug: str = ""
    last_proposal_id: str = ""
    last_search_query: str = ""
    last_module: str = "general"
    last_briefing_headlines: list[dict[str, str]] = field(default_factory=list)
    last_coding_mode: str = ""
    chat_model: str = ""
    memory_namespace: str = "default"
    recent_files: list[str] = field(default_factory=list)
    pending_clarification: dict | None = None

    def note_file(self, path: str) -> None:
        self.last_file = path
        if path and path not in self.recent_files:
            self.recent_files.insert(0, path)
            self.recent_files = self.recent_files[:10]

    def note_image(self, path: str) -> None:
        self.last_image = path

    def note_audio(self, path: str) -> None:
        self.last_audio = path

    def note_data(self, path: str) -> None:
        self.last_data_path = path

    def note_document(self, path: str) -> None:
        self.last_document_path = path
        self.note_file(path)

    def note_knowledge(self, slug: str) -> None:
        self.last_knowledge_slug = (slug or "").strip()

    def note_proposal(self, proposal_id: str) -> None:
        self.last_proposal_id = proposal_id

    def note_search(self, query: str) -> None:
        self.last_search_query = query

    def note_briefing_headlines(self, headlines: list[dict[str, str]]) -> None:
        slim: list[dict[str, str]] = []
        for item in headlines[:12]:
            slim.append({
                k: str(item[k])
                for k in ("title", "url", "source", "category", "published")
                if item.get(k)
            })
        self.last_briefing_headlines = slim
        self.last_module = "briefing"

    def note_module(self, module: str) -> None:
        self.last_module = module

    def note_memory_namespace(self, namespace: str) -> None:
        self.memory_namespace = (namespace or "default").strip() or "default"

    def note_coding_mode(self, mode: str) -> None:
        if mode:
            self.last_coding_mode = mode

    def note_chat_model(self, model: str) -> None:
        self.chat_model = (model or "").strip()

    def resolve_path(self, path: str | None) -> str:
        if path:
            return path
        if self.last_file:
            return self.last_file
        try:
            from jarvis.editor_context import get_context
            ctx = get_context()
            if ctx and ctx.relative_file:
                return ctx.relative_file
        except Exception:
            pass
        return ""

    def resolve_image(self, path: str | None) -> str:
        if path:
            return path
        return self.last_image

    def resolve_audio(self, path: str | None) -> str:
        if path:
            return path
        return self.last_audio

    def resolve_data(self, path: str | None) -> str:
        if path:
            return path
        return self.last_data_path

    def resolve_document(self, path: str | None) -> str:
        if path:
            return path
        return self.last_document_path

    def context_summary(self) -> str:
        parts = []
        if self.last_file:
            parts.append(f"last_file={self.last_file}")
        if self.last_image:
            parts.append(f"last_image={self.last_image}")
        if self.last_audio:
            parts.append(f"last_audio={self.last_audio}")
        if self.last_data_path:
            parts.append(f"last_data={self.last_data_path}")
        if self.last_document_path:
            parts.append(f"last_document={self.last_document_path}")
        if self.last_knowledge_slug:
            parts.append(f"last_knowledge={self.last_knowledge_slug}")
        if self.last_proposal_id:
            parts.append(f"last_proposal={self.last_proposal_id}")
        if self.last_coding_mode:
            parts.append(f"last_coding_mode={self.last_coding_mode}")
        if self.recent_files:
            parts.append(f"recent_files={', '.join(self.recent_files[:5])}")
        if self.memory_namespace and self.memory_namespace != "default":
            parts.append(f"memory_ns={self.memory_namespace}")
        if self.chat_model:
            parts.append(f"chat_model={self.chat_model}")
        if self.last_briefing_headlines:
            titles = "; ".join((h.get("title") or "")[:60] for h in self.last_briefing_headlines[:4])
            if titles:
                parts.append(f"briefing_headlines={titles}")
        return "; ".join(parts) if parts else "none"

    def clear(self) -> None:
        self.last_file = ""
        self.last_image = ""
        self.last_audio = ""
        self.last_data_path = ""
        self.last_document_path = ""
        self.last_knowledge_slug = ""
        self.last_proposal_id = ""
        self.last_search_query = ""
        self.last_briefing_headlines = []
        self.last_coding_mode = ""
        self.recent_files.clear()
        self.pending_clarification = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_file": self.last_file,
            "last_image": self.last_image,
            "last_audio": self.last_audio,
            "last_data_path": self.last_data_path,
            "last_document_path": self.last_document_path,
            "last_knowledge_slug": self.last_knowledge_slug,
            "last_proposal_id": self.last_proposal_id,
            "last_search_query": self.last_search_query,
            "last_briefing_headlines": list(self.last_briefing_headlines),
            "last_module": self.last_module,
            "last_coding_mode": self.last_coding_mode,
            "chat_model": self.chat_model,
            "memory_namespace": self.memory_namespace,
            "recent_files": list(self.recent_files),
            "pending_clarification": self.pending_clarification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "SessionContext":
        if not data:
            return cls()
        return cls(
            last_file=data.get("last_file", ""),
            last_image=data.get("last_image", ""),
            last_audio=data.get("last_audio", ""),
            last_data_path=data.get("last_data_path", ""),
            last_document_path=data.get("last_document_path", ""),
            last_knowledge_slug=data.get("last_knowledge_slug", ""),
            last_proposal_id=data.get("last_proposal_id", ""),
            last_search_query=data.get("last_search_query", ""),
            last_briefing_headlines=list(data.get("last_briefing_headlines") or []),
            last_module=data.get("last_module", "general"),
            last_coding_mode=data.get("last_coding_mode", ""),
            chat_model=data.get("chat_model", ""),
            memory_namespace=data.get("memory_namespace", "default"),
            recent_files=list(data.get("recent_files") or []),
            pending_clarification=data.get("pending_clarification"),
        )
