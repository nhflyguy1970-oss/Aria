"""Record MCP-sourced material in the existing evidence system.

The anti-fabrication rule from Milestone 7 is the whole point here: content that
arrived over MCP is a source that was *retrieved*, not one that was inspected,
independent or verified. Nothing in this module marks anything verified; that
remains the evidence layer's decision, based on its own rules.
"""

from __future__ import annotations

from typing import Any


def record_resource_evidence(
    envelope: dict[str, Any],
    *,
    context_id: str,
    claim_text: str = "",
) -> dict[str, Any]:
    """Turn a successful MCP resource retrieval into evidence with provenance."""
    from jarvis import evidence as ev

    if envelope.get("status") != "success":
        # A failed retrieval must stay a failure; it never becomes a source.
        return {
            "recorded": False,
            "reason": f"retrieval {envelope.get('status')}: {envelope.get('error')}",
        }

    provider = envelope.get("provider_id") or "mcp"
    uri = envelope.get("target") or ""
    contents = (envelope.get("result") or {}).get("contents") or []
    text = "\n".join(c.get("text") or "" for c in contents).strip()

    source_id = ev.add_source(f"mcp://{provider}/{uri}", context_id=context_id)
    # The content genuinely came back, so the source was reached — but ARIA has
    # not independently confirmed anything about it.
    ev.mark_source_inspected(source_id)
    evidence_id = ev.add_evidence(
        source_id,
        text[:4000] or "(empty resource)",
        context_id=context_id,
        evidence_type=ev.FULL_TEXT,
    )
    out = {
        "recorded": True,
        "source_id": source_id,
        "evidence_id": evidence_id,
        "provider": provider,
        "uri": uri,
        "provenance": {
            **(envelope.get("provenance") or {}),
            "chain": ["provider", "resource", "retrieved_content", "evidence"],
        },
        "verification": "none",
    }
    if claim_text:
        claim_id = ev.add_claim(claim_text, context_id=context_id)
        ev.link(claim_id, evidence_id, ev.SUPPORTS)
        out["claim_id"] = claim_id
        out["provenance"]["chain"].append("claim")
    return out
