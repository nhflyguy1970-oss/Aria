"""Knowledge Registry — tracks every knowledge source on the workstation."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, JOURNAL_DIR, PROJECT_ROOT

logger = logging.getLogger("jarvis.knowledge.registry")

REGISTRY_DIR = DATA_DIR / "knowledge"
REGISTRY_FILE = REGISTRY_DIR / "registry.json"
REGISTRY_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _source_id(source_type: str, location: str) -> str:
    digest = hashlib.sha256(f"{source_type}:{location}".encode()).hexdigest()[:16]
    return f"{source_type.replace('_', '-')}-{digest}"


@dataclass
class KnowledgeSource:
    id: str
    type: str
    label: str
    location: str
    namespace: str = "default"
    indexing_status: str = "unknown"
    embedding_status: str = "none"
    document_count: int = 0
    chunk_count: int = 0
    last_indexed: str = ""
    last_modified: str = ""
    last_sync: str = ""
    last_successful_sync: str = ""
    health: str = "unknown"
    errors: list[str] = field(default_factory=list)
    retrieval_available: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeSource:
        return cls(
            id=str(data.get("id") or ""),
            type=str(data.get("type") or "mixed"),
            label=str(data.get("label") or ""),
            location=str(data.get("location") or ""),
            namespace=str(data.get("namespace") or "default"),
            indexing_status=str(data.get("indexing_status") or "unknown"),
            embedding_status=str(data.get("embedding_status") or "none"),
            document_count=int(data.get("document_count") or 0),
            chunk_count=int(data.get("chunk_count") or 0),
            last_indexed=str(data.get("last_indexed") or ""),
            last_modified=str(data.get("last_modified") or ""),
            last_sync=str(data.get("last_sync") or ""),
            last_successful_sync=str(data.get("last_successful_sync") or ""),
            health=str(data.get("health") or "unknown"),
            errors=list(data.get("errors") or []),
            retrieval_available=bool(data.get("retrieval_available")),
            metadata=dict(data.get("metadata") or {}),
        )


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_FILE.is_file():
        return {"version": REGISTRY_VERSION, "sources": {}, "updated_at": ""}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("sources", {})
            return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Corrupt knowledge registry: %s", exc)
    return {"version": REGISTRY_VERSION, "sources": {}, "updated_at": ""}


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    data["version"] = REGISTRY_VERSION
    data["updated_at"] = _utc_now()
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    except OSError:
        return ""


def _dir_stats(path: Path, *, extensions: set[str] | None = None) -> tuple[int, str]:
    if not path.is_dir():
        return 0, ""
    count = 0
    latest = 0.0
    for item in path.rglob("*"):
        if not item.is_file() or item.name.startswith("."):
            continue
        if extensions and item.suffix.lower() not in extensions:
            continue
        count += 1
        try:
            latest = max(latest, item.stat().st_mtime)
        except OSError:
            continue
    modified = (
        datetime.fromtimestamp(latest, tz=timezone.utc).isoformat(timespec="seconds") if latest else ""
    )
    return count, modified


def _embed_status() -> str:
    try:
        from jarvis import llm

        if llm.embed_available():
            return "ready"
        return "offline"
    except Exception:
        return "offline"


def _discover_document_library() -> KnowledgeSource:
    from jarvis.document_pipeline import DOCUMENTS_DIR
    from jarvis.documents_rag import INDEX_FILE, index_needs_rebuild

    doc_count, modified = _dir_stats(DOCUMENTS_DIR, extensions={".pdf", ".docx"})
    chunk_count = 0
    last_indexed = _mtime_iso(INDEX_FILE) if INDEX_FILE.exists() else ""
    errors: list[str] = []
    if INDEX_FILE.exists():
        try:
            chunks = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
            if isinstance(chunks, list):
                chunk_count = len(chunks)
        except Exception as exc:
            errors.append(str(exc)[:120])

    if doc_count == 0:
        status, health = "empty", "offline"
    elif index_needs_rebuild():
        status, health = "stale", "degraded"
    elif chunk_count:
        status, health = "indexed", "healthy"
    else:
        status, health = "unknown", "degraded"

    embed = _embed_status()
    retrieval = chunk_count > 0 and embed in ("ready", "partial")

    return KnowledgeSource(
        id=_source_id("document_library", str(DOCUMENTS_DIR)),
        type="document_library",
        label="Document Library",
        location=str(DOCUMENTS_DIR),
        namespace="aria:documents",
        indexing_status=status,
        embedding_status=embed if chunk_count else "none",
        document_count=doc_count,
        chunk_count=chunk_count,
        last_indexed=last_indexed,
        last_modified=modified,
        health=health,
        errors=errors,
        retrieval_available=retrieval,
        metadata={"index_file": str(INDEX_FILE)},
    )


def _discover_code_index() -> KnowledgeSource:
    from jarvis.code_index import CODE_INDEX

    chunk_count = 0
    last_indexed = _mtime_iso(CODE_INDEX) if CODE_INDEX.exists() else ""
    errors: list[str] = []
    if CODE_INDEX.exists():
        try:
            chunks = json.loads(CODE_INDEX.read_text(encoding="utf-8"))
            if isinstance(chunks, list):
                chunk_count = len(chunks)
        except Exception as exc:
            errors.append(str(exc)[:120])

    root = PROJECT_ROOT
    file_count, modified = _dir_stats(root, extensions={
        ".py", ".js", ".ts", ".tsx", ".md", ".yaml", ".yml", ".sh", ".go", ".rs",
    })
    embed = _embed_status()
    if chunk_count:
        status, health = "indexed", "healthy" if embed == "ready" else "degraded"
    elif file_count:
        status, health = "stale", "degraded"
    else:
        status, health = "empty", "offline"

    return KnowledgeSource(
        id=_source_id("code_index", str(root)),
        type="code_index",
        label=f"Code Index ({root.name})",
        location=str(root),
        namespace="aria:code",
        indexing_status=status,
        embedding_status=embed if chunk_count else "none",
        document_count=file_count,
        chunk_count=chunk_count,
        last_indexed=last_indexed,
        last_modified=modified,
        health=health,
        errors=errors,
        retrieval_available=chunk_count > 0 and embed == "ready",
        metadata={"index_file": str(CODE_INDEX)},
    )


def _discover_project(meta: dict[str, Any]) -> KnowledgeSource:
    slug = str(meta.get("slug") or "")
    root = Path((meta.get("paths") or {}).get("root") or "")
    git_path = str(meta.get("git_path") or "").strip()
    source_type = "git_repository" if git_path else "project_folder"
    location = git_path or str(root)
    md_count, modified = _dir_stats(root, extensions={".md", ".markdown"}) if root.is_dir() else (0, "")
    pdf_count, _ = _dir_stats(root, extensions={".pdf", ".docx"}) if root.is_dir() else (0, "")
    doc_count = md_count + pdf_count
    status = "indexed" if doc_count else ("empty" if root.is_dir() else "error")
    health = "healthy" if root.is_dir() else "error"
    return KnowledgeSource(
        id=_source_id(source_type, location),
        type=source_type,
        label=str(meta.get("title") or slug),
        location=location,
        namespace=f"project:{slug}",
        indexing_status=status,
        embedding_status="none",
        document_count=doc_count,
        last_modified=modified or str(meta.get("updated") or ""),
        health=health,
        retrieval_available=root.is_dir() and doc_count > 0,
        metadata={"slug": slug, "git_path": git_path},
    )


def _discover_memory() -> KnowledgeSource:
    from jarvis.config import MEMORY_DB_FILE, MEMORY_FILE

    location = str(MEMORY_DB_FILE if MEMORY_DB_FILE.exists() else MEMORY_FILE)
    count = 0
    errors: list[str] = []
    embed = _embed_status()
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        if hasattr(mem, "list_entries"):
            count = len(mem.list_entries(limit=5000))
        elif hasattr(mem, "search"):
            count = len(mem.search("", limit=100))
    except Exception as exc:
        errors.append(str(exc)[:120])

    health = "healthy" if count else "offline"
    return KnowledgeSource(
        id=_source_id("conversation", location),
        type="conversation",
        label="Conversation Memory",
        location=location,
        namespace="aria",
        indexing_status="indexed" if count else "empty",
        embedding_status=embed if count else "none",
        document_count=count,
        last_modified=_mtime_iso(Path(location)) if Path(location).exists() else "",
        health=health,
        errors=errors,
        retrieval_available=count > 0,
        metadata={"backend": "memory"},
    )


def _discover_journal() -> KnowledgeSource:
    count, modified = _dir_stats(JOURNAL_DIR, extensions={".md", ".json", ".txt"})
    return KnowledgeSource(
        id=_source_id("notes", str(JOURNAL_DIR)),
        type="notes",
        label="Journal & Notes",
        location=str(JOURNAL_DIR),
        namespace="journal",
        indexing_status="indexed" if count else "empty",
        embedding_status="none",
        document_count=count,
        last_modified=modified,
        health="healthy" if JOURNAL_DIR.is_dir() else "offline",
        retrieval_available=count > 0,
    )


def _discover_learned_sources() -> list[KnowledgeSource]:
    sources: list[KnowledgeSource] = []
    try:
        from jarvis.document_learning import list_sources as learned_list

        for entry in learned_list(limit=100):
            loc = str(entry.get("path") or entry.get("url") or "")
            stype = str(entry.get("type") or "website")
            if stype in ("pdf",):
                ktype = "pdf"
            elif stype in ("docx",):
                ktype = "docx"
            elif entry.get("url"):
                ktype = "website"
            else:
                ktype = "markdown"
            sources.append(
                KnowledgeSource(
                    id=str(entry.get("id") or _source_id(ktype, loc)),
                    type=ktype,
                    label=str(entry.get("title") or loc)[:120],
                    location=loc,
                    namespace="aria:learned",
                    indexing_status="indexed",
                    embedding_status="ready" if entry.get("learned_at") else "partial",
                    document_count=1,
                    last_indexed=str(entry.get("ingested_at") or ""),
                    last_modified=str(entry.get("learned_at") or entry.get("ingested_at") or ""),
                    health="healthy",
                    retrieval_available=bool(loc),
                    metadata={"url": entry.get("url") or "", "lessons": entry.get("lessons") or 0},
                )
            )
    except Exception as exc:
        logger.debug("Learned sources scan: %s", exc)
    return sources


def _discover_datasets() -> KnowledgeSource | None:
    datasets_dir = DATA_DIR / "datasets"
    if not datasets_dir.is_dir():
        return None
    count, modified = _dir_stats(datasets_dir)
    return KnowledgeSource(
        id=_source_id("dataset", str(datasets_dir)),
        type="dataset",
        label="Datasets",
        location=str(datasets_dir),
        namespace="aria:datasets",
        indexing_status="indexed" if count else "empty",
        document_count=count,
        last_modified=modified,
        health="healthy" if count else "offline",
        retrieval_available=count > 0,
    )


def _discover_youtube() -> KnowledgeSource | None:
    yt_dir = DATA_DIR / "youtube"
    if not yt_dir.is_dir():
        return None
    count, modified = _dir_stats(yt_dir, extensions={".txt", ".md", ".json", ".vtt"})
    return KnowledgeSource(
        id=_source_id("youtube", str(yt_dir)),
        type="youtube",
        label="YouTube Transcripts",
        location=str(yt_dir),
        namespace="aria:youtube",
        indexing_status="indexed" if count else "empty",
        document_count=count,
        last_modified=modified,
        health="healthy" if count else "offline",
        retrieval_available=count > 0,
    )


def _discover_archives() -> KnowledgeSource | None:
    archive_dir = DATA_DIR / "archives"
    if not archive_dir.is_dir():
        return None
    count, modified = _dir_stats(archive_dir)
    return KnowledgeSource(
        id=_source_id("archive", str(archive_dir)),
        type="archive",
        label="Imported Archives",
        location=str(archive_dir),
        namespace="aria:archives",
        indexing_status="indexed" if count else "empty",
        document_count=count,
        last_modified=modified,
        health="healthy" if count else "offline",
        retrieval_available=False,
    )


def discover_all_sources() -> list[KnowledgeSource]:
    """Scan workstation and return all knowledge sources."""
    sources: list[KnowledgeSource] = [
        _discover_document_library(),
        _discover_code_index(),
        _discover_memory(),
        _discover_journal(),
    ]
    sources.extend(_discover_learned_sources())

    try:
        from jarvis.project_registry import list_projects

        for meta in list_projects():
            sources.append(_discover_project(meta))
    except Exception as exc:
        logger.debug("Project scan: %s", exc)

    for optional in (_discover_datasets(), _discover_youtube(), _discover_archives()):
        if optional is not None:
            sources.append(optional)

    docs_dir = PROJECT_ROOT / "docs"
    if docs_dir.is_dir():
        count, modified = _dir_stats(docs_dir, extensions={".md", ".markdown"})
        sources.append(
            KnowledgeSource(
                id=_source_id("documentation", str(docs_dir)),
                type="documentation",
                label="Project Documentation",
                location=str(docs_dir),
                namespace="aria:docs",
                indexing_status="indexed" if count else "empty",
                document_count=count,
                last_modified=modified,
                health="healthy",
                retrieval_available=count > 0,
            )
        )

    return sources


def sync_registry(*, persist: bool = True) -> dict[str, Any]:
    """Refresh knowledge registry from live workstation state."""
    now = _utc_now()
    discovered = discover_all_sources()
    data = _load_registry()
    merged: dict[str, dict[str, Any]] = dict(data.get("sources") or {})

    for src in discovered:
        existing = merged.get(src.id, {})
        payload = src.to_dict()
        payload["last_sync"] = now
        if src.health in ("healthy", "degraded") and src.indexing_status != "error":
            payload["last_successful_sync"] = now
        elif existing.get("last_successful_sync"):
            payload["last_successful_sync"] = existing["last_successful_sync"]
        merged[src.id] = payload

    data["sources"] = merged
    if persist:
        _save_registry(data)

    sources = [KnowledgeSource.from_dict(v) for v in merged.values()]
    healthy = sum(1 for s in sources if s.health == "healthy")
    retrieval = sum(1 for s in sources if s.retrieval_available)
    return {
        "ok": True,
        "synced_at": now,
        "source_count": len(sources),
        "healthy_count": healthy,
        "retrieval_count": retrieval,
        "sources": [s.to_dict() for s in sorted(sources, key=lambda s: s.label.lower())],
    }


def list_sources(*, refresh: bool = False) -> list[KnowledgeSource]:
    if refresh:
        sync_registry()
    data = _load_registry()
    sources = data.get("sources") or {}
    if not sources:
        return [KnowledgeSource.from_dict(s) for s in sync_registry().get("sources", [])]
    return [KnowledgeSource.from_dict(v) for v in sources.values()]


def get_source(source_id: str) -> KnowledgeSource | None:
    data = _load_registry()
    raw = (data.get("sources") or {}).get(source_id)
    return KnowledgeSource.from_dict(raw) if raw else None


def registry_snapshot(*, refresh: bool = False) -> dict[str, Any]:
    if refresh:
        return sync_registry()
    data = _load_registry()
    sources = [KnowledgeSource.from_dict(v) for v in (data.get("sources") or {}).values()]
    if not sources:
        return sync_registry()
    healthy = sum(1 for s in sources if s.health == "healthy")
    retrieval = sum(1 for s in sources if s.retrieval_available)
    stale = sum(1 for s in sources if s.indexing_status == "stale")
    errors = sum(1 for s in sources if s.health == "error")
    return {
        "ok": errors == 0,
        "updated_at": data.get("updated_at") or "",
        "source_count": len(sources),
        "healthy_count": healthy,
        "retrieval_count": retrieval,
        "stale_count": stale,
        "error_count": errors,
        "sources": [s.to_dict() for s in sorted(sources, key=lambda s: s.label.lower())],
    }


def format_registry_markdown(*, refresh: bool = False) -> str:
    snap = registry_snapshot(refresh=refresh)
    lines = [
        "## Knowledge Registry",
        f"**{snap.get('source_count', 0)} sources** · "
        f"{snap.get('retrieval_count', 0)} searchable · "
        f"{snap.get('healthy_count', 0)} healthy",
        "",
    ]
    for src in snap.get("sources") or []:
        mark = "●" if src.get("retrieval_available") else "○"
        status = src.get("indexing_status", "?")
        health = src.get("health", "?")
        count = src.get("document_count", 0)
        lines.append(
            f"{mark} **{src.get('label')}** (`{src.get('type')}`) — "
            f"{count} docs · {status} · {health}"
        )
        if src.get("last_indexed"):
            lines.append(f"  - indexed: {src['last_indexed']}")
        if src.get("errors"):
            lines.append(f"  - errors: {src['errors'][0]}")
    return "\n".join(lines)
