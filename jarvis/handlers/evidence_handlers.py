"""Evidence & Verification handlers — sources, evidence, claims, verification, provenance."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action(
    "evidence_source_add", module="general", description="Record a source for evidence"
)
def evidence_source_add(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    url = (params.get("url") or "").strip()
    if not url:
        return err("A source needs a url.", module="general")
    try:
        sid = ev.add_source(
            url,
            context_id=(params.get("context_id") or "").strip(),
            title=params.get("title") or "",
            publisher=params.get("publisher") or "",
            source_type=params.get("source_type") or "web",
        )
    except ev.EvidenceError as exc:
        return err(str(exc), module="general")
    return ok(
        f"Source `{sid}` recorded (discovered).",
        module="general",
        source_id=sid,
        source=ev.get_source(sid),
    )


@register_action("evidence_add", module="general", description="Attach evidence to a source")
def evidence_add(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    source_id = (params.get("source_id") or "").strip()
    excerpt = (params.get("excerpt") or "").strip()
    if not source_id or not excerpt:
        return err("evidence_add needs source_id and excerpt.", module="general")
    try:
        eid = ev.add_evidence(
            source_id,
            excerpt,
            context_id=(params.get("context_id") or "").strip(),
            claim_id=(params.get("claim_id") or "").strip() or None,
            evidence_type=params.get("evidence_type") or ev.SNIPPET,
        )
    except ev.EvidenceError as exc:
        return err(str(exc), module="general", error_kind="evidence_integrity")
    return ok(
        f"Evidence `{eid}` recorded.",
        module="general",
        evidence_id=eid,
        evidence=ev.get_evidence(eid),
    )


@register_action("evidence_claim_add", module="general", description="Create a claim")
def evidence_claim_add(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    text = (params.get("text") or params.get("claim") or "").strip()
    if not text:
        return err("A claim needs text.", module="general")
    try:
        cid = ev.add_claim(
            text,
            context_id=(params.get("context_id") or "").strip(),
            origin=params.get("origin") or "agent",
        )
    except ev.EvidenceError as exc:
        return err(str(exc), module="general")
    return ok(
        f"Claim `{cid}` created (proposed).",
        module="general",
        claim_id=cid,
        claim=ev.get_claim(cid),
    )


@register_action("evidence_link", module="general", description="Relate evidence to a claim")
def evidence_link(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    claim_id = (params.get("claim_id") or "").strip()
    evidence_id = (params.get("evidence_id") or "").strip()
    relation = (params.get("relation") or ev.SUPPORTS).strip()
    try:
        ev.link(claim_id, evidence_id, relation, note=params.get("note") or "")
    except ev.EvidenceError as exc:
        return err(str(exc), module="general", error_kind="evidence_integrity")
    return ok(f"{relation}: {evidence_id} → {claim_id}", module="general")


@register_action(
    "evidence_claim_get", module="general", description="Show a claim and its evidence", info=True
)
def evidence_claim_get(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    claim_id = (params.get("claim_id") or params.get("id") or "").strip()
    claim = ev.get_claim(claim_id)
    if not claim:
        return err(f"No claim `{claim_id}`.", module="general")
    rows = ev.claim_evidence(claim_id)
    vers = ev.verifications(claim_id)
    lines = [
        f"**Claim** `{claim['id']}` — {claim['status']} (confidence: {claim['confidence']})",
        claim["text"],
        f"Evidence: {len(rows)} · Verifications: {len(vers)} · Conflicts: {len(ev.conflicts(claim_id))}",
    ]
    for r in rows[:8]:
        mark = "inspected" if r["inspected"] else r["access_state"]
        lines.append(f"- {r['relation']}: {r['url']} ({r['evidence_type']}, {mark})")
    return ok("\n".join(lines), module="general", claim=claim, evidence=rows, verifications=vers)


@register_action(
    "evidence_list_claims", module="general", description="List claims in a context", info=True
)
def evidence_list_claims(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    context_id = (params.get("context_id") or "").strip()
    items = ev.claims(context_id)
    if not items:
        return ok("No claims.", module="general", claims=[])
    lines = [f"- `{c['id']}` [{c['status']}/{c['confidence']}] {c['text'][:70]}" for c in items]
    return ok("\n".join(lines), module="general", claims=items)


@register_action("evidence_verify", module="general", description="Verify a claim from evidence")
def evidence_verify(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    claim_id = (params.get("claim_id") or "").strip()
    method = (params.get("method") or ev.INDEPENDENT_SOURCES).strip()
    try:
        result = ev.verify(
            claim_id,
            method=method,
            verifier=(params.get("verifier") or "").strip(),
            model=(params.get("model") or "").strip(),
        )
    except ev.EvidenceError as exc:
        return err(str(exc), module="general")
    lines = [
        f"**{result['result']}** (confidence: {result['confidence']}) via {result['method']}",
        result["explanation"],
        f"Why: {result['confidence_reason']}",
        f"Independence: {result['independence']['level']} "
        f"({result['independence']['distinct_domains']} domain(s))",
    ]
    return ok("\n".join(lines), module="general", verification=result)


@register_action(
    "evidence_provenance",
    module="general",
    description="Trace a claim back through evidence and sources",
    info=True,
)
def evidence_provenance(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    claim_id = (params.get("claim_id") or params.get("id") or "").strip()
    data = ev.provenance(claim_id) if claim_id else None
    if not data:
        return err(f"No claim `{claim_id}`.", module="general")
    lines = [f"**Provenance for** `{claim_id}`: {data['claim']['text'][:80]}"]
    for hop in data["chain"]:
        lines.append(
            f"- {hop['relation']} ← {hop['evidence']['type']} "
            f"({'inspected' if hop['evidence']['inspected'] else hop['source']['access_state']}) "
            f"← {hop['source']['url']}"
        )
    if data["conflicts"]:
        lines.append(f"Conflicts preserved: {len(data['conflicts'])}")
    if data["unresolved"]:
        lines.append(f"Unresolved: {len(data['unresolved'])}")
    return ok("\n".join(lines), module="general", provenance=data)


@register_action(
    "evidence_conflicts", module="general", description="Show preserved contradictions", info=True
)
def evidence_conflicts(assistant, params: dict, message: str) -> dict:
    from jarvis import evidence as ev

    claim_id = (params.get("claim_id") or "").strip()
    rows = ev.conflicts(claim_id)
    if not rows:
        return ok("No conflicts recorded.", module="general", conflicts=[])
    lines = [f"- [{c['resolution']}] {c['explanation']}" for c in rows]
    return ok("\n".join(lines), module="general", conflicts=rows)
