"""Passive Conversation Trace metadata builder (execution only — no CoT).

Observes routing outcomes. Never participates in routing or cognition.
"""

from __future__ import annotations

from typing import Any


def _profile_flags() -> dict[str, Any]:
    try:
        from aria_core.identity import is_uncensored, profile_name

        unc = bool(is_uncensored())
        return {
            "profile": "uncensored" if unc else "standard",
            "profile_name": profile_name(),
            "uncensored": unc,
        }
    except Exception:
        try:
            from jarvis.config import is_uncensored

            unc = bool(is_uncensored())
            return {
                "profile": "uncensored" if unc else "standard",
                "profile_name": "Aria",
                "uncensored": unc,
            }
        except Exception:
            return {"profile": "standard", "profile_name": "Aria", "uncensored": False}


def _organ_slot(
    *,
    used: bool = False,
    read: bool = False,
    write: bool = False,
    skipped: bool = True,
    latency_ms: float | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "used": used,
        "read": read,
        "write": write,
        "skipped": skipped if not used else False,
        "latency_ms": latency_ms,
        "errors": list(errors or []),
    }


def infer_organs(intent: dict[str, Any], action: str) -> dict[str, Any]:
    """Best-effort organ usage from intent/action — metadata only."""
    stage = str(intent.get("router_stage") or intent.get("router") or "")
    reflex = stage in ("pre_nlu_reflex",) or intent.get("router") == "reflex"
    organs = {
        "memory": _organ_slot(),
        "knowledge": _organ_slot(),
        "reference": _organ_slot(),
        "planning": _organ_slot(),
        "reasoning": _organ_slot(),
        "runtime": _organ_slot(),
        "learning": _organ_slot(),
        "applications": _organ_slot(),
    }
    if reflex or action in (
        "greeting",
        "reflex_reply",
        "session_interrupt",
        "session_continue",
        "session_repeat",
        "clear",
        "capabilities",
        "models_info",
    ):
        return organs

    if action in ("remember", "memory_forget", "memory_correct", "forget"):
        organs["memory"] = _organ_slot(used=True, write=True, skipped=False)
    elif action in ("recall", "memory_search", "memory_about_user"):
        organs["memory"] = _organ_slot(used=True, read=True, skipped=False)
    elif action == "cognitive_compose":
        caps = intent.get("params", {}).get("capabilities") or []
        plan = intent.get("params", {}).get("plan") or {}
        for name in caps or plan.get("selected") or []:
            key = str(name)
            if key in organs:
                organs[key] = _organ_slot(used=True, read=True, skipped=False)
        for name in plan.get("executed") or []:
            key = str(name)
            if key in organs:
                organs[key] = _organ_slot(used=True, read=True, skipped=False)
    elif action in ("search_reference", "reference") or "reference" in action:
        organs["reference"] = _organ_slot(used=True, read=True, skipped=False)
    elif action.startswith("runtime_") or action == "status_summary":
        organs["runtime"] = _organ_slot(used=True, read=True, skipped=False)
    elif action in ("learn_about", "learn"):
        organs["learning"] = _organ_slot(used=True, write=True, skipped=False)
        organs["knowledge"] = _organ_slot(used=True, write=True, skipped=False)
    elif action.startswith("plan") or action in ("planner_set_timer",):
        organs["planning"] = _organ_slot(used=True, write=True, skipped=False)
    elif action == "chat":
        organs["memory"] = _organ_slot(used=True, read=True, skipped=False)
        organs["reasoning"] = _organ_slot(used=True, read=True, skipped=False)
        organs["knowledge"] = _organ_slot(used=True, read=True, skipped=False)
    elif action.startswith("coding_") or action.startswith("ha_"):
        organs["applications"] = _organ_slot(used=True, read=True, skipped=False)
        organs["reasoning"] = _organ_slot(used=True, read=True, skipped=False)
    else:
        organs["reasoning"] = _organ_slot(used=True, read=True, skipped=False)
    return organs


def build_stages(
    *,
    intent: dict[str, Any],
    action: str,
    route: str,
    handler: str,
    latency_ms: float | None,
    route_latency_ms: float | None,
    organs: dict[str, Any],
    error: str | None,
) -> list[dict[str, Any]]:
    """Linear execution stages for waterfall / user view (metadata only)."""
    stages: list[dict[str, Any]] = []
    reflex_used = (
        intent.get("router") == "reflex"
        or str(intent.get("router_stage") or "") == "pre_nlu_reflex"
    )
    stages.append(
        {
            "id": "reflex",
            "label": "Reflex",
            "status": "matched" if reflex_used else "escalated",
            "latency_ms": route_latency_ms if reflex_used else None,
            "detail": {
                "matched": reflex_used,
                "category": intent.get("reflex_category"),
                "pattern": intent.get("reflex_pattern"),
                "confidence": intent.get("reflex_confidence"),
                "reason": intent.get("thinking") or intent.get("route_reason"),
            },
        }
    )
    nlu = intent.get("semantic_report") or intent.get("nlu") or {}
    semantic = nlu.get("semantic") if isinstance(nlu, dict) else {}
    nlu_invoked = bool(semantic) or str(intent.get("router_stage") or "").startswith("nlu")
    stages.append(
        {
            "id": "nlu",
            "label": "NLU",
            "status": "invoked" if nlu_invoked and not reflex_used else "skipped",
            "latency_ms": (semantic or {}).get("latency_ms")
            if isinstance(semantic, dict)
            else None,
            "detail": {
                "invoked": nlu_invoked and not reflex_used,
                "intent": (semantic or {}).get("intent")
                if isinstance(semantic, dict)
                else intent.get("final_intent"),
                "confidence": intent.get("route_confidence") or (semantic or {}).get("confidence"),
                "model": (semantic or {}).get("model") if isinstance(semantic, dict) else None,
                "clarification": bool(intent.get("needs_clarification")),
            },
        }
    )
    stages.append(
        {
            "id": "capabilities",
            "label": "Capability Bus",
            "status": "skipped" if reflex_used else "passthrough",
            "detail": {
                "requested": [] if reflex_used else [action],
                "execution_order": [] if reflex_used else [action],
                "skipped": ["*"] if reflex_used else [],
            },
        }
    )
    stages.append(
        {
            "id": "cognition",
            "label": "Cognitive Orchestrator",
            "status": "skipped" if reflex_used else "passthrough",
            "detail": {
                "pipeline": None if reflex_used else action,
                "subsystems_consulted": [k for k, v in organs.items() if v.get("used")],
                "subsystems_skipped": [k for k, v in organs.items() if v.get("skipped")],
            },
        }
    )
    for name, slot in organs.items():
        if slot.get("used") or not reflex_used:
            stages.append(
                {
                    "id": f"organ.{name}",
                    "label": name.title(),
                    "status": (
                        "error"
                        if slot.get("errors")
                        else ("used" if slot.get("used") else "skipped")
                    ),
                    "latency_ms": slot.get("latency_ms"),
                    "detail": slot,
                }
            )
    stages.append(
        {
            "id": "response",
            "label": "Response",
            "status": "error" if error else "ok",
            "latency_ms": latency_ms,
            "detail": {"handler": handler, "route": route, "action": action},
        }
    )
    return stages


def _capability_plan_block(intent: dict[str, Any], action: str) -> dict[str, Any]:
    """Planning + execution visibility for Conversation Trace (metadata only)."""
    from aria_core.observability import capability_plan_view

    params = intent.get("params") or {}
    plan = params.get("plan") if isinstance(params.get("plan"), dict) else {}
    # Prefer post-exec plan if attached after compose
    if isinstance(params.get("composed_plan"), dict):
        plan = params["composed_plan"]
    view = capability_plan_view(plan, action=action)
    provenance = plan.get("provenance") or params.get("provenance") or []
    confidence = plan.get("section_confidence") or params.get("section_confidence") or {}
    return {
        **view,
        "provenance": provenance,
        "section_confidence": confidence,
        "final_response_latency_ms": params.get("compose_duration_ms")
        or plan.get("duration_ms")
        or (plan.get("plan_view") or {}).get("final_response_latency_ms"),
        "composition_stage_label": (
            "composer"
            if action == "cognitive_compose" or plan.get("combine")
            else "single_capability"
        ),
    }


def _execution_metadata(
    intent: dict[str, Any],
    *,
    action: str,
    route: str,
) -> dict[str, Any]:
    """Capability/provider/model/hardware — never CoT."""
    explicit = intent.get("execution") if isinstance(intent.get("execution"), dict) else {}
    usage = intent.get("usage") if isinstance(intent.get("usage"), dict) else {}
    result = intent.get("result") if isinstance(intent.get("result"), dict) else {}
    result_usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    merged = {**usage, **result_usage, **explicit}

    request_class = str(
        explicit.get("request_class") or intent.get("request_class") or action or "chat"
    ).lower()

    plan: dict[str, Any] = {}
    try:
        from jarvis.inference.execution_policy import resolve_execution

        # Chat-style LLM actions need require_llm; reflex/reference stay non-LLM.
        require_llm = None
        if action in ("chat", "code", "review", "vision", "planner", "reason"):
            require_llm = True
        plan = resolve_execution(request_class, require_llm=require_llm).to_dict()
    except Exception:
        plan = {}

    return {
        "capability": merged.get("capability") or plan.get("capability") or action,
        "provider": merged.get("execution_provider")
        or merged.get("provider")
        or plan.get("provider")
        or ("none" if route in ("Greeting", "Local") else "ollama"),
        "model": merged.get("execution_model") or merged.get("model") or plan.get("model"),
        "hardware": merged.get("execution_hardware")
        or merged.get("hardware")
        or plan.get("hardware"),
        "execution_path": merged.get("execution_path") or plan.get("execution_path") or route,
        "workload": merged.get("execution_workload") or plan.get("workload"),
        "benchmark_profile": merged.get("execution_source") or plan.get("source"),
        "benchmark_reason": merged.get("execution_reason") or plan.get("reason"),
        "fallback_reason": merged.get("execution_fallback_reason")
        or plan.get("fallback_reason")
        or "",
        "fallback_model": merged.get("execution_fallback_model") or None,
        "fallback_hardware": merged.get("execution_fallback_hardware") or None,
        "expected_latency_ms": plan.get("expected_latency_ms"),
        "confidence": plan.get("confidence"),
        "latency_ms": merged.get("total_duration_ms") or merged.get("latency_ms"),
    }


def build_conversation_trace(
    *,
    prompt: str,
    intent: dict[str, Any],
    action: str,
    route: str,
    handler: str,
    latency_ms: float | None,
    route_latency_ms: float | None,
    response_length: int,
    error: str | None,
    conversation_id: str,
    request_id: str = "",
) -> dict[str, Any]:
    """Assemble Conversation Trace block attached to a routing record."""
    profile = _profile_flags()
    reflex_used = (
        intent.get("router") == "reflex"
        or str(intent.get("router_stage") or "") == "pre_nlu_reflex"
    )
    nlu = intent.get("semantic_report") or intent.get("nlu") or {}
    semantic = nlu.get("semantic") if isinstance(nlu, dict) else {}
    organs = infer_organs(intent, action)
    stages = build_stages(
        intent=intent,
        action=action,
        route=route,
        handler=handler,
        latency_ms=latency_ms,
        route_latency_ms=route_latency_ms,
        organs=organs,
        error=error,
    )
    return {
        "schema": "conversation_trace/1",
        "conversation_id": conversation_id,
        "request_id": request_id or "",
        "prompt_len": len(prompt or ""),
        "response_len": int(response_length or 0),
        **profile,
        "latency_ms": latency_ms,
        "route_latency_ms": route_latency_ms,
        "reflex": {
            "used": reflex_used,
            "matched": reflex_used,
            "escalated": not reflex_used,
            "category": intent.get("reflex_category"),
            "pattern": intent.get("reflex_pattern"),
            "confidence": intent.get("reflex_confidence"),
            "latency_ms": route_latency_ms if reflex_used else None,
            "reason": intent.get("thinking") if reflex_used else "escalated_to_cognition",
        },
        "nlu": {
            "invoked": bool(semantic) and not reflex_used,
            "intent": (semantic or {}).get("intent") if isinstance(semantic, dict) else None,
            "confidence": intent.get("route_confidence"),
            "model": (semantic or {}).get("model") if isinstance(semantic, dict) else None,
            "latency_ms": (semantic or {}).get("latency_ms")
            if isinstance(semantic, dict)
            else None,
            "clarification_requested": bool(intent.get("needs_clarification")),
        },
        "execution": _execution_metadata(intent, action=action, route=route),
        "memory_operation": {
            "action": action
            if action.startswith("memory")
            or action
            in (
                "remember",
                "recall",
                "forget",
            )
            else None,
            "retrieval": intent.get("memory_retrieval")
            or (intent.get("params") or {}).get("memory_retrieval"),
        },
        "capability_bus": {
            "requested": []
            if reflex_used
            else (
                list((intent.get("params") or {}).get("capabilities") or [action])
                if action == "cognitive_compose"
                else [action]
            ),
            "execution_order": []
            if reflex_used
            else (
                list(
                    ((intent.get("params") or {}).get("plan") or {}).get("execution_order")
                    or (intent.get("params") or {}).get("capabilities")
                    or [action]
                )
                if action == "cognitive_compose"
                else [action]
            ),
            "skipped": ["all"]
            if reflex_used
            else (
                list(((intent.get("params") or {}).get("plan") or {}).get("skipped") or [])
                if action == "cognitive_compose"
                else []
            ),
            "failures": [error] if error else [],
        },
        "cognition": {
            "pipeline": None if reflex_used else action,
            "execution_order": []
            if reflex_used
            else (
                list(
                    ((intent.get("params") or {}).get("plan") or {}).get("execution_order")
                    or (intent.get("params") or {}).get("capabilities")
                    or [action]
                )
                if action == "cognitive_compose"
                else [action]
            ),
            "subsystems_consulted": [k for k, v in organs.items() if v.get("used")],
            "subsystems_skipped": [k for k, v in organs.items() if v.get("skipped")],
            "composition_stage": action == "cognitive_compose",
            "latency_ms": None if reflex_used else latency_ms,
        },
        "organs": organs,
        "capability_plan": _capability_plan_block(intent, action),
        "reference": _reference_diagnostics(intent, action),
        "events": {
            "note": "Event counts correlated at Mission Control read time",
            "published": None,
            "names": [],
        },
        "stages": stages,
        "summary": _summary_line(
            reflex_used=reflex_used,
            action=action,
            organs=organs,
            latency_ms=latency_ms,
            error=error,
        ),
    }


def _reference_diagnostics(intent: dict[str, Any], action: str) -> dict[str, Any]:
    """Attach Reference Engine execution metadata when Reference participated."""
    params = intent.get("params") or {}
    diag = params.get("reference_diagnostics")
    if not diag:
        data = params.get("reference_data") or {}
        if isinstance(data, dict):
            diag = data.get("diagnostics")
    if not diag:
        try:
            from jarvis.reference_engine import reference_history

            hist = reference_history(limit=1)
            if hist and (
                action in ("search_reference", "reference", "cognitive_compose")
                or "reference" in action
            ):
                diag = hist[-1]
        except Exception:
            diag = None
    used = bool(
        action in ("search_reference", "reference")
        or "reference" in (params.get("capabilities") or [])
        or (isinstance(diag, dict) and diag.get("mode"))
    )
    if not isinstance(diag, dict):
        return {
            "used": used,
            "note": "No reference diagnostics attached",
        }
    return {
        "used": True,
        "mode": diag.get("mode"),
        "documents_searched": diag.get("documents_searched"),
        "documents_selected": diag.get("documents_selected") or [],
        "documents_rejected": diag.get("documents_rejected") or [],
        "ranking_scores": [
            {"title": d.get("title"), "score": d.get("score")}
            for d in (diag.get("documents_selected") or [])
        ],
        "stages": diag.get("stages") or {},
        "search_ms": diag.get("search_ms"),
        "ranking_ms": diag.get("ranking_ms"),
        "qa_ms": diag.get("qa_ms"),
        "summarization_ms": diag.get("summarization_ms"),
        "composition_ms": diag.get("composition_ms"),
        "total_ms": diag.get("total_ms"),
        "unknown": bool(diag.get("unknown")),
        "dump_blocked": bool(diag.get("dump_blocked", True)),
    }


def _summary_line(
    *,
    reflex_used: bool,
    action: str,
    organs: dict[str, Any],
    latency_ms: float | None,
    error: str | None,
) -> str:
    used = [k for k, v in organs.items() if v.get("used")]
    if reflex_used:
        path = f"Reflex → {action}"
    elif used:
        path = f"Intent {action} → " + " → ".join(u.title() for u in used[:4])
    else:
        path = f"Intent {action}"
    lat = f"{latency_ms} ms" if latency_ms is not None else "—"
    status = "ERROR" if error else "OK"
    return f"{path} · {status} · {lat}"


def format_user_view(trace: dict[str, Any], *, prompt_preview: str = "") -> str:
    """Plain-text execution view — no CoT / hidden prompts."""
    lines = ["-" * 60]
    if prompt_preview:
        lines.append(f"Prompt ({trace.get('prompt_len', 0)} chars)")
        lines.append((prompt_preview or "")[:200])
        lines.append("↓")
    for stage in trace.get("stages") or []:
        label = stage.get("label") or stage.get("id")
        status = stage.get("status") or ""
        ms = stage.get("latency_ms")
        ms_s = f" · {ms} ms" if ms is not None else ""
        lines.append(f"{label}: {status}{ms_s}")
        detail = stage.get("detail") or {}
        if stage.get("id") == "reflex":
            lines.append(f"  Matched: {'Yes' if detail.get('matched') else 'No'}")
            if detail.get("category"):
                lines.append(f"  Category: {detail.get('category')}")
        if stage.get("id") == "nlu" and detail.get("invoked"):
            lines.append(f"  Intent: {detail.get('intent') or '—'}")
            if detail.get("confidence") is not None:
                lines.append(f"  Confidence: {detail.get('confidence')}")
        if str(stage.get("id") or "").startswith("organ."):
            flags = []
            if detail.get("read"):
                flags.append("Read")
            if detail.get("write"):
                flags.append("Write")
            if detail.get("skipped"):
                flags.append("Skipped")
            if flags:
                lines.append("  " + " · ".join(flags))
        lines.append("↓")
    lines.append(f"Response · Latency: {trace.get('latency_ms', '—')} ms")
    lines.append(f"Profile: {trace.get('profile', 'standard')}")
    lines.append("-" * 60)
    return "\n".join(lines)
