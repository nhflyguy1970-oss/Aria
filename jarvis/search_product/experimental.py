"""Experimental Search features — researched carefully, gated."""

from __future__ import annotations

from typing import Any

from jarvis.search_product.intent import classify_intent
from jarvis.search_product.pipeline import run_search


def experimental_status() -> dict[str, Any]:
    return {
        "ok": True,
        "features": [
            {
                "id": "answer_vs_browse",
                "name": "Answer vs Browse mode",
                "status": "available",
                "note": "Auto mode picks answer when query is question-like; browse for find/list.",
            },
            {
                "id": "agent_multihop",
                "name": "Agent multi-hop",
                "status": "stub",
                "note": "Agents should call run_search repeatedly; no second engine.",
            },
            {
                "id": "voice_demo",
                "name": "Voice search demo",
                "status": "bridge",
                "note": "Use Voice product STT → /api/search/product/query.",
            },
            {
                "id": "vision_similarity",
                "name": "Vision similarity search",
                "status": "opt_in",
                "note": "Requires Gallery opt-in corpus; Vision supplies text/embedding hints.",
            },
            {
                "id": "adaptive_ranking",
                "name": "Adaptive ranking",
                "status": "partial",
                "note": "History facet frequency already soft-boosts ranking.",
            },
        ],
    }


def answer_vs_browse(query: str) -> dict[str, Any]:
    intent = classify_intent(query)
    mode = "answer" if intent.get("answer_leaning") and not intent.get("browse_leaning") else "browse"
    result = run_search(query, mode=mode, limit=8)
    return {
        "ok": True,
        "recommended_mode": mode,
        "intent": intent,
        "search": result,
        "chat_handoff": mode == "answer",
    }
