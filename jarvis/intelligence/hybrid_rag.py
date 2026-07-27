"""Production-grade hybrid RAG: keyword + vector + simple rerank + citations."""

from __future__ import annotations

import logging
import math
import re
import json
from typing import Any

log = logging.getLogger("jarvis.intelligence.hybrid_rag")


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-z0-9]{3,}", (text or "").lower())}


def _keyword_score(query: str, text: str, title: str = "") -> float:
    q = _tokenize(query)
    if not q:
        return 0.0
    body = (text or "").lower()
    head = (title or "").lower()
    score = 0.0
    for t in q:
        score += body.count(t) * 1.0
        score += head.count(t) * 2.5
    # BM25-ish length normalization
    length = max(1, len(body) / 500)
    return score / math.sqrt(length)


def expand_query(query: str) -> list[str]:
    """Lightweight query expansion (synonym-ish variants without network)."""
    q = (query or "").strip()
    if not q:
        return []
    variants = [q]
    lower = q.lower()
    replacements = (
        ("how do i", "how to"),
        ("what's", "what is"),
        ("summarize", "summary overview"),
        ("how to fix", "how to repair"),
        ("find", "search locate"),
    )
    for a, b in replacements:
        if a in lower:
            variants.append(re.sub(re.escape(a), b, q, flags=re.I))
    # Deduplicate preserving order
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        key = v.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(v.strip())
    return out[:4]


def _read_json_chunks(path, *, limit: int) -> list[dict]:
    try:
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return data[:limit]
    except Exception:
        return []


def _collect_chunks(limit_per_source: int = 40) -> list[dict[str, Any]]:
    """Load existing indexes only — never rebuild/embed during search."""
    chunks: list[dict[str, Any]] = []
    try:
        from jarvis import documents_rag

        for c in _read_json_chunks(documents_rag.INDEX_FILE, limit=limit_per_source):
            chunks.append(
                {
                    "corpus": "documents",
                    "source": c.get("source") or "",
                    "title": c.get("title") or c.get("source") or "document",
                    "text": c.get("text") or "",
                    "embedding": c.get("embedding") or [],
                }
            )
    except Exception as exc:
        log.debug("documents corpus unavailable: %s", exc)

    try:
        from jarvis import rag

        for c in _read_json_chunks(rag.RAG_INDEX, limit=limit_per_source):
            chunks.append(
                {
                    "corpus": "project",
                    "source": c.get("source") or "",
                    "title": c.get("source") or "project",
                    "text": c.get("text") or "",
                    "embedding": c.get("embedding") or [],
                }
            )
    except Exception as exc:
        log.debug("project corpus unavailable: %s", exc)

    return chunks


def _vector_score(query_emb: list[float], emb: list[float]) -> float:
    if not query_emb or not emb:
        return 0.0
    try:
        from jarvis import llm

        return float(llm.cosine_similarity(query_emb, emb))
    except Exception:
        return 0.0


def rerank(candidates: list[dict[str, Any]], query: str, *, top_k: int = 8) -> list[dict[str, Any]]:
    """Simple cross-feature reranker (keyword + vector + title overlap)."""
    for c in candidates:
        kw = float(c.get("keyword_score") or 0.0)
        vec = float(c.get("vector_score") or 0.0)
        title = (c.get("title") or "").lower()
        title_boost = 0.15 if any(t in title for t in list(_tokenize(query))[:6]) else 0.0
        c["rerank_score"] = (0.45 * vec) + (0.45 * min(1.0, kw / 8.0)) + title_boost
    candidates.sort(key=lambda x: float(x.get("rerank_score") or 0), reverse=True)
    return candidates[:top_k]


def _citation(hit: dict[str, Any], idx: int) -> dict[str, Any]:
    score = float(hit.get("rerank_score") or hit.get("vector_score") or hit.get("keyword_score") or 0)
    confidence = max(0.0, min(1.0, score if score <= 1 else score / 10.0))
    return {
        "id": f"cite-{idx}",
        "corpus": hit.get("corpus"),
        "source": hit.get("source"),
        "title": hit.get("title"),
        "excerpt": (hit.get("text") or "")[:320],
        "score": round(float(hit.get("rerank_score") or 0), 4),
        "confidence": round(confidence, 3),
    }


def hybrid_search(
    query: str,
    *,
    limit: int = 6,
    corpora: list[str] | None = None,
) -> dict[str, Any]:
    """Hybrid keyword + vector search with expansion, rerank, and citations."""
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "empty_query", "hits": [], "citations": [], "expanded": []}

    expanded = expand_query(q)
    chunks = _collect_chunks()
    if corpora:
        allowed = set(corpora)
        chunks = [c for c in chunks if c.get("corpus") in allowed]

    if not chunks:
        return {
            "ok": True,
            "hits": [],
            "citations": [],
            "expanded": expanded,
            "warnings": ["No indexed corpora available — reindex documents or project RAG."],
            "mode": "empty",
        }

    query_emb: list[float] = []
    mode = "keyword"
    try:
        from jarvis import llm
        import os

        # Avoid blocking on remote embed during unit tests / offline
        if os.getenv("JARVIS_HYBRID_RAG_EMBED", "1").strip().lower() not in ("0", "false", "no"):
            if getattr(llm, "embed_available", lambda: False)():
                query_emb = llm.embed_text(q) or []
                if query_emb:
                    mode = "hybrid"
    except Exception as exc:
        log.debug("embed unavailable: %s", exc)

    scored: list[dict[str, Any]] = []
    for c in chunks:
        best_kw = max(_keyword_score(v, c["text"], c.get("title") or "") for v in expanded)
        vec = _vector_score(query_emb, c.get("embedding") or []) if query_emb else 0.0
        if best_kw <= 0 and vec <= 0.15:
            continue
        item = dict(c)
        item["keyword_score"] = best_kw
        item["vector_score"] = vec
        scored.append(item)

    ranked = rerank(scored, q, top_k=max(limit, 8))
    hits = ranked[:limit]
    citations = [_citation(h, i + 1) for i, h in enumerate(hits)]
    return {
        "ok": True,
        "query": q,
        "expanded": expanded,
        "mode": mode,
        "hits": [
            {
                "corpus": h.get("corpus"),
                "source": h.get("source"),
                "title": h.get("title"),
                "text": h.get("text"),
                "keyword_score": round(float(h.get("keyword_score") or 0), 4),
                "vector_score": round(float(h.get("vector_score") or 0), 4),
                "rerank_score": round(float(h.get("rerank_score") or 0), 4),
            }
            for h in hits
        ],
        "citations": citations,
        "warnings": [] if mode == "hybrid" else ["Embeddings offline — keyword/hybrid-degraded mode."],
    }


def format_cited_context(result: dict[str, Any], *, max_chars: int = 6000) -> str:
    """Build a prompt context block with citation markers."""
    hits = result.get("hits") or []
    if not hits:
        return ""
    parts: list[str] = ["Retrieved context (cite sources by [cite-N]):"]
    used = 0
    for i, h in enumerate(hits, start=1):
        block = f"[cite-{i}] ({h.get('title') or h.get('source')})\n{(h.get('text') or '')[:900]}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)
