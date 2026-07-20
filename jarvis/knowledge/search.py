"""Unified search across all knowledge sources."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from jarvis.knowledge.registry import KnowledgeSource, list_sources, sync_registry

logger = logging.getLogger("jarvis.knowledge.search")

_STRATEGY_HINTS = {
    "code": re.compile(r"\b(code|function|class|import|repo|git|python|typescript)\b", re.I),
    "document": re.compile(r"\b(pdf|docx|document|warranty|manual|paper)\b", re.I),
    "conversation": re.compile(r"\b(we discussed|remember when|conversation|said|told you)\b", re.I),
    "web": re.compile(r"\b(latest|news|current|today|web)\b", re.I),
}


def _score_hit(hit: dict[str, Any], *, strategy: str) -> float:
    base = float(hit.get("score") or hit.get("similarity") or 0.5)
    if strategy == "semantic":
        return base
    if strategy == "keyword":
        return min(0.95, 0.35 + base * 0.1)
    return base


def _search_documents(query: str, limit: int) -> list[dict[str, Any]]:
    from jarvis.documents_rag import search

    hits = search(query, limit=limit)
    out: list[dict[str, Any]] = []
    for h in hits:
        out.append({
            "source_type": "document_library",
            "source_label": "Document Library",
            "title": h.get("title") or h.get("source", "document"),
            "excerpt": (h.get("text") or "")[:400],
            "location": h.get("source", ""),
            "strategy": "semantic",
            "score": 0.85,
            "raw": h,
        })
    return out


def _search_git_repos(query: str, limit: int) -> list[dict[str, Any]]:
    try:
        from jarvis.knowledge.git_sync import list_repo_states
        from jarvis.knowledge.repo_index import index_path_for_repo, search_repo_index

        hits: list[dict[str, Any]] = []
        for st in list_repo_states():
            if not st.retrieval_available:
                continue
            index_path = index_path_for_repo(Path(st.path))
            for h in search_repo_index(index_path, query, limit=limit):
                hits.append({
                    "source_type": "git_repository",
                    "source_label": st.label,
                    "title": h.get("source", "code"),
                    "excerpt": (h.get("text") or "")[:400],
                    "location": f"{st.path}:{h.get('source', '')}",
                    "strategy": "semantic",
                    "score": 0.82,
                    "raw": {**h, "branch": st.branch, "head": st.head[:8]},
                })
        return sorted(hits, key=lambda x: x.get("score", 0), reverse=True)[:limit]
    except Exception as exc:
        logger.debug("Git repo search: %s", exc)
        return []


def _search_code(query: str, limit: int) -> list[dict[str, Any]]:
    git_hits = _search_git_repos(query, limit)
    if git_hits:
        return git_hits
    from jarvis.code_index import search

    hits = search(query, limit=limit)
    out: list[dict[str, Any]] = []
    for h in hits:
        out.append({
            "source_type": "code_index",
            "source_label": "Code Index",
            "title": h.get("source", "code"),
            "excerpt": (h.get("text") or "")[:400],
            "location": h.get("source", ""),
            "strategy": "semantic",
            "score": float(h.get("score") or 0.8),
            "raw": h,
        })
    return out


def _search_memory(query: str, limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        try:
            from aria_core import acm_bridge

            if acm_bridge.acm_is_authoritative():
                hits = acm_bridge.primary_search(query, limit=limit)
                for h in hits:
                    content = h.get("content") or h.get("text") or str(h)
                    out.append({
                        "source_type": "conversation",
                        "source_label": "ACM Cognition",
                        "title": (h.get("id") or "acm")[:40],
                        "excerpt": content[:400],
                        "location": h.get("namespace") or "acm",
                        "strategy": "acm_authority",
                        "score": float(h.get("score") or 0.7),
                        "raw": h,
                    })
                return out
        except Exception:
            pass
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        if not hasattr(mem, "search"):
            return out
        hits = mem.search(query, limit=limit)
        for h in hits:
            content = h.get("content") or h.get("text") or str(h)
            out.append({
                "source_type": "conversation",
                "source_label": "Conversation Memory",
                "title": (h.get("id") or "memory")[:40],
                "excerpt": content[:400],
                "location": h.get("namespace") or "memory",
                "strategy": "semantic",
                "score": float(h.get("score") or 0.7),
                "raw": h,
            })
    except Exception as exc:
        logger.debug("Memory search: %s", exc)
    return out


def _search_journal(query: str, limit: int) -> list[dict[str, Any]]:
    from jarvis.config import JOURNAL_DIR

    terms = [t.lower() for t in re.findall(r"\w{3,}", query.lower())]
    if not terms or not JOURNAL_DIR.is_dir():
        return []
    scored: list[tuple[int, Path, str]] = []
    for path in JOURNAL_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in (".md", ".txt", ".json"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lower = text.lower()
        score = sum(lower.count(t) for t in terms)
        if score:
            scored.append((score, path, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for score, path, text in scored[:limit]:
        out.append({
            "source_type": "notes",
            "source_label": "Journal & Notes",
            "title": path.name,
            "excerpt": text[:400],
            "location": str(path),
            "strategy": "keyword",
            "score": _score_hit({"score": score}, strategy="keyword"),
            "raw": {"path": str(path)},
        })
    return out


def _search_project_docs(query: str, limit: int) -> list[dict[str, Any]]:
    terms = [t.lower() for t in re.findall(r"\w{3,}", query.lower())]
    if not terms:
        return []
    out: list[dict[str, Any]] = []
    try:
        from jarvis.project_registry import list_projects

        for meta in list_projects():
            root = Path((meta.get("paths") or {}).get("root") or "")
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if path.suffix.lower() not in (".md", ".markdown", ".txt", ".pdf", ".docx"):
                    continue
                if not path.is_file():
                    continue
                from jarvis.knowledge.doc_guards import is_developer_doc_request, is_internal_doc

                if is_internal_doc(str(path)) and not is_developer_doc_request(query):
                    continue
                try:
                    if path.suffix.lower() in (".pdf", ".docx"):
                        continue
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                lower = text.lower()
                score = sum(lower.count(t) for t in terms)
                if not score:
                    continue
                out.append({
                    "source_type": "project_folder",
                    "source_label": str(meta.get("title") or meta.get("slug")),
                    "title": str(path.relative_to(root)),
                    "excerpt": text[:400],
                    "location": str(path),
                    "strategy": "keyword",
                    "score": _score_hit({"score": score}, strategy="keyword"),
                    "raw": {"project": meta.get("slug")},
                })
    except Exception as exc:
        logger.debug("Project doc search: %s", exc)
    return sorted(out, key=lambda h: h.get("score", 0), reverse=True)[:limit]


def _search_learned(query: str, limit: int) -> list[dict[str, Any]]:
    terms = [t.lower() for t in re.findall(r"\w{3,}", query.lower())]
    if not terms:
        return []
    out: list[dict[str, Any]] = []
    try:
        from jarvis.document_learning import list_sources as learned_list

        for entry in learned_list(limit=100):
            title = str(entry.get("title") or "")
            blob = f"{title} {entry.get('path') or ''} {entry.get('url') or ''}".lower()
            score = sum(blob.count(t) for t in terms)
            if not score:
                continue
            out.append({
                "source_type": str(entry.get("type") or "website"),
                "source_label": "Learned Sources",
                "title": title[:120],
                "excerpt": title,
                "location": str(entry.get("path") or entry.get("url") or ""),
                "strategy": "keyword",
                "score": _score_hit({"score": score}, strategy="keyword"),
                "raw": entry,
            })
    except Exception as exc:
        logger.debug("Learned search: %s", exc)
    return sorted(out, key=lambda h: h.get("score", 0), reverse=True)[:limit]


def _pick_strategies(query: str, sources: list[KnowledgeSource]) -> list[str]:
    strategies: list[str] = []
    if any(s.retrieval_available and s.type == "code_index" for s in sources):
        if _STRATEGY_HINTS["code"].search(query):
            strategies.append("code")
    if any(s.retrieval_available and s.type == "document_library" for s in sources):
        if _STRATEGY_HINTS["document"].search(query) or "code" not in strategies:
            strategies.append("documents")
    if any(s.retrieval_available and s.type == "conversation" for s in sources):
        if _STRATEGY_HINTS["conversation"].search(query):
            strategies.append("memory")
    if any(s.retrieval_available and s.type in ("notes", "journal") for s in sources):
        strategies.append("journal")
    if any(s.type in ("project_folder", "git_repository", "documentation") for s in sources):
        strategies.append("projects")
    if any(s.type in ("website", "pdf", "docx", "markdown") for s in sources):
        strategies.append("learned")

    if not strategies:
        strategies = ["documents", "code", "memory", "journal", "projects", "learned"]
    return strategies


def unified_search(
    query: str,
    *,
    limit: int = 12,
    refresh_registry: bool = False,
) -> dict[str, Any]:
    """Search all knowledge sources; Aria picks strategies automatically."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "query required", "hits": []}

    if refresh_registry:
        sync_registry()

    sources = list_sources()
    strategies = _pick_strategies(query, sources)
    per_strategy = max(3, limit // max(1, len(strategies)))

    all_hits: list[dict[str, Any]] = []
    searched: list[str] = []

    for strategy in strategies:
        try:
            if strategy == "documents":
                hits = _search_documents(query, per_strategy)
            elif strategy == "code":
                hits = _search_code(query, per_strategy)
            elif strategy == "memory":
                hits = _search_memory(query, per_strategy)
            elif strategy == "journal":
                hits = _search_journal(query, per_strategy)
            elif strategy == "projects":
                hits = _search_project_docs(query, per_strategy)
            elif strategy == "learned":
                hits = _search_learned(query, per_strategy)
            else:
                hits = []
            if hits:
                searched.append(strategy)
            all_hits.extend(hits)
        except Exception as exc:
            logger.warning("Unified search strategy %s failed: %s", strategy, exc)

    all_hits.sort(key=lambda h: float(h.get("score") or 0), reverse=True)
    hits = all_hits[:limit]

    return {
        "ok": True,
        "query": query,
        "strategies": strategies,
        "searched": searched,
        "hit_count": len(hits),
        "hits": hits,
        "sources_available": sum(1 for s in sources if s.retrieval_available),
    }


def format_unified_results(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Search failed: {result.get('error', 'unknown error')}"
    query = result.get("query", "")
    hits = result.get("hits") or []
    if not hits:
        return f"No matches for **{query}** across workstation knowledge."
    lines = [
        f"**Unified search:** _{query}_",
        f"_{len(hits)} result(s) from {', '.join(result.get('searched') or result.get('strategies') or [])}_",
        "",
    ]
    for hit in hits:
        label = hit.get("source_label") or hit.get("source_type")
        title = hit.get("title") or "untitled"
        excerpt = (hit.get("excerpt") or "").strip().replace("\n", " ")[:280]
        lines.append(f"- **[{label}]** {title} — {excerpt}")
    return "\n".join(lines)
