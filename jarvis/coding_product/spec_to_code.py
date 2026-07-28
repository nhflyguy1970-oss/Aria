"""Spec-to-code workflow — Documents → plan → proposal → apply → verify.

Maintains document references. Never auto-applies.
"""

from __future__ import annotations

from typing import Any


def spec_to_plan(
    assistant: Any,
    *,
    document_id: str = "",
    document_path: str = "",
    query: str = "",
) -> dict[str, Any]:
    """Build an implementation plan from a document / RAG hit."""
    refs: list[dict[str, str]] = []
    content = ""
    title = ""

    if document_path:
        try:
            from pathlib import Path

            p = Path(document_path).expanduser()
            content = p.read_text(encoding="utf-8")[:12000]
            title = p.name
            refs.append({"type": "path", "id": str(p), "title": title})
        except Exception as exc:
            return {"ok": False, "error": f"Could not read document: {exc}"}
    elif document_id or query:
        try:
            from jarvis import documents_rag

            hits = documents_rag.search(query or document_id, limit=5) if hasattr(documents_rag, "search") else []
            if not hits and hasattr(documents_rag, "query"):
                hits = documents_rag.query(query or document_id, limit=5) or []
            for h in hits or []:
                refs.append(
                    {
                        "type": "rag",
                        "id": str(h.get("id") or h.get("doc_id") or ""),
                        "title": str(h.get("title") or h.get("path") or "doc"),
                        "snippet": str(h.get("snippet") or h.get("text") or "")[:400],
                    }
                )
                content += (h.get("snippet") or h.get("text") or "") + "\n\n"
            title = refs[0]["title"] if refs else (query or document_id)
        except Exception as exc:
            # Soft-fail: still allow plan from query text
            content = query or document_id
            title = query or document_id or "spec"
            refs.append({"type": "query", "id": "", "title": title, "note": str(exc)})
    else:
        return {"ok": False, "error": "Provide document_id, document_path, or query"}

    plan_steps = [
        "Read and extract requirements from the referenced document(s)",
        "Identify touch points in the coding root",
        "Draft a minimal implementation proposal (diff)",
        "Operator reviews Quality Brief",
        "Operator Applies",
        "Operator Verifies (syntax / tests)",
    ]
    plan_text = (
        f"# Implementation plan\n\n"
        f"**Source:** {title}\n\n"
        f"**References:**\n"
        + ("\n".join(f"- {r.get('title')} (`{r.get('id')}`)" for r in refs) or "- (none)")
        + "\n\n**Steps:**\n"
        + "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan_steps))
        + "\n\n**Spec excerpt:**\n```\n"
        + (content[:2000] or "(empty)")
        + "\n```\n"
    )
    return {
        "ok": True,
        "title": title,
        "plan": plan_text,
        "steps": plan_steps,
        "document_refs": refs,
        "spec_excerpt": content[:4000],
        "auto_applied": False,
    }


def spec_to_proposal(
    assistant: Any,
    *,
    document_id: str = "",
    document_path: str = "",
    query: str = "",
    max_steps: int = 4,
) -> dict[str, Any]:
    """Create a coding proposal from a document-backed plan."""
    plan = spec_to_plan(
        assistant,
        document_id=document_id,
        document_path=document_path,
        query=query,
    )
    if not plan.get("ok"):
        return plan

    task = (
        "Implement according to this specification. Keep changes minimal and testable.\n\n"
        f"{plan.get('plan', '')}\n\n"
        f"Spec excerpt:\n{plan.get('spec_excerpt', '')[:3000]}"
    )
    try:
        from jarvis.coding_agent import CodingAgent

        agent = CodingAgent(assistant.coding._base(), max_steps=max_steps)
        result = agent.run(task, mode="agent")
        if not result.ok or not result.files:
            return {
                "ok": False,
                "error": result.message or "Agent produced no files",
                "plan": plan,
                "document_refs": plan.get("document_refs"),
            }
        proposal_id, payload = assistant._store_agent_proposal(
            result.files,
            mode="spec_to_code",
            explanation=result.explanation or plan.get("title") or "spec-to-code",
        )
        # Attach document refs onto pending proposal
        payload["document_refs"] = plan.get("document_refs")
        assistant.pending_proposals[proposal_id] = {
            k: v for k, v in payload.items() if not str(k).startswith("_")
        }
        assistant.pending_proposals[proposal_id]["document_refs"] = plan.get("document_refs")
        assistant._persist_proposals()
        return {
            "ok": True,
            "proposal_id": proposal_id,
            "plan": plan,
            "document_refs": plan.get("document_refs"),
            "syntax_ok": payload.get("syntax_ok"),
            "diff": result.diff or "",
            "message": (
                f"Spec-to-code proposal `{proposal_id}` ready. "
                "Review the diff and Quality Brief, then Apply. Verify after apply."
            ),
            "auto_applied": False,
            "requires_apply_approval": True,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "plan": plan, "document_refs": plan.get("document_refs")}
