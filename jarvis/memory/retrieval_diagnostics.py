"""Memory retrieval diagnostics — measure ranking without schema changes.

Records candidate scores (keyword/semantic/recency/type) and the selected winner
for Conversation Trace and Mission Control. Never stores memory contents in
the Mission Control history path.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from jarvis.modules.memory_common import (
    is_fact_question,
    is_journal_entry,
    is_user_facing_entry,
    keyword_score,
    normalize_memory_query,
    relevance_score,
    type_rank_boost,
)

_LOCK = threading.Lock()
_LAST: dict[str, Any] | None = None
_RECENT: list[dict[str, Any]] = []
_RECENT_LIMIT = 80


def _recency_score(entry: dict) -> float:
    from datetime import UTC, datetime

    from jarvis.modules.memory_common import parse_ts

    age_days = max(0, (datetime.now(UTC) - parse_ts(entry.get("timestamp", ""))).days)
    return max(0.25, 1.0 - age_days * 0.008)


def _focus_score(entry: dict, query_lower: str) -> float:
    """Prefer short topic-focused facts over long journal megablobs."""
    content = (entry.get("content") or "").strip()
    if not content:
        return 0.0
    length = len(content)
    # Tight facts (~<120 chars) score highest; megablobs decay.
    focus = 1.0 if length <= 120 else max(0.2, 1.0 - (length - 120) / 500.0)
    if is_journal_entry(entry):
        focus *= 0.35
    # Bonus when the query is a large share of the content footprint.
    if query_lower and query_lower in content.lower():
        share = min(1.0, len(query_lower) / max(1, length))
        focus += 0.15 * share
    return focus


def _semantic_score(entry: dict, query: str, get_embedding, set_embedding) -> float:
    from jarvis import llm

    if not llm.embed_available():
        return 0.0
    query_emb = llm.embed_text(query)
    if not query_emb:
        return 0.0
    emb = get_embedding(entry) if get_embedding else entry.get("embedding") or []
    if not emb:
        emb = llm.embed_text(entry.get("content") or "")
        if set_embedding and emb:
            set_embedding(entry, emb)
    if not emb:
        return 0.0
    return float(llm.cosine_similarity(query_emb, emb))


def score_candidate(
    entry: dict,
    query: str,
    *,
    get_embedding=None,
    set_embedding=None,
    include_semantic: bool = False,
) -> dict[str, Any]:
    q = normalize_memory_query(query).lower().strip() or (query or "").lower().strip()
    kw = keyword_score(entry, q)
    recency = _recency_score(entry)
    focus = _focus_score(entry, q)
    type_boost = type_rank_boost(entry)
    semantic = (
        _semantic_score(entry, q or query, get_embedding, set_embedding)
        if include_semantic and kw <= 0
        else 0.0
    )
    # Composite: keyword dominates when present; otherwise semantic; always apply focus/type/recency.
    base = kw * 10.0 if kw > 0 else semantic * 8.0
    total = (base + relevance_score(entry)) * focus * (1.0 if kw > 0 or semantic > 0.3 else 0.5)
    return {
        "id": entry.get("id"),
        "type": entry.get("type"),
        "keyword_score": round(kw, 4),
        "semantic_score": round(semantic, 4),
        "recency_score": round(recency, 4),
        "focus_score": round(focus, 4),
        "type_boost": round(type_boost, 4),
        "relevance_score": round(relevance_score(entry), 4),
        "total_score": round(total, 4),
        "content_len": len(entry.get("content") or ""),
        "journal": is_journal_entry(entry),
        "user_facing": is_user_facing_entry(entry),
    }


def rank_for_query(
    entries: list[dict],
    query: str,
    *,
    intent: str = "memory_search",
    limit: int = 10,
    fact_mode: bool | None = None,
    get_embedding=None,
    set_embedding=None,
) -> tuple[list[dict], dict[str, Any]]:
    """Rank candidates and return (hits, diagnostics_public). Never embeds content in diagnostics."""
    t0 = time.perf_counter()
    fact_mode = is_fact_question(query) if fact_mode is None else fact_mode
    pool = [e for e in entries if is_user_facing_entry(e)]
    if fact_mode:
        # Fact answers prefer typed facts/preferences — not journal notes.
        pool = [
            e
            for e in pool
            if e.get("type") in ("fact", "preference") and not is_journal_entry(e)
        ] or [e for e in pool if not is_journal_entry(e)] or pool

    scored: list[tuple[float, dict, dict]] = []
    keyword_any = any(
        keyword_score(e, normalize_memory_query(query).lower().strip() or query.lower()) > 0
        for e in pool
    )
    for e in pool:
        detail = score_candidate(
            e,
            query,
            get_embedding=get_embedding,
            set_embedding=set_embedding,
            include_semantic=not keyword_any,
        )
        if detail["total_score"] <= 0 and detail["keyword_score"] <= 0 and detail["semantic_score"] <= 0:
            continue
        if keyword_any and detail["keyword_score"] <= 0:
            continue
        scored.append((detail["total_score"], e, detail))

    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [e for _, e, _ in scored[:limit]]
    selected = scored[0] if scored else None
    rejected = [
        {
            "id": d["id"],
            "type": d["type"],
            "total_score": d["total_score"],
            "reason_rejected": _reject_reason(d, selected[2] if selected else None),
        }
        for _, _, d in scored[1:6]
    ]
    ranking_ms = round((time.perf_counter() - t0) * 1000, 3)
    decision = {
        "query": (query or "")[:120],
        "normalized_query": normalize_memory_query(query)[:120],
        "intent": intent,
        "fact_mode": fact_mode,
        "candidate_count": len(pool),
        "ranked_count": len(scored),
        "selected_id": selected[2]["id"] if selected else None,
        "selected_type": selected[2]["type"] if selected else None,
        "selected_scores": (
            {
                k: selected[2][k]
                for k in (
                    "keyword_score",
                    "semantic_score",
                    "recency_score",
                    "focus_score",
                    "type_boost",
                    "total_score",
                )
            }
            if selected
            else None
        ),
        "reason_selected": (
            "highest composite score (keyword×focus×type, journal demoted)"
            if selected
            else "no candidates"
        ),
        "rejected": rejected,
        "ranking_latency_ms": ranking_ms,
        "confidence": min(1.0, (selected[2]["total_score"] / 40.0) if selected else 0.0),
    }
    _store_decision(decision)
    _emit_core(decision)
    return hits, decision


def _reject_reason(detail: dict, winner: dict | None) -> str:
    if not winner:
        return "not selected"
    if detail.get("journal") and not winner.get("journal"):
        return "journal demoted below focused fact"
    if detail.get("total_score", 0) < winner.get("total_score", 0):
        return "lower composite score"
    return "not top ranked"


def _store_decision(decision: dict[str, Any]) -> None:
    global _LAST
    with _LOCK:
        _LAST = dict(decision)
        _RECENT.append(dict(decision))
        if len(_RECENT) > _RECENT_LIMIT:
            del _RECENT[: len(_RECENT) - _RECENT_LIMIT]


def _emit_core(decision: dict[str, Any]) -> None:
    try:
        from aria_core import memory_manager as mm

        mm.record_retrieval_decision(decision)
    except Exception:
        pass


def last_retrieval_decision() -> dict[str, Any] | None:
    with _LOCK:
        return dict(_LAST) if _LAST else None


def recent_retrieval_decisions(*, limit: int = 40) -> list[dict[str, Any]]:
    with _LOCK:
        return [dict(d) for d in _RECENT[-limit:]]


def attach_decision_to_intent(intent: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    """Public metadata for Conversation Trace (no contents)."""
    out = dict(intent)
    out["memory_retrieval"] = {
        "intent": decision.get("intent"),
        "normalized_query": decision.get("normalized_query"),
        "selected_id": decision.get("selected_id"),
        "selected_type": decision.get("selected_type"),
        "candidate_count": decision.get("candidate_count"),
        "confidence": decision.get("confidence"),
        "ranking_latency_ms": decision.get("ranking_latency_ms"),
        "reason_selected": decision.get("reason_selected"),
        "rejected_ids": [r.get("id") for r in (decision.get("rejected") or [])],
        "rejected_reasons": [r.get("reason_rejected") for r in (decision.get("rejected") or [])],
    }
    return out
