"""Shared memory store helpers (search, scoring, parsing)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Callable

from jarvis import llm

MEMORY_TYPES = ("fact", "auto", "note", "preference", "project", "failure", "success", "strategy", "teaching")
DEFAULT_NAMESPACE = "default"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def to_public(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if k != "embedding"}


def relevance_score(entry: dict) -> float:
    base = float(entry.get("relevance", 1.0))
    age_days = max(0, (datetime.now(timezone.utc) - parse_ts(entry.get("timestamp", ""))).days)
    decay = max(0.25, 1.0 - age_days * 0.008)
    access_boost = min(0.4, int(entry.get("access_count", 0)) * 0.04)
    type_penalty = 0.85 if entry.get("type") == "auto" else 1.0
    return (base * decay + access_boost) * type_penalty


def keyword_score(entry: dict, query_lower: str) -> float:
    content = entry.get("content", "").lower()
    tags = " ".join(entry.get("tags") or []).lower()
    if query_lower in content:
        return 3.0 + content.count(query_lower) * 0.1
    words = [w for w in re.split(r"\W+", query_lower) if len(w) > 2]
    if words and all(w in content or w in tags for w in words):
        return 2.0
    if any(query_lower in t.lower() for t in entry.get("tags", [])):
        return 1.5
    return 0.0


def normalize_entry(entry: dict, index: int = 0) -> dict:
    entry.setdefault("id", f"m{index}")
    entry.setdefault("namespace", DEFAULT_NAMESPACE)
    if isinstance(entry.get("tags"), str):
        try:
            entry["tags"] = json.loads(entry["tags"])
        except json.JSONDecodeError:
            entry["tags"] = []
    entry.setdefault("tags", [])
    entry.setdefault("access_count", 0)
    entry.setdefault("relevance", 1.0)
    entry.setdefault("timestamp", utc_now())
    if entry.get("type") not in MEMORY_TYPES:
        entry["type"] = "note"
    return entry


def search_pool(
    pool: list[dict],
    query: str,
    limit: int,
    *,
    namespace: str | None,
    get_embedding: Callable[[dict], list[float]],
    set_embedding: Callable[[dict, list[float]], None],
    touch: Callable[[str], None],
    flush_touches: Callable[[], None],
) -> list[dict]:
    query_lower = query.lower().strip()
    if namespace:
        pool = [e for e in pool if e.get("namespace") == namespace]

    keyword_matches = [e for e in pool if keyword_score(e, query_lower) > 0]
    if keyword_matches:
        ranked = sorted(
            keyword_matches,
            key=lambda e: (keyword_score(e, query_lower), relevance_score(e)),
            reverse=True,
        )
        results = ranked[:limit]
        for e in results:
            touch(e["id"])
        flush_touches()
        return [to_public(e) for e in results]

    if not llm.embed_available():
        return []

    query_emb = llm.embed_text(query)
    if not query_emb:
        return []

    scored: list[tuple[float, dict]] = []
    for e in pool:
        emb = get_embedding(e)
        if not emb:
            emb = llm.embed_text(e["content"])
            set_embedding(e, emb)
        sim = llm.cosine_similarity(query_emb, emb)
        if sim > 0.3:
            scored.append((sim * relevance_score(e), e))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [e for _, e in scored[:limit]]
    for e in results:
        touch(e["id"])
    flush_touches()
    return [to_public(e) for e in results]


def parse_remember(text: str) -> tuple[str, str, str | None]:
    text = (text or "").replace("\r\n", "\n").strip()
    lower = text.lower()
    namespace = None
    if m := re.search(r"\b(?:in|for)\s+(?:namespace|project)\s+[`'\"]?(\w[\w-]*)[`'\"]?", lower):
        namespace = m.group(1)
        text = re.sub(
            r"\b(?:in|for)\s+(?:namespace|project)\s+[`'\"]?\w[\w-]*[`'\"]?\s*",
            "",
            text,
            flags=re.I,
        )
    for prefix in (
        r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
        r"^(these|the following)\s+facts?\s*:?\s*",
        r"^facts?\s*:?\s*",
    ):
        text = re.sub(prefix, "", text, flags=re.I).strip()
    entry_type = "fact"
    if re.search(r"\b(preference|prefer)\b", lower):
        entry_type = "preference"
    elif re.search(r"\b(project|codename)\b", lower):
        entry_type = "project"
    return text.strip(), entry_type, namespace


def split_remember_facts(content: str) -> list[str]:
    text = (content or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    skip = re.compile(
        r"^(do not summarize|just reply|reply with|no summary|stored\.?)\b",
        re.I,
    )
    lines = [ln for ln in lines if not skip.search(ln)]
    if len(lines) >= 2:
        return lines
    return [text] if text else []
