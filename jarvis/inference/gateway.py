"""Unified inference gateway — Ollama primary, LiteLLM optional router."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from jarvis.inference.policy import InferenceRoute, select_route

logger = logging.getLogger("jarvis.inference")


def litellm_url() -> str:
    return os.getenv("JARVIS_LITELLM_URL", "http://127.0.0.1:4000").rstrip("/")


def litellm_available() -> bool:
    try:
        with urllib.request.urlopen(f"{litellm_url()}/health/readiness", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def gateway_status() -> dict[str, Any]:
    from jarvis.inference.policy import route_summary

    summary = route_summary()
    summary["litellm_url"] = litellm_url()
    return summary


def _ollama_chat_with_usage(model: str, messages: list[dict], **kwargs) -> tuple[str, dict]:
    from ollama import chat

    from jarvis.llm import _normalize_chat_kwargs, _with_system, usage_from_response
    from jarvis.ollama_runtime import default_options

    normalized = _normalize_chat_kwargs(kwargs)
    options = dict(normalized.get("options") or {})
    for key, value in default_options().items():
        options.setdefault(key, value)
    normalized["options"] = options

    response = chat(model=model, messages=_with_system(messages), **normalized)
    return response["message"]["content"], usage_from_response(response)


def _ollama_stream(model: str, messages: list[dict], **kwargs) -> Iterator[str]:
    from ollama import chat

    from jarvis.llm import _normalize_chat_kwargs, _with_system
    from jarvis.ollama_runtime import default_options

    normalized = _normalize_chat_kwargs(kwargs)
    options = dict(normalized.get("options") or {})
    for key, value in default_options().items():
        options.setdefault(key, value)
    normalized["options"] = options

    stream = chat(
        model=model,
        messages=_with_system(messages),
        stream=True,
        **normalized,
    )
    for chunk in stream:
        if chunk.get("message", {}).get("content"):
            yield chunk["message"]["content"]


def _litellm_chat_with_usage(model: str, messages: list[dict], **kwargs) -> tuple[str, dict]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    options = kwargs.get("options") or {}
    if "temperature" in kwargs:
        payload["temperature"] = kwargs["temperature"]
    elif "temperature" in options:
        payload["temperature"] = options["temperature"]
    if "num_predict" in options:
        payload["max_tokens"] = options["num_predict"]
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{litellm_url()}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            req, timeout=int(os.getenv("JARVIS_LITELLM_TIMEOUT", "120"))
        ) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:400]
        raise RuntimeError(f"LiteLLM error ({exc.code}): {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"LiteLLM unavailable at {litellm_url()}: {exc}") from exc

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    text = message.get("content") or ""
    usage = data.get("usage") or {}
    usage_out = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "backend": "litellm",
        "model": model,
    }
    return text, usage_out


def _litellm_stream(model: str, messages: list[dict], **kwargs) -> Iterator[str]:
    payload = {"model": model, "messages": messages, "stream": True}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{litellm_url()}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(
        req, timeout=int(os.getenv("JARVIS_LITELLM_TIMEOUT", "120"))
    ) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                data = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            delta = ((data.get("choices") or [{}])[0].get("delta") or {}).get("content")
            if delta:
                yield delta


def chat_with_usage(
    model: str,
    messages: list[dict],
    *,
    role: str = "general",
    route: InferenceRoute | None = None,
    **kwargs,
) -> tuple[str, dict]:
    """Route chat to the best available backend with benchmark-driven model/hardware."""
    from jarvis.inference.execution_policy import apply_policy_to_route
    from jarvis.nlu.placement import ollama_options_for_device

    overlay = apply_policy_to_route(model=model, role=role)
    chosen_model = str(overlay.get("model") or model)
    hardware = str(overlay.get("hardware") or "cpu")
    options = dict(kwargs.get("options") or {})
    for key, value in ollama_options_for_device(hardware).items():
        options.setdefault(key, value)
    kwargs["options"] = options

    chosen = route or select_route(
        chosen_model,
        role=role,
        messages=messages,
        lock_model=overlay.get("source") == "benchmark",
    )
    if chosen.backend == "litellm":
        try:
            text, usage = _litellm_chat_with_usage(chosen.model, messages, **kwargs)
            usage["route_reason"] = chosen.reason
            usage["execution_model"] = chosen.model
            usage["execution_hardware"] = hardware
            usage["execution_source"] = overlay.get("source")
            usage["execution_reason"] = overlay.get("reason")
            usage["execution_workload"] = overlay.get("workload")
            return text, usage
        except Exception as exc:
            logger.warning("LiteLLM failed (%s), falling back to Ollama: %s", chosen.reason, exc)
    text, usage = _ollama_chat_with_usage(chosen.model, messages, **kwargs)
    usage["backend"] = "ollama"
    usage["route_reason"] = (
        chosen.reason
        if route
        else select_route(
            chosen_model,
            role=role,
            messages=messages,
            lock_model=overlay.get("source") == "benchmark",
        ).reason
    )
    usage["execution_model"] = chosen.model
    usage["execution_hardware"] = hardware
    usage["execution_provider"] = "ollama"
    usage["execution_source"] = overlay.get("source")
    usage["execution_reason"] = overlay.get("reason")
    usage["execution_workload"] = overlay.get("workload")
    usage["execution_fallback_model"] = overlay.get("fallback_model")
    usage["execution_fallback_hardware"] = overlay.get("fallback_hardware")
    return text, usage


def stream_chat(
    model: str,
    messages: list[dict],
    *,
    role: str = "general",
    route: InferenceRoute | None = None,
    **kwargs,
) -> Iterator[str]:
    from jarvis.inference.execution_policy import apply_policy_to_route
    from jarvis.nlu.placement import ollama_options_for_device

    overlay = apply_policy_to_route(model=model, role=role)
    chosen_model = str(overlay.get("model") or model)
    hardware = str(overlay.get("hardware") or "cpu")
    options = dict(kwargs.get("options") or {})
    for key, value in ollama_options_for_device(hardware).items():
        options.setdefault(key, value)
    kwargs["options"] = options

    chosen = route or select_route(
        chosen_model,
        role=role,
        messages=messages,
        lock_model=overlay.get("source") == "benchmark",
    )
    if chosen.backend == "litellm":
        try:
            yield from _litellm_stream(chosen.model, messages, **kwargs)
            return
        except Exception as exc:
            logger.warning("LiteLLM stream failed, falling back to Ollama: %s", exc)
    yield from _ollama_stream(chosen.model, messages, **kwargs)


def embed_text(model: str, text: str) -> list[float]:
    """Embeddings always local via Ollama for now."""
    from jarvis.llm import embed as ollama_embed

    return ollama_embed(model, text)
