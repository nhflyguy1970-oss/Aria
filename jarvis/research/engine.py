"""Deep research engine — plan, search, collect, analyse, synthesise.

Execution substrate is the existing mission system: a research job creates a
mission whose steps are `research_step` actions, so the background mission
worker runs it, the mission engine supplies checkpoints, pause/resume,
cancellation, retry/backoff and crash recovery. Nothing here re-implements a
queue, a checkpoint mechanism or an agent framework.

Search and source ranking reuse jarvis.web_search and
jarvis.research_verification.classify_source_tier.

Every phase is idempotent: re-running it after a recovery must not duplicate
questions, sources, evidence or claims, which is why the store dedupes on
natural keys rather than trusting the caller.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

from jarvis.research import store

log = logging.getLogger("jarvis.research")

PHASES = ("plan", "search", "collect", "analyze", "synthesize")

MAX_QUESTIONS = 4
MAX_SOURCES_PER_QUERY = 5
MAX_SOURCES_INSPECTED = 8

# Injectable so unit tests never touch the network.
SearchFn = Callable[[str, int], list[dict]]
FetchFn = Callable[[str], str]


def _default_search(query: str, limit: int) -> list[dict]:
    from jarvis.web_search import search

    return search(query, limit=limit) or []


def _default_fetch(url: str) -> str:
    """Retrieve source text.

    ARIA's browser agent is optional and heavy; when it is unavailable the
    engine records that the source was not inspected rather than pretending it
    read the page.
    """
    from jarvis.p2_flags import browser_agent_enabled

    if not browser_agent_enabled():
        raise RuntimeError("browser agent disabled; source not retrieved")
    from jarvis.browser_agent import navigate

    result = navigate(url) or {}
    text = result.get("text") or result.get("content") or ""
    if not text:
        raise RuntimeError("no content retrieved")
    return text


def _tier(url: str, title: str = "", snippet: str = "") -> int:
    try:
        from jarvis.research_verification import classify_source_tier

        return int(classify_source_tier(url, title, snippet))
    except Exception:
        return 3


# ------------------------------------------------------------------ phases


def phase_plan(research_id: str) -> dict[str, Any]:
    """Decompose the objective into research questions and a plan."""
    job = store.get_job(research_id)
    if not job:
        raise ValueError(f"No research job {research_id}")
    objective = job["objective"]

    questions = decompose(objective)
    for seq, q in enumerate(questions):
        store.add_question(research_id, q, seq)
    plan = [f"search: {q}" for q in questions] + ["collect", "analyze", "synthesize"]
    store.save_plan(research_id, plan)
    return {"questions": len(questions), "plan_steps": len(plan)}


def decompose(objective: str) -> list[str]:
    """Turn an objective into concrete sub-questions.

    Deliberately deterministic: research must be reproducible and testable, and
    the milestone forbids depending on the live internet or a model in tests.
    """
    text = (objective or "").strip()
    if not text:
        return []
    base = text.rstrip("?").strip()
    questions = [
        f"What is {base}?",
        f"What is the evidence for {base}?",
        f"What are counterarguments or contradicting evidence about {base}?",
        f"What remains uncertain or disputed about {base}?",
    ]
    return questions[:MAX_QUESTIONS]


def phase_search(research_id: str, search_fn: SearchFn | None = None) -> dict[str, Any]:
    """Run a search per question and record deduplicated sources."""
    search_fn = search_fn or _default_search
    found = 0
    for q in store.questions(research_id):
        query = q["text"]
        try:
            hits = search_fn(query, MAX_SOURCES_PER_QUERY) or []
        except Exception as exc:  # noqa: BLE001 - a failed search is data, not a crash
            store.record_search(research_id, query, 0, error=f"{type(exc).__name__}: {exc}")
            continue
        store.record_search(research_id, query, len(hits))
        for hit in hits:
            url = (hit.get("url") or hit.get("href") or "").strip()
            if not url:
                continue
            title = hit.get("title") or ""
            snippet = hit.get("snippet") or hit.get("body") or ""
            sid = store.add_source(
                research_id,
                url,
                title=title,
                snippet=snippet,
                tier=_tier(url, title, snippet),
                query=query,
            )
            if sid is not None:
                found += 1
    return {"sources_seen": found, "unique_sources": len(store.sources(research_id))}


def phase_collect(research_id: str, fetch_fn: FetchFn | None = None) -> dict[str, Any]:
    """Retrieve source material and turn it into evidence.

    A source that cannot be retrieved is recorded with its error. Its search
    snippet is still usable evidence, but the source is not marked inspected —
    the engine never claims to have read something it did not.
    """
    fetch_fn = fetch_fn or _default_fetch
    inspected = failed = collected = 0
    for source in store.sources(research_id)[:MAX_SOURCES_INSPECTED]:
        sid = source["id"]
        if source["inspected"]:
            continue  # idempotent: already collected before an interruption
        try:
            content = fetch_fn(source["url"])
            store.mark_inspected(sid, content)
            inspected += 1
            excerpt = content.strip()[:1200]
        except Exception as exc:  # noqa: BLE001
            store.mark_retrieval_failed(sid, f"{type(exc).__name__}: {exc}")
            failed += 1
            excerpt = (source["snippet"] or "").strip()
        if excerpt:
            store.add_evidence(research_id, sid, excerpt)
            collected += 1
    return {"inspected": inspected, "retrieval_failed": failed, "evidence": collected}


_NEGATION = re.compile(
    r"\b(not|no|never|false|myth|debunk\w*|disput\w*|contrary|however|but|refut\w*|incorrect)\b",
    re.I,
)


def phase_analyze(research_id: str) -> dict[str, Any]:
    """Build claims from evidence and record supporting/contradicting stances."""
    job = store.get_job(research_id)
    if not job:
        raise ValueError(f"No research job {research_id}")
    objective = job["objective"].rstrip("?").strip()

    claim_id = store.add_claim(research_id, objective, kind=store.FACT)
    rows = store.evidence(research_id)
    supports = contradicts = 0

    for ev in rows:
        stance = store.CONTRADICTS if _NEGATION.search(ev["excerpt"] or "") else store.SUPPORTS
        store.link_evidence(claim_id, ev["id"], stance)
        if stance == store.CONTRADICTS:
            contradicts += 1
        else:
            supports += 1

    # Independent verification: agreeing evidence from distinct sources.
    linked = store.claim_evidence(claim_id)
    supporting_sources = {r["source_id"] for r in linked if r["stance"] == store.SUPPORTS}
    if len(supporting_sources) >= 2:
        for r in linked:
            if r["stance"] == store.SUPPORTS:
                store.link_evidence(claim_id, r["evidence_id"], store.VERIFIES)
                break

    verified = len(supporting_sources) >= 2 and contradicts == 0
    confidence = _confidence(supports, contradicts, len(supporting_sources))
    store.set_claim_verdict(claim_id, verified=verified, confidence=confidence)

    # Mirror into the shared evidence layer (Milestone 7) so the claim is
    # traceable and verifiable outside research too. Research keeps its own
    # tables for backward compatibility; the evidence layer is authoritative
    # for verification.
    _mirror_to_evidence(research_id, objective)

    if contradicts:
        store.add_unresolved(
            research_id,
            f"Sources disagree about: {objective} ({supports} supporting, {contradicts} contradicting)",
        )
    if not rows:
        store.add_unresolved(research_id, f"No evidence was collected for: {objective}")
    if supports and len(supporting_sources) < 2:
        store.add_unresolved(research_id, f"Only one independent source supports: {objective}")

    return {
        "claims": len(store.claims(research_id)),
        "supports": supports,
        "contradicts": contradicts,
        "verified": verified,
        "confidence": confidence,
    }


def _mirror_to_evidence(research_id: str, objective: str) -> dict[str, Any]:
    """Project research sources/evidence/claims into the shared evidence model."""
    from jarvis import evidence as ev

    claim_id = ev.add_claim(objective, context_id=research_id, origin="research")
    source_map: dict[int, str] = {}
    for src in store.sources(research_id):
        try:
            sid = ev.add_source(
                src["url"],
                context_id=research_id,
                title=src["title"],
                metadata={"research_source_id": src["id"], "query": src["query"]},
            )
        except ev.EvidenceError:
            continue
        source_map[src["id"]] = sid
        if src["inspected"]:
            ev.mark_source_inspected(sid, retrieved_at=src["inspected_at"])
        elif src["retrieval_error"]:
            ev.mark_source_unavailable(sid, src["retrieval_error"])

    for row in store.evidence(research_id):
        sid = source_map.get(row["source_id"])
        if not sid:
            continue
        source = ev.get_source(sid)
        # A snippet stays a snippet: only genuinely inspected sources may
        # contribute full-text evidence.
        kind = ev.FULL_TEXT if source["access_state"] == ev.INSPECTED else ev.SNIPPET
        eid = ev.add_evidence(
            sid, row["excerpt"], context_id=research_id, claim_id=claim_id, evidence_type=kind
        )
        relation = ev.CONTRADICTS if _NEGATION.search(row["excerpt"] or "") else ev.SUPPORTS
        ev.link(claim_id, eid, relation)

    result = ev.verify(claim_id, verifier="research_engine")
    return {
        "claim_id": claim_id,
        "verification": result["result"],
        "confidence": result["confidence"],
    }


def _confidence(supports: int, contradicts: int, independent_sources: int) -> str:
    if not supports and not contradicts:
        return "none"
    if contradicts and supports:
        return "contested"
    if contradicts and not supports:
        return "contradicted"
    if independent_sources >= 2:
        return "high"
    return "low"


def phase_synthesize(research_id: str) -> dict[str, Any]:
    """Produce the inspectable final result with citations tied to real sources."""
    job = store.get_job(research_id)
    if not job:
        raise ValueError(f"No research job {research_id}")

    claim_rows = store.claims(research_id)
    open_questions = store.unresolved(research_id)
    lines: list[str] = [f"# Research: {job['objective']}", ""]
    overall = "none"

    for claim in claim_rows:
        linked = store.claim_evidence(claim["id"])
        sup = [r for r in linked if r["stance"] == store.SUPPORTS]
        con = [r for r in linked if r["stance"] == store.CONTRADICTS]
        ver = [r for r in linked if r["stance"] == store.VERIFIES]
        overall = claim["confidence"]
        lines.append(f"## Claim: {claim['text']}")
        lines.append(
            f"- kind: {claim['kind']} · confidence: {claim['confidence']} · "
            f"verified: {'yes' if claim['verified'] else 'no'}"
        )
        lines.append(f"- supporting evidence: {len(sup)} · contradicting: {len(con)}")
        if ver:
            lines.append(f"- independently corroborated by {len(ver)} source(s)")
        if con:
            lines.append("- **sources disagree** — the disagreement is preserved below")
        for row in sup[:5]:
            lines.append(f"  - supports [{row['title'] or row['url']}]({row['url']})")
        for row in con[:5]:
            lines.append(f"  - contradicts [{row['title'] or row['url']}]({row['url']})")
        lines.append("")

    inspected = store.sources(research_id, inspected_only=True)
    all_sources = store.sources(research_id)
    lines.append("## Citations")
    if not all_sources:
        lines.append("- none")
    for s in all_sources:
        state = (
            "inspected" if s["inspected"] else f"not inspected ({s['retrieval_error'] or 'n/a'})"
        )
        lines.append(f"- [{s['title'] or s['url']}]({s['url']}) — tier {s['tier']}, {state}")

    if open_questions:
        lines.append("")
        lines.append("## Unresolved")
        for u in open_questions:
            lines.append(f"- {u['text']}")

    synthesis = "\n".join(lines)
    store.save_synthesis(research_id, synthesis, overall)
    return {
        "synthesis_chars": len(synthesis),
        "claims": len(claim_rows),
        "sources": len(all_sources),
        "inspected": len(inspected),
        "unresolved": len(open_questions),
        "confidence": overall,
    }


# ------------------------------------------------------------------ dispatch


def run_phase(
    research_id: str,
    phase: str,
    *,
    search_fn: SearchFn | None = None,
    fetch_fn: FetchFn | None = None,
) -> dict[str, Any]:
    """Execute one research phase. Called from the mission step handler."""
    if phase not in PHASES:
        raise ValueError(f"Unknown research phase: {phase}")
    store.set_status(research_id, store.RUNNING)
    if phase == "plan":
        return phase_plan(research_id)
    if phase == "search":
        return phase_search(research_id, search_fn)
    if phase == "collect":
        return phase_collect(research_id, fetch_fn)
    if phase == "analyze":
        return phase_analyze(research_id)
    return phase_synthesize(research_id)


def mission_steps(research_id: str) -> list[dict[str, Any]]:
    """The research pipeline expressed as mission steps."""
    return [
        {
            "name": f"research:{phase}",
            "action": "research_step",
            "params": {"research_id": research_id, "phase": phase},
        }
        for phase in PHASES
    ]


def create_research(objective: str) -> dict[str, str]:
    """Create a research job plus the mission that will execute it."""
    from jarvis import missions

    research_id = store.create_job(objective)
    mission_id = missions.create_mission(
        f"Research: {objective}", steps=mission_steps(research_id), kind="research"
    )
    store.set_mission(research_id, mission_id)
    missions.worker.wake()
    return {"research_id": research_id, "mission_id": mission_id}


def status(research_id: str) -> dict[str, Any] | None:
    """Everything needed to understand a research job without opening the DB."""
    from jarvis import missions

    job = store.get_job(research_id)
    if not job:
        return None
    mission = missions.status(job["mission_id"]) if job.get("mission_id") else None
    srcs = store.sources(research_id)
    return {
        "research_id": job["id"],
        "objective": job["objective"],
        "status": job["status"],
        "mission": mission,
        "plan": job["plan"],
        "questions": [q["text"] for q in store.questions(research_id)],
        "searches": len(store.searches(research_id)),
        "sources": len(srcs),
        "sources_inspected": sum(1 for s in srcs if s["inspected"]),
        "evidence": len(store.evidence(research_id)),
        "claims": len(store.claims(research_id)),
        "unresolved": [u["text"] for u in store.unresolved(research_id)],
        "confidence": job.get("confidence"),
        "synthesis": job.get("synthesis"),
        "error": job.get("error"),
        "evidence_claims": _evidence_claims(research_id),
    }


def _provenance_for(research_id: str) -> list[dict[str, Any]]:
    """Full claim -> evidence -> source -> verification chains for this job."""
    from jarvis import evidence as ev

    return [ev.provenance(c["id"]) for c in ev.claims(research_id)]


def _evidence_claims(research_id: str) -> list[dict[str, Any]]:
    """Verification state for this research job, from the shared evidence layer."""
    from jarvis import evidence as ev

    out = []
    for claim in ev.claims(research_id):
        vers = ev.verifications(claim["id"])
        out.append(
            {
                "claim_id": claim["id"],
                "text": claim["text"],
                "status": claim["status"],
                "confidence": claim["confidence"],
                "verification": vers[-1] if vers else None,
                "conflicts": len(ev.conflicts(claim["id"])),
            }
        )
    return out


def report(research_id: str) -> dict[str, Any] | None:
    """Full inspectable result: source -> evidence -> claim -> synthesis."""
    job = store.get_job(research_id)
    if not job:
        return None
    claim_rows = []
    for claim in store.claims(research_id):
        claim_rows.append({**claim, "evidence": store.claim_evidence(claim["id"])})
    return {
        "research_id": research_id,
        "objective": job["objective"],
        "status": job["status"],
        "confidence": job.get("confidence"),
        "synthesis": job.get("synthesis"),
        "questions": store.questions(research_id),
        "searches": store.searches(research_id),
        "sources": store.sources(research_id),
        "evidence": store.evidence(research_id),
        "claims": claim_rows,
        "unresolved": store.unresolved(research_id),
        "evidence_claims": _evidence_claims(research_id),
        "provenance": _provenance_for(research_id),
    }
