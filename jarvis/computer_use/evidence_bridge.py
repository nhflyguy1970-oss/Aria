"""Browser inspection → evidence, without weakening Milestone 7's guarantees.

A page is only recorded as inspected when text was actually extracted. A
screenshot proves a render happened, not that content was read, so it is
attached as provenance metadata and never as full-text evidence — otherwise an
image would silently satisfy "inspected".
"""

from __future__ import annotations

from typing import Any

from jarvis.computer_use import engine


def capture_page_evidence(
    session_id: str,
    url: str,
    *,
    context_id: str,
    claim_id: str = "",
    relation: str = "supports",
    driver: Any = None,
    agent_id: str = "",
    allow_local: bool = False,
) -> dict[str, Any]:
    """Navigate, extract, and record the true retrieval state in the evidence layer."""
    from jarvis import evidence as ev

    source_id = ev.add_source(url, context_id=context_id, title="")
    nav = engine.perform(
        session_id,
        "navigate",
        {"url": url},
        driver=driver,
        agent_id=agent_id,
        allow_local=allow_local,
    )
    if not nav["ok"]:
        ev.mark_source_unavailable(source_id, f"{nav['error_kind']}: {nav['error']}")
        return {
            "ok": False,
            "source_id": source_id,
            "inspected": False,
            "error": nav["error"],
            "error_kind": nav["error_kind"],
            "evidence_id": None,
        }

    extracted = engine.perform(
        session_id, "extract", {}, driver=driver, agent_id=agent_id, allow_local=allow_local
    )
    text = ((extracted.get("result") or {}).get("text") or "").strip() if extracted["ok"] else ""
    if not text:
        # Rendered but nothing readable: that is not inspection.
        ev.mark_source_unavailable(
            source_id, extracted.get("error") or "no text extracted from page"
        )
        return {
            "ok": False,
            "source_id": source_id,
            "inspected": False,
            "error": extracted.get("error") or "no extractable content",
            "error_kind": extracted.get("error_kind") or "extraction",
            "evidence_id": None,
        }

    ev.mark_source_inspected(source_id)
    evidence_id = ev.add_evidence(
        source_id,
        text,
        context_id=context_id,
        claim_id=claim_id or None,
        evidence_type=ev.FULL_TEXT,
        provenance=f"browser:{session_id}:{nav.get('url') or url}",
    )
    if claim_id:
        ev.link(claim_id, evidence_id, relation)
    return {
        "ok": True,
        "source_id": source_id,
        "evidence_id": evidence_id,
        "inspected": True,
        "url": nav.get("url") or url,
        "title": nav.get("title") or "",
        "chars": len(text),
    }
