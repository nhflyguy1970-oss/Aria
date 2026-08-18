"""Verification engine — deterministic, explainable claim verification.

Every result names the method that produced it and the evidence it considered,
so a caller can tell what the verdict actually rests on. Nothing here upgrades
a claim on assertion alone: verification is computed from persisted evidence
and source access states, and a model's opinion is recorded as one input, never
as corroboration.

Confidence is a defined function of the evidence, not a number a model emits.
"""

from __future__ import annotations

import logging
from typing import Any

from jarvis.evidence import store

log = logging.getLogger("jarvis.evidence")

# Verification methods.
INDEPENDENT_SOURCES = "independent_sources"
CONTRADICTION_ANALYSIS = "contradiction_analysis"
SOURCE_QUALITY = "source_quality"
CROSS_SOURCE_CONSISTENCY = "cross_source_consistency"
DIRECT_INSPECTION = "direct_inspection"
MANUAL = "manual"
METHODS = (
    INDEPENDENT_SOURCES,
    CONTRADICTION_ANALYSIS,
    SOURCE_QUALITY,
    CROSS_SOURCE_CONSISTENCY,
    DIRECT_INSPECTION,
    MANUAL,
)

# Results.
VERIFIED = "verified"
SUPPORTED = "supported"
CONTESTED = "contested"
CONTRADICTED = "contradicted"
INSUFFICIENT = "insufficient_evidence"
UNRESOLVED = "unresolved"

# Confidence bands.
HIGH = "high"
MODERATE = "moderate"
LOW = "low"
NONE = "none"

# A model's assertion is evidence of what the model said — never of the world.
NON_CORROBORATING = (store.MODEL_ASSERTION,)


def independence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Assess whether supporting evidence comes from genuinely distinct sources.

    Two rows from the same canonical source, or the same domain, are not
    independent corroboration. Where the system cannot establish independence
    it says so rather than assuming it.
    """
    source_ids = {r["source_id"] for r in rows}
    domains = {(r.get("domain") or "").lower() for r in rows if r.get("domain")}
    blank_domains = any(not (r.get("domain") or "") for r in rows)

    if len(source_ids) <= 1:
        level = store.NOT_INDEPENDENT
    elif len(domains) <= 1:
        # Distinct URLs on one domain — same publisher, so not corroboration.
        level = store.NOT_INDEPENDENT
    elif blank_domains:
        level = store.UNKNOWN_INDEPENDENCE
    else:
        level = store.INDEPENDENT

    return {
        "level": level,
        "distinct_sources": len(source_ids),
        "distinct_domains": len(domains),
        "domains": sorted(d for d in domains if d),
    }


def _partition(claim_id: str) -> dict[str, list[dict[str, Any]]]:
    rows = store.claim_evidence(claim_id)
    return {
        "all": rows,
        "supporting": [r for r in rows if r["relation"] == store.SUPPORTS],
        "contradicting": [r for r in rows if r["relation"] == store.CONTRADICTS],
        "weakening": [r for r in rows if r["relation"] == store.WEAKENS],
        "corroborating": [
            r
            for r in rows
            if r["relation"] == store.SUPPORTS and r["evidence_type"] not in NON_CORROBORATING
        ],
        "inspected": [r for r in rows if r["inspected"]],
    }


def score_confidence(
    parts: dict[str, list[dict[str, Any]]], indep: dict[str, Any]
) -> dict[str, Any]:
    """Explainable confidence. Every contributing factor is returned with it."""
    supporting = parts["corroborating"]
    contradicting = parts["contradicting"]
    inspected = parts["inspected"]
    tiers = [r["tier"] for r in supporting if r.get("tier") is not None]
    best_tier = min(tiers) if tiers else 4

    factors = {
        "supporting_evidence": len(supporting),
        "contradicting_evidence": len(contradicting),
        "independent_sources": indep["distinct_sources"]
        if indep["level"] == store.INDEPENDENT
        else 0,
        "independence": indep["level"],
        "inspected_evidence": len(inspected),
        "best_source_tier": best_tier,
        "excluded_non_corroborating": len(parts["supporting"]) - len(supporting),
    }

    if not supporting and not contradicting:
        return {"confidence": NONE, "factors": factors, "reason": "no evidence attached"}
    if contradicting and not supporting:
        return {"confidence": LOW, "factors": factors, "reason": "only contradicting evidence"}
    if contradicting:
        # Strong contradiction can never read as unqualified high confidence.
        return {
            "confidence": LOW if len(contradicting) >= len(supporting) else MODERATE,
            "factors": factors,
            "reason": "supporting and contradicting evidence both present",
        }
    if indep["level"] == store.INDEPENDENT and inspected and best_tier <= 2:
        return {
            "confidence": HIGH,
            "factors": factors,
            "reason": "independent, inspected, high-quality supporting sources with no contradiction",
        }
    if indep["level"] == store.INDEPENDENT:
        return {
            "confidence": MODERATE,
            "factors": factors,
            "reason": "independent supporting sources, but not all inspected or high-tier",
        }
    return {
        "confidence": LOW,
        "factors": factors,
        "reason": f"support is {indep['level']} ({indep['distinct_domains']} distinct domain(s))",
    }


def verify(
    claim_id: str,
    *,
    method: str = INDEPENDENT_SOURCES,
    verifier: str = "",
    model: str = "",
    record: bool = True,
) -> dict[str, Any]:
    """Verify a claim from its persisted evidence and return a structured result."""
    if method not in METHODS:
        raise store.EvidenceError(f"Unknown verification method: {method}")
    claim = store.get_claim(claim_id)
    if not claim:
        raise store.EvidenceError(f"No such claim: {claim_id}")

    parts = _partition(claim_id)
    indep = independence(parts["corroborating"])
    scored = score_confidence(parts, indep)
    confidence = scored["confidence"]

    if method == DIRECT_INSPECTION:
        result = VERIFIED if parts["inspected"] and not parts["contradicting"] else INSUFFICIENT
        explanation = (
            f"{len(parts['inspected'])} inspected evidence item(s); "
            f"{len(parts['contradicting'])} contradicting"
        )
    elif method == CONTRADICTION_ANALYSIS:
        if parts["contradicting"] and parts["corroborating"]:
            result = CONTESTED
        elif parts["contradicting"]:
            result = CONTRADICTED
        elif parts["corroborating"]:
            result = SUPPORTED
        else:
            result = INSUFFICIENT
        explanation = (
            f"{len(parts['corroborating'])} supporting vs "
            f"{len(parts['contradicting'])} contradicting"
        )
    elif method == SOURCE_QUALITY:
        best = scored["factors"]["best_source_tier"]
        result = SUPPORTED if best <= 2 and parts["corroborating"] else INSUFFICIENT
        explanation = f"best supporting source tier {best}"
    elif method == CROSS_SOURCE_CONSISTENCY:
        result = (
            SUPPORTED
            if indep["level"] == store.INDEPENDENT and not parts["contradicting"]
            else CONTESTED
            if parts["contradicting"]
            else INSUFFICIENT
        )
        explanation = f"independence={indep['level']}, domains={indep['distinct_domains']}"
    else:  # INDEPENDENT_SOURCES
        if parts["contradicting"]:
            result = CONTESTED
        elif indep["level"] == store.INDEPENDENT and len(parts["corroborating"]) >= 2:
            result = VERIFIED
        elif parts["corroborating"]:
            result = SUPPORTED
        else:
            result = INSUFFICIENT
        explanation = (
            f"{len(parts['corroborating'])} corroborating item(s) across "
            f"{indep['distinct_domains']} domain(s); independence={indep['level']}"
        )

    if result == INSUFFICIENT:
        confidence = NONE if not parts["all"] else LOW

    outcome = {
        "claim_id": claim_id,
        "claim": claim["text"],
        "method": method,
        "result": result,
        "confidence": confidence,
        "confidence_reason": scored["reason"],
        "factors": scored["factors"],
        "independence": indep,
        "explanation": explanation,
        "evidence_considered": [
            {
                "evidence_id": r["evidence_id"],
                "relation": r["relation"],
                "type": r["evidence_type"],
                "inspected": bool(r["inspected"]),
                "source_id": r["source_id"],
                "url": r["url"],
                "access_state": r["access_state"],
                "tier": r["tier"],
            }
            for r in parts["all"]
        ],
        "verifier": verifier,
        "model": model,
    }

    if record:
        outcome["verification_id"] = store.add_verification(
            claim_id,
            method=method,
            result=result,
            confidence=confidence,
            verifier=verifier,
            independent_sources=indep["distinct_sources"]
            if indep["level"] == store.INDEPENDENT
            else 0,
            independence=indep["level"],
            explanation=f"{explanation} | {scored['reason']}",
            inputs={
                "factors": scored["factors"],
                "evidence": [r["evidence_id"] for r in parts["all"]],
            },
            model=model,
        )
        store.set_claim_state(claim_id, _claim_state_for(result), confidence)
        _record_conflicts(claim_id, parts)
        if result in (CONTESTED, INSUFFICIENT, CONTRADICTED):
            store.add_unresolved(
                claim["context_id"],
                f"{result}: {claim['text'][:140]} ({explanation})",
                claim_id=claim_id,
            )

    return outcome


def _claim_state_for(result: str) -> str:
    return {
        VERIFIED: store.VERIFIED,
        SUPPORTED: store.SUPPORTED,
        CONTESTED: store.CONTESTED,
        CONTRADICTED: store.CONTRADICTED,
        INSUFFICIENT: store.UNRESOLVED,
        UNRESOLVED: store.UNRESOLVED,
    }.get(result, store.PROPOSED)


def _record_conflicts(claim_id: str, parts: dict[str, list[dict[str, Any]]]) -> None:
    """Preserve each supporting/contradicting pair rather than resolving it."""
    for support in parts["corroborating"]:
        for against in parts["contradicting"]:
            store.add_conflict(
                claim_id,
                support["evidence_id"],
                against["evidence_id"],
                explanation=(
                    f"{support['domain'] or support['url']} supports; "
                    f"{against['domain'] or against['url']} contradicts"
                ),
            )


def provenance(claim_id: str) -> dict[str, Any] | None:
    """The full chain: claim -> evidence -> source -> inspection -> verification."""
    claim = store.get_claim(claim_id)
    if not claim:
        return None
    rows = store.claim_evidence(claim_id)
    chain = []
    for r in rows:
        chain.append(
            {
                "relation": r["relation"],
                "evidence": {
                    "id": r["evidence_id"],
                    "type": r["evidence_type"],
                    "inspected": bool(r["inspected"]),
                    "excerpt": r["excerpt"][:400],
                    "provenance": r["provenance"],
                },
                "source": {
                    "id": r["source_id"],
                    "url": r["url"],
                    "domain": r["domain"],
                    "title": r["title"],
                    "tier": r["tier"],
                    "access_state": r["access_state"],
                },
            }
        )
    return {
        "claim": claim,
        "chain": chain,
        "verifications": store.verifications(claim_id),
        "conflicts": store.conflicts(claim_id),
        "unresolved": [
            u for u in store.unresolved(claim["context_id"]) if u["claim_id"] == claim_id
        ],
    }
