"""Connections — product layer over the Knowledge Graph store.

User-facing name: Connections
Implementation: Knowledge Graph (graph_store)

NOT Memory. NOT Documents. NOT Knowledge Briefs.
ACM is the only cognitive source of truth.
The graph mirrors adopted / explicitly approved relationships.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.modules.graph_store import get_graph_store, reset_graph_store_for_tests  # noqa: F401

log = logging.getLogger("jarvis.connections")

PHILOSOPHY = (
    "Connections model relationships. Memory is autobiography. "
    "Documents are files. Knowledge Briefs are researched topics. "
    "ACM remains the only cognitive source of truth — the graph mirrors, never replaces."
)

MIN_CHAT_CONFIDENCE = 0.55
ACTIVITY_FILE = DATA_DIR / "connections_activity.json"
UNDO_FILE = DATA_DIR / "connections_undo.json"
PENDING_FILE = DATA_DIR / "connections_pending_ingest.json"

_KIND_HINTS = {
    "person": ("person", "people", "mr", "mrs", "dr"),
    "place": ("place", "city", "town", "street", "home", "office"),
    "organization": ("org", "company", "inc", "llc", "lab", "team"),
    "project": ("project", "repo", "codebase"),
    "concept": ("concept", "idea", "topic"),
    "document": ("document", "manual", "pdf", "warranty"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: Any) -> Any:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _note_activity(kind: str, detail: dict[str, Any]) -> None:
    items = _load_json(ACTIVITY_FILE, [])
    if not isinstance(items, list):
        items = []
    items.insert(0, {"id": uuid.uuid4().hex[:10], "kind": kind, "at": _now(), **detail})
    _save_json(ACTIVITY_FILE, items[:100])


def _push_undo(action: str, snapshot: dict[str, Any]) -> str:
    items = _load_json(UNDO_FILE, [])
    if not isinstance(items, list):
        items = []
    uid = uuid.uuid4().hex[:12]
    items.insert(0, {"id": uid, "action": action, "at": _now(), "snapshot": snapshot})
    _save_json(UNDO_FILE, items[:30])
    return uid


def infer_kind(name: str, hint: str = "") -> str:
    blob = f"{hint} {name}".lower()
    for kind, keys in _KIND_HINTS.items():
        if any(k in blob for k in keys):
            return kind
    if name.isupper() and len(name) <= 6:
        return "acronym"
    if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$", name or ""):
        return "person"
    return "entity"


def health() -> dict[str, Any]:
    store = get_graph_store()
    st = store.stats() if hasattr(store, "stats") else {}
    activity = _load_json(ACTIVITY_FILE, [])
    last = activity[0] if isinstance(activity, list) and activity else None
    path = getattr(store, "path", None)
    return {
        "ok": True,
        "backend": getattr(store, "backend", "unknown"),
        "status": "ok",
        "health": "healthy",
        "node_count": int(st.get("nodes") or 0),
        "relationship_count": int(st.get("edges") or 0),
        "orphans": int(st.get("orphans") or 0),
        "missing_provenance": int(st.get("missing_provenance") or 0),
        "namespaces": store.namespaces() if hasattr(store, "namespaces") else [],
        "last_ingest": next((a for a in (activity or []) if a.get("kind") == "ingest"), None),
        "last_cleanup": next((a for a in (activity or []) if a.get("kind") in ("prune", "cleanup")), None),
        "last_activity": last,
        "storage": str(path) if path else "",
        "philosophy": PHILOSOPHY,
        "product_name": "Connections",
        "implementation": "knowledge_graph",
    }


def connections_home() -> dict[str, Any]:
    store = get_graph_store()
    h = health()
    recent = store.recent_activity(limit=12) if hasattr(store, "recent_activity") else []
    pending = _load_json(PENDING_FILE, [])
    return {
        "ok": True,
        "philosophy": PHILOSOPHY,
        "health": h,
        "overview": {
            "nodes": h["node_count"],
            "relationships": h["relationship_count"],
            "namespaces": h["namespaces"],
            "orphans": h["orphans"],
            "missing_provenance": h["missing_provenance"],
        },
        "recent_activity": recent,
        "pending_ingest": pending if isinstance(pending, list) else [],
        "quick_actions": [
            {"id": "search", "label": "Search"},
            {"id": "browse", "label": "Browse"},
            {"id": "import", "label": "Review import"},
            {"id": "cleanup", "label": "Cleanup"},
            {"id": "assistant", "label": "Relationship assistant"},
        ],
        "identity": {
            "documents": "Document Intelligence",
            "knowledge": "Knowledge Briefs",
            "connections": "Knowledge Graph (this view)",
            "memory": "Autobiographical cognition (ACM)",
        },
    }


def search_connections(
    query: str,
    *,
    limit: int = 20,
    namespace: str = "",
    kind: str = "",
    mode: str = "all",
) -> dict[str, Any]:
    """Search entities and relationships. mode: all|entities|relationships|namespace|project|document|people|places|organizations|concepts."""
    q = (query or "").strip()
    store = get_graph_store()
    ns = namespace
    kind_filter = kind
    mode = (mode or "all").lower()
    if mode == "project":
        ns = ns or q
        q = q if namespace else ""
    if mode == "people":
        kind_filter = "person"
    elif mode == "places":
        kind_filter = "place"
    elif mode == "organizations":
        kind_filter = "organization"
    elif mode == "concepts":
        kind_filter = "concept"
    elif mode == "document":
        kind_filter = "document"

    nodes: list[dict] = []
    edges: list[dict] = []
    if mode in ("all", "entities", "namespace", "project", "people", "places", "organizations", "concepts", "document"):
        if hasattr(store, "list_nodes"):
            nodes = store.list_nodes(namespace=ns, kind=kind_filter, limit=limit, q=q)
        else:
            nodes = store.search_nodes(q or " ", limit=limit, namespace=ns) if hasattr(store, "search_nodes") else []
            if kind_filter:
                nodes = [n for n in nodes if (n.get("kind") or "") == kind_filter]
    if mode in ("all", "relationships", "namespace", "project", "document"):
        if hasattr(store, "list_edges"):
            edges = store.list_edges(namespace=ns, limit=limit, q=q)
        if mode == "document" and q:
            edges = [e for e in edges if q.lower() in str(e.get("document") or "").lower()]

    return {
        "ok": True,
        "query": query,
        "mode": mode,
        "nodes": nodes[:limit],
        "relationships": edges[:limit],
        "count": len(nodes) + len(edges),
    }


def entity_page(name: str, *, namespace: str = "") -> dict[str, Any]:
    store = get_graph_store()
    node = store.get_node(name, namespace=namespace or None) if hasattr(store, "get_node") else None
    if not node:
        return {"ok": False, "error": "entity not found"}
    rels = store.neighbors(node["name"], depth=1, limit=40)
    docs = sorted({r.get("document") for r in rels if r.get("document")})
    projects = sorted({r.get("project") for r in rels if r.get("project")} | ({node.get("project")} if node.get("project") else set()))
    memory_ids = sorted({node.get("memory_id"), *[r.get("memory_id") for r in rels if r.get("memory_id")]} - {""})
    return {
        "ok": True,
        "entity": node,
        "relationships": rels,
        "documents": [d for d in docs if d],
        "projects": [p for p in projects if p],
        "memory_links": list(memory_ids),
        "knowledge_references": [],  # briefs stay separate; filled by UI link only
    }


def create_entity(
    name: str,
    *,
    kind: str = "entity",
    namespace: str = "default",
    description: str = "",
    source: str = "manual",
    confidence: float = 1.0,
    project: str = "",
    document: str = "",
) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "name required"}
    store = get_graph_store()
    kind = kind or infer_kind(name)
    props = {
        "source": source or "manual",
        "confidence": float(confidence),
        "description": description or "",
        "project": project or "",
        "document": document or "",
    }
    nid = store.merge_node(name, kind=kind, namespace=namespace or "default", props=props)
    _note_activity("create_entity", {"name": name, "namespace": namespace})
    return {"ok": True, "id": nid, "entity": store.get_node(name, namespace=namespace) if hasattr(store, "get_node") else {"name": name}}


def create_relationship(
    subject: str,
    predicate: str,
    obj: str,
    *,
    namespace: str = "default",
    source: str = "manual",
    confidence: float = 1.0,
    memory_id: str = "",
    document: str = "",
    project: str = "",
    journal: str = "",
    description: str = "",
) -> dict[str, Any]:
    subject, obj = (subject or "").strip(), (obj or "").strip()
    if not subject or not obj or not (predicate or "").strip():
        return {"ok": False, "error": "subject, predicate, and object required"}
    if source in ("", "unknown") and not memory_id:
        return {"ok": False, "error": "provenance required — anonymous relationships are not allowed"}
    store = get_graph_store()
    props = {
        "source": source,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "document": document or "",
        "project": project or "",
        "journal": journal or "",
        "description": description or "",
    }
    eid = store.merge_relationship(
        subject,
        predicate,
        obj,
        namespace=namespace or "default",
        memory_id=memory_id or "",
        props=props,
    )
    _note_activity("ingest", {"subject": subject, "predicate": predicate, "object": obj, "source": source})
    return {"ok": True, "id": eid}


def propose_ingest_from_text(
    text: str,
    *,
    namespace: str = "default",
    source: str = "ai_suggestion",
    document: str = "",
    project: str = "",
) -> dict[str, Any]:
    """Extract candidates for review — does NOT write the graph."""
    from jarvis.intelligence.knowledge_graph import extract_entities, extract_relationships

    entities = extract_entities(text)
    relationships = extract_relationships(text)
    for e in entities:
        e["kind"] = infer_kind(e.get("name") or "", e.get("kind") or "")
        e["confidence"] = 0.45
        e["source"] = source
    for r in relationships:
        r["confidence"] = 0.45
        r["source"] = source
        r["document"] = document
        r["project"] = project
    pending_id = uuid.uuid4().hex[:12]
    pending = {
        "id": pending_id,
        "created": _now(),
        "namespace": namespace or "default",
        "source": source,
        "document": document,
        "project": project,
        "text_preview": (text or "")[:400],
        "entities": entities,
        "relationships": relationships,
        "status": "pending",
    }
    items = _load_json(PENDING_FILE, [])
    if not isinstance(items, list):
        items = []
    items.insert(0, pending)
    _save_json(PENDING_FILE, items[:50])
    return {"ok": True, "pending": pending, "message": "Review and approve to persist — nothing written yet."}


def approve_pending_ingest(pending_id: str, *, selected_entities: list[str] | None = None, selected_rels: list[int] | None = None) -> dict[str, Any]:
    items = _load_json(PENDING_FILE, [])
    if not isinstance(items, list):
        return {"ok": False, "error": "no pending"}
    pending = next((p for p in items if p.get("id") == pending_id), None)
    if not pending:
        return {"ok": False, "error": "pending not found"}
    ns = pending.get("namespace") or "default"
    source = pending.get("source") or "ai_suggestion"
    ent_names = set(selected_entities) if selected_entities is not None else None
    rel_idxs = set(selected_rels) if selected_rels is not None else None
    created_n = 0
    created_r = 0
    for e in pending.get("entities") or []:
        name = e.get("name") or ""
        if ent_names is not None and name not in ent_names:
            continue
        create_entity(
            name,
            kind=e.get("kind") or "entity",
            namespace=ns,
            source=source,
            confidence=float(e.get("confidence") or 0.45),
            document=pending.get("document") or "",
            project=pending.get("project") or "",
        )
        created_n += 1
    for i, r in enumerate(pending.get("relationships") or []):
        if rel_idxs is not None and i not in rel_idxs:
            continue
        create_relationship(
            r.get("subject") or "",
            r.get("predicate") or "RELATED_TO",
            r.get("object") or "",
            namespace=ns,
            source=source,
            confidence=float(r.get("confidence") or 0.45),
            document=pending.get("document") or r.get("document") or "",
            project=pending.get("project") or r.get("project") or "",
        )
        created_r += 1
    pending["status"] = "approved"
    pending["approved_at"] = _now()
    _save_json(PENDING_FILE, items)
    _note_activity("ingest", {"pending_id": pending_id, "nodes": created_n, "edges": created_r})
    return {"ok": True, "nodes": created_n, "relationships": created_r}


def dismiss_pending_ingest(pending_id: str) -> dict[str, Any]:
    items = _load_json(PENDING_FILE, [])
    if not isinstance(items, list):
        return {"ok": False, "error": "no pending"}
    for p in items:
        if p.get("id") == pending_id:
            p["status"] = "dismissed"
            p["dismissed_at"] = _now()
            _save_json(PENDING_FILE, items)
            return {"ok": True}
    return {"ok": False, "error": "pending not found"}


def delete_entity(name: str, *, namespace: str = "default") -> dict[str, Any]:
    store = get_graph_store()
    result = store.delete_node(name, namespace=namespace)
    if result.get("ok"):
        uid = _push_undo("delete_node", result.get("snapshot") or {})
        result["undo_id"] = uid
        _note_activity("delete", {"name": name, "namespace": namespace})
    return result


def delete_relationship(edge_id: str) -> dict[str, Any]:
    store = get_graph_store()
    result = store.delete_edge(edge_id)
    if result.get("ok"):
        uid = _push_undo("delete_edge", result.get("snapshot") or {})
        result["undo_id"] = uid
        _note_activity("delete", {"edge_id": edge_id})
    return result


def prune_orphans(*, namespace: str = "") -> dict[str, Any]:
    store = get_graph_store()
    result = store.prune_orphans(namespace=namespace)
    if result.get("ok"):
        uid = _push_undo("prune", result.get("snapshot") or {})
        result["undo_id"] = uid
        _note_activity("prune", {"count": result.get("pruned"), "namespace": namespace})
    return result


def cleanup_queries_namespace() -> dict[str, Any]:
    """Remove pollution from the deprecated queries soft-ingest namespace."""
    store = get_graph_store()
    result = store.clear_namespace("queries")
    if result.get("ok"):
        uid = _push_undo("clear_namespace", result.get("snapshot") or {})
        result["undo_id"] = uid
        _note_activity("cleanup", {"namespace": "queries"})
    return result


def undo_last(undo_id: str = "") -> dict[str, Any]:
    items = _load_json(UNDO_FILE, [])
    if not isinstance(items, list) or not items:
        return {"ok": False, "error": "nothing to undo"}
    entry = None
    if undo_id:
        entry = next((i for i in items if i.get("id") == undo_id), None)
    else:
        entry = items[0]
    if not entry:
        return {"ok": False, "error": "undo entry not found"}
    snap = entry.get("snapshot") or {}
    store = get_graph_store()
    action = entry.get("action")
    restored = 0
    if action == "delete_node":
        node = snap.get("node") or {}
        if node.get("name"):
            store.merge_node(
                node["name"],
                kind=node.get("kind") or "entity",
                namespace=node.get("namespace") or "default",
                memory_id=node.get("memory_id") or "",
                props=node.get("props") or {},
            )
            restored += 1
        for e in snap.get("edges") or []:
            store.merge_relationship(
                e.get("subject") or "",
                e.get("predicate") or "RELATED_TO",
                e.get("object") or "",
                namespace=e.get("namespace") or "default",
                memory_id=e.get("memory_id") or "",
                props=e.get("props") or {},
            )
            restored += 1
    elif action == "delete_edge":
        e = snap.get("edge") or {}
        if e:
            store.merge_relationship(
                e.get("subject") or "",
                e.get("predicate") or "RELATED_TO",
                e.get("object") or "",
                namespace=e.get("namespace") or "default",
                memory_id=e.get("memory_id") or "",
                props=e.get("props") or {},
            )
            restored += 1
    elif action == "prune":
        for n in snap.get("nodes") or []:
            store.merge_node(
                n.get("name") or "",
                kind=n.get("kind") or "entity",
                namespace=n.get("namespace") or "default",
                memory_id=n.get("memory_id") or "",
                props=n.get("props") or {},
            )
            restored += 1
    elif action == "merge":
        drop = snap.get("drop") or {}
        if drop.get("name"):
            store.merge_node(
                drop["name"],
                kind=drop.get("kind") or "entity",
                namespace=drop.get("namespace") or "default",
                memory_id=drop.get("memory_id") or "",
                props=drop.get("props") or {},
            )
            restored += 1
    elif action == "clear_namespace":
        for n in snap.get("nodes") or []:
            store.merge_node(
                n.get("name") or "",
                kind=n.get("kind") or "entity",
                namespace=n.get("namespace") or "default",
                memory_id=n.get("memory_id") or "",
                props=n.get("props") or {},
            )
            restored += 1
        for e in snap.get("edges") or []:
            store.merge_relationship(
                e.get("subject") or "",
                e.get("predicate") or "RELATED_TO",
                e.get("object") or "",
                namespace=e.get("namespace") or "default",
                memory_id=e.get("memory_id") or "",
                props=e.get("props") or {},
            )
            restored += 1
    else:
        return {"ok": False, "error": f"unsupported undo action: {action}"}
    items = [i for i in items if i.get("id") != entry.get("id")]
    _save_json(UNDO_FILE, items)
    _note_activity("undo", {"undo_id": entry.get("id"), "restored": restored})
    return {"ok": True, "restored": restored}


def merge_entities(keep: str, drop: str, *, namespace: str = "default") -> dict[str, Any]:
    store = get_graph_store()
    preview = {
        "keep": store.get_node(keep, namespace=namespace) if hasattr(store, "get_node") else {"name": keep},
        "drop": store.get_node(drop, namespace=namespace) if hasattr(store, "get_node") else {"name": drop},
    }
    result = store.merge_entities(keep, drop, namespace=namespace)
    if result.get("ok"):
        uid = _push_undo("merge", result.get("snapshot") or preview)
        result["undo_id"] = uid
        result["preview"] = preview
        _note_activity("merge", {"keep": keep, "drop": drop})
    return result


def mirror_adopted_memory(candidate: dict[str, Any], *, memory_id: str = "") -> dict[str, Any]:
    """ACM adopt → graph mirror. Never the reverse."""
    from jarvis.relationship_memory import parse_relationship_link, extract_triples_heuristic

    content = (candidate.get("content") or "").strip()
    tags = [str(t).lower() for t in (candidate.get("tags") or [])]
    mid = memory_id or str(candidate.get("memory_id") or "")
    ns = candidate.get("namespace") or "relationships"
    conf = float(candidate.get("confidence") or 0.85)
    triples = parse_relationship_link(content)
    if not triples and ("relationship" in tags or any(t.startswith("pred:") for t in tags)):
        triples = extract_triples_heuristic(content)
    if not triples:
        # Single-fact mirror as RELATED_TO User only when tagged relationship
        if "relationship" not in tags and not any(t.startswith("pred:") for t in tags):
            return {"ok": True, "mirrored": 0, "skipped": "not a relationship candidate"}
        return {"ok": True, "mirrored": 0, "skipped": "no parseable triples"}
    count = 0
    for subj, pred, obj in triples:
        create_relationship(
            subj,
            pred,
            obj,
            namespace=ns,
            source="memory",
            confidence=conf,
            memory_id=mid,
        )
        count += 1
    return {"ok": True, "mirrored": count}


def project_namespace(slug: str) -> str:
    s = re.sub(r"[^a-z0-9_-]+", "-", (slug or "").strip().lower()).strip("-")
    return f"project:{s}" if s else "default"


def project_subgraph(slug: str, *, limit: int = 40) -> dict[str, Any]:
    ns = project_namespace(slug)
    store = get_graph_store()
    nodes = store.list_nodes(namespace=ns, limit=limit) if hasattr(store, "list_nodes") else []
    edges = store.list_edges(namespace=ns, limit=limit) if hasattr(store, "list_edges") else []
    return {"ok": True, "slug": slug, "namespace": ns, "nodes": nodes, "relationships": edges}


def relationship_assistant() -> dict[str, Any]:
    """Suggest improvements — never auto-modify."""
    store = get_graph_store()
    suggestions: list[dict[str, Any]] = []
    nodes = store.list_nodes(limit=200) if hasattr(store, "list_nodes") else []
    edges = store.list_edges(limit=200) if hasattr(store, "list_edges") else []
    # duplicates by normalized name across namespaces
    by_norm: dict[str, list] = {}
    for n in nodes:
        key = re.sub(r"\s+", " ", (n.get("name") or "").strip().lower())
        by_norm.setdefault(key, []).append(n)
    for key, group in by_norm.items():
        if len(group) > 1:
            suggestions.append(
                {
                    "type": "duplicate",
                    "message": f"Possible duplicate entities for “{group[0].get('name')}”",
                    "entities": group,
                    "action": "merge",
                }
            )
    for e in edges:
        if float(e.get("confidence") or 0) < 0.5:
            suggestions.append(
                {
                    "type": "low_confidence",
                    "message": f"Low confidence: {e.get('subject')} —{e.get('predicate')}→ {e.get('object')}",
                    "relationship": e,
                }
            )
        if (e.get("source") or "unknown") == "unknown" and not e.get("memory_id"):
            suggestions.append(
                {
                    "type": "missing_provenance",
                    "message": f"Missing provenance on {e.get('subject')} —{e.get('predicate')}→ {e.get('object')}",
                    "relationship": e,
                }
            )
    st = store.stats()
    if int(st.get("orphans") or 0) > 0:
        suggestions.append(
            {
                "type": "orphans",
                "message": f"{st['orphans']} orphan node(s) with no relationships",
                "action": "prune",
            }
        )
    return {"ok": True, "suggestions": suggestions[:40], "auto_modify": False}


def explain_relationship(subject: str, obj: str, *, namespace: str = "") -> dict[str, Any]:
    store = get_graph_store()
    rels = []
    for edge in store.neighbors(subject, depth=1, limit=50):
        if edge.get("object", "").lower() == obj.strip().lower() or edge.get("subject", "").lower() == obj.strip().lower():
            if not namespace or edge.get("namespace") == namespace:
                rels.append(edge)
    if not rels:
        return {"ok": False, "error": "no relationship found", "explanations": []}
    explanations = []
    for e in rels:
        prov = e.get("provenance") or {}
        explanations.append(
            {
                "relationship": e,
                "why": (
                    f"Connected as {e.get('predicate')} with source={prov.get('source') or e.get('source')}, "
                    f"confidence={prov.get('confidence', e.get('confidence'))}, "
                    f"memory_id={prov.get('memory_id') or e.get('memory_id') or 'none'}, "
                    f"document={prov.get('document') or e.get('document') or 'none'}."
                ),
                "confidence": e.get("confidence"),
                "provenance": prov,
                "conflicts": [],
            }
        )
    return {"ok": True, "explanations": explanations}


def chat_grounding_context(message: str, *, limit: int = 6, min_confidence: float = MIN_CHAT_CONFIDENCE) -> dict[str, Any]:
    """Ground chat only with high-confidence, provenance-backed relationships."""
    from jarvis.relationship_memory import parse_relationship_recall_query, _entity_tokens

    store = get_graph_store()
    if int((store.stats() or {}).get("nodes") or 0) == 0:
        return {"ok": True, "context": "", "triples": [], "used": False}
    q = parse_relationship_recall_query(message) or ""
    tokens = _entity_tokens(message)
    if q:
        tokens = [q] + tokens
    if not tokens:
        return {"ok": True, "context": "", "triples": [], "used": False}
    raw = store.related_triples(tokens[:4], depth=1, limit=limit * 3) if hasattr(store, "related_triples") else []
    trusted = []
    for t in raw:
        conf = float(t.get("confidence") or 0)
        src = (t.get("source") or (t.get("provenance") or {}).get("source") or "unknown")
        mid = t.get("memory_id") or (t.get("provenance") or {}).get("memory_id") or ""
        if conf < min_confidence:
            continue
        if src in ("unknown", "") and not mid:
            continue
        trusted.append(t)
        if len(trusted) >= limit:
            break
    if not trusted:
        return {"ok": True, "context": "", "triples": [], "used": False}
    lines = []
    for t in trusted:
        prov = t.get("provenance") or {}
        why = f"source={prov.get('source') or t.get('source')}, confidence={t.get('confidence')}"
        lines.append(
            f"- {t['subject']} —[{t['predicate']}]→ {t['object']} ({why})"
        )
    block = (
        "Trusted Connections (relationship layer — not autobiographical Memory; "
        "only use when relevant; cite provenance):\n" + "\n".join(lines)
    )
    return {"ok": True, "context": block, "triples": trusted, "used": True}


def format_recall_markdown(result: dict[str, Any]) -> str:
    triples = result.get("triples") or []
    if not triples:
        return "_No trusted connections found._"
    lines = ["**Connections** (mirrored relationships — ACM remains cognitive SoT):"]
    for t in triples:
        prov = t.get("provenance") or {}
        lines.append(
            f"• **{t.get('subject')}** —{t.get('predicate')}→ **{t.get('object')}** "
            f"_(source: {prov.get('source') or t.get('source')}, "
            f"confidence: {t.get('confidence')})_"
        )
    return "\n".join(lines)
