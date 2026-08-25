"""Semantic search over the document library (data/documents/)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path

from jarvis import llm
from jarvis.config import DATA_DIR
from jarvis.document_pipeline import DOCUMENT_EXTENSIONS, DOCUMENTS_DIR, parse_document
from jarvis.model_store import model_for

log = logging.getLogger("jarvis.documents_rag")

INDEX_FILE = DATA_DIR / "documents_index.json"
MAX_CHUNK = 1200
SIMILARITY_THRESHOLD = 0.22
# Parity with document_pipeline.DOCUMENT_EXTENSIONS
INDEX_EXTENSIONS = frozenset(DOCUMENT_EXTENSIONS)

# In-process index cache — avoid re-parsing 4MB JSON on every Search hit.
_INDEX_MEM: dict[str, object] = {"mtime": None, "chunks": None}


def _doc_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()


def _chunks(text: str, source: str, title: str) -> list[dict]:
    sha = _doc_sha(text)
    parts = []
    for i in range(0, len(text), MAX_CHUNK):
        chunk = text[i : i + MAX_CHUNK].strip()
        if chunk:
            parts.append({
                "source": source, "title": title, "text": chunk,
                # What this chunk was made from, so a later run can tell an
                # unchanged document from a changed one without re-embedding
                # it to find out.
                "doc_sha": sha,
                "embed_model": model_for("embed"),
            })
    return parts


def _latest_document_mtime() -> float:
    if not DOCUMENTS_DIR.is_dir():
        return 0.0
    latest = 0.0
    for path in DOCUMENTS_DIR.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in INDEX_EXTENSIONS:
            continue
        if ".cache" in path.parts:
            continue
        try:
            latest = max(latest, path.stat().st_mtime)
        except OSError:
            continue
    return latest


def _eligible_documents() -> set[str]:
    """Relative paths of every file the index is supposed to cover."""
    out: set[str] = set()
    if not DOCUMENTS_DIR.is_dir():
        return out
    for path in DOCUMENTS_DIR.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in INDEX_EXTENSIONS:
            continue
        if ".cache" in path.parts:
            continue
        try:
            out.add(str(path.relative_to(DOCUMENTS_DIR)))
        except ValueError:
            continue
    return out


def index_needs_rebuild() -> bool:
    if not INDEX_FILE.is_file():
        return True
    try:
        if _latest_document_mtime() > INDEX_FILE.stat().st_mtime:
            return True
    except OSError:
        return True
    # An mtime comparison only ever notices documents that were added or
    # edited. Deleting one leaves every surviving mtime untouched, so the
    # index went on serving documents that no longer exist -- which is exactly
    # how a withdrawn document stays retrievable. Compare membership too.
    cached = _read_index_file()
    if cached is None:
        return True
    indexed = {str(c.get("source") or "") for c in cached}
    indexed.discard("")
    return indexed != _eligible_documents()


def _read_index_file() -> list[dict] | None:
    if not INDEX_FILE.is_file():
        return None
    try:
        mtime = INDEX_FILE.stat().st_mtime
        cached = _INDEX_MEM.get("chunks")
        if cached is not None and _INDEX_MEM.get("mtime") == mtime:
            return list(cached)  # type: ignore[arg-type]
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            _INDEX_MEM["mtime"] = mtime
            _INDEX_MEM["chunks"] = data
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt documents index — rebuilding: %s", exc)
    return None


def _semantic_allowed() -> bool:
    """Cold-loading nomic-embed (~7–16s) exceeds the Search corpus wall.

    Only run semantic documents search when the embed runner is already
    resident (or explicitly forced). Otherwise keyword search is the owner path.
    """
    import os

    force = os.getenv("JARVIS_DOCS_FORCE_SEMANTIC", "").lower() in ("1", "true", "yes")
    if force:
        return True
    try:
        from jarvis.ollama_runtime import model_resident

        return model_resident(llm.model_for("embed"))
    except Exception:
        return False


def _search_impl(query: str, limit: int = 5) -> list[dict]:
    chunks = _load_index()
    if not chunks:
        return []
    keyword_hits = _keyword_search(query, chunks, limit)
    if not llm.embed_available() or not _semantic_allowed():
        return keyword_hits
    q_emb = llm.embed_text(query)
    if not q_emb:
        return keyword_hits
    scored = []
    for c in chunks:
        emb = c.get("embedding") or []
        if not emb:
            continue
        scored.append((llm.cosine_similarity(q_emb, emb), c))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [c for s, c in scored[:limit] if s > SIMILARITY_THRESHOLD]
    # Prefer semantic when it finds hits; otherwise keep keyword results.
    return hits or keyword_hits


def build_index(*, force: bool = False) -> list[dict]:
    from aiplatform.applications.knowledge_retrieval.bridge import CORPUS_DOCUMENT_LIBRARY
    from jarvis.modules.knowledge_retrieval_adapter import knowledge_index_build

    return knowledge_index_build(CORPUS_DOCUMENT_LIBRARY, _build_index_impl, force=force)


def _collect_documents() -> list[tuple[str, str, str]]:
    """(relative path, title, text) for every indexable document."""
    out: list[tuple[str, str, str]] = []
    if not DOCUMENTS_DIR.is_dir():
        return out
    for path in sorted(DOCUMENTS_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in INDEX_EXTENSIONS:
            continue
        if path.name.startswith(".") or ".cache" in path.parts:
            continue
        try:
            doc = parse_document(path)
            text = doc.full_text.strip()
            if not text:
                continue
            out.append((str(path.relative_to(DOCUMENTS_DIR)),
                        doc.title or path.stem, text))
        except Exception as exc:
            log.warning("Skip document index %s: %s", path, exc)
    return out


def _write_index(chunks: list[dict]) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(INDEX_FILE)
    tmp = INDEX_FILE.with_suffix(INDEX_FILE.suffix + ".tmp")
    tmp.write_text(json.dumps(chunks, indent=0), encoding="utf-8")
    os.replace(tmp, INDEX_FILE)
    _INDEX_MEM["mtime"] = None
    _INDEX_MEM["chunks"] = None


def _unembedded(chunks: list[dict]) -> list[dict]:
    """Chunks that carry no vector, and say so.

    An empty `embedding` is what semantic scoring skips, and `embed_pending`
    makes the reason explicit rather than leaving a caller to infer it from an
    empty list -- the difference between "indexed, matched nothing" and "never
    embedded".
    """
    out = []
    for c in chunks:
        c["embedding"] = []
        c["embed_pending"] = True
        out.append(c)
    return out


def _build_index_impl(*, force: bool = False) -> list[dict]:
    """Bring the index up to date, embedding only what actually changed.

    A full rebuild used to be the only option, and at ~20 s per chunk (every
    embedding paid a cold model load) that put a 1,000-chunk corpus at roughly
    six hours -- so in practice the index was never rebuilt, and withdrawn
    documents kept being served. Reusing the vectors of unchanged documents
    and embedding the rest inside one resident session turns that into a job
    measured in seconds.

    `force` re-reads every document but still reuses vectors whose document
    content and embedding model are unchanged; only a model change or an edit
    costs a new embedding.
    """
    existing = _read_index_file() or []
    if not force and existing and not index_needs_rebuild():
        return existing

    docs = _collect_documents()
    if not docs:
        _write_index([])
        return []

    model = model_for("embed")
    # Vectors worth keeping: same document content, same embedding model, and
    # an embedding that is actually there. A chunk stored with an empty vector
    # is an index entry that can never match, so it is treated as missing.
    reusable: dict[tuple[str, str, str], list[dict]] = {}
    for c in existing:
        if not c.get("embedding"):
            continue
        if str(c.get("embed_model") or "") != model:
            continue
        key = (str(c.get("source") or ""), str(c.get("doc_sha") or ""),
               str(c.get("text") or ""))
        reusable.setdefault(key, []).append(c)

    final: list[dict] = []
    needed: list[dict] = []
    for rel, title, text in docs:
        for chunk in _chunks(text, rel, title):
            key = (chunk["source"], chunk["doc_sha"], chunk["text"])
            hit = reusable.get(key)
            if hit:
                final.append(hit.pop())
                if not hit:
                    reusable.pop(key, None)
            else:
                needed.append(chunk)

    if not needed:
        log.info("Document index current: %d chunks, nothing to embed", len(final))
        _write_index(final)
        return final

    if not llm.embed_available():
        # No embedding model. The chunk text is still worth indexing --
        # _search_impl scores only chunks that actually carry a vector and
        # falls back to keyword search -- so dropping these would lose
        # keyword retrieval for no gain. Mark them so the state is truthful
        # and the next build retries them.
        log.warning(
            "Embedding model unavailable - %d chunk(s) indexed for keyword "
            "search only", len(needed),
        )
        final.extend(_unembedded(needed))
        _write_index(final)
        return final

    batch_size = max(1, int(os.getenv("JARVIS_EMBED_BATCH", "32")))
    embedded = failed = 0
    with llm.embed_session():
        for start in range(0, len(needed), batch_size):
            batch = needed[start : start + batch_size]
            try:
                vectors = llm.embed_batch([c["text"] for c in batch])
            except llm.EmbeddingError as exc:
                # Bounded: this batch is done being tried. The text is still
                # indexed for keyword search, flagged as carrying no vector so
                # nothing treats it as semantically searchable and the next
                # build picks it up again.
                failed += len(batch)
                log.error("Embedding batch failed (%s) - %d chunk(s) indexed "
                          "for keyword search only", exc, len(batch))
                final.extend(_unembedded(batch))
                _write_index(final)
                continue
            for chunk, vec in zip(batch, vectors):
                if not vec:
                    failed += 1
                    final.extend(_unembedded([chunk]))
                    continue
                chunk["embedding"] = vec
                chunk.pop("embed_pending", None)
                final.append(chunk)
                embedded += 1
            # Checkpoint after every batch so an interrupted run resumes from
            # here instead of starting the whole corpus again.
            _write_index(final)

    _write_index(final)
    log.info(
        "Document index updated: %d chunks (%d reused, %d embedded, %d failed)",
        len(final), len(final) - embedded, embedded, failed,
    )
    return final


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


def _hits_to_citations(hits: list[dict], *, why: str = "Matched library search") -> list[dict]:
    citations = []
    for i, h in enumerate(hits, 1):
        citations.append(
            {
                "id": f"doc-{i}",
                "title": h.get("title") or h.get("source") or "document",
                "source": h.get("source") or "",
                "excerpt": (h.get("text") or "")[:280].strip(),
                "why": why,
                "score": h.get("score"),
            }
        )
    return citations


def search_with_citations(
    query: str,
    *,
    limit: int = 8,
    project_scope: bool = False,
) -> dict:
    hits = search(query, limit=limit)
    if project_scope:
        try:
            from jarvis.active_project import coding_root_for_slug, get_active_slug

            slug = get_active_slug()
            root = coding_root_for_slug(slug) if slug else None
            if slug:
                filtered = []
                for h in hits:
                    src = (h.get("source") or "").lower()
                    title = (h.get("title") or "").lower()
                    if slug in src or slug in title:
                        filtered.append(h)
                    elif root and str(root).lower() in src:
                        filtered.append(h)
                if filtered:
                    hits = filtered
        except Exception:
            pass
    citations = _hits_to_citations(
        hits,
        why="Project-scoped match" if project_scope else "Library relevance match",
    )
    return {
        "query": query,
        "hits": hits,
        "citations": citations,
        "markdown": format_hits_markdown(query, hits, citations=citations),
    }


def context_for_query(query: str, limit: int = 4) -> tuple[str, list[str], list[dict]]:
    """Return (context, warnings, citations). Citations always accompany retrieval."""
    warnings: list[str] = []
    chunks = _load_index()
    if not chunks:
        warnings.append(
            "Document library is empty — upload files in Documents or drop into data/documents/."
        )
        return "", warnings, []
    if not llm.embed_available():
        warnings.append("Embed model offline — using keyword document search.")
    hits = search(query, limit=limit)
    if not hits:
        return "", warnings, []
    citations = _hits_to_citations(hits)
    lines = ["Document library (cite [doc-N] when used):"]
    for c in citations:
        hit = next((h for h in hits if (h.get("source") or "") == c["source"]), None)
        text = (hit or hits[0]).get("text") or c.get("excerpt") or ""
        lines.append(f"[{c['id']}] {c['title']} ({c['source']})\n{text[:800]}")
    return "\n\n".join(lines), warnings, citations


def format_hits_markdown(query: str, hits: list[dict], *, citations: list[dict] | None = None) -> str:
    if not hits:
        return f"No document library matches for **{query}**."
    cites = citations or _hits_to_citations(hits)
    lines = [f"**Document search:** _{query}_", "", "**Sources**"]
    for c in cites:
        excerpt = (c.get("excerpt") or "")[:400].strip()
        lines.append(f"- **[{c['id']}] {c.get('title')}** — {excerpt}…")
        if c.get("why"):
            lines.append(f"  - Why: {c['why']}")
        src = c.get("source") or ""
        if src:
            lines.append(f"  - Path: `{src}`")
    lines.append("")
    lines.append(
        "_Say **summarize** / **ask** with a path, or open Documents for Preview / Learn (candidates)._"
    )
    return "\n".join(lines)
