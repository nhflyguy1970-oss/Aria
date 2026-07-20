"""Nightly memory consolidation — distill branch/auto memories into durable facts."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime, timedelta

from jarvis import llm

log = logging.getLogger("jarvis.memory_consolidation")

_CONSOLIDATION_TAG = "brain-consolidated"


def _recent_cutoff(days: int = 2) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def _collect_source_entries(memory_store, *, limit: int = 40) -> list[dict]:
    cutoff = _recent_cutoff()
    sources: list[dict] = []
    for e in memory_store.list_entries(entry_type="auto"):
        if (e.get("timestamp") or "") >= cutoff:
            sources.append(e)
    for e in memory_store.list_entries(entry_type="note"):
        tags = e.get("tags") or []
        if "branch-summary" in tags and (e.get("timestamp") or "") >= cutoff:
            sources.append(e)
    sources.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return sources[:limit]


def _distill_facts(blob: str, *, max_facts: int = 6) -> list[str]:
    if not blob.strip():
        return []
    prompt = (
        "Distill durable user facts from these memory notes. "
        "Merge duplicates. Skip transient chat, questions, and one-off tasks. "
        "Each fact: one complete sentence about the user. "
        f"Max {max_facts} facts. "
        'Return JSON only: {"facts": ["..."]}.\n\n'
        f"Notes:\n{blob[:6000]}"
    )
    try:
        raw = llm.ask(
            llm.summarization_model(),
            [{"role": "user", "content": prompt}],
            role="summarization",
        ).strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        return [
            f.strip()
            for f in data.get("facts", [])
            if isinstance(f, str) and len(f.strip()) >= 12
        ][:max_facts]
    except Exception as exc:
        log.debug("Consolidation LLM skipped: %s", exc)
        return []


def run_consolidation(memory_store, *, target_namespace: str = "profile") -> dict:
    """Distill recent notes into durable facts via ACM encode (M4 — no SoT distill-write)."""
    from jarvis.brain_memory import consolidation_enabled
    from jarvis.memory_context import detect_project_namespace

    if not consolidation_enabled():
        return {"skipped": True, "reason": "disabled", "added": 0, "removed": 0}

    sources = _collect_source_entries(memory_store)
    if not sources:
        return {"skipped": True, "reason": "no_sources", "added": 0, "removed": 0}

    blob = "\n".join(f"- {e.get('content', '')[:500]}" for e in sources)
    facts = _distill_facts(blob)
    if not facts:
        return {"skipped": True, "reason": "llm_empty", "added": 0, "removed": 0}

    ns = target_namespace or detect_project_namespace()
    added = 0
    for fact in facts:
        try:
            from aria_core import acm_bridge

            if acm_bridge.acm_is_authoritative():
                acm_bridge.primary_remember(
                    fact,
                    entry_type="fact",
                    tags=[_CONSOLIDATION_TAG, "auto-learn"],
                    namespace=ns,
                )
                added += 1
                continue
        except Exception:
            pass
        if memory_store.similar_exists(fact, namespace=ns):
            continue
        memory_store.add(
            "fact",
            fact,
            tags=[_CONSOLIDATION_TAG, "auto-learn"],
            namespace=ns,
        )
        added += 1

    return {"skipped": False, "added": added, "sources": len(sources), "namespace": ns}
