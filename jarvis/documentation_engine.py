"""Documentation engine — local project docs first, web search last resort."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR


def _search_roots() -> list[Path]:
    roots: list[Path] = []
    for env in ("AI_ROOT", "JARVIS_ROOT", "AI_PLATFORM_ROOT"):
        val = (os.getenv(env) or "").strip()
        if val:
            roots.append(Path(val))
    roots.extend(
        [
            Path(__file__).resolve().parents[2],
            Path(__file__).resolve().parents[2].parent / "AI-Platform",
            DATA_DIR,
        ]
    )
    seen: set[str] = set()
    out: list[Path] = []
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def _local_doc_hits(query: str, *, limit: int = 8) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return []
    terms = [t for t in q.split() if len(t) > 2]
    hits: list[dict[str, Any]] = []

    for root in _search_roots():
        if not root.is_dir():
            continue
        candidates: list[Path] = []
        for name in ("README.md", "readme.md"):
            p = root / name
            if p.is_file():
                candidates.append(p)
        docs = root / "docs"
        if docs.is_dir():
            candidates.extend(docs.rglob("*.md"))
            candidates.extend(docs.rglob("*.rst"))
            adr = docs / "adr"
            if adr.is_dir():
                candidates.extend(adr.rglob("*.md"))
        for path in candidates:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lower = text.lower()
            score = sum(1 for t in terms if t in lower or t in path.name.lower())
            if score <= 0 and q not in path.name.lower():
                continue
            snippet = text[:1200].strip()
            hits.append(
                {
                    "path": str(path),
                    "title": path.name,
                    "score": score,
                    "snippet": snippet,
                    "source": "local",
                }
            )
    hits.sort(key=lambda h: (-h["score"], h["path"]))
    return hits[:limit]


def search_documentation(query: str, *, subject: str = "") -> dict[str, Any]:
    """Search local documentation; web search is explicit fallback only."""
    q = (subject or query or "").strip()
    local = _local_doc_hits(q)

    try:
        from jarvis.knowledge.search import unified_search

        registry_hits = unified_search(q, limit=5)
        for hit in registry_hits:
            if hit.get("type") in ("documentation", "project_folder", "git_repository"):
                local.append(
                    {
                        "path": hit.get("path") or hit.get("id") or "",
                        "title": hit.get("title") or hit.get("id") or "doc",
                        "score": hit.get("score") or 1,
                        "snippet": (hit.get("snippet") or hit.get("text") or "")[:1200],
                        "source": "knowledge_registry",
                    }
                )
    except Exception:
        pass

    try:
        from jarvis.documents_rag import search as doc_rag_search

        for hit in doc_rag_search(q, limit=4):
            local.append(
                {
                    "path": hit.get("path", ""),
                    "title": hit.get("title") or hit.get("path", "document"),
                    "score": hit.get("score", 1),
                    "snippet": (hit.get("text") or hit.get("snippet") or "")[:1200],
                    "source": "document_library",
                }
            )
    except Exception:
        pass

    local.sort(key=lambda h: (-int(h.get("score") or 0), str(h.get("path"))))
    local = local[:10]

    if local:
        lines = [f"### {h.get('title')} (`{h.get('source')}`)" for h in local[:5]]
        body = "\n\n".join(
            f"{title}\n{h.get('snippet', '')[:800]}"
            for title, h in zip(lines, local[:5], strict=False)
        )
        return {
            "ok": True,
            "message": body,
            "hits": local,
            "source": "local",
            "module": "documentation",
        }

    if os.getenv("JARVIS_DOCS_WEB_FALLBACK", "0").strip().lower() in ("1", "true", "yes"):
        from jarvis.web_search import search

        web = search(q, max_results=5)
        return {
            "ok": True,
            "message": web.get("summary") or "No local documentation found; web results attached.",
            "hits": web.get("results") or [],
            "source": "web_fallback",
            "module": "documentation",
        }

    return {
        "ok": True,
        "message": (
            f"No local documentation found for **{q}**.\n\n"
            "Searched README, docs/, ADRs, knowledge collections, and document library.\n"
            "Say *search the web for …* if you need external documentation."
        ),
        "hits": [],
        "source": "none",
        "module": "documentation",
    }
