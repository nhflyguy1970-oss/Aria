"""Timeout / failure classification — never dump everything as STREAM_IDLE_TIMEOUT."""

from __future__ import annotations

from typing import Any


def classify_failure(
    *,
    code: str = "",
    message: str = "",
    provider_alive: bool | None = None,
    got_progress: bool = False,
    probe: dict[str, Any] | None = None,
    http_status: int | None = None,
) -> dict[str, Any]:
    """Return structured failure class + operator-facing explanation."""
    msg = (message or "").lower()
    code_u = (code or "").upper()
    probe = probe or {}
    detail = str(probe.get("detail") or probe.get("error") or "").lower()

    cls = "unknown_timeout"
    title = "Provider timed out"
    explanation = "The model provider did not complete the response in time."

    # Classify stream timeouts before generic unreachable so mid-stream loss
    # is "provider_disconnected" rather than "provider_unreachable".
    if code_u == "FIRST_PROGRESS_TIMEOUT" or (not got_progress and "timeout" in msg and "stopped receiving" not in msg):
        if provider_alive:
            cls = "first_token_timeout"
            title = "No tokens received"
            explanation = (
                "The provider accepted the request but never produced the first token. "
                "It may be loading a model or wedged on generate."
            )
        else:
            cls = "provider_disconnected"
            title = "Provider disconnected"
            explanation = "No first token arrived and the provider did not respond to a health ping."
    elif code_u == "STREAM_IDLE_TIMEOUT" or "stopped receiving tokens" in msg:
        if provider_alive:
            cls = "stream_stalled"
            title = "Stream stalled"
            explanation = (
                "Tokens started, then stopped. The provider is still reachable but the stream went idle."
            )
        else:
            cls = "provider_disconnected"
            title = "Provider disconnected mid-stream"
            explanation = "The stream went idle and the provider no longer responds to health checks."
    elif provider_alive is False or "connection refused" in msg or "unreachable" in msg:
        cls = "provider_unreachable"
        title = "Provider unreachable"
        explanation = "Aria could not reach the model provider endpoint."
    elif "oom" in msg or "out of memory" in msg or ("cuda" in msg and "memory" in msg):
        cls = "oom"
        title = "Out of memory"
        explanation = "The provider or GPU ran out of memory while generating."
    elif "context" in msg and ("long" in msg or "length" in msg or "too large" in msg):
        cls = "context_too_large"
        title = "Context too large"
        explanation = "The prompt or conversation likely exceeded the model context window."
    elif "loading" in msg or "pulling" in msg or code_u == "MODEL_LOADING":
        cls = "model_loading"
        title = "Model loading"
        explanation = "The provider is still loading the selected model into memory."
    elif "crash" in msg or "segfault" in msg or "exited" in msg:
        cls = "model_crashed"
        title = "Model crashed"
        explanation = "The model process appears to have crashed mid-generation."
    elif "overloaded" in msg or "busy" in msg or "429" in msg or http_status == 429:
        cls = "provider_overloaded"
        title = "Provider overloaded"
        explanation = "The provider is busy or rate-limiting requests."
    elif "gpu" in msg and ("unavailable" in msg or "not found" in msg):
        cls = "gpu_unavailable"
        title = "GPU unavailable"
        explanation = "GPU acceleration is unavailable; the provider may be stuck on CPU."
    elif "network" in msg or "broken pipe" in msg or "reset by peer" in msg:
        cls = "network_interruption"
        title = "Network interruption"
        explanation = "The HTTP stream to the provider was interrupted."
    elif "wedged" in detail or (probe.get("ok") is False and "timeout" in detail):
        cls = "provider_overloaded"
        title = "Provider generate path wedged"
        explanation = "Tags may respond, but a generate probe timed out — the daemon is likely wedged."

    actions = _recommended_actions(cls, provider_alive=provider_alive)
    return {
        "ok": True,
        "class": cls,
        "code": code_u or cls.upper(),
        "title": title,
        "explanation": explanation,
        "provider_alive": provider_alive,
        "got_progress": got_progress,
        "recommended_actions": actions,
        "message": message,
    }


def _recommended_actions(cls: str, *, provider_alive: bool | None) -> list[dict[str, str]]:
    actions = [
        {"id": "retry", "label": "Retry"},
        {"id": "diagnostics", "label": "View Diagnostics"},
    ]
    if cls in ("provider_unreachable", "provider_disconnected", "network_interruption"):
        actions.insert(1, {"id": "restart_provider", "label": "Restart Provider"})
        actions.insert(1, {"id": "reconnect", "label": "Reconnect"})
    elif cls in ("stream_stalled", "first_token_timeout", "provider_overloaded", "model_loading"):
        actions.insert(1, {"id": "restart_provider", "label": "Restart Provider"})
        actions.insert(1, {"id": "switch_model", "label": "Switch Model"})
        if provider_alive is False:
            actions.insert(1, {"id": "reconnect", "label": "Reconnect"})
    elif cls in ("oom", "context_too_large", "model_crashed"):
        actions.insert(1, {"id": "switch_model", "label": "Switch Model"})
        actions.insert(1, {"id": "restart_provider", "label": "Restart Provider"})
    else:
        actions.insert(1, {"id": "switch_model", "label": "Switch Model"})
        actions.insert(1, {"id": "switch_provider", "label": "Switch Provider"})
        actions.insert(1, {"id": "restart_provider", "label": "Restart Provider"})
    # dedupe by id preserving order
    seen = set()
    out = []
    for a in actions:
        if a["id"] in seen:
            continue
        seen.add(a["id"])
        out.append(a)
    return out


def operator_copy(classified: dict[str, Any], *, provider: str = "", model: str = "") -> str:
    lines = [
        classified.get("title") or "Provider issue",
        "",
        classified.get("explanation") or "",
    ]
    if provider:
        lines.append(f"Provider: {provider}")
    if model:
        lines.append(f"Model: {model}")
    lines.append(f"Class: {classified.get('class')}")
    return "\n".join(lines).strip()
