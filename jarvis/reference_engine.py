"""Reference Engine — local README, docs, ADRs, manuals, knowledge, web (last resort)."""

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
            Path(__file__).resolve().parents[1],
            Path(__file__).resolve().parents[1].parent / "AI-Platform",
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


def _local_reference_hits(query: str, *, limit: int = 8) -> list[dict[str, Any]]:
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
            candidates.extend(docs.rglob("*.pdf"))
            adr = docs / "adr"
            if adr.is_dir():
                candidates.extend(adr.rglob("*.md"))
        for path in candidates:
            try:
                if path.suffix.lower() == ".pdf":
                    text = path.name
                else:
                    text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lower = text.lower() if isinstance(text, str) else path.name.lower()
            score = sum(1 for t in terms if t in lower or t in path.name.lower())
            if score <= 0 and q not in path.name.lower():
                continue
            snippet = (text[:1200] if isinstance(text, str) else path.name).strip()
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


def search_reference(query: str, *, subject: str = "") -> dict[str, Any]:
    """Search reference sources; web is explicit fallback only."""
    q = (subject or query or "").strip()
    local = _local_reference_hits(q)

    try:
        from jarvis.knowledge.search import unified_search

        for hit in unified_search(q, limit=5):
            if hit.get("type") in ("documentation", "project_folder", "git_repository"):
                local.append(
                    {
                        "path": hit.get("path") or hit.get("id") or "",
                        "title": hit.get("title") or hit.get("id") or "reference",
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
        body = "\n\n".join(
            f"### {h.get('title')} (`{h.get('source')}`)\n{h.get('snippet', '')[:800]}"
            for h in local[:5]
        )
        return {
            "ok": True,
            "message": body,
            "hits": local,
            "source": "local",
            "module": "reference",
        }

    if os.getenv("JARVIS_REFERENCE_WEB_FALLBACK", "0").strip().lower() in ("1", "true", "yes"):
        from jarvis.web_search import search

        web = search(q, max_results=5)
        return {
            "ok": True,
            "message": web.get("summary") or "No local reference found; web results attached.",
            "hits": web.get("results") or [],
            "source": "web_fallback",
            "module": "reference",
        }

    return {
        "ok": True,
        "message": (
            f"No local reference found for **{q}**.\n\n"
            "Searched README, docs/, ADRs, manuals, knowledge collections, and document library.\n"
            "Say *search the web for …* if you need external documentation."
        ),
        "hits": [],
        "source": "none",
        "module": "reference",
    }


# Backward compatibility
search_documentation = search_reference
