"""Relationship memory — knowledge graph of entities and connections."""

from __future__ import annotations

import json
import logging
import os
import re

from jarvis import llm
from jarvis.modules.graph_store import get_graph_store

logger = logging.getLogger("jarvis.relationship_memory")

RELATIONSHIP_NAMESPACE = "relationships"

_PREDICATE_ALIASES = {
    "work on": "WORKS_ON",
    "works on": "WORKS_ON",
    "working on": "WORKS_ON",
    "use": "USES",
    "uses": "USES",
    "using": "USES",
    "prefer": "PREFERS",
    "prefers": "PREFERS",
    "know": "KNOWS",
    "knows": "KNOWS",
    "live in": "LIVES_IN",
    "lives in": "LIVES_IN",
    "part of": "PART_OF",
    "is part of": "PART_OF",
    "member of": "MEMBER_OF",
    "related to": "RELATED_TO",
    "connected to": "RELATED_TO",
    "owns": "OWNS",
    "manage": "MANAGES",
    "manages": "MANAGES",
    "built with": "USES",
    "runs on": "RUNS_ON",
    "depends on": "DEPENDS_ON",
}

_LINK_ARROW = re.compile(
    r"^(?:please\s+)?(?:link|connect)\s+(.+?)\s*(?:->|→)\s*([A-Z_][A-Z0-9_]*)\s*(?:->|→)\s*(.+)$",
    re.I,
)
_LINK_VERB = re.compile(
    r"^(?:please\s+)?(?:link|connect|remember)\s+(.+?)\s+"
    r"(works on|work on|uses|use|prefers|prefer|knows|know|lives in|live in|"
    r"is part of|part of|member of|related to|connected to|owns|manages|manage|"
    r"built with|runs on|depends on)\s+(.+)$",
    re.I,
)
_IS_A_OF = re.compile(
    r"^(?:remember\s+)?(.+?)\s+is\s+(?:a|an)\s+(.+?)\s+(?:of|for|at)\s+(.+)$",
    re.I,
)
_RECALL = re.compile(
    r"\b(?:connections?|relationships?|graph|linked to|connected to)\s+(?:for|of|about|with)\s+(.+)$"
    r"|\bwhat(?:'s| is)\s+connected to\s+(.+)$"
    r"|\bwho\s+(?:works on|uses|knows)\s+(.+)$",
    re.I,
)

_HEURISTIC_RULES: list[tuple[re.Pattern[str], str, int, int]] = [
    (re.compile(r"\b(?:user|the user)\s+prefers?\s+(.+)", re.I), "PREFERS", 0, 1),
    (re.compile(r"\b(?:user|the user)\s+uses?\s+(.+)", re.I), "USES", 0, 1),
    (re.compile(r"\b(?:user|the user)\s+works?\s+on\s+(.+)", re.I), "WORKS_ON", 0, 1),
    (re.compile(r"\bproject\s+[`'\"]?(\w[\w-]*)[`'\"]?", re.I), "WORKS_ON", 0, 1),
    (re.compile(r"\b(.+?)\s+runs?\s+(?:on|locally on)\s+(.+)", re.I), "RUNS_ON", 0, 1),
    (re.compile(r"\b(.+?)\s+depends?\s+on\s+(.+)", re.I), "DEPENDS_ON", 0, 1),
]


def _subject_default(name: str = "User") -> str:
    return name


def normalize_predicate(raw: str) -> str:
    key = (raw or "").strip().lower()
    return _PREDICATE_ALIASES.get(key, re.sub(r"[^A-Za-z0-9_]+", "_", key.upper()) or "RELATED_TO")


def parse_relationship_link(text: str) -> list[tuple[str, str, str]]:
    """Parse explicit link commands → [(subject, predicate, object)]."""
    raw = (text or "").strip()
    if not raw:
        return []
    m = _LINK_ARROW.match(raw)
    if m:
        return [(m.group(1).strip(), normalize_predicate(m.group(2)), m.group(3).strip())]
    m = _LINK_VERB.match(raw)
    if m:
        return [(m.group(1).strip(), normalize_predicate(m.group(2)), m.group(3).strip())]
    m = _IS_A_OF.match(raw)
    if m:
        return [(m.group(1).strip(), "MEMBER_OF", m.group(3).strip())]
    return []


def parse_relationship_recall_query(message: str) -> str:
    m = _RECALL.search((message or "").strip())
    if not m:
        return ""
    return (m.group(1) or m.group(2) or "").strip()


def extract_triples_heuristic(content: str, *, default_subject: str = "User") -> list[tuple[str, str, str]]:
    text = (content or "").strip()
    if not text:
        return []
    triples: list[tuple[str, str, str]] = []
    for pat, pred, sub_g, obj_g in _HEURISTIC_RULES:
        m = pat.search(text)
        if not m:
            continue
        subj = m.group(sub_g).strip() if sub_g else default_subject
        obj = m.group(obj_g).strip() if obj_g else ""
        if subj and obj:
            if subj.lower() in ("user", "the user"):
                subj = default_subject
            triples.append((subj, pred, obj.rstrip(".")))
    return triples


def extract_triples_llm(content: str) -> list[tuple[str, str, str]]:
    if not content or len(content) < 12:
        return []
    prompt = (
        "Extract entity relationships as JSON. Each triple: subject, predicate (SCREAMING_SNAKE), object. "
        "Only durable connections (people, projects, tools, places). Max 3 triples. "
        'Return {"triples":[{"subject":"...","predicate":"WORKS_ON","object":"..."}]}. '
        "Empty array if none.\n\n"
        f"Text:\n{content}"
    )
    try:
        raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}]).strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        out: list[tuple[str, str, str]] = []
        for item in data.get("triples") or []:
            if not isinstance(item, dict):
                continue
            s = str(item.get("subject") or "").strip()
            p = normalize_predicate(str(item.get("predicate") or "RELATED_TO"))
            o = str(item.get("object") or "").strip()
            if s and o:
                out.append((s, p, o))
        return out[:3]
    except Exception as exc:
        logger.debug("LLM triple extract failed: %s", exc)
        return []


def record_link(
    subject: str,
    predicate: str,
    obj: str,
    *,
    namespace: str = RELATIONSHIP_NAMESPACE,
    memory_id: str = "",
) -> dict:
    graph = get_graph_store()
    graph.merge_relationship(
        subject,
        predicate,
        obj,
        namespace=namespace,
        memory_id=memory_id,
    )
    return {
        "subject": subject.strip(),
        "predicate": normalize_predicate(predicate),
        "object": obj.strip(),
        "namespace": namespace,
    }


def record_links(
    triples: list[tuple[str, str, str]],
    *,
    namespace: str = RELATIONSHIP_NAMESPACE,
    memory_id: str = "",
) -> list[dict]:
    stored: list[dict] = []
    for subject, predicate, obj in triples:
        if subject.strip() and obj.strip():
            stored.append(
                record_link(subject, predicate, obj, namespace=namespace, memory_id=memory_id)
            )
    return stored


def sync_memory_entry(entry: dict) -> list[dict]:
    """Extract and store relationships when a memory entry is added."""
    if not entry or entry.get("type") in ("failure", "success", "auto"):
        return []
    content = (entry.get("content") or "").strip()
    if len(content) < 8:
        return []
    memory_id = str(entry.get("id") or "")
    namespace = entry.get("namespace") or RELATIONSHIP_NAMESPACE
    triples = extract_triples_heuristic(content)
    if os.getenv("JARVIS_GRAPH_LLM_EXTRACT", "").strip().lower() in ("1", "true", "yes"):
        triples.extend(extract_triples_llm(content))
    if not triples:
        return []
  # dedupe
    seen: set[tuple[str, str, str]] = set()
    unique: list[tuple[str, str, str]] = []
    for t in triples:
        key = (t[0].lower(), t[1], t[2].lower())
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return record_links(unique, namespace=namespace, memory_id=memory_id)


def recall_relationships(query: str, *, limit: int = 12) -> dict:
    graph = get_graph_store()
    q = (query or "").strip()
    nodes = graph.search_nodes(q, limit=6) if q else []
    names = [n["name"] for n in nodes]
    if q and q not in names:
        names.insert(0, q)
    triples = graph.related_triples(names[:4], depth=2, limit=limit) if names else []
    if not triples and q:
        triples = graph.neighbors(q, depth=2, limit=limit)
    return {
        "query": q,
        "nodes": nodes,
        "triples": triples,
        "stats": graph.stats(),
        "backend": graph.backend,
    }


def relationship_stats() -> dict:
    graph = get_graph_store()
    return {"backend": graph.backend, **graph.stats()}


def _entity_tokens(message: str) -> list[str]:
    words = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?|\b[a-z]{4,}\b", message or "")
    stop = {
        "what", "when", "where", "which", "about", "help", "please", "could",
        "would", "should", "there", "their", "this", "that", "with", "from",
        "have", "been", "being", "your", "mine", "does", "doing",
    }
    return [w for w in words if w.lower() not in stop][:6]


def relationship_context_for_chat(message: str, *, limit: int = 8) -> str:
    """Inject relevant subgraph when message mentions known entities."""
    graph = get_graph_store()
    if graph.stats().get("nodes", 0) == 0:
        return ""
    tokens = _entity_tokens(message)
    if not tokens:
        return ""
    triples = graph.related_triples(tokens, depth=1, limit=limit)
    if not triples:
        for token in tokens:
            hits = graph.search_nodes(token, limit=2)
            if hits:
                triples = graph.neighbors(hits[0]["name"], depth=1, limit=limit)
                break
    if not triples:
        return ""
    lines = [
        f"- {t['subject']} —[{t['predicate']}]→ {t['object']}"
        for t in triples[:limit]
    ]
    return "Known relationships (use as grounded context):\n" + "\n".join(lines)


def format_triples_markdown(triples: list[dict]) -> str:
    if not triples:
        return "_No connections found._"
    return "\n".join(
        f"• **{t['subject']}** —{t['predicate']}→ **{t['object']}**"
        for t in triples
    )
