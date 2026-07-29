"""Unified ranking service — one place for score fusion."""

from __future__ import annotations

import re
import time
from typing import Any


def _keyword_overlap(query: str, text: str) -> float:
    q_tokens = set(re.findall(r"[a-z0-9_]{2,}", (query or "").lower()))
    if not q_tokens:
        return 0.0
    t = (text or "").lower()
    hits = sum(1 for tok in q_tokens if tok in t)
    return hits / max(1, len(q_tokens))


def rank_results(
    results: list[dict[str, Any]],
    *,
    query: str,
    intent: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    history_boost: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Re-score and sort SearchResults. Mutates score/confidence in copies."""
    intent = intent or {}
    context = context or {}
    history_boost = history_boost or {}
    primary = intent.get("primary") or ""
    project = str(context.get("project") or "").lower()
    view = str(context.get("view") or "").lower()
    now = time.time()

    ranked: list[dict[str, Any]] = []
    for hit in results:
        h = dict(hit)
        base = float(h.get("score") or 0.5)
        text = f"{h.get('title', '')} {h.get('summary', '')} {h.get('preview', '')}"
        kw = _keyword_overlap(query, text)
        strategy = str(h.get("strategy") or "")
        semantic_bonus = 0.08 if strategy in ("semantic", "acm_authority", "hybrid") else 0.0
        intent_bonus = 0.12 if h.get("source") == primary else 0.0
        if primary == "everything":
            intent_bonus = 0.0
        view_bonus = 0.06 if view and view in str(h.get("open", {}).get("view") or "") else 0.0
        project_bonus = 0.05 if project and project in text.lower() else 0.0
        hist = float(history_boost.get(str(h.get("source") or ""), 0.0))
        # Soft recency if metadata has timestamp
        recency = 0.0
        ts = (h.get("metadata") or {}).get("timestamp") or (h.get("metadata") or {}).get("indexed")
        if ts:
            try:
                # ISO-ish or epoch
                if isinstance(ts, (int, float)):
                    age = max(0.0, now - float(ts))
                else:
                    from datetime import datetime

                    age = max(0.0, now - datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp())
                recency = max(0.0, 0.1 - min(age, 86400 * 30) / (86400 * 30) * 0.1)
            except Exception:
                recency = 0.0
        fused = (
            base * 0.55
            + kw * 0.22
            + semantic_bonus
            + intent_bonus
            + view_bonus
            + project_bonus
            + min(0.1, hist)
            + recency
        )
        fused = max(0.0, min(1.0, fused))
        h["score"] = round(fused, 4)
        h["confidence"] = round(min(0.99, fused * 0.9 + 0.05), 4)
        h["metadata"] = {
            **(h.get("metadata") or {}),
            "rank_components": {
                "base": round(base, 4),
                "keyword": round(kw, 4),
                "semantic_bonus": semantic_bonus,
                "intent_bonus": intent_bonus,
                "view_bonus": view_bonus,
                "project_bonus": project_bonus,
                "history": round(hist, 4),
                "recency": round(recency, 4),
            },
        }
        # Highlight query tokens present in title/preview
        tokens = re.findall(r"[a-z0-9_]{3,}", (query or "").lower())[:6]
        highlights = [t for t in tokens if t in text.lower()]
        if highlights:
            h["highlights"] = highlights
        ranked.append(h)

    ranked.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
    return ranked


def dedupe_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop near-duplicates by source+title+location fingerprint."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for h in results:
        key = f"{h.get('source')}|{(h.get('title') or '').lower()}|{(h.get('location') or '').lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out
