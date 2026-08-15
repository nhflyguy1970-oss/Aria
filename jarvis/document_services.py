"""Documents & RAG product services — Home, upload, citations, candidates, project pack.

Documents = personal document intelligence (local). Not Drive/SharePoint/Notion.
Learn stages Memory candidates only — never silent ACM autobiography.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.document_pipeline import DOCUMENT_EXTENSIONS, DOCUMENTS_DIR, documents_dir, parse_document

log = logging.getLogger("jarvis.document_services")

IMPORTS_FILE = DATA_DIR / "document_imports.json"
RECENT_SEARCHES_FILE = DATA_DIR / "document_recent_searches.json"
INDEX_JOB_FILE = DATA_DIR / "document_index_job.json"

SMART_TYPES = (
    "manual",
    "receipt",
    "invoice",
    "warranty",
    "specification",
    "reference",
    "book",
    "research",
    "project_document",
    "other",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clip(text: str, n: int = 160) -> str:
    t = (text or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def _load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(path)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def index_health() -> dict[str, Any]:
    from jarvis.documents_rag import INDEX_FILE, index_needs_rebuild, _read_index_file
    from jarvis.documents_rag import llm as doc_llm

    chunks = _read_index_file() or []
    with_emb = sum(1 for c in chunks if c.get("embedding"))
    docs = {c.get("source") for c in chunks if c.get("source")}
    job = _load_json(INDEX_JOB_FILE, {})
    embed_ok = False
    embed_model = ""
    try:
        embed_ok = bool(doc_llm.embed_available())
    except Exception:
        embed_ok = False
    try:
        if embed_ok and hasattr(doc_llm, "embed_model"):
            embed_model = str(doc_llm.embed_model() or "")
    except Exception:
        embed_model = ""
    return {
        "ok": True,
        "index_file": str(INDEX_FILE),
        "exists": INDEX_FILE.is_file(),
        "chunk_count": len(chunks),
        "document_count": len(docs),
        "embedded_chunks": with_emb,
        "embedding_coverage": round(with_emb / len(chunks), 3) if chunks else 0.0,
        "embed_available": embed_ok,
        "embed_model": embed_model,
        "needs_rebuild": index_needs_rebuild(),
        "last_indexed": datetime.fromtimestamp(INDEX_FILE.stat().st_mtime, tz=timezone.utc).isoformat()
        if INDEX_FILE.is_file()
        else "",
        "mode": "hybrid (keyword + vector)" if with_emb else "keyword fallback",
        "job": job,
    }


def note_recent_search(query: str) -> None:
    q = (query or "").strip()
    if not q:
        return
    data = _load_json(RECENT_SEARCHES_FILE, {"searches": []})
    searches = [s for s in (data.get("searches") or []) if isinstance(s, dict)]
    searches = [s for s in searches if (s.get("q") or "").lower() != q.lower()]
    searches.insert(0, {"q": q, "at": _now()})
    _save_json(RECENT_SEARCHES_FILE, {"searches": searches[:20]})


def recent_searches(limit: int = 8) -> list[dict[str, str]]:
    data = _load_json(RECENT_SEARCHES_FILE, {"searches": []})
    return list(data.get("searches") or [])[:limit]


def recent_imports(limit: int = 12) -> list[dict[str, Any]]:
    data = _load_json(IMPORTS_FILE, {"imports": []})
    return list(data.get("imports") or [])[:limit]


def _record_import(entry: dict[str, Any]) -> None:
    data = _load_json(IMPORTS_FILE, {"imports": []})
    imports = list(data.get("imports") or [])
    imports.insert(0, entry)
    _save_json(IMPORTS_FILE, {"imports": imports[:100]})


def classify_document(title: str, text: str = "") -> dict[str, Any]:
    """Smart import suggestion — never auto-creates memories."""
    blob = f"{title}\n{text[:2000]}".lower()
    scores: dict[str, int] = {t: 0 for t in SMART_TYPES}
    rules = {
        "warranty": ("warranty", "coverage", "guaranteed", "defect"),
        "receipt": ("receipt", "paid", "transaction", "card ending"),
        "invoice": ("invoice", "amount due", "bill to", "remit"),
        "manual": ("manual", "instructions", "how to", "user guide", "operating"),
        "specification": ("specification", "spec sheet", "datasheet", "tolerance"),
        "research": ("abstract", "doi:", "references", "hypothesis"),
        "book": ("chapter", "isbn", "table of contents"),
        "project_document": ("readme", "architecture", "api design", "changelog"),
    }
    for kind, keys in rules.items():
        for k in keys:
            if k in blob:
                scores[kind] += 2
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "reference"
    return {
        "suggested_type": best,
        "index": True,
        "stage_candidates": best in ("warranty", "manual", "specification", "project_document", "research"),
        "message": "Index only — Memory candidates require explicit Learn (never automatic).",
    }


def save_upload(
    filename: str,
    content: bytes,
    *,
    subdir: str = "uploads",
    reindex: bool = True,
) -> dict[str, Any]:
    documents_dir()
    safe = Path(filename or "upload.bin").name
    if Path(safe).suffix.lower() not in DOCUMENT_EXTENSIONS:
        return {"ok": False, "message": f"Unsupported type: {safe}"}
    dest_dir = DOCUMENTS_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe
    if dest.exists():
        stem, suf = dest.stem, dest.suffix
        n = 2
        while (dest_dir / f"{stem}-{n}{suf}").exists():
            n += 1
        dest = dest_dir / f"{stem}-{n}{suf}"
    dest.write_bytes(content)
    suggestion = classify_document(dest.name)
    _record_import(
        {
            "path": str(dest),
            "name": dest.name,
            "at": _now(),
            "bytes": len(content),
            "source": "upload",
            "suggested_type": suggestion["suggested_type"],
        }
    )
    chunk_count = 0
    if reindex:
        from jarvis.documents_rag import build_index

        try:
            chunks = build_index(force=True)
            chunk_count = len(chunks)
        except Exception as exc:
            chunk_count = 0
            log.warning("reindex after upload: %s", exc)
    return {
        "ok": True,
        "path": str(dest),
        "name": dest.name,
        "chunks": chunk_count,
        "suggestion": suggestion,
        "message": f"Imported **{dest.name}** into the document library.",
    }


def import_folder(folder: str, *, reindex: bool = True) -> dict[str, Any]:
    root = Path(folder or "").expanduser().resolve()
    if not root.is_dir():
        return {"ok": False, "message": f"Not a folder: {folder}"}
    # Hard caps — unrestricted rglob of Downloads/Desktop wedged the whole serve process.
    # Walk with depth limit; never materialize the full tree first.
    # Do NOT reindex per file — that rebuilt the full RAG index N times under the chat lock.
    max_files = 40
    max_depth = 4
    max_scan = 2500
    max_bytes = 8_000_000
    imported: list[dict[str, Any]] = []
    errors: list[str] = []
    scanned = 0
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            rel = Path(dirpath).relative_to(root)
            depth = 0 if str(rel) == "." else len(rel.parts)
            if depth >= max_depth:
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in sorted(filenames):
                scanned += 1
                if scanned > max_scan or len(imported) >= max_files:
                    break
                if name.startswith("."):
                    continue
                path = Path(dirpath) / name
                if path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                    continue
                try:
                    if path.stat().st_size > max_bytes:
                        errors.append(f"{path.name}: skipped (>{max_bytes} bytes)")
                        continue
                    data = path.read_bytes()
                    result = save_upload(path.name, data, subdir="imports", reindex=False)
                    if result.get("ok"):
                        imported.append({"name": result["name"], "path": result["path"]})
                    else:
                        errors.append(result.get("message") or path.name)
                except Exception as exc:
                    errors.append(f"{path.name}: {exc}")
            if scanned > max_scan or len(imported) >= max_files:
                break
    except Exception as exc:
        return {"ok": False, "message": f"Could not scan folder: {exc}"}

    chunk_count = 0
    if imported and reindex:
        from jarvis.documents_rag import build_index

        try:
            chunks = build_index(force=True)
            chunk_count = len(chunks)
        except Exception as exc:
            log.warning("reindex after folder import: %s", exc)
            errors.append(f"reindex: {exc}")
    elif imported and not reindex:
        # Schedule a single background rebuild so chat never holds the request lock on RAG.
        import threading

        def _bg_reindex() -> None:
            try:
                from jarvis.documents_rag import build_index

                build_index(force=True)
            except Exception as exc:
                log.warning("background reindex after folder import: %s", exc)

        threading.Thread(target=_bg_reindex, name="doc-import-reindex", daemon=True).start()

    msg = (
        f"Imported {len(imported)} file(s) from `{root}` "
        f"(cap {max_files}, depth {max_depth}"
        + (f", index chunks {chunk_count}" if reindex else ", reindex queued")
        + ")."
    )
    if len(imported) >= max_files or scanned > max_scan:
        msg += " Scan capped — import again or narrow the folder for more."
    return {
        "ok": True,
        "imported": imported,
        "count": len(imported),
        "errors": errors[:20],
        "message": msg,
        "capped": len(imported) >= max_files or scanned > max_scan,
        "chunks": chunk_count,
    }


def preview_document(path: str) -> dict[str, Any]:
    from jarvis.document_learning import resolve_document_path

    resolved = resolve_document_path(path)
    if not resolved:
        return {"ok": False, "message": "Document path not allowed or not found"}
    p = Path(resolved)
    if not p.is_file():
        return {"ok": False, "message": "Document not found"}
    try:
        doc = parse_document(p)
    except Exception as exc:
        return {"ok": False, "message": str(exc)}
    suggestion = classify_document(doc.title, doc.full_text)
    project = ""
    try:
        from jarvis.active_project import get_active_slug

        project = get_active_slug()
    except Exception:
        pass
    return {
        "ok": True,
        "document": {
            **doc.to_dict(),
            "modified": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
            "size": p.stat().st_size,
            "suffix": p.suffix.lower(),
            "location": str(p),
            "project": project,
            "preview": doc.excerpt,
            "suggestion": suggestion,
        },
    }


def search_library(
    query: str,
    *,
    limit: int = 8,
    project_scope: bool = True,
) -> dict[str, Any]:
    from jarvis.documents_rag import search_with_citations

    note_recent_search(query)
    result = search_with_citations(query, limit=limit, project_scope=project_scope)
    return {"ok": True, **result}


def stage_learn_candidates(
    path: str = "",
    *,
    url: str = "",
    text: str = "",
    title: str = "",
) -> dict[str, Any]:
    """Extract lessons and stage Memory candidates — never encode into ACM."""
    from jarvis.document_learning import (
        extract_document_learnings,
        ingest_file,
        ingest_text,
        ingest_url,
        resolve_document_path,
    )
    from jarvis.memory_services import propose_candidate

    doc = None
    source_path = ""
    source_type = "file"
    if url:
        ing = ingest_url(url)
        if not ing.ok:
            return {"ok": False, "message": ing.message}
        doc = parse_document(ing.path)
        source_path = ing.path
        source_type = "web"
    elif text.strip():
        ing = ingest_text(text, title=title or "pasted document")
        if not ing.ok:
            return {"ok": False, "message": ing.message}
        doc = parse_document(ing.path)
        source_path = ing.path
        source_type = "text"
    else:
        resolved = resolve_document_path(path)
        if not resolved or not Path(resolved).is_file():
            # try ingest/copy only when caller provided a path that resolve accepts later via ingest
            ing = ingest_file(path, copy_to_library=True)
            if not ing.ok:
                return {"ok": False, "message": ing.message or "Document path not allowed or not found"}
            resolved = ing.path
        doc = parse_document(resolved)
        source_path = str(resolved)

    facts = extract_document_learnings(doc.full_text, title=doc.title)
    if not facts:
        return {
            "ok": False,
            "message": "Could not extract candidate lessons from this document.",
            "path": source_path,
        }

    ns = "default"
    try:
        from jarvis.active_project import get_active_slug

        slug = get_active_slug()
        if slug:
            ns = slug
    except Exception:
        pass

    candidates = []
    for fact in facts:
        cand = propose_candidate(
            fact,
            source="document",
            entry_type="fact",
            namespace=ns,
            tags=["document-learn", f"doc-type:{source_type}", f"doc:{Path(source_path).name[:40]}"],
            evidence=f"From document: {doc.title}",
            confidence=0.55,
        )
        candidates.append(cand.get("candidate") or cand)

    return {
        "ok": True,
        "path": source_path,
        "title": doc.title,
        "candidates": candidates,
        "count": len(candidates),
        "message": (
            f"Staged **{len(candidates)}** Memory candidate(s) from **{doc.title}**. "
            "Review in Memory → Adopt. Documents never write autobiography directly."
        ),
    }


def project_retrieval_pack(slug: str | None = None) -> dict[str, Any]:
    from jarvis.active_project import get_active_slug, identity_for_slug

    target = (slug or get_active_slug() or "").strip()
    identity = identity_for_slug(target) if target else {}
    docs = []
    for d in list_library_enriched(limit=30):
        # Prefer files under project git_path name or recent imports when project active
        if target and target.replace("-", "") in (d.get("name") or "").lower().replace("-", ""):
            docs.append(d)
        elif not target:
            docs.append(d)
    if target and not docs:
        docs = list_library_enriched(limit=8)

    git_docs: list[dict[str, str]] = []
    git_path = identity.get("git_path") or ""
    if git_path and Path(git_path).is_dir():
        for name in ("README.md", "README", "docs", "CONTRIBUTING.md"):
            p = Path(git_path) / name
            if p.is_file():
                git_docs.append({"name": name, "path": str(p)})
            elif p.is_dir():
                for child in sorted(p.glob("*.md"))[:6]:
                    git_docs.append({"name": child.name, "path": str(child)})

    return {
        "ok": True,
        "slug": target,
        "identity": identity,
        "knowledge_namespace": identity.get("knowledge_namespace") or "",
        "library_documents": docs[:12],
        "git_documentation": git_docs[:12],
        "continue_working": [
            {"id": "ask", "label": "Ask with project sources"},
            {"id": "search", "label": "Search project docs"},
            {"id": "projects", "label": "Open Project Home", "view": "projects"},
        ],
        "summary": (
            f"Project `{target}` retrieval pack — library + git docs + knowledge NS "
            f"`{identity.get('knowledge_namespace') or '—'}`."
            if target
            else "No active project — library-wide retrieval."
        ),
    }


def document_briefing() -> dict[str, Any]:
    health = index_health()
    recent = list_library_enriched(limit=8)
    imports = recent_imports(8)
    candidates: list[dict] = []
    try:
        from jarvis.memory_services import list_candidates

        for c in (list_candidates(status="pending").get("candidates") or [])[:8]:
            tags = c.get("tags") or []
            if "document-learn" in tags or (c.get("source") or "") == "document":
                candidates.append({"id": c.get("id"), "content": _clip(c.get("content") or "", 120)})
    except Exception:
        pass
    pack = project_retrieval_pack()
    lines = [
        "# Document briefing",
        "",
        f"**Library:** {health.get('document_count', 0)} docs · {health.get('chunk_count', 0)} chunks",
        f"**Index:** {health.get('mode')} · embed {'online' if health.get('embed_available') else 'offline'}",
        f"**Needs rebuild:** {'yes' if health.get('needs_rebuild') else 'no'}",
        "",
        "## Recent documents",
    ]
    for d in recent[:5]:
        lines.append(f"- {d.get('name')} ({d.get('suffix') or ''})")
    lines.extend(["", "## Recent imports"])
    if imports:
        for i in imports[:5]:
            lines.append(f"- {i.get('name')} — {i.get('suggested_type') or 'file'}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Memory candidates from documents"])
    if candidates:
        for c in candidates:
            lines.append(f"- {c.get('content')}")
    else:
        lines.append("- (none pending)")
    lines.extend(["", "## Project relevance", pack.get("summary") or "—"])
    text = "\n".join(lines)
    return {
        "ok": True,
        "briefing": text,
        "health": health,
        "recent": recent,
        "candidates": candidates,
        "project_pack": pack,
        "message": text,
    }


def ask_with_sources(
    question: str,
    *,
    mode: str = "library",
    paths: list[str] | None = None,
    folder: str = "",
) -> dict[str, Any]:
    """Retrieve with explicit source scope + citations."""
    from jarvis.documents_rag import search_with_citations
    from jarvis.document_pipeline import answer_document

    q = (question or "").strip()
    if not q:
        return {"ok": False, "message": "Ask a question."}

    citations: list[dict] = []
    if mode == "document" and paths:
        answers = []
        for path in paths[:3]:
            try:
                doc = parse_document(path)
                ans = answer_document(doc, q)
                answers.append(f"### {doc.title}\n{ans}")
                citations.append(
                    {
                        "id": f"doc-{len(citations)+1}",
                        "title": doc.title,
                        "source": path,
                        "excerpt": _clip(doc.excerpt, 200),
                        "why": "User-selected source",
                    }
                )
            except Exception as exc:
                answers.append(f"### {path}\n_{exc}_")
        return {
            "ok": True,
            "answer": "\n\n".join(answers),
            "citations": citations,
            "mode": mode,
            "message": _format_cited_answer("\n\n".join(answers), citations),
        }

    scope = mode == "project"
    result = search_with_citations(q, limit=6, project_scope=scope)
    citations = result.get("citations") or []
    # Prefer hybrid if available
    try:
        from jarvis.intelligence.hybrid_rag import hybrid_search, format_cited_context

        hybrid = hybrid_search(q, limit=6)
        if hybrid.get("citations"):
            citations = hybrid["citations"]
            ctx = format_cited_context(hybrid)
            from jarvis import llm

            system = (
                "Answer using ONLY the cited document excerpts. "
                "Cite sources as [cite-N] or [doc-N]. If insufficient, say so."
            )
            answer = llm.ask_with_system(
                llm.document_model() if hasattr(llm, "document_model") else llm.general_model(),
                system,
                f"Question: {q}\n\n{ctx}",
                role="document",
            )
            return {
                "ok": True,
                "answer": answer,
                "citations": citations,
                "mode": "hybrid",
                "message": _format_cited_answer(answer, citations),
            }
    except Exception as exc:
        log.debug("hybrid ask fallback: %s", exc)

    hits = result.get("hits") or []
    if not hits:
        return {"ok": False, "message": "No matching documents.", "citations": []}
    excerpt = "\n\n".join(
        f"[{c.get('id')}] {c.get('title')}\n{c.get('excerpt')}" for c in citations
    )
    from jarvis import llm

    system = "Answer using ONLY the excerpts. Cite [doc-N]. If insufficient, say so."
    answer = llm.ask_with_system(
        llm.document_model() if hasattr(llm, "document_model") else llm.general_model(),
        system,
        f"Question: {q}\n\n{excerpt}",
        role="document",
    )
    return {
        "ok": True,
        "answer": answer,
        "citations": citations,
        "mode": mode,
        "message": _format_cited_answer(answer, citations),
    }


def _format_cited_answer(answer: str, citations: list[dict]) -> str:
    lines = [answer.strip(), "", "**Sources**"]
    if not citations:
        lines.append("_No citations — answer may be ungrounded._")
    for c in citations:
        lines.append(
            f"- **[{c.get('id')}]** {c.get('title') or c.get('source')} — {_clip(c.get('excerpt') or '', 120)}"
            + (f" _(why: {c.get('why')})_" if c.get("why") else "")
        )
    return "\n".join(lines)


def list_library_enriched(*, limit: int = 50, offset: int = 0, q: str = "") -> list[dict[str, Any]]:
    root = documents_dir()
    items: list[dict[str, Any]] = []
    ql = (q or "").lower()
    for path in sorted(root.rglob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file() or path.suffix.lower() not in DOCUMENT_EXTENSIONS:
            continue
        if path.name.startswith(".") or ".cache" in path.parts:
            continue
        if ql and ql not in path.name.lower() and ql not in str(path).lower():
            continue
        items.append(
            {
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
                "suffix": path.suffix.lower(),
                "relative": str(path.relative_to(root)),
            }
        )
    return items[offset : offset + limit]


def documents_home() -> dict[str, Any]:
    health = index_health()
    docs = list_library_enriched(limit=40)
    candidates: list[dict] = []
    try:
        from jarvis.memory_services import list_candidates

        for c in (list_candidates(status="pending").get("candidates") or [])[:10]:
            if (c.get("source") or "") == "document" or "document-learn" in (c.get("tags") or []):
                candidates.append(
                    {
                        "id": c.get("id"),
                        "content": _clip(c.get("content") or "", 140),
                    }
                )
    except Exception:
        pass
    pack = project_retrieval_pack()
    return {
        "ok": True,
        "philosophy": (
            "Documents is Aria's personal document intelligence layer — local files, "
            "grounded search, Memory candidates. Not Drive, SharePoint, or Notion."
        ),
        "health": health,
        "documents": docs,
        "document_count": health.get("document_count") or len(docs),
        "recent_searches": recent_searches(),
        "recent_imports": recent_imports(),
        "candidates": candidates,
        "project_pack": pack,
        "quick_actions": [
            {"id": "upload", "label": "Upload"},
            {"id": "import_folder", "label": "Import Folder"},
            {"id": "ask", "label": "Ask Aria"},
            {"id": "summarize", "label": "Summarize"},
            {"id": "learn", "label": "Learn → candidates"},
            {"id": "rebuild", "label": "Rebuild Search Index"},
            {"id": "briefing", "label": "Document Briefing"},
            {"id": "memory", "label": "Open Memory", "view": "memory"},
            {"id": "projects", "label": "Open Projects", "view": "projects"},
        ],
    }


def set_index_job(status: str, **extra: Any) -> None:
    payload = {"status": status, "updated": _now(), **extra}
    _save_json(INDEX_JOB_FILE, payload)


def rebuild_search_index(*, force: bool = True) -> dict[str, Any]:
    from jarvis.documents_rag import build_index

    set_index_job("running")
    try:
        chunks = build_index(force=force)
        set_index_job("idle", chunks=len(chunks))
        health = index_health()
        return {
            "ok": True,
            "chunks": len(chunks),
            "health": health,
            "message": f"Search index rebuilt — {len(chunks)} chunk(s).",
        }
    except Exception as exc:
        set_index_job("error", error=str(exc))
        return {"ok": False, "message": str(exc)}
