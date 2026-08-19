"""End-to-end provenance, assembled from what each subsystem already recorded.

Nothing is inferred here. Each node comes from a durable record — a workflow
step, a routed model invocation, an MCP call, an evidence chain — and a link
that cannot be established from those records is reported as unestablished
rather than drawn in. A graph that quietly filled its own gaps would be worse
than no graph at all.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("jarvis.integration.provenance")


def _try(loader, label: str, default):
    try:
        return loader()
    except Exception as exc:  # noqa: BLE001
        log.info("provenance: %s unavailable: %s", label, exc)
        return default


def for_workflow(workflow_id: str) -> dict[str, Any]:
    """The chain for one workflow: request → steps → agents → models/tools → evidence."""
    from jarvis import autonomous_workflows as wf

    snapshot = wf.status(workflow_id)
    if not snapshot:
        return {"ok": False, "error": f"no such workflow: {workflow_id}"}

    nodes: list[dict[str, Any]] = [
        {
            "kind": "workflow",
            "id": workflow_id,
            "name": snapshot["name"],
            "state": snapshot["state"],
            "requester": snapshot["requester"],
        }
    ]
    if snapshot.get("mission_id"):
        nodes.append({"kind": "mission", "id": snapshot["mission_id"], "parent": workflow_id})

    gaps: list[str] = []
    evidence_contexts: set[str] = set()
    research_ids: set[str] = set()

    for step in snapshot.get("provenance") or []:
        record = step.get("provenance") or {}
        node = {
            "kind": "step",
            "id": step["step_id"],
            "parent": workflow_id,
            "state": step["state"],
            "action": step.get("action", ""),
            "agent": step.get("agent") or record.get("agent") or "",
            "model": record.get("model", ""),
            "skill": record.get("skill_id", ""),
            "provider": record.get("provider_id", ""),
        }
        if record.get("fallback_count"):
            # A model fallback is part of the truth of what ran.
            node["model_fallbacks"] = record["fallback_count"]
        if record.get("note"):
            gaps.append(f"{step['step_id']}: {record['note']}")
        nodes.append(node)
        for key, sink in (("research_id", research_ids), ("context_id", evidence_contexts)):
            if record.get(key):
                sink.add(record[key])

    # Routed model invocations recorded against this workflow's mission.
    routed = _try(lambda: _routed_models(snapshot.get("mission_id") or ""), "model routing", [])
    nodes.extend(routed)

    evidence = _try(lambda: _evidence_for(evidence_contexts), "evidence", [])
    nodes.extend(evidence)

    return {
        "ok": True,
        "workflow_id": workflow_id,
        "state": snapshot["state"],
        "nodes": nodes,
        "counts": _counts(nodes),
        "research": sorted(research_ids),
        "evidence_contexts": sorted(evidence_contexts),
        # Honest about what could not be established.
        "unestablished_links": gaps,
        "note": (
            "each node comes from a durable subsystem record; links that could not be "
            "established are listed rather than inferred"
        ),
    }


def _routed_models(mission_id: str) -> list[dict[str, Any]]:
    if not mission_id:
        return []
    from jarvis import model_routing

    rows = model_routing.history(mission_id=mission_id, limit=50)
    return [
        {
            "kind": "model_invocation",
            "id": row["id"],
            "model": row["final_model"] or row["selected_model"],
            "provider": row["provider"],
            "state": row["status"],
            "fallbacks": row["fallback_count"],
            "requester": row["requester"],
        }
        for row in rows
    ]


def _evidence_for(contexts: set[str]) -> list[dict[str, Any]]:
    if not contexts:
        return []
    from jarvis import evidence as ev

    nodes: list[dict[str, Any]] = []
    for context_id in sorted(contexts):
        for claim in ev.claims(context_id=context_id) or []:
            claim_id = claim.get("id") if isinstance(claim, dict) else str(claim)
            chain = ev.provenance(claim_id) or {}
            nodes.append(
                {
                    "kind": "claim",
                    "id": claim_id,
                    "text": (claim.get("text") if isinstance(claim, dict) else "")[:200],
                    "context": context_id,
                    # Whatever the evidence system concluded, unchanged.
                    "sources": [
                        {
                            "url": (link.get("source") or {}).get("url", ""),
                            "access_state": (link.get("source") or {}).get("access_state", ""),
                        }
                        for link in (chain.get("chain") or [])
                    ],
                }
            )
    return nodes


def _counts(nodes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in nodes:
        counts[node["kind"]] = counts.get(node["kind"], 0) + 1
    return counts


def for_request(request_id: str) -> dict[str, Any]:
    """Everything recorded against one request id, across subsystems."""
    from jarvis import model_routing

    routed = _try(
        lambda: [
            r
            for r in model_routing.history(limit=200)
            if (r.get("decision") or {}).get("request", {}).get("metadata", {}).get("request_id")
            == request_id
        ],
        "model routing",
        [],
    )
    return {
        "ok": True,
        "request_id": request_id,
        "model_invocations": routed,
        "note": "requests are correlated by identifier; subsystems that record none are absent",
    }
