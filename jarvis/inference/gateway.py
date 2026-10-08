"""Unified inference gateway — Ollama primary, LiteLLM optional router."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from jarvis.inference import boundary
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
    boundary.require_local_model_name(model)
    from ollama import chat

    from jarvis.llm import _normalize_chat_kwargs, _with_system, usage_from_response
    from jarvis.ollama_runtime import default_options

    normalized = _normalize_chat_kwargs(kwargs)
    options = dict(normalized.get("options") or {})
    for key, value in default_options().items():
        options.setdefault(key, value)
    normalized["options"] = options

    keep_alive = normalized.pop("keep_alive", None)
    if keep_alive is None:
        keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30m").strip() or "30m"

    response = chat(
        model=model,
        messages=_with_system(messages),
        keep_alive=keep_alive,
        **normalized,
    )
    return response["message"]["content"], usage_from_response(response)


def _ollama_stream(
    model: str,
    messages: list[dict],
    *,
    usage: dict[str, Any] | None = None,
    **kwargs,
) -> Iterator[str]:
    boundary.require_local_model_name(model)
    from ollama import chat

    from jarvis.llm import _normalize_chat_kwargs, _with_system, usage_from_response
    from jarvis.ollama_runtime import default_options

    normalized = _normalize_chat_kwargs(kwargs)
    options = dict(normalized.get("options") or {})
    for key, value in default_options().items():
        options.setdefault(key, value)
    normalized["options"] = options

    keep_alive = normalized.pop("keep_alive", None)
    if keep_alive is None:
        keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30m").strip() or "30m"

    stream = chat(
        model=model,
        messages=_with_system(messages),
        stream=True,
        keep_alive=keep_alive,
        **normalized,
    )
    for chunk in stream:
        if usage is not None:
            usage.update(usage_from_response(chunk))
        if chunk.get("message", {}).get("content"):
            yield chunk["message"]["content"]


def _cloud_guard(model: str) -> None:
    """Last line before network egress: the global cloud policy, re-checked."""
    refusal = boundary.cloud_refusal(model)
    if refusal:
        raise boundary.CloudNotPermitted(f"cloud call to {model!r} blocked: {refusal}")


def _litellm_chat_with_usage(model: str, messages: list[dict], **kwargs) -> tuple[str, dict]:
    _cloud_guard(model)
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
    _cloud_guard(model)
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


def _prepare(model: str, role: str, kwargs: dict[str, Any]) -> tuple[dict, str, str, bool]:
    """Execution-policy overlay (benchmark/Settings model, device options)."""
    from jarvis.inference.execution_policy import apply_policy_to_route
    from jarvis.nlu.placement import ollama_options_for_device

    overlay = apply_policy_to_route(model=model, role=role)
    chosen_model = str(overlay.get("model") or model)
    hardware = str(overlay.get("hardware") or "cpu")
    options = dict(kwargs.get("options") or {})
    for key, value in ollama_options_for_device(hardware).items():
        options.setdefault(key, value)
    kwargs["options"] = options
    lock = overlay.get("source") in ("benchmark", "user_config", "env", "explicit")
    return overlay, chosen_model, hardware, lock


def _authorize(
    chosen: InferenceRoute, role: str, receipt: boundary.Receipt
) -> InferenceRoute:
    """Re-check the route at execution time — a caller-supplied route included."""
    if boundary.is_cloud_model(chosen.model) or getattr(chosen, "cloud", False):
        refusal = boundary.cloud_refusal(chosen.model, privacy=receipt.privacy)
        if refusal:
            receipt.policy.append(f"cloud refused: {refusal}")
            return InferenceRoute(
                backend="ollama",
                model=boundary.local_fallback(role),
                reason=f"cloud_refused: {refusal}",
                local=True,
            )
        if chosen.backend != "litellm":
            # A cloud target with no cloud gateway: answer locally, say so.
            receipt.policy.append("cloud gateway unavailable; installed local model used")
            return InferenceRoute(
                backend="ollama",
                model=boundary.local_fallback(role),
                reason="cloud_gateway_unavailable_local_fallback",
                local=True,
            )
    else:
        reason = str(getattr(chosen, "reason", "") or "")
        if reason.startswith("cloud_refused") or "local_fallback" in reason:
            receipt.policy.append(reason)
    return chosen


def _trace(chosen: InferenceRoute, hardware: str, overlay: dict, *, stream: bool) -> None:
    try:
        from jarvis.routing_trace import record_gateway

        decision = {
            "backend": chosen.backend,
            "model": chosen.model,
            "reason": chosen.reason,
            "hardware": hardware,
            "execution_path": "cloud"
            if getattr(chosen, "cloud", False)
            else ("local_gpu" if hardware != "cpu" else "cpu"),
            "provider": "litellm" if chosen.backend == "litellm" else "ollama",
            "policy_source": overlay.get("source"),
        }
        if stream:
            decision["stream"] = True
        record_gateway(decision=decision)
    except Exception:
        pass


def _usage_fields(
    usage: dict, chosen: InferenceRoute, hardware: str, overlay: dict, receipt: boundary.Receipt
) -> None:
    final = receipt.final
    usage["backend"] = "litellm" if chosen.backend == "litellm" else "ollama"
    usage["route_reason"] = chosen.reason
    usage["execution_model"] = final.model if final else chosen.model
    usage["execution_hardware"] = hardware
    usage["execution_provider"] = final.provider if final else usage["backend"]
    usage["execution_locality"] = final.locality if final else boundary.LOCAL
    usage["execution_source"] = overlay.get("source")
    usage["execution_reason"] = overlay.get("reason")
    usage["execution_workload"] = overlay.get("workload")
    usage["execution_fallback_model"] = overlay.get("fallback_model")
    usage["execution_fallback_hardware"] = overlay.get("fallback_hardware")
    usage["receipt"] = receipt.to_dict()


def _run_sync(chosen: InferenceRoute, messages: list[dict], kwargs: dict, receipt) -> tuple[str, dict]:
    attempt = receipt.attempt(chosen.model)
    try:
        if chosen.backend == "litellm":
            text, usage = _litellm_chat_with_usage(chosen.model, messages, **kwargs)
        else:
            text, usage = _ollama_chat_with_usage(chosen.model, messages, **kwargs)
    except boundary.InferenceError as exc:
        attempt.finish("failed", error=str(exc))
        raise
    except Exception as exc:  # noqa: BLE001 - classified: provider fault
        attempt.finish("failed", error=f"{type(exc).__name__}: {exc}")
        raise boundary.ProviderUnavailable(
            f"{attempt.provider} model {chosen.model!r} failed: {exc}"
        ) from exc
    attempt.output_chars = len(text or "")
    attempt.prompt_tokens = (usage or {}).get("prompt_tokens")
    attempt.completion_tokens = (usage or {}).get("completion_tokens")
    attempt.finish("completed")
    return text, dict(usage or {})


def chat_with_usage(
    model: str,
    messages: list[dict],
    *,
    role: str = "general",
    route: InferenceRoute | None = None,
    privacy: str = "",
    **kwargs,
) -> tuple[str, dict]:
    """One completed answer, from the model the policy allows, with a receipt.

    A cloud attempt that fails before answering may be replaced by the
    installed local model for the role; the receipt lists both attempts. A
    policy refusal, a capability mismatch or a local failure is raised, never
    papered over.
    """
    overlay, chosen_model, hardware, lock = _prepare(model, role, kwargs)
    receipt = boundary.Receipt(
        role=role,
        requested_model=model,
        privacy=boundary.privacy_class(messages, privacy),
        stream=False,
    )
    chosen = route or select_route(chosen_model, role=role, messages=messages, lock_model=lock)
    chosen = _authorize(chosen, role, receipt)
    boundary.check_capabilities(chosen.model, boundary.requirements_from_kwargs(kwargs, messages))
    _trace(chosen, hardware, overlay, stream=False)
    try:
        text, usage = _run_sync(chosen, messages, kwargs, receipt)
    except boundary.ProviderUnavailable as exc:
        if not (chosen.backend == "litellm" and exc.fallback_eligible):
            receipt.close("failed")
            raise
        logger.warning("Cloud attempt failed (%s); trying installed local model", exc)
        fallback = InferenceRoute(
            backend="ollama",
            model=boundary.local_fallback(role),
            reason="cloud_failed_local_fallback",
            local=True,
        )
        receipt.policy.append("cloud attempt failed before answering; local fallback")
        boundary.check_capabilities(
            fallback.model, boundary.requirements_from_kwargs(kwargs, messages)
        )
        try:
            text, usage = _run_sync(fallback, messages, kwargs, receipt)
        except boundary.InferenceError:
            receipt.close("failed")
            raise
        chosen = fallback
    except boundary.InferenceError:
        receipt.close("failed")
        raise
    receipt.close("completed")
    _usage_fields(usage, chosen, hardware, overlay, receipt)
    return text, usage


def _ollama_tools(model: str, messages: list[dict], tools: list[dict], **kwargs) -> tuple[dict, dict]:
    boundary.require_local_model_name(model)
    from ollama import chat

    from jarvis.llm import usage_from_response

    response = chat(model=model, messages=messages, tools=tools, **kwargs)
    message = response.get("message") or {}
    calls = []
    for call in message.get("tool_calls") or []:
        fn = call.get("function") or {}
        args = fn.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"_unparsed": args}
        calls.append({"name": fn.get("name") or "", "arguments": args or {}})
    return {"content": message.get("content") or "", "tool_calls": calls}, usage_from_response(response)


def _litellm_tools(model: str, messages: list[dict], tools: list[dict], **kwargs) -> tuple[dict, dict]:
    _cloud_guard(model)
    body = json.dumps({"model": model, "messages": messages, "tools": tools, "stream": False})
    req = urllib.request.Request(
        f"{litellm_url()}/v1/chat/completions",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=int(os.getenv("JARVIS_LITELLM_TIMEOUT", "120"))) as resp:
        data = json.loads(resp.read().decode())
    choice = (data.get("choices") or [{}])[0]
    if choice.get("finish_reason") not in (None, "stop", "tool_calls"):
        raise RuntimeError(f"provider ended the turn with {choice.get('finish_reason')!r}")
    message = choice.get("message") or {}
    calls = []
    for call in message.get("tool_calls") or []:
        fn = call.get("function") or {}
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {"_unparsed": fn.get("arguments")}
        calls.append({"name": fn.get("name") or "", "arguments": args})
    usage = data.get("usage") or {}
    return {"content": message.get("content") or "", "tool_calls": calls}, {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
    }


def chat_with_tools(
    model: str,
    messages: list[dict],
    tools: list[dict],
    *,
    role: str = "tool_calling",
    route: InferenceRoute | None = None,
    privacy: str = "",
    **kwargs,
) -> tuple[dict, dict]:
    """A structured tool-call turn under the same policy as chat.

    Returns ``{"content", "tool_calls": [{"name", "arguments"}]}`` from one
    *completed* attempt, plus usage with a receipt. The gateway never executes
    tools: ARIA acts only on a completed response, so a failed or replaced
    attempt can never have triggered a side effect.
    """
    overlay, chosen_model, hardware, lock = _prepare(model, role, kwargs)
    kwargs.pop("options", None)
    receipt = boundary.Receipt(
        role=role,
        requested_model=model,
        privacy=boundary.privacy_class(messages, privacy),
        stream=False,
    )
    chosen = route or select_route(chosen_model, role=role, messages=messages, lock_model=lock)
    chosen = _authorize(chosen, role, receipt)
    _trace(chosen, hardware, overlay, stream=False)

    def run(target: InferenceRoute) -> tuple[dict, dict]:
        boundary.check_capabilities(target.model, {"tools"})
        attempt = receipt.attempt(target.model)
        try:
            if target.backend == "litellm":
                result, usage = _litellm_tools(target.model, messages, tools)
            else:
                result, usage = _ollama_tools(target.model, messages, tools)
        except boundary.InferenceError as exc:
            attempt.finish("failed", error=str(exc))
            raise
        except Exception as exc:  # noqa: BLE001
            attempt.finish("failed", error=f"{type(exc).__name__}: {exc}")
            raise boundary.ProviderUnavailable(f"{target.model!r} failed: {exc}") from exc
        attempt.prompt_tokens = usage.get("prompt_tokens")
        attempt.completion_tokens = usage.get("completion_tokens")
        attempt.finish("completed")
        return result, usage

    try:
        try:
            result, usage = run(chosen)
        except boundary.ProviderUnavailable:
            if chosen.backend != "litellm":
                raise
            receipt.policy.append("cloud tool turn failed before answering; local fallback")
            chosen = InferenceRoute(
                backend="ollama",
                model=boundary.local_fallback(role),
                reason="cloud_failed_local_fallback",
                local=True,
            )
            result, usage = run(chosen)
    except boundary.InferenceError:
        receipt.close("failed")
        raise
    receipt.close("completed")
    _usage_fields(usage, chosen, hardware, overlay, receipt)
    return result, usage


def _attempt_stream(
    chosen: InferenceRoute,
    messages: list[dict],
    kwargs: dict,
    receipt: boundary.Receipt,
    usage: dict | None,
    cancel_check,
) -> Iterator[str]:
    """One streaming attempt. Failure before output → ProviderUnavailable;
    failure after output → StreamInterrupted (never continued elsewhere)."""
    attempt = receipt.attempt(chosen.model)
    produced = 0
    try:
        if chosen.backend == "litellm":
            source = _litellm_stream(chosen.model, messages, **kwargs)
        else:
            source = _ollama_stream(chosen.model, messages, usage=usage, **kwargs)
        for chunk in source:
            if cancel_check is not None and cancel_check():
                attempt.finish("cancelled")
                close = getattr(source, "close", None)
                if close:
                    close()
                return
            if not chunk:
                continue
            if attempt.first_token_ms is None:
                attempt.first_token_ms = round((time.time() - attempt.started_at) * 1000, 1)
            produced += len(chunk)
            attempt.output_chars = produced
            yield chunk
    except boundary.InferenceError as exc:
        attempt.finish("failed", error=str(exc))
        raise
    except Exception as exc:  # noqa: BLE001 - classified below
        if produced:
            attempt.finish("interrupted", error=f"{type(exc).__name__}: {exc}")
            raise boundary.StreamInterrupted(
                f"The {attempt.provider} response was interrupted after {produced} characters "
                f"({type(exc).__name__}). The partial answer is incomplete and was not "
                "continued by another model.",
                provider=attempt.provider,
                model=chosen.model,
                partial_chars=produced,
            ) from exc
        attempt.finish("failed", error=f"{type(exc).__name__}: {exc}")
        raise boundary.ProviderUnavailable(
            f"{attempt.provider} model {chosen.model!r} failed before answering: {exc}"
        ) from exc
    if usage is not None:
        attempt.prompt_tokens = usage.get("prompt_tokens")
        attempt.completion_tokens = usage.get("completion_tokens")
    attempt.finish("completed")


def stream_chat(
    model: str,
    messages: list[dict],
    *,
    role: str = "general",
    route: InferenceRoute | None = None,
    privacy: str = "",
    cancel_check=None,
    **kwargs,
) -> Iterator[str]:
    """Stream one attempt's answer under the same policy as sync chat.

    Fallback to the installed local model happens only when the first attempt
    failed before producing output. Once text has been streamed, a failure
    raises StreamInterrupted: the receipt records it, and nothing from a second
    model is appended to a partial first answer.
    """
    usage = kwargs.pop("usage", None)
    overlay, chosen_model, hardware, lock = _prepare(model, role, kwargs)
    receipt = boundary.Receipt(
        role=role,
        requested_model=model,
        privacy=boundary.privacy_class(messages, privacy),
        stream=True,
    )
    chosen = route or select_route(chosen_model, role=role, messages=messages, lock_model=lock)
    chosen = _authorize(chosen, role, receipt)
    boundary.check_capabilities(chosen.model, boundary.requirements_from_kwargs(kwargs, messages))
    _trace(chosen, hardware, overlay, stream=True)
    if usage is not None:
        _usage_fields(usage, chosen, hardware, overlay, receipt)
    status = "failed"
    try:
        try:
            yield from _attempt_stream(chosen, messages, kwargs, receipt, usage, cancel_check)
        except boundary.ProviderUnavailable as exc:
            if chosen.backend != "litellm":
                raise
            logger.warning("Cloud stream failed before output (%s); local fallback", exc)
            receipt.policy.append("cloud stream failed before output; local fallback")
            chosen = InferenceRoute(
                backend="ollama",
                model=boundary.local_fallback(role),
                reason="cloud_failed_local_fallback",
                local=True,
            )
            boundary.check_capabilities(
                chosen.model, boundary.requirements_from_kwargs(kwargs, messages)
            )
            yield from _attempt_stream(chosen, messages, kwargs, receipt, usage, cancel_check)
        final = receipt.final
        status = final.status if final else "failed"
    except boundary.StreamInterrupted:
        status = "interrupted"
        raise
    finally:
        receipt.close(status)
        if usage is not None:
            _usage_fields(usage, chosen, hardware, overlay, receipt)


def embed_text(model: str, text: str) -> list[float]:
    """Embeddings always local via Ollama — honor chat-priority / keep_alive=0."""
    from jarvis.llm import embed_text as jarvis_embed_text
    from jarvis.llm import model_for

    # Prefer role resolution when caller passes a blank model.
    if not (model or "").strip():
        model = model_for("embed")
    # Temporarily force model_for to the requested name when it differs.
    if (model or "").strip() and (model_for("embed") or "").strip() != (model or "").strip():
        from ollama import embed

        from jarvis.ollama_runtime import chat_priority_active, unload_model

        if chat_priority_active():
            return []
        try:
            response = embed(model=model, input=text, keep_alive=0)
            vectors = response["embeddings"][0]
        except Exception:
            return []
        try:
            unload_model(model)
        except Exception:
            pass
        return vectors
    return jarvis_embed_text(text)
