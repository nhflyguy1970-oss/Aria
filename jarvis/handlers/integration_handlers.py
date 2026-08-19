"""Integration handlers — the control surface for ARIA as one system.

These do not execute work themselves. They answer "what are you doing", "how
would you approach this", "stop", "resume", "recover", "show me the chain" — and
delegate every actual operation to the subsystem that owns it.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _env():
    from jarvis import integration

    return integration


@register_action(
    "aria_status",
    module="general",
    description="What ARIA is doing right now, across every subsystem",
    info=True,
)
def aria_status(assistant, params: dict, message: str) -> dict:
    env = _env()
    snapshot = env.environment_status(limit=int(params.get("limit") or 50))
    lines = [f"**ARIA is {snapshot['state']}**"]
    lines.extend(f"- {line}" for line in snapshot["doing"])
    policy = snapshot["policy"]
    lines.append(
        f"Autonomy: {policy['autonomy']}"
        + (" (SAFE MODE — nothing new will start)" if policy["safe_mode"] else "")
        + f" · worker {'on' if policy['worker_enabled'] else 'off'}"
    )
    if snapshot["unavailable"]:
        lines.append("Unavailable: " + ", ".join(sorted(snapshot["unavailable"])))
    return ok("\n".join(lines), module="general", environment=snapshot)


@register_action(
    "aria_plan",
    module="general",
    description="Explain how ARIA would approach a request, without doing it",
    info=True,
)
def aria_plan(assistant, params: dict, message: str) -> dict:
    env = _env()
    request = (params.get("request") or message or "").strip()
    if not request:
        return err("aria_plan needs a request.", module="general")
    try:
        decision = env.triage(
            request,
            autonomy=(params.get("autonomy") or "").strip(),
            requester=(params.get("requester") or "").strip(),
        )
    except env.PolicyError as exc:
        return err(str(exc), module="general", error_kind="policy")
    if decision["route"] in (env.AGENT, env.WORKFLOW):
        decision["suggested_agent"] = env.suggested_agent(decision["capabilities"])
    return ok(decision["explanation"], module="general", plan=decision)


@register_action(
    "aria_autonomy",
    module="general",
    description="Show the current autonomy level and what it permits",
    info=True,
)
def aria_autonomy(assistant, params: dict, message: str) -> dict:
    env = _env()
    snapshot = env.policy_snapshot()
    lines = [
        f"**Autonomy: {snapshot['autonomy']}**" + (" — SAFE MODE" if snapshot["safe_mode"] else ""),
        f"Permits: {', '.join(snapshot['capabilities'])}",
        f"Bounds: {snapshot['bounds']}",
        snapshot["notes"],
    ]
    return ok("\n".join(lines), module="general", policy=snapshot)


@register_action(
    "aria_recover",
    module="general",
    description="Report work interrupted by a restart (apply+force to make it resumable)",
    info=True,
)
def aria_recover(assistant, params: dict, message: str) -> dict:
    env = _env()
    apply = bool(params.get("apply"))
    outcome = env.recover_on_demand(apply=apply, force=bool(params.get("force")))
    parts = [f"{k}: {len(v)}" for k, v in outcome["recovered"].items() if v]
    if outcome["total"]:
        head = "Recovered" if outcome.get("applied") else "Interrupted work"
        text = f"{head} {outcome['total']} item(s) — " + ", ".join(parts)
    else:
        text = "No interrupted work."
    if outcome.get("refused"):
        text += "\n\n" + outcome["refused"]
    startup = outcome.get("startup") or {}
    if startup.get("total"):
        text += f"\n\nThis process recovered {startup['total']} item(s) at startup."
    if outcome["errors"]:
        return err(
            text + f" (errors: {outcome['errors']})",
            module="general",
            error_kind="partial_recovery",
            recovery=outcome,
        )
    return ok(text, module="general", recovery=outcome)


@register_action(
    "aria_provenance",
    module="general",
    description="Show the end-to-end chain behind a piece of autonomous work",
    info=True,
)
def aria_provenance(assistant, params: dict, message: str) -> dict:
    env = _env()
    workflow_id = (params.get("workflow_id") or "").strip()
    request_id = (params.get("request_id") or "").strip()
    if workflow_id:
        graph = env.for_workflow(workflow_id)
        if not graph.get("ok"):
            return err(graph.get("error") or "not found", module="general", error_kind="not_found")
        lines = [
            f"**Provenance for {workflow_id}** — {graph['state']}",
            "Nodes: " + ", ".join(f"{k}×{v}" for k, v in sorted(graph["counts"].items())),
        ]
        if graph["unestablished_links"]:
            lines.append("Unestablished: " + "; ".join(graph["unestablished_links"][:4]))
        return ok("\n".join(lines), module="general", provenance=graph)
    if request_id:
        return ok(
            f"Provenance for request {request_id}",
            module="general",
            provenance=env.for_request(request_id),
        )
    return err("aria_provenance needs workflow_id or request_id.", module="general")


@register_action(
    "aria_lifecycle",
    module="general",
    description="Explain a subsystem state in ARIA's unified lifecycle",
    info=True,
)
def aria_lifecycle(assistant, params: dict, message: str) -> dict:
    kind = (params.get("kind") or "").strip()
    state = (params.get("state") or "").strip()
    if not kind or not state:
        return err("aria_lifecycle needs kind and state.", module="general")
    from jarvis.integration import lifecycle

    detail = lifecycle.as_dict(kind, state)
    return ok(
        f"{kind}/{state} → {detail['state']}: {detail['description']}",
        module="general",
        lifecycle=detail,
    )
