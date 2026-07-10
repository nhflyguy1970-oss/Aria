"""Routing inspector — record platform execution paths (not LLM chain-of-thought)."""

from __future__ import annotations

import contextvars
import os
import time
from typing import Any

_HIGH_LATENCY_MS = float(os.getenv("JARVIS_ROUTING_HIGH_LATENCY_MS", "2000"))
_PENDING: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "routing_pending", default=None
)


def classify_route(action: str) -> str:
    act = (action or "chat").strip()
    if act.startswith("runtime_") or act == "status_summary":
        return "Runtime"
    if act in ("web_search", "learn_about"):
        return "Search" if act == "web_search" else "Knowledge"
    if act in ("reference_search", "documentation_search") or act.startswith(
        ("reference_", "documentation_")
    ):
        return "Reference"
    if act.startswith("memory_") or act in ("remember", "recall"):
        return "Memory"
    if act.startswith("coding_") or act in (
        "find_references",
        "extract_function",
        "move_module",
        "rename_symbol",
        "syntax_check",
        "lsp_definition",
        "lsp_references",
        "lsp_hover",
        "lsp_format",
        "lsp_symbols",
    ):
        return "Coding"
    if act in (
        "generate_image",
        "edit_image",
        "inpaint_image",
        "analyze_image",
        "describe_image",
        "ocr_image",
        "ocr_structured_image",
        "image_to_code",
        "analyze_region",
        "compare_images",
        "batch_vision",
        "analyze_video_frame",
    ):
        return "Vision"
    if act.startswith("ha_") or "homeassistant" in act:
        return "Automation"
    if "voice" in act or "audio" in act or act == "transcribe":
        return "Voice"
    if act in ("inference_status",) or act.startswith("inference_"):
        return "Inference"
    if act.startswith("workstation_") or act in (
        "upgrade_wizard",
        "upgrade_apply",
        "upgrade_verify",
        "upgrade_rollback",
    ):
        return "Planning"
    if act in ("morning_briefing", "briefing_news_detail"):
        return "Knowledge"
    if act.endswith("_job") or act in ("media_job",):
        return "Jobs"
    if act == "chat":
        return "Chat"
    if act in ("capabilities", "models_info", "greeting"):
        return "Tools"
    return act or "Chat"


def handler_for_action(action: str) -> str:
    route = classify_route(action)
    mapping = {
        "Runtime": "RuntimeClient",
        "Search": "WebSearch",
        "Knowledge": "KnowledgeEngine",
        "Reference": "ReferenceEngine",
        "Memory": "MemoryStore",
        "Coding": "EngineeringEngine",
        "Vision": "VisionPipeline",
        "Voice": "AudioPipeline",
        "Automation": "AutomationEngine",
        "Inference": "InferenceGateway",
        "Planning": "WorkstationOps",
        "Jobs": "JobsCenter",
        "Chat": "ConversationEngine",
        "Tools": "Capabilities",
    }
    return mapping.get(route, action)


def backend_for_route(route: str, *, mission_control_source: str | None = None) -> str:
    if route == "Runtime":
        if mission_control_source == "http":
            return "Mission Control API"
        if mission_control_source == "in_process":
            return "Mission Control"
        return "Mission Control"
    if route == "Search":
        return "WebSearch"
    if route in ("Knowledge", "Memory"):
        return route
    if route == "Coding":
        return "Engineering"
    if route == "Reference":
        return "Local Reference"
    if route == "Chat":
        return "LLM"
    return route


def build_execution_flow(
    *,
    prompt: str,
    intent: str,
    route: str,
    handler: str,
    backend: str,
    stage: str,
) -> list[str]:
    lines = ["User", "    ↓", "Conversation Context", "    ↓", "Natural Language Understanding"]
    if route == "Runtime":
        lines.extend(
            ["    ↓", "Runtime Priority", "    ↓", handler, "    ↓", backend, "    ↓", "Response"]
        )
    elif route == "Search":
        lines.extend(["    ↓", "Web Search", "    ↓", "Summarizer", "    ↓", "Response"])
    elif route == "Knowledge":
        lines.extend(["    ↓", "Knowledge Engine", "    ↓", handler, "    ↓", "Response"])
    elif route == "Reference":
        lines.extend(["    ↓", "Reference Engine", "    ↓", "Local Sources", "    ↓", "Response"])
    elif route == "Memory":
        lines.extend(["    ↓", "Memory Store", "    ↓", handler, "    ↓", "Response"])
    elif route == "Coding":
        lines.extend(["    ↓", "Coding Router", "    ↓", handler, "    ↓", "Response"])
    elif route == "Vision":
        lines.extend(["    ↓", "Vision Router", "    ↓", handler, "    ↓", "Response"])
    elif route == "Chat":
        lines.extend(["    ↓", "General Chat", "    ↓", "LLM", "    ↓", "Response"])
    else:
        lines.extend(["    ↓", route, "    ↓", handler, "    ↓", backend, "    ↓", "Response"])
    return lines


def _mission_control_source() -> str | None:
    try:
        from jarvis.runtime_client import get_runtime_client

        client = get_runtime_client()
        mode = client._connection_mode  # noqa: SLF001
        return mode if mode in ("http", "in_process") else None
    except Exception:
        return None


def begin_routing(
    *,
    prompt: str,
    intent: dict[str, Any],
    conversation_id: str = "",
    route_latency_ms: float | None = None,
) -> None:
    _PENDING.set(
        {
            "prompt": prompt,
            "intent": intent,
            "conversation_id": conversation_id,
            "route_latency_ms": route_latency_ms,
            "t_start": time.perf_counter(),
        }
    )


def complete_routing(result: dict[str, Any] | None = None, *, error: str | None = None) -> None:
    ctx = _PENDING.get()
    if not ctx:
        return
    _PENDING.set(None)
    latency_ms = round((time.perf_counter() - ctx["t_start"]) * 1000, 1)
    record_prompt_execution(
        prompt=ctx["prompt"],
        intent=ctx["intent"],
        conversation_id=ctx.get("conversation_id") or "",
        latency_ms=latency_ms,
        route_latency_ms=ctx.get("route_latency_ms"),
        result=result,
        error=error,
    )


def record_prompt_execution(
    *,
    prompt: str,
    intent: dict[str, Any],
    conversation_id: str = "",
    latency_ms: float | None = None,
    route_latency_ms: float | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Record one complete prompt execution path."""
    action = str(intent.get("action") or "chat")
    trace = intent.get("route_trace") or {}
    route = str(trace.get("route") or classify_route(action))
    handler = str(trace.get("handler") or intent.get("route_handler") or handler_for_action(action))
    mc_source = None
    if route == "Runtime":
        mc_source = _mission_control_source()
    backend = backend_for_route(route, mission_control_source=mc_source)
    fallback_used = bool(
        intent.get("route_reason") == "finalize_web_search_guard"
        or trace.get("reason", "").find("fallback") >= 0
        or (trace.get("stage") == "fallback_chat" and action != "chat")
    )
    response_length = 0
    if result:
        msg = result.get("message") or result.get("answer") or ""
        if isinstance(msg, str):
            response_length = len(msg)
        if not error and result.get("ok") is False:
            error = str(result.get("error") or result.get("message") or "")[:500] or None

    record = {
        "conversation_id": conversation_id,
        "prompt": (prompt or "")[:500],
        "intent": action,
        "route": route,
        "handler": handler,
        "backend": backend,
        "latency_ms": latency_ms,
        "route_latency_ms": route_latency_ms,
        "confidence": trace.get("confidence") or intent.get("route_confidence"),
        "fallback_used": fallback_used,
        "fallback": trace.get("reason") if fallback_used else None,
        "mission_control_source": mc_source,
        "response_length": response_length,
        "error": error,
        "flow": build_execution_flow(
            prompt=prompt,
            intent=action,
            route=route,
            handler=handler,
            backend=backend,
            stage=str(trace.get("stage") or ""),
        ),
        "filter_category": route,
        "stage": trace.get("stage"),
        "reason": trace.get("reason"),
        "rule_matched": intent.get("route_reason") or trace.get("reason"),
        "router_stage": trace.get("stage"),
        "mc_endpoint": "/api/mission-control" if route == "Runtime" else None,
        "semantic_report": intent.get("semantic_report") or intent.get("nlu") or {},
        "clarification_accepted": bool(intent.get("clarification_accepted")),
        "clarification_rejected": bool(intent.get("clarification_rejected")),
        "final_intent": intent.get("final_intent"),
        "confidence_band": intent.get("confidence_band"),
        "flag_for_review": bool(intent.get("flag_for_review")),
        "debug": {
            "intent_classifier_result": action,
            "rule_matched": intent.get("route_reason") or trace.get("reason"),
            "router_stage": trace.get("stage"),
            "selected_handler": handler,
            "mission_control_endpoint": "/api/mission-control" if route == "Runtime" else None,
            "execution_duration_ms": latency_ms,
            "route_latency_ms": route_latency_ms,
        },
    }
    try:
        from aiplatform.mission_control.routing_log import record_routing

        saved = record_routing(record)
    except ImportError:
        saved = _local_record(record)
    else:
        saved = saved or record
    try:
        from aiplatform.mission_control.timeline import record_timeline_event

        record_timeline_event(
            "routing_complete",
            application="aria",
            component="router",
            category="routing",
            severity="error" if error else "info",
            duration_ms=int(latency_ms) if latency_ms else None,
            source="routing_inspector",
            result="error" if error else "ok",
            detail=f"{action} → {route} ({handler})",
            related_routing_id=str(saved.get("id") or ""),
        )
    except Exception:
        pass
    return saved


def _local_record(record: dict[str, Any]) -> dict[str, Any]:
    import json
    import uuid
    from pathlib import Path

    from jarvis.config import DATA_DIR

    path = Path(DATA_DIR) / "routing_log.jsonl"
    item = {**record, "id": str(uuid.uuid4()), "ts": time.time()}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return item


def last_routing_record() -> dict[str, Any] | None:
    try:
        from aiplatform.mission_control.routing_log import list_routing

        items = list_routing(limit=1)
        return items[0] if items else None
    except ImportError:
        return None


def routing_history(*, limit: int = 10) -> list[dict[str, Any]]:
    try:
        from aiplatform.mission_control.routing_log import list_routing

        return list_routing(limit=limit)
    except ImportError:
        return []


def routing_stats_summary() -> dict[str, Any]:
    try:
        from aiplatform.mission_control.routing_log import routing_stats

        return routing_stats()
    except ImportError:
        return {"ok": True, "count": 0}


def format_routing_record_markdown(record: dict[str, Any] | None) -> str:
    if not record:
        return "No routing records yet."
    lines = [
        "## Last routing decision",
        "",
        f"**Prompt:** {record.get('prompt')}",
        f"**Intent:** `{record.get('intent')}`",
        f"**Route:** {record.get('route')}",
        f"**Handler:** {record.get('handler')}",
        f"**Backend:** {record.get('backend')}",
        f"**Latency:** {record.get('latency_ms')} ms",
        f"**Confidence:** {record.get('confidence')}",
        f"**Fallback:** {record.get('fallback') or 'None'}",
        f"**Mission Control source:** {record.get('mission_control_source') or '—'}",
    ]
    if record.get("error"):
        lines.append(f"**Error:** {record.get('error')}")
    flow = record.get("flow") or []
    if flow:
        lines.extend(["", "**Execution flow:**", "```", *flow, "```"])
    return "\n".join(lines)


def format_routing_stats_markdown(stats: dict[str, Any]) -> str:
    if not stats.get("count"):
        return "No routing statistics yet."
    last = stats.get("last_route") or {}
    return "\n".join(
        [
            "## Routing statistics",
            "",
            f"**Records:** {stats.get('count')}",
            f"**Average latency:** {stats.get('average_latency_ms')} ms",
            f"**Last intent:** `{last.get('intent', '—')}`",
            f"**Runtime:** {stats.get('runtime_pct')}%",
            f"**Knowledge:** {stats.get('knowledge_pct')}%",
            f"**Search:** {stats.get('search_pct')}%",
            f"**Tools:** {stats.get('tool_pct')}%",
            f"**Fallback:** {stats.get('fallback_pct')}%",
            f"**Errors:** {stats.get('error_pct')}%",
        ]
    )


def live_status_class(record: dict[str, Any]) -> str:
    if record.get("error"):
        return "error"
    if record.get("fallback_used"):
        return "fallback"
    lat = record.get("latency_ms")
    if lat is not None and float(lat) >= _HIGH_LATENCY_MS:
        return "high_latency"
    return "ok"


ROUTING_COMMANDS = {
    "routing": "routing_last",
    "routing last": "routing_last",
    "routing history": "routing_history",
    "routing stats": "routing_stats",
}


def is_routing_command(message: str) -> str | None:
    text = (message or "").strip().lower()
    if text.startswith("/"):
        text = text[1:].strip()
    return ROUTING_COMMANDS.get(text)
