"""Model routing handlers — inventory, explainable routing, health, audit."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _routing():
    from jarvis import model_routing

    return model_routing


def _number(params: dict, key: str, default):
    """Read a number, keeping an explicit zero.

    `params.get(key) or default` quietly turns a deliberate 0 into the default,
    which silently gave "no fallbacks" two of them.
    """
    raw = params.get(key)
    if raw is None or raw == "":
        return default
    return raw


def _request_from_params(params: dict):
    from jarvis.model_routing.request import (
        BALANCED,
        DEFAULT_OUTPUT_RESERVE,
        RoutingRequest,
    )

    excluded = params.get("excluded_models") or []
    if isinstance(excluded, str):
        excluded = [excluded]
    required = params.get("required_capabilities") or []
    if isinstance(required, str):
        required = [required]
    # Validate names here so an unknown capability is reported as a bad request.
    # Normalisation happens deep inside routing, where the ValueError escaped the
    # handler and surfaced as an internal "execution" failure instead.
    from jarvis.model_routing import capabilities as caps

    required = [caps.normalise(c) for c in required]
    return RoutingRequest(
        task_type=(params.get("task_type") or "general").strip(),
        role=(params.get("role") or "").strip(),
        required_capabilities=tuple(required),
        min_context_tokens=int(_number(params, "min_context_tokens", 0)),
        require_tools=bool(params.get("require_tools")),
        require_vision=bool(params.get("require_vision")),
        require_structured_output=bool(params.get("require_structured_output")),
        local_only=bool(params.get("local_only", True)),
        preferred_model=(params.get("preferred_model") or "").strip(),
        preferred_provider=(params.get("preferred_provider") or "").strip(),
        output_reserve_tokens=int(_number(params, "output_reserve_tokens", DEFAULT_OUTPUT_RESERVE)),
        timeout_s=float(_number(params, "timeout_s", 120.0)),
        excluded_models=tuple(excluded),
        latency_preference=(params.get("latency_preference") or BALANCED).strip(),
        max_fallbacks=int(_number(params, "max_fallbacks", 2)),
        agent_id=(params.get("agent_id") or params.get("requester") or "").strip(),
        skill_id=(params.get("skill_id") or "").strip(),
        mission_id=(params.get("mission_id") or "").strip(),
        requester=(params.get("requester") or params.get("agent_id") or "").strip(),
    )


@register_action(
    "model_inventory",
    module="general",
    description="List available models with discovered capabilities",
    info=True,
)
def model_inventory(assistant, params: dict, message: str) -> dict:
    routing = _routing()
    models = routing.all_profiles(force=bool(params.get("refresh")))
    if not models:
        return err(
            "No models discovered. Is the model provider reachable?",
            module="general",
            error_kind="no_models",
            models=[],
        )
    rows = [m.to_dict() for m in models]
    lines = [
        f"- `{m['model_id']}` ctx={m['context_window'] or '?'} "
        f"tools={m['capabilities'].get('tool_use', 'unknown')} "
        f"vision={m['capabilities'].get('vision', 'unknown')} "
        f"[{m['latency_class']}]"
        for m in rows[: int(params.get("limit") or 20)]
    ]
    return ok("\n".join(lines), module="general", models=rows, count=len(rows))


@register_action(
    "model_route",
    module="general",
    description="Explain which model would be selected for a task",
    info=True,
)
def model_route(assistant, params: dict, message: str) -> dict:
    routing = _routing()
    try:
        request = _request_from_params(params)
    except ValueError as exc:
        return err(str(exc), module="general", error_kind="invalid_request")
    decision = routing.route(request)
    if not decision.ok:
        return err(
            decision.reason,
            module="general",
            error_kind="no_compatible_model",
            decision=decision.to_dict(),
        )
    lines = [
        f"**{decision.selected_model}** ({decision.provider}) — {decision.selection_method}",
        decision.reason,
        f"Compatible: {len(decision.accepted())} · Rejected: {len(decision.rejected())}",
    ]
    if decision.capability_evidence:
        lines.append(
            "Evidence: "
            + ", ".join(f"{k}={v}" for k, v in sorted(decision.capability_evidence.items()))
        )
    return ok("\n".join(lines), module="general", decision=decision.to_dict())


@register_action(
    "model_health",
    module="general",
    description="Show model health and routing counters",
    info=True,
)
def model_health(assistant, params: dict, message: str) -> dict:
    routing = _routing()
    entries = routing.snapshot()
    counters = routing.counters()
    if not entries:
        return ok(
            "No model health recorded yet.",
            module="general",
            health=[],
            counters=counters,
        )
    lines = [
        f"- `{h['model_id']}` ok={h['successes']} fail={h['failures']} "
        f"rate={h['failure_rate']} avg={h['average_latency_ms']}ms"
        + (f" AVOIDED ({h['last_failure_kind']})" if h["avoided"] else "")
        for h in entries
    ]
    return ok("\n".join(lines), module="general", health=entries, counters=counters)


@register_action(
    "model_health_reset", module="general", description="Clear a model's temporary avoidance"
)
def model_health_reset(assistant, params: dict, message: str) -> dict:
    routing = _routing()
    model = (params.get("model") or "").strip()
    if not model:
        return err("model_health_reset needs model.", module="general")
    if not routing.clear_health(model):
        return err(f"No health record for {model}.", module="general", error_kind="not_tracked")
    return ok(f"Cleared avoidance for `{model}`.", module="general", model=model)


@register_action(
    "model_routing_history",
    module="general",
    description="Show routed model invocations",
    info=True,
)
def model_routing_history(assistant, params: dict, message: str) -> dict:
    routing = _routing()
    invocation_id = (params.get("invocation_id") or "").strip()
    if invocation_id:
        from jarvis.model_routing import store as routing_store

        record = routing_store.get(invocation_id)
        if not record:
            return err(f"No such routing record: {invocation_id}", module="general")
        return ok(
            f"`{record['final_model'] or record['selected_model']}` — {record['status']}",
            module="general",
            invocation=record,
        )
    rows = routing.history(
        model=(params.get("model") or "").strip(),
        requester=(params.get("requester") or "").strip(),
        mission_id=(params.get("mission_id") or "").strip(),
        limit=int(params.get("limit") or 20),
    )
    if not rows:
        return ok("No routed invocations recorded.", module="general", invocations=[])
    lines = [
        f"- `{r['id']}` {r['final_model'] or r['selected_model']} [{r['status']}]"
        + (f" fallback×{r['fallback_count']}" if r["fallback_count"] else "")
        for r in rows
    ]
    return ok("\n".join(lines), module="general", invocations=rows)


@register_action(
    "model_execute",
    module="general",
    description="Run a prompt on a routed model, with bounded fallback",
)
def model_execute(assistant, params: dict, message: str) -> dict:
    """Route, invoke and fall back — the whole path in one action.

    This is where routing stops being advice and becomes what actually ran.
    The result names the model that produced it, and says plainly when that was
    not the first choice.
    """
    routing = _routing()
    prompt = (params.get("prompt") or message or "").strip()
    if not prompt:
        return err("model_execute needs a prompt.", module="general")
    try:
        request = _request_from_params(params)
    except ValueError as exc:
        return err(str(exc), module="general", error_kind="invalid_request")

    mission_id = request.mission_id
    cancel_check = None
    if mission_id:
        from jarvis.missions import store as mstore

        def cancel_check() -> bool:  # noqa: E306
            return mstore.cancel_requested(mission_id)

    validator = None
    if request.require_structured_output:
        import json as _json

        def validator(result) -> bool:  # noqa: E306
            try:
                _json.loads(str(result))
                return True
            except (TypeError, ValueError):
                return False

    payload = {
        "prompt": prompt,
        "system": (params.get("system") or "").strip(),
        "role": request.role or "conversation",
    }
    if request.require_structured_output:
        # Ollama constrains decoding to JSON when asked; this is the provider
        # feature the structured_output capability is based on.
        payload["options"] = {"format": "json"}

    envelope = routing.execute(request, payload, cancel_check=cancel_check, validator=validator)
    text = (
        f"`{envelope['final_model'] or envelope['selected_model']}` → {envelope['status']}"
        f" ({envelope['duration_ms']}ms)"
    )
    if envelope["status"] != routing.SUCCESS:
        return err(
            envelope.get("error") or text,
            module="general",
            error_kind=envelope.get("failure_kind") or envelope["status"],
            envelope=envelope,
        )
    return ok(
        text
        + (f" [fallback ×{envelope['fallback_count']}]" if envelope["fallback_active"] else ""),
        module="general",
        envelope=envelope,
        response=envelope["result"],
        model=envelope["final_model"],
    )


@register_action(
    "model_step",
    module="general",
    description="Run a routed model call as a mission step (used by the mission worker)",
)
def model_step(assistant, params: dict, message: str) -> dict:
    """Mission-backed routed execution; honours mission cancellation."""
    routing = _routing()
    result = model_execute(assistant, params, message)
    if result.get("ok"):
        return result
    envelope = result.get("envelope") or {}
    status = envelope.get("status")
    # A returned dict counts as a completed step, so a failed or cancelled model
    # call has to raise or the mission would record work that did not happen.
    from jarvis.missions.engine import MissionCancelled, RetryableError

    detail = f"model {status}: {envelope.get('error') or result.get('message')}"
    if status == routing.CANCELLED:
        raise MissionCancelled(detail)
    if envelope.get("failure_kind") in ("timeout", "connection_failure", "unavailable"):
        raise RetryableError(detail)
    raise RuntimeError(detail)
