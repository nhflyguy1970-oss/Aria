"""Knowledge graph platform helpers — extract + explicit ingest API.

Writes require provenance. Query soft-ingest is forbidden.
Prefer jarvis.connections_services for product flows (review → approve).
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger("jarvis.intelligence.knowledge_graph")

_ENTITY_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}|[A-Z]{2,}(?:\s+[A-Z]{2,})?)\b"
)
_REL_PATTERNS = (
    (re.compile(r"(.+?)\s+(?:is|are)\s+(?:a|an|the)?\s*(.+)", re.I), "IS_A"),
    (re.compile(r"(.+?)\s+(?:works at|works for)\s+(.+)", re.I), "WORKS_AT"),
    (re.compile(r"(.+?)\s+(?:owns|has)\s+(.+)", re.I), "HAS"),
    (re.compile(r"(.+?)\s+(?:related to|connected to)\s+(.+)", re.I), "RELATED_TO"),
    (re.compile(r"(.+?)\s+(?:uses|depends on)\s+(.+)", re.I), "USES"),
)


def extract_entities(text: str, *, limit: int = 24) -> list[dict[str, str]]:
    """Lightweight entity extraction (capitalized spans + tags)."""
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in _ENTITY_RE.finditer(text or ""):
        name = m.group(1).strip()
        if len(name) < 2 or name.lower() in seen:
            continue
        if name.lower() in {"the", "this", "that", "when", "where", "what", "aria", "i"}:
            continue
        seen.add(name.lower())
        kind = "acronym" if name.isupper() else "entity"
        found.append({"name": name, "kind": kind})
        if len(found) >= limit:
            break
    return found


def extract_relationships(text: str, *, limit: int = 20) -> list[dict[str, str]]:
    rels: list[dict[str, str]] = []
    for line in re.split(r"[\n.]+", text or ""):
        line = line.strip()
        if len(line) < 8:
            continue
        for pat, pred in _REL_PATTERNS:
            m = pat.search(line)
            if not m:
                continue
            subj = m.group(1).strip()[:80]
            obj = m.group(2).strip()[:80]
            if subj and obj:
                rels.append({"subject": subj, "predicate": pred, "object": obj})
            if len(rels) >= limit:
                return rels
    return rels


def get_store():
    from jarvis.modules.graph_store import get_graph_store

    return get_graph_store()


def ingest_text(
    text: str,
    *,
    namespace: str = "default",
    memory_id: str = "",
    source: str = "manual",
    confidence: float = 0.7,
    document: str = "",
    project: str = "",
    explicit: bool = True,
) -> dict[str, Any]:
    """Merge extracted entities/relationships.

    Requires explicit=True (default). Soft/query ingest is rejected.
    Prefer connections_services.propose_ingest_from_text + approve for UI flows.
    """
    if not explicit:
        return {
            "ok": False,
            "error": "implicit_ingest_forbidden",
            "message": "Graph writes require explicit approval. Use Connections review → approve.",
        }
    if namespace == "queries":
        return {
            "ok": False,
            "error": "queries_namespace_forbidden",
            "message": "Query soft-ingest is disabled to prevent graph pollution.",
        }
    if (source or "unknown") in ("", "unknown") and not memory_id:
        source = "manual"
    entities = extract_entities(text)
    relationships = extract_relationships(text)
    store = get_store()
    props_base = {
        "source": source,
        "confidence": float(confidence),
        "document": document or "",
        "project": project or "",
    }
    node_ids: list[str] = []
    rel_ids: list[str] = []
    for ent in entities:
        try:
            nid = store.merge_node(
                ent["name"],
                kind=ent.get("kind") or "entity",
                namespace=namespace,
                memory_id=memory_id,
                props=props_base,
            )
            node_ids.append(nid)
        except Exception as exc:
            log.debug("merge_node failed: %s", exc)
    for rel in relationships:
        try:
            rid = store.merge_relationship(
                rel["subject"],
                rel["predicate"],
                rel["object"],
                namespace=namespace,
                memory_id=memory_id,
                props=props_base,
            )
            rel_ids.append(rid)
        except Exception as exc:
            log.debug("merge_relationship failed: %s", exc)
    return {
        "ok": True,
        "entities": entities,
        "relationships": relationships,
        "nodes_merged": len(node_ids),
        "rels_merged": len(rel_ids),
        "stats": store.stats() if hasattr(store, "stats") else {},
    }


def search_graph(query: str, *, limit: int = 12, namespace: str = "") -> dict[str, Any]:
    store = get_store()
    if hasattr(store, "search_nodes"):
        try:
            nodes = store.search_nodes(query, limit=limit, namespace=namespace)
        except TypeError:
            nodes = store.search_nodes(query, limit=limit)
    else:
        nodes = []
    triples: list[dict] = []
    names = [n.get("name") or n.get("id") for n in nodes if isinstance(n, dict)]
    names = [n for n in names if n]
    if names and hasattr(store, "related_triples"):
        triples = store.related_triples(names, limit=limit)
    return {
        "ok": True,
        "query": query,
        "nodes": nodes,
        "triples": triples,
        "backend": getattr(store, "backend", "unknown"),
        "stats": store.stats() if hasattr(store, "stats") else {},
    }


def neighbors(name: str, *, depth: int = 1, limit: int = 24) -> dict[str, Any]:
    store = get_store()
    return {
        "ok": True,
        "name": name,
        "neighbors": store.neighbors(name, depth=depth, limit=limit),
        "backend": getattr(store, "backend", "unknown"),
    }
