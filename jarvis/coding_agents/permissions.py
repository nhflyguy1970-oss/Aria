"""Current coding-plan authority, derived from ARIA state rather than LLM flags."""
from __future__ import annotations
import secrets
import time
from collections.abc import Mapping
from jarvis.coding_agents import discovery, projects, runs, supervisor
from jarvis.integration import policy

class ProposalConflict(runs.AgentRunError):
    """An untrusted proposal conflicts with the current authorization receipt."""

def for_plan(plan_id: str, *, approval_token: str = "") -> dict:
    plan = runs.get_plan(plan_id, with_nonce=True)
    if not plan:
        raise ProposalConflict("no such saved coding plan")
    intact = plan["plan_hash"] == runs._hash(
        plan["agent"], plan["project"], plan["mode"], plan["task"],
        plan["timeout_s"], plan["project_scope"],
    )
    try:
        runs._check_project_scope(plan)
    except runs.AgentRunError:
        intact = False
    project = projects.get(plan["project"])
    kind, _ = supervisor.classify(plan["task"])
    choice = supervisor.select_agent(kind, plan["mode"], named=plan["agent"], project=project)
    eligible = bool(project) and choice.get("agent") == plan["agent"] and "error" not in choice
    state = plan["status"]
    approved = (state == runs.APPROVED and float(plan.get("expires_at") or 0) > time.time()) or (
        state == runs.PROPOSED and bool(approval_token)
        and secrets.compare_digest(str(plan["nonce"]), str(approval_token))
    )
    policy_ok = not any(policy.refusal(cap) for cap in ("coding", "mission"))
    may_start = bool(intact and eligible and approved and policy_ok)
    next_action = ("repropose_plan" if not intact else
                   "report_existing_run" if state == runs.CONSUMED else
                   "resolve_policy_block" if not policy_ok else
                   "revalidate_selected_certificate" if not eligible else
                   "execute_approved_plan" if may_start else "request_execution_approval")
    return {"selected_agent": plan["agent"], "may_start": may_start,
            "may_fallback": False, "may_deploy": False, "preserve_dirty": True,
            "requires_owner_approval": not bool(approved), "next_action": next_action}

def validate_proposal(receipt: Mapping, params: Mapping) -> None:
    """Reject claims; never merge model values into the authoritative receipt."""
    aliases = {"may_execute": "may_start"}
    names = set(receipt) | set(aliases)
    proposals = [{key: value for key, value in params.items() if key in names}]
    for name in ("permissions", "permission_proposal"):
        if name in params:
            if not isinstance(params[name], Mapping):
                raise ProposalConflict("permission proposal must be an object")
            proposals.append(params[name])
    for proposal in proposals:
        for key, value in proposal.items():
            field = aliases.get(key, key)
            if field not in receipt:
                raise ProposalConflict("unknown permission proposal field")
            expected = receipt[field]
            if field == "selected_agent" and isinstance(value, str):
                allowed = {expected.casefold(), discovery.LABELS.get(expected, expected).casefold(),
                           *(x.casefold() for x in discovery.ALIASES.get(expected, ()))}
                valid = value.casefold() in allowed
            else:
                valid = type(value) is type(expected) and value == expected
            if not valid:
                raise ProposalConflict(f"permission proposal conflicts with ARIA authority: {field}")
