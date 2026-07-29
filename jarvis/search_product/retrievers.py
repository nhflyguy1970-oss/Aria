"""Corpus retrievers — products own data; Search normalizes to SearchResult."""

from __future__ import annotations

import logging
import re
from typing import Any, Callable

from jarvis.search_product.contract import make_result

logger = logging.getLogger("jarvis.search_product.retrievers")


def _safe(fn: Callable[[], list[dict[str, Any]]], label: str) -> list[dict[str, Any]]:
    try:
        return fn()
    except Exception as exc:
        logger.warning("Search retriever %s failed: %s", label, exc)
        return []


def retrieve_documents(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.documents_rag import search

        hits = search(query, limit=limit)
        out = []
        for h in hits:
            title = h.get("title") or h.get("source") or "document"
            text = (h.get("text") or "")[:400]
            out.append(
                make_result(
                    source="documents",
                    source_label="Documents",
                    title=str(title),
                    summary=text,
                    preview=text,
                    location=str(h.get("source") or ""),
                    score=0.85,
                    strategy="semantic",
                    open_action={"view": "documents", "query": query, "location": h.get("source")},
                    icon="documents",
                )
            )
        return out

    return _safe(_run, "documents")


def retrieve_memory(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        out: list[dict[str, Any]] = []
        try:
            from aria_core import acm_bridge

            if acm_bridge.acm_is_authoritative():
                hits = acm_bridge.primary_search(query, limit=limit)
                for h in hits:
                    content = h.get("content") or h.get("text") or str(h)
                    out.append(
                        make_result(
                            source="memory",
                            source_label="ACM Cognition",
                            title=str(h.get("id") or "acm")[:40],
                            summary=content[:280],
                            preview=content[:400],
                            location=str(h.get("namespace") or "acm"),
                            score=float(h.get("score") or 0.7),
                            strategy="acm_authority",
                            open_action={"view": "memory", "query": query, "id": h.get("id")},
                            metadata={"namespace": h.get("namespace")},
                            icon="memory",
                        )
                    )
                if out:
                    return out
        except Exception as exc:
            logger.debug("ACM search: %s", exc)
        try:
            from jarvis.assistant_instance import get_assistant

            asst = get_assistant()
            mem = getattr(asst, "memory", None)
            if mem and hasattr(mem, "search"):
                for h in mem.search(query, limit=limit) or []:
                    content = h.get("content") or h.get("text") or str(h)
                    out.append(
                        make_result(
                            source="memory",
                            source_label="Conversation Memory",
                            title=str(h.get("id") or "memory")[:40],
                            summary=content[:280],
                            preview=content[:400],
                            location=str(h.get("namespace") or "memory"),
                            score=float(h.get("score") or 0.65),
                            strategy="keyword",
                            open_action={"view": "memory", "query": query, "id": h.get("id")},
                            icon="memory",
                        )
                    )
        except Exception as exc:
            logger.debug("MemoryStore search: %s", exc)
        return out

    return _safe(_run, "memory")


def retrieve_code(query: str, limit: int, *, mode: str = "auto") -> list[dict[str, Any]]:
    def _run():
        out: list[dict[str, Any]] = []
        # grep is opt-in via code_mode=grep only (avoid unbounded tree walks in federation)
        want_semantic = mode in ("auto", "semantic")
        if want_semantic:
            try:
                from jarvis.knowledge.git_sync import list_repo_states
                from jarvis.knowledge.repo_index import index_path_for_repo, search_repo_index
                from pathlib import Path

                for st in list_repo_states():
                    if not st.retrieval_available:
                        continue
                    index_path = index_path_for_repo(Path(st.path))
                    for h in search_repo_index(index_path, query, limit=limit):
                        out.append(
                            make_result(
                                source="code",
                                source_label=st.label,
                                title=str(h.get("source") or "code"),
                                summary=(h.get("text") or "")[:280],
                                preview=(h.get("text") or "")[:400],
                                location=f"{st.path}:{h.get('source', '')}",
                                score=0.82,
                                strategy="semantic",
                                open_action={
                                    "view": "coding",
                                    "query": query,
                                    "mode": "semantic",
                                    "location": f"{st.path}:{h.get('source', '')}",
                                },
                                metadata={"branch": st.branch, "code_mode": "semantic"},
                                icon="code",
                            )
                        )
            except Exception as exc:
                logger.debug("Git repo search: %s", exc)
            if not out:
                try:
                    from jarvis.code_index import search

                    for h in search(query, limit=limit):
                        out.append(
                            make_result(
                                source="code",
                                source_label="Code Index",
                                title=str(h.get("source") or "code"),
                                summary=(h.get("text") or "")[:280],
                                preview=(h.get("text") or "")[:400],
                                location=str(h.get("source") or ""),
                                score=float(h.get("score") or 0.8),
                                strategy="semantic",
                                open_action={"view": "coding", "query": query, "mode": "semantic"},
                                metadata={"code_mode": "semantic"},
                                icon="code",
                            )
                        )
                except Exception as exc:
                    logger.debug("code_index: %s", exc)
        if mode == "grep":
            try:
                from jarvis import fs
                from jarvis.config import PROJECT_ROOT

                # Explicit grep mode only — full-tree walk is too costly for default federation.
                for path, line_no, line in fs.search_files(query, PROJECT_ROOT)[:limit]:
                    out.append(
                        make_result(
                            source="code",
                            source_label="Code Grep",
                            title=f"{path}:{line_no}",
                            summary=line[:280],
                            preview=line[:400],
                            location=f"{path}:{line_no}",
                            score=0.72,
                            strategy="grep",
                            open_action={
                                "view": "coding",
                                "query": query,
                                "mode": "grep",
                                "location": f"{path}:{line_no}",
                            },
                            metadata={"code_mode": "grep", "line": line_no},
                            icon="code",
                        )
                    )
            except Exception as exc:
                logger.debug("grep search: %s", exc)
        return out[:limit]

    return _safe(_run, "code")


def retrieve_journal(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        out = []
        try:
            from jarvis.modules.journal import JournalStore

            store = JournalStore()
            for h in store.search(query, limit=limit) or []:
                title = h.get("title") or h.get("content") or h.get("date") or "journal"
                text = h.get("text") or h.get("content") or h.get("excerpt") or ""
                out.append(
                    make_result(
                        source="journal",
                        source_label="Journal & Notes",
                        title=str(title)[:120],
                        summary=str(text)[:280],
                        preview=str(text)[:400],
                        location=str(h.get("date") or h.get("section") or h.get("id") or ""),
                        score=0.7,
                        strategy="keyword",
                        open_action={"view": "journal", "query": query, "id": h.get("id"), "date": h.get("date")},
                        icon="journal",
                    )
                )
        except Exception as exc:
            logger.debug("journal primary: %s", exc)
            try:
                from jarvis.project_journal import ProjectJournal

                for h in ProjectJournal().search(query, limit=limit) or []:
                    text = h.get("text") or h.get("content") or ""
                    out.append(
                        make_result(
                            source="journal",
                            source_label="Project Journal",
                            title=str(h.get("title") or "entry"),
                            summary=str(text)[:280],
                            preview=str(text)[:400],
                            location=str(h.get("id") or ""),
                            score=0.65,
                            strategy="keyword",
                            open_action={"view": "journal", "query": query},
                            icon="journal",
                        )
                    )
            except Exception as exc2:
                logger.debug("journal: %s", exc2)
        return out

    return _safe(_run, "journal")


def retrieve_projects(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from pathlib import Path

        from jarvis.project_registry import list_projects

        out = []
        q = query.lower()
        tokens = re.findall(r"\w{3,}", q)
        for meta in list_projects() or []:
            if not isinstance(meta, dict):
                continue
            blob = f"{meta.get('title', '')} {meta.get('slug', '')} {meta.get('description', '')}".lower()
            title = str(meta.get("title") or meta.get("slug") or "project")
            path = str(meta.get("path") or meta.get("root") or meta.get("folder") or "")
            matched = (q and q in blob) or any(w in blob for w in tokens)
            doc_hits = []
            root_path = path
            if not root_path and meta.get("slug"):
                try:
                    from jarvis.project_registry import PROJECTS_ROOT

                    root_path = str(PROJECTS_ROOT / meta["slug"])
                except Exception:
                    root_path = ""
            if root_path and q:
                try:
                    root = Path(root_path)
                    if root.is_dir():
                        for p in list(root.rglob("*.md"))[:40]:
                            try:
                                text = p.read_text(encoding="utf-8", errors="ignore")
                            except OSError:
                                continue
                            if q in text.lower():
                                doc_hits.append((p, text[:400]))
                                if len(doc_hits) >= 2:
                                    break
                except Exception:
                    pass
            if matched:
                out.append(
                    make_result(
                        source="projects",
                        source_label=title,
                        title=title,
                        summary=str(meta.get("description") or path)[:280],
                        preview=str(meta.get("description") or path)[:400],
                        location=path or str(meta.get("slug") or ""),
                        score=0.75,
                        strategy="keyword",
                        open_action={"view": "projects", "query": query, "slug": meta.get("slug")},
                        icon="projects",
                    )
                )
            for p, excerpt in doc_hits:
                out.append(
                    make_result(
                        source="projects",
                        source_label=title,
                        title=p.name,
                        summary=excerpt[:280],
                        preview=excerpt,
                        location=str(p),
                        score=0.78,
                        strategy="keyword",
                        open_action={"view": "projects", "query": query, "location": str(p)},
                        icon="projects",
                    )
                )
            if len(out) >= limit:
                break
        return out[:limit]

    return _safe(_run, "projects")


def retrieve_learned(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        out = []
        try:
            from jarvis.knowledge.registry import list_sources

            q = query.lower()
            for s in list_sources():
                if s.type not in ("website", "pdf", "docx", "markdown"):
                    continue
                blob = f"{s.label} {s.location} {s.type}".lower()
                if q not in blob and not any(w in blob for w in re.findall(r"\w{3,}", q)):
                    continue
                out.append(
                    make_result(
                        source="learned",
                        source_label="Learned Sources",
                        title=s.label,
                        summary=f"{s.type}: {s.location}",
                        preview=f"{s.type}: {s.location}",
                        location=s.location,
                        score=0.6,
                        strategy="keyword",
                        open_action={"view": "documents", "query": query, "location": s.location},
                        metadata={"type": s.type},
                        icon="learned",
                    )
                )
                if len(out) >= limit:
                    break
        except Exception as exc:
            logger.debug("learned: %s", exc)
        return out

    return _safe(_run, "learned")


def retrieve_graph(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.connections_services import search_connections

        data = search_connections(query, limit=limit, mode="all")
        out = []
        for n in data.get("nodes") or []:
            name = n.get("name") or n.get("id") or "entity"
            out.append(
                make_result(
                    source="graph",
                    source_label="Connections",
                    title=str(name),
                    summary=str(n.get("kind") or n.get("summary") or "")[:280],
                    preview=str(n.get("summary") or n.get("kind") or "")[:400],
                    location=str(n.get("namespace") or ""),
                    score=0.8,
                    strategy="graph",
                    open_action={"view": "connections", "query": query, "entity": name},
                    metadata={"kind": n.get("kind"), "facet_alias": "connections"},
                    icon="connections",
                )
            )
        for e in data.get("relationships") or []:
            title = f"{e.get('source')} → {e.get('target')}"
            out.append(
                make_result(
                    source="connections",
                    source_label="Relationships",
                    title=title,
                    summary=str(e.get("relation") or e.get("type") or "")[:280],
                    preview=str(e.get("document") or "")[:400],
                    location=str(e.get("document") or ""),
                    score=0.75,
                    strategy="graph",
                    open_action={"view": "connections", "query": query},
                    icon="connections",
                )
            )
        return out[:limit]

    return _safe(_run, "graph")


def retrieve_connections(query: str, limit: int) -> list[dict[str, Any]]:
    # Same store; tag as connections for facet filter clarity
    hits = retrieve_graph(query, limit)
    for h in hits:
        if h.get("source") == "graph":
            h["source"] = "connections"
            h["source_label"] = "Connections"
    return hits


def retrieve_audio(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.audio_search import search

        out = []
        for h in search(query, limit=limit):
            out.append(
                make_result(
                    source="audio",
                    source_label="Audio Transcripts",
                    title=str(h.get("title") or h.get("path") or "audio"),
                    summary=str(h.get("snippet") or "")[:280],
                    preview=str(h.get("snippet") or h.get("transcript") or "")[:400],
                    location=str(h.get("path") or ""),
                    score=0.7,
                    strategy="keyword",
                    open_action={"view": "audio", "query": query, "path": h.get("path")},
                    metadata={"indexed": h.get("indexed")},
                    icon="audio",
                )
            )
        return out

    return _safe(_run, "audio")


def retrieve_web(query: str, limit: int) -> list[dict[str, Any]]:
    """Web facet returns handoff results — Chat owns synthesis."""
    def _run():
        from jarvis import web_search

        out = []
        for h in web_search.search(query, limit=min(limit, 8)):
            out.append(
                make_result(
                    source="web",
                    source_label="Web",
                    title=str(h.get("title") or h.get("href") or h.get("url") or "web"),
                    summary=str(h.get("snippet") or h.get("body") or "")[:280],
                    preview=str(h.get("snippet") or h.get("body") or "")[:400],
                    location=str(h.get("url") or h.get("href") or ""),
                    score=0.7,
                    strategy="web",
                    open_action={
                        "view": "chat",
                        "query": query,
                        "handoff": "web_search",
                        "url": h.get("url") or h.get("href"),
                    },
                    metadata={"backend": web_search.backend_name(), "chat_synthesis": True},
                    icon="web",
                )
            )
        return out

    return _safe(_run, "web")


def retrieve_planner(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.planner_store import list_tasks

        q = query.lower()
        out = []
        for t in list_tasks(include_completed=True):
            text = f"{t.get('text', '')} {t.get('notes', '')} {t.get('project', '')}".lower()
            if q not in text and not all(w in text for w in re.findall(r"\w{2,}", q)):
                continue
            out.append(
                make_result(
                    source="planner",
                    source_label="Planner",
                    title=str(t.get("text") or "task")[:120],
                    summary=str(t.get("notes") or t.get("project") or "")[:280],
                    preview=str(t.get("notes") or "")[:400],
                    location=str(t.get("id") or ""),
                    score=0.74,
                    strategy="keyword",
                    open_action={"view": "planner", "query": query, "id": t.get("id")},
                    metadata={"completed": t.get("completed"), "priority": t.get("priority")},
                    icon="planner",
                )
            )
            if len(out) >= limit:
                break
        return out

    return _safe(_run, "planner")


def retrieve_calendar(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.calendar_bridges import search_hits

        out = []
        for hit in search_hits(query, limit=limit):
            out.append(
                make_result(
                    source="calendar",
                    source_label="Calendar",
                    title=hit.get("title") or "Calendar",
                    summary=hit.get("summary") or "",
                    preview=hit.get("summary") or hit.get("title") or "",
                    location=str(hit.get("day") or ""),
                    score=float(hit.get("score") or 0.7),
                    strategy="keyword",
                    open_action={"view": "calendar", "query": query, "day": hit.get("day")},
                    icon="calendar",
                )
            )
        return out[:limit]

    return _safe(_run, "calendar")


def retrieve_gallery(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.gallery_product.library import list_images

        data = list_images(offset=0, limit=min(80, limit * 4), query=query, include_artifacts=False)
        images = data.get("images") if isinstance(data, dict) else data
        out = []
        for img in images or []:
            title = img.get("title") or img.get("prompt") or img.get("id") or "image"
            prompt = img.get("prompt") or img.get("meta", {}).get("prompt") if isinstance(img.get("meta"), dict) else img.get("prompt")
            out.append(
                make_result(
                    source="gallery",
                    source_label="Gallery",
                    title=str(title)[:120],
                    summary=str(prompt or "")[:280],
                    preview=str(prompt or "")[:400],
                    location=str(img.get("id") or img.get("path") or ""),
                    score=0.7,
                    strategy="keyword",
                    open_action={"view": "gallery", "query": query, "id": img.get("id")},
                    icon="gallery",
                )
            )
            if len(out) >= limit:
                break
        return out

    return _safe(_run, "gallery")


def retrieve_home_assistant(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.home_assistant_product.entities import search

        data = search(q=query, limit=limit)
        entities = data.get("results") or data.get("entities") or []
        out = []
        for e in entities:
            eid = e.get("entity_id") or e.get("id") or ""
            name = e.get("friendly_name") or e.get("name") or eid
            out.append(
                make_result(
                    source="home_assistant",
                    source_label="Home Assistant",
                    title=str(name),
                    summary=str(e.get("state") or e.get("domain") or "")[:280],
                    preview=f"{eid} · {e.get('state', '')}",
                    location=str(eid),
                    score=0.76,
                    strategy="keyword",
                    open_action={"view": "workstation", "query": query, "entity_id": eid},
                    metadata={"domain": e.get("domain")},
                    icon="home_assistant",
                )
            )
        return out[:limit]

    return _safe(_run, "home_assistant")


def retrieve_flytying(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        from jarvis.flytying.search import unified_search

        data = unified_search(query, limit=limit)
        hits = data.get("results") or data.get("hits") or []
        out = []
        for h in hits:
            if not isinstance(h, dict):
                continue
            title = h.get("name") or h.get("title") or h.get("pattern") or "pattern"
            rid = h.get("recipe_id") or h.get("id") or ""
            out.append(
                make_result(
                    source="flytying",
                    source_label="Fly Tying",
                    title=str(title),
                    summary=str(h.get("summary") or h.get("fly_type") or h.get("type") or "")[:280],
                    preview=str(h.get("summary") or h.get("recipe") or "")[:400],
                    location=str(rid),
                    score=float(h.get("quality_score") or h.get("score") or 0.75),
                    strategy=str(data.get("search_mode") or "hybrid"),
                    open_action={"view": "flytying", "query": query, "id": rid},
                    icon="flytying",
                )
            )
        return out[:limit]

    return _safe(_run, "flytying")


def retrieve_automation(query: str, limit: int) -> list[dict[str, Any]]:
    def _run():
        try:
            from jarvis.automation.home import search_automation

            data = search_automation(query, limit=limit)
        except Exception:
            data = {"hits": []}
        items = data.get("hits") or data.get("items") or data.get("results") or []
        out = []
        for it in items:
            title = it.get("title") or it.get("name") or it.get("id") or "automation"
            out.append(
                make_result(
                    source="automation",
                    source_label="Automation",
                    title=str(title),
                    summary=str(it.get("description") or it.get("kind") or it.get("type") or "")[:280],
                    preview=str(it.get("description") or it.get("action") or "")[:400],
                    location=str(it.get("id") or it.get("slug") or ""),
                    score=0.7,
                    strategy="keyword",
                    open_action={"view": "automation", "query": query, "id": it.get("id") or it.get("slug")},
                    icon="automation",
                )
            )
            if len(out) >= limit:
                break
        return out

    return _safe(_run, "automation")


def retrieve_settings(query: str, limit: int) -> list[dict[str, Any]]:
    """Settings facet — catalog only; products own stores."""

    def _run():
        from jarvis.settings_product.catalog import search_catalog

        out = []
        for e in search_catalog(query, limit=limit):
            open_action = dict(e.get("deep_link") or {})
            open_action.setdefault("view", "settings")
            out.append(
                make_result(
                    source="settings",
                    source_label="Settings",
                    title=str(e.get("title") or e.get("id")),
                    summary=str(e.get("description") or "")[:280],
                    preview=f"{e.get('category')} · owner {e.get('owner')}",
                    location=str(e.get("id") or ""),
                    score=0.88,
                    strategy="catalog",
                    open_action=open_action,
                    metadata={
                        "category": e.get("category"),
                        "owner": e.get("owner"),
                        "pref_id": e.get("id"),
                        "aliases": e.get("aliases"),
                    },
                    icon="settings",
                )
            )
        return out

    return _safe(_run, "settings")


def retrieve_dashboard(query: str, limit: int) -> list[dict[str, Any]]:
    """Dashboard/Home facet — widget catalog + deep links; products own data."""

    def _run():
        from jarvis.dashboard_product.widgets import search_widgets

        out = []
        for e in search_widgets(query, limit=limit):
            open_action = dict(e.get("deep_link") or {"view": "dashboard", "widget": e.get("id")})
            open_action.setdefault("view", "dashboard")
            out.append(
                make_result(
                    source="dashboard",
                    source_label="Home",
                    title=str(e.get("title") or e.get("id")),
                    summary=str(e.get("description") or "")[:280],
                    preview=f"{e.get('category')} · owner {e.get('owner')}",
                    location=str(e.get("id") or ""),
                    score=0.87,
                    strategy="catalog",
                    open_action=open_action,
                    metadata={
                        "category": e.get("category"),
                        "owner": e.get("owner"),
                        "widget_id": e.get("id"),
                        "aliases": e.get("aliases"),
                    },
                    icon="dashboard",
                )
            )
        # Always include Home itself on broad queries
        q = (query or "").lower()
        if not out or any(t in q for t in ("home", "dashboard", "brief", "attention")):
            out.insert(
                0,
                make_result(
                    source="dashboard",
                    source_label="Home",
                    title="Home",
                    summary="Aria Home — what is happening, what next, where to go.",
                    preview="Dashboard product",
                    location="home",
                    score=0.95,
                    strategy="catalog",
                    open_action={"view": "dashboard"},
                    icon="dashboard",
                ),
            )
        return out[:limit]

    return _safe(_run, "dashboard")


def retrieve_layouts(query: str, limit: int) -> list[dict[str, Any]]:
    """Layouts facet — shell presentation profiles; Search indexes, Layouts applies."""

    def _run():
        from jarvis.layouts_product.catalog import search_builtins
        from jarvis.layouts_product.store import load_customs

        out = []
        for e in search_builtins(query, limit=limit):
            out.append(
                make_result(
                    source="layouts",
                    source_label="Layouts",
                    title=f"Apply {e.get('label')}",
                    summary=str(e.get("description") or "")[:280],
                    preview=f"{e.get('kind')} · frozen starter",
                    location=str(e.get("id") or ""),
                    score=0.9,
                    strategy="catalog",
                    open_action={"type": "apply_layout", "layout_id": e.get("id"), "view": None},
                    metadata={"layout_id": e.get("id"), "kind": e.get("kind")},
                    icon="layouts",
                )
            )
        q = (query or "").lower()
        for cid, snap in load_customs().items():
            blob = f"{cid} {snap.get('label') or ''}".lower()
            if q and q not in blob:
                continue
            out.append(
                make_result(
                    source="layouts",
                    source_label="Layouts",
                    title=f"Apply {snap.get('label') or cid}",
                    summary="Custom shell layout",
                    preview="custom",
                    location=cid,
                    score=0.86,
                    strategy="catalog",
                    open_action={"type": "apply_layout", "layout_id": cid},
                    metadata={"layout_id": cid, "kind": "custom"},
                    icon="layouts",
                )
            )
        if not q or "layout" in q:
            out.insert(
                0,
                make_result(
                    source="layouts",
                    source_label="Layouts",
                    title="Open Layouts",
                    summary="Shell presentation profiles — Ctrl+Shift+L",
                    preview="Layouts product",
                    location="layouts",
                    score=0.95,
                    strategy="catalog",
                    open_action={"type": "open_layouts"},
                    icon="layouts",
                ),
            )
        return out[:limit]

    return _safe(_run, "layouts")


def retrieve_notifications(query: str, limit: int) -> list[dict[str, Any]]:
    """Notifications facet — Search indexes; Notifications owns delivery/inbox."""

    def _run():
        from jarvis.notifications_product.digest import build_digest
        from jarvis.notifications_product.history import load_history
        from jarvis.notifications_product.pipeline import unread_summary

        q = (query or "").lower()
        out = []
        summary = unread_summary()
        out.append(
            make_result(
                source="notifications",
                source_label="Notifications",
                title="Open Notifications",
                summary="Durable inbox — what still needs your attention (Ctrl+Shift+A)",
                preview=f"{summary.get('unread') or 0} unread · {summary.get('critical') or 0} critical",
                location="notifications",
                score=0.96,
                strategy="catalog",
                open_action={"type": "open_notifications"},
                icon="notifications",
            )
        )
        if not q or any(t in q for t in ("unread", "alert", "inbox", "activity")):
            out.append(
                make_result(
                    source="notifications",
                    source_label="Notifications",
                    title="Unread notifications",
                    summary="Filter Activity Center to unread",
                    preview="unread",
                    location="unread",
                    score=0.9,
                    strategy="catalog",
                    open_action={"type": "open_notifications", "filter": "unread"},
                    icon="notifications",
                )
            )
        if not q or any(t in q for t in ("error", "fail", "critical")):
            out.append(
                make_result(
                    source="notifications",
                    source_label="Notifications",
                    title="Errors & failures",
                    summary="Filter to error severity",
                    preview="errors",
                    location="err",
                    score=0.88,
                    strategy="catalog",
                    open_action={"type": "open_notifications", "filter": "err"},
                    icon="notifications",
                )
            )
        if not q or "digest" in q or "today" in q:
            digest = build_digest("needs_attention")
            out.append(
                make_result(
                    source="notifications",
                    source_label="Notifications",
                    title=digest.get("title") or "Needs attention",
                    summary=str(digest.get("summary") or "")[:280],
                    preview=f"{digest.get('count') or 0} events",
                    location="digest",
                    score=0.85,
                    strategy="digest",
                    open_action={"type": "open_notifications", "filter": "unread"},
                    icon="notifications",
                )
            )
        for item in load_history(limit=min(limit, 8)):
            blob = f"{item.get('title')} {item.get('summary')} {item.get('source')}".lower()
            if q and q not in blob:
                continue
            out.append(
                make_result(
                    source="notifications",
                    source_label="Notifications",
                    title=str(item.get("title") or "Notification"),
                    summary=str(item.get("summary") or "")[:280],
                    preview=str(item.get("severity") or "info"),
                    location=str(item.get("id") or ""),
                    score=0.7,
                    strategy="history",
                    open_action={"type": "open_notifications", "id": item.get("id")},
                    metadata={"notification_id": item.get("id")},
                    icon="notifications",
                )
            )
        return out[:limit]

    return _safe(_run, "notifications")


RETRIEVERS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "documents": retrieve_documents,
    "memory": retrieve_memory,
    "code": retrieve_code,
    "journal": retrieve_journal,
    "projects": retrieve_projects,
    "learned": retrieve_learned,
    "graph": retrieve_graph,
    "connections": retrieve_connections,
    "audio": retrieve_audio,
    "web": retrieve_web,
    "planner": retrieve_planner,
    "calendar": retrieve_calendar,
    "gallery": retrieve_gallery,
    "home_assistant": retrieve_home_assistant,
    "flytying": retrieve_flytying,
    "automation": retrieve_automation,
    "settings": retrieve_settings,
    "dashboard": retrieve_dashboard,
    "layouts": retrieve_layouts,
    "notifications": retrieve_notifications,
}
