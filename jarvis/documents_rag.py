"""Semantic search over the document library (data/documents/)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from jarvis import llm
from jarvis.config import DATA_DIR
from jarvis.document_pipeline import DOCUMENTS_DIR, parse_document

log = logging.getLogger("jarvis.documents_rag")

INDEX_FILE = DATA_DIR / "documents_index.json"
MAX_CHUNK = 1200
SIMILARITY_THRESHOLD = 0.22


def _chunks(text: str, source: str, title: str) -> list[dict]:
    parts = []
    for i in range(0, len(text), MAX_CHUNK):
        chunk = text[i : i + MAX_CHUNK].strip()
        if chunk:
            parts.append({"source": source, "title": title, "text": chunk})
    return parts


def _latest_document_mtime() -> float:
    if not DOCUMENTS_DIR.is_dir():
        return 0.0
    latest = 0.0
    for path in DOCUMENTS_DIR.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in (".pdf", ".docx"):
            continue
        try:
            latest = max(latest, path.stat().st_mtime)
        except OSError:
            continue
    return latest


def index_needs_rebuild() -> bool:
    if not INDEX_FILE.is_file():
        return True
    try:
        return _latest_document_mtime() > INDEX_FILE.stat().st_mtime
    except OSError:
        return True


def _read_index_file() -> list[dict] | None:
    if not INDEX_FILE.is_file():
        return None
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt documents index — rebuilding: %s", exc)
    return None


def build_index(*, force: bool = False) -> list[dict]:
    from aiplatform.applications.knowledge_retrieval.bridge import CORPUS_DOCUMENT_LIBRARY
    from jarvis.modules.knowledge_retrieval_adapter import knowledge_index_build

    return knowledge_index_build(CORPUS_DOCUMENT_LIBRARY, _build_index_impl, force=force)


def _build_index_impl(*, force: bool = False) -> list[dict]:
    if not force:
        existing = _read_index_file()
        if existing is not None and not index_needs_rebuild():
            return existing
    chunks: list[dict] = []
    if not DOCUMENTS_DIR.is_dir():
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text("[]", encoding="utf-8")
        return []
    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".pdf", ".docx"):
            continue
        if path.name.startswith("."):
            continue
        try:
            doc = parse_document(path)
            text = doc.full_text.strip()
            if not text:
                continue
            rel = str(path.relative_to(DOCUMENTS_DIR))
            chunks.extend(_chunks(text, rel, doc.title or path.stem))
        except Exception as exc:
            log.warning("Skip document index %s: %s", path, exc)
    embed_ok = llm.embed_available()
    for c in chunks:
        c["embedding"] = llm.embed_text(c["text"]) if embed_ok else []
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(INDEX_FILE)
    INDEX_FILE.write_text(json.dumps(chunks, indent=0), encoding="utf-8")
    log.info("Document index built: %d chunks", len(chunks))
    return chunks


def _load_index(*, auto_refresh: bool = True) -> list[dict]:
    if auto_refresh and index_needs_rebuild():
        return build_index(force=True)
    data = _read_index_file()
    if data is not None:
        return data
    return build_index(force=True)


def _keyword_search(query: str, chunks: list[dict], limit: int) -> list[dict]:
    terms = [t.lower() for t in re.findall(r"\w{3,}", query.lower())]
    if not terms:
        return []
    scored: list[tuple[int, dict]] = []
    for c in chunks:
        text = (c.get("text") or "").lower()
        title = (c.get("title") or c.get("source") or "").lower()
        score = sum(text.count(t) * 2 + title.count(t) * 3 for t in terms)
        if score:
            scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]


def search(query: str, limit: int = 5) -> list[dict]:
    from aiplatform.applications.knowledge_retrieval.bridge import CORPUS_DOCUMENT_LIBRARY
    from jarvis.modules.knowledge_retrieval_adapter import knowledge_search

    return knowledge_search(CORPUS_DOCUMENT_LIBRARY, _search_impl, query, limit=limit)


def _search_impl(query: str, limit: int = 5) -> list[dict]:
    chunks = _load_index()
    if not chunks:
        return []
    if llm.embed_available():
        q_emb = llm.embed_text(query)
        if q_emb:
            scored = []
            for c in chunks:
                emb = c.get("embedding") or []
                if not emb:
                    continue
                scored.append((llm.cosine_similarity(q_emb, emb), c))
            scored.sort(key=lambda x: x[0], reverse=True)
            hits = [c for s, c in scored[:limit] if s > SIMILARITY_THRESHOLD]
            if hits:
                return hits
    return _keyword_search(query, chunks, limit)


def context_for_query(query: str, limit: int = 4) -> tuple[str, list[str]]:
    warnings: list[str] = []
    chunks = _load_index()
    if not chunks:
        warnings.append("Document library is empty — add PDFs/DOCX under data/documents/.")
        return "", warnings
    if not llm.embed_available():
        warnings.append("Embed model offline — using keyword document search.")
    hits = search(query, limit=limit)
    if not hits:
        return "", warnings
    ctx = "Document library:\n" + "\n---\n".join(
        f"[{h.get('title') or h['source']}]\n{h['text']}" for h in hits
    )
    return ctx, warnings


def format_hits_markdown(query: str, hits: list[dict]) -> str:
    if not hits:
        return f"No document library matches for **{query}**."
    lines = [f"**Document search:** _{query}_", ""]
    for h in hits:
        title = h.get("title") or h.get("source", "document")
        excerpt = (h.get("text") or "")[:400].strip()
        lines.append(f"- **{title}** — {excerpt}…")
    lines.append("")
    lines.append("_Attach a file or say **summarize** with a path for full Q&A._")
    return "\n".join(lines)
