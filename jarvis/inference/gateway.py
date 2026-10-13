"""Unified inference gateway — Ollama primary, LiteLLM optional router."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from jarvis.inference import boundary
from jarvis.inference.policy import InferenceRoute, _estimate_context_tokens, select_route

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

    from jarvis import gpu_scheduler

    with gpu_scheduler.admit_ollama(model, options) as job:
        options.update(job.options)
        call = _ollama_client_chat(job)
        # Always stream internally: closing the stream is what stops Ollama when the
        # thermal / host-RAM cutoff fires mid-generation.
        parts: list[str] = []
        usage: dict[str, Any] = {}
        stream = call(model=model, messages=_with_system(messages), stream=True, keep_alive=keep_alive, **normalized)
        try:
            for chunk in stream:
                job.check()
                usage.update(usage_from_response(chunk))
                parts.append((chunk.get("message") or {}).get("content") or "")
        finally:
            close = getattr(stream, "close", None)
            if close:
                close()
        return "".join(parts), usage


def _ollama_client_chat(job):
    """The chat callable for an admitted job: ARIA's default Ollama, or the RX 7600 helper."""
    if not job.host:
        from ollama import chat

        return chat
    from ollama import Client

    return Client(host=job.host).chat


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

    from jarvis import gpu_scheduler

    with gpu_scheduler.admit_ollama(model, options) as job:
        options.update(job.options)
        stream = _ollama_client_chat(job)(
            model=model,
            messages=_with_system(messages),
            stream=True,
            keep_alive=keep_alive,
            **normalized,
        )
        try:
            for chunk in stream:
                job.check()  # thermal / host-RAM cutoff stops the generation
                if usage is not None:
                    usage.update(usage_from_response(chunk))
                if chunk.get("message", {}).get("content"):
                    yield chunk["message"]["content"]
        finally:
            close = getattr(stream, "close", None)
            if close:
                close()


def _cloud_guard(model: str) -> None:
    """Last line before network egress: the global cloud policy, re-checked,
    and — for paid cloud models — an owner-authorized, priced reservation."""
    refusal = boundary.cloud_refusal(model)
    if refusal:
        raise boundary.CloudNotPermitted(f"cloud call to {model!r} blocked: {refusal}")
    if boundary.is_cloud_model(model):
        from jarvis.inference.cloud_policy import require_reservation

        require_reservation(boundary.provider_of(model))


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

    explicit_model = bool(kwargs.pop("explicit_model", False))
    overlay = apply_policy_to_route(model=model, role=role)
    if explicit_model or boundary.is_cloud_model(model):
        # A selected provider/model must survive the second policy overlay.
        overlay = {**overlay, "model": model, "source": "explicit", "reason": "explicit model selection"}
    chosen_model = str(overlay.get("model") or model)
    hardware = str(overlay.get("hardware") or "cpu")
    options = dict(kwargs.get("options") or {})
    for key, value in ollama_options_for_device(hardware).items():
        options.setdefault(key, value)
    kwargs["options"] = options
    lock = overlay.get("source") in ("benchmark", "user_config", "env", "explicit")
    return overlay, chosen_model, hardware, lock


def _require_selected_model(chosen, requested: str, explicit: bool, receipt) -> None:
    if explicit and chosen.model != requested:
        reason = chosen.reason
        if reason == "cloud_gateway_unavailable_local_fallback":
            reason = "provider credentials are locked/missing, or its gateway is unavailable"
        receipt.policy.append(f"selected model refused: {reason}; no substitution")
        receipt.close("failed")
        raise boundary.CloudNotPermitted(
            f"Selected model `{requested}` could not be used: {reason}. No fallback was run."
        )


def _note_overlay(receipt, requested: str, chosen_model: str, overlay: dict, route) -> None:
    """Say so when execution policy replaced the requested model before routing."""
    if route is None and chosen_model and chosen_model != requested:
        receipt.policy.append(
            f"execution policy ({overlay.get('source') or 'default'}) selected "
            f"{chosen_model} instead of {requested}"
        )


# Short structured jobs. An uncapped utility call let a base completion model
# generate for 8+ minutes on the 7k-token router prompt (it never emits a stop
# token); a thinking model spends its budget thinking. Callers' explicit
# options still win.
UTILITY_OUTPUT_CAPS = {"router": 256, "tool_calling": 256, "summarization": 512, "learning": 512}


# Everyday chat roles. Measured 2026-10-12 on the RTX 3060 (same prompt, cooled
# start): gemma4:12b's default thinking pass spent 73% of its tokens thinking —
# 4.2 kJ and 25 s per reply vs 1.5 kJ with think=false — and on longer replies
# the first visible token took 36-43 s (45 s first-progress budget) while the
# card climbed to the 82 C cutoff. Reasoning/specialist roles keep thinking.
# JARVIS_CHAT_THINKING=1 restores it; a caller's explicit ``think`` always wins.
CHAT_ROLES = frozenset({"conversation", "general", "fast_chat"})


def _utility_defaults(role: str, chosen: InferenceRoute, kwargs: dict) -> None:
    if (
        role in CHAT_ROLES
        and chosen.backend == "ollama"
        and os.getenv("JARVIS_CHAT_THINKING", "0").strip() != "1"
    ):
        caps = boundary.model_capabilities(chosen.model)
        if caps and "thinking" in caps:
            kwargs.setdefault("think", False)
    cap = UTILITY_OUTPUT_CAPS.get(role)
    if cap is None or chosen.backend != "ollama":
        return
    options = dict(kwargs.get("options") or {})
    options.setdefault("num_predict", cap)
    kwargs["options"] = options
    caps = boundary.model_capabilities(chosen.model)
    if caps and "thinking" in caps:
        kwargs.setdefault("think", False)


LOCAL_RETRY_DELAY_S = 2.0  # lets a racing eviction / VRAM release settle
LOCAL_RECONNECT_DELAY_S = 5.0  # an Ollama restart takes a few seconds to listen again


def _local_recovery_routes(
    chosen: InferenceRoute,
    exc: BaseException,
    *,
    role: str,
    explicit_model: bool,
    receipt: boundary.Receipt,
    kwargs: dict,
    messages: list[dict],
    cancel_check=None,
) -> Iterator[InferenceRoute]:
    """Bounded recovery after a *local* attempt failed before any output.

    At most one retry of the same model (transient faults only), then at most
    one other installed local model from the owner's role settings. Never a
    cloud model, never a substitute for an explicitly selected model, and every
    step is written to the receipt. ``JARVIS_LOCAL_RECOVERY=0`` turns it off.
    """
    if chosen.backend != "ollama" or os.getenv("JARVIS_LOCAL_RECOVERY", "1").strip() == "0":
        return
    category = boundary.classify_failure(exc)
    receipt.failure_category = category
    if category in boundary.RETRYABLE_LOCAL:
        receipt.policy.append(f"{chosen.model} failed before answering ({category}); retrying once")
        logger.warning("Local model %s failed before answering (%s); retrying once", chosen.model, category)
        delay = LOCAL_RECONNECT_DELAY_S if category == "connection_refused" else LOCAL_RETRY_DELAY_S
        deadline = time.monotonic() + delay
        while time.monotonic() < deadline:
            if cancel_check is not None and cancel_check():
                raise boundary.InferenceCancelled("cancelled before retry")
            time.sleep(0.25)
        yield InferenceRoute(backend="ollama", model=chosen.model, reason=f"local_retry:{category}", local=True)
    if explicit_model or category not in boundary.SUBSTITUTABLE_LOCAL:
        return
    substitute = boundary.local_substitute(role, failed=chosen.model)
    if not substitute:
        receipt.policy.append("no other installed local model is configured; no fallback")
        return
    try:
        boundary.check_capabilities(substitute, boundary.requirements_from_kwargs(kwargs, messages))
    except boundary.CapabilityMismatch:
        receipt.policy.append(f"local fallback {substitute} lacks a required capability; not used")
        return
    receipt.policy.append(f"{chosen.model} unavailable ({category}); local fallback to {substitute}")
    logger.warning("Local model %s unavailable (%s); falling back to %s", chosen.model, category, substitute)
    yield InferenceRoute(backend="ollama", model=substitute, reason=f"local_fallback:{category}", local=True)


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
        if chosen.backend not in ("litellm", "native"):
            # A cloud target with no cloud transport: answer locally, say so.
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


@dataclass
class _CloudCall:
    provider: str
    native_model: str
    reservation: Any
    disclosure: Any
    max_output_tokens: int


def _max_output(kwargs: dict) -> int:
    options = kwargs.get("options") or {}
    try:
        return max(1, int(options.get("num_predict") or kwargs.get("max_tokens") or 1024))
    except (TypeError, ValueError):
        return 1024


def _admit_cloud(
    chosen: InferenceRoute, role: str, receipt: boundary.Receipt, messages: list[dict], kwargs: dict,
    *, explicit_model: bool = False,
) -> tuple[InferenceRoute, _CloudCall | None]:
    """Owner authorization, pricing, budget and disclosure — before any send.

    A refusal is a decision, not a fault: the request is answered by the
    installed local model and the receipt says why. Nothing is transmitted.
    """
    if chosen.backend == "litellm" and not boundary.is_cloud_model(chosen.model):
        return chosen, None  # a local model served through the LiteLLM proxy
    if chosen.backend not in ("native", "litellm"):
        return chosen, None
    from jarvis.inference import cloud_policy
    from jarvis.inference.providers import split_model

    provider, native_model = split_model(chosen.model)
    max_out = _max_output(kwargs)
    try:
        reservation = cloud_policy.preflight(
            provider,
            chosen.model,
            role,
            input_tokens=_estimate_context_tokens(messages),
            max_output_tokens=max_out,
        )
        disclosure = cloud_policy.prepare_messages(messages, reservation.context_classes)
    except cloud_policy.PolicyRefused as exc:
        receipt.policy.append(f"cloud refused: {exc}")
        if explicit_model:
            receipt.close("failed")
            raise
        return (
            InferenceRoute(
                backend="ollama",
                model=boundary.local_fallback(role),
                reason=f"cloud_refused: {exc}",
                local=True,
            ),
            None,
        )
    receipt.policy.append(
        f"cloud authorized by {reservation.authorization_id}: shares "
        f"{', '.join(sorted(disclosure.shared)) or 'nothing'}; withheld "
        f"{', '.join(sorted(disclosure.withheld)) or 'nothing'}; worst case "
        f"${reservation.worst_case_usd:.4f}"
    )
    return chosen, _CloudCall(provider, native_model, reservation, disclosure, max_out)


def _native_request(cloud: _CloudCall, kwargs: dict, tools=None, cancel_check=None):
    from jarvis.inference.providers.base import Request

    options = kwargs.get("options") or {}
    return Request(
        model=cloud.native_model,
        messages=cloud.disclosure.messages,
        tools=tools,
        max_output_tokens=cloud.max_output_tokens,
        temperature=options.get("temperature"),
        timeout=float(os.getenv("JARVIS_CLOUD_TIMEOUT", "120")),
        cancel_check=cancel_check,
    )


def _settle(cloud: _CloudCall, receipt: boundary.Receipt, attempt, status: str) -> None:
    from jarvis.inference import cloud_policy

    try:
        cost = cloud_policy.record_usage(
            cloud.reservation,
            receipt_id=receipt.id,
            status=status,
            input_tokens=attempt.prompt_tokens,
            output_tokens=attempt.completion_tokens,
        )
        receipt.policy.append(f"estimated cost ${cost:.6f} ({status})")
    except Exception:  # noqa: BLE001 - accounting must never hide the outcome
        logger.exception("Cloud usage accounting failed for %s", receipt.id)


def _native_call(chosen: InferenceRoute, cloud: _CloudCall, kwargs: dict, receipt, tools=None):
    """One paid call through a native adapter, under its reservation."""
    from jarvis.inference import cloud_policy
    from jarvis.inference.providers import adapter_for

    adapter = adapter_for(cloud.provider)
    attempt = receipt.attempt(chosen.model)
    cloud_policy.record_disclosure(
        cloud.disclosure,
        receipt_id=receipt.id,
        provider=cloud.provider,
        model=chosen.model,
        role=receipt.role,
        authorization_id=cloud.reservation.authorization_id,
    )
    token = cloud_policy.activate(cloud.reservation)
    try:
        result = adapter.chat(_native_request(cloud, kwargs, tools=tools))
    except boundary.InferenceError as exc:
        attempt.finish("failed", error=str(exc))
        _settle(cloud, receipt, attempt, "failed")
        raise
    finally:
        cloud_policy.deactivate(token)
    attempt.output_chars = len(result.text or "")
    attempt.prompt_tokens = result.usage.input_tokens
    attempt.completion_tokens = result.usage.output_tokens
    if result.finish in ("length", "filtered"):
        receipt.policy.append(f"provider finished with {result.finish!r}")
    attempt.finish("completed")
    _settle(cloud, receipt, attempt, "completed")
    usage = {
        "prompt_tokens": result.usage.input_tokens,
        "completion_tokens": result.usage.output_tokens,
        "provider_model": result.model,
        "provider_request_id": result.provider_request_id,
        "finish": result.finish,
    }
    return result, usage


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
            "provider": chosen.backend if chosen.backend in ("litellm", "native") else "ollama",
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
    usage["backend"] = chosen.backend if chosen.backend in ("litellm", "native") else "ollama"
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


def _run_sync(
    chosen: InferenceRoute, messages: list[dict], kwargs: dict, receipt, cloud=None
) -> tuple[str, dict]:
    if chosen.backend == "native":
        result, usage = _native_call(chosen, cloud, kwargs, receipt)
        return result.text, usage
    attempt = receipt.attempt(chosen.model)
    token = None
    try:
        if chosen.backend == "litellm":
            if cloud is not None:
                from jarvis.inference import cloud_policy

                cloud_policy.record_disclosure(
                    cloud.disclosure, receipt_id=receipt.id, provider=cloud.provider,
                    model=chosen.model, role=receipt.role,
                    authorization_id=cloud.reservation.authorization_id,
                )
                messages = cloud.disclosure.messages
                token = cloud_policy.activate(cloud.reservation)
            text, usage = _litellm_chat_with_usage(chosen.model, messages, **kwargs)
        else:
            text, usage = _ollama_chat_with_usage(chosen.model, messages, **kwargs)
    except boundary.InferenceError as exc:
        attempt.finish("failed", error=str(exc))
        if cloud is not None:
            _settle(cloud, receipt, attempt, "failed")
        raise
    except Exception as exc:  # noqa: BLE001 - classified: provider fault
        attempt.finish("failed", error=f"{type(exc).__name__}: {exc}")
        if cloud is not None:
            _settle(cloud, receipt, attempt, "failed")
        raise boundary.ProviderUnavailable(
            f"{attempt.provider} model {chosen.model!r} failed: {exc}"
        ) from exc
    finally:
        if token is not None:
            from jarvis.inference import cloud_policy

            cloud_policy.deactivate(token)
    attempt.output_chars = len(text or "")
    attempt.prompt_tokens = (usage or {}).get("prompt_tokens")
    attempt.completion_tokens = (usage or {}).get("completion_tokens")
    attempt.finish("completed")
    if cloud is not None:
        _settle(cloud, receipt, attempt, "completed")
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
    installed local model for the role; a local attempt gets the bounded
    recovery in ``_local_recovery_routes``. The receipt lists every attempt.
    A policy refusal or a capability mismatch is raised, never papered over.
    """
    explicit_model = bool(kwargs.get("explicit_model", False))
    overlay, chosen_model, hardware, lock = _prepare(model, role, kwargs)
    receipt = boundary.Receipt(
        role=role,
        requested_model=model,
        privacy=boundary.privacy_class(messages, privacy),
        stream=False,
    )
    _note_overlay(receipt, model, chosen_model, overlay, route)
    chosen = route or select_route(chosen_model, role=role, messages=messages, lock_model=lock)
    _require_selected_model(chosen, model, explicit_model, receipt)
    chosen = _authorize(chosen, role, receipt)
    _require_selected_model(chosen, model, explicit_model, receipt)
    boundary.check_capabilities(chosen.model, boundary.requirements_from_kwargs(kwargs, messages))
    chosen, cloud = _admit_cloud(chosen, role, receipt, messages, kwargs, explicit_model=explicit_model)
    _utility_defaults(role, chosen, kwargs)
    _trace(chosen, hardware, overlay, stream=False)
    try:
        text, usage = _run_sync(chosen, messages, kwargs, receipt, cloud)
    except boundary.ProviderUnavailable as exc:
        if chosen.backend == "ollama":
            last: boundary.ProviderUnavailable = exc
            for step in _local_recovery_routes(
                chosen, exc, role=role, explicit_model=explicit_model,
                receipt=receipt, kwargs=kwargs, messages=messages,
            ):
                chosen = step
                try:
                    text, usage = _run_sync(chosen, messages, kwargs, receipt)
                    break
                except boundary.ProviderUnavailable as again:
                    last = again
            else:
                receipt.failure_category = receipt.failure_category or boundary.classify_failure(last)
                receipt.close("failed")
                raise last
            receipt.close("completed")
            _usage_fields(usage, chosen, hardware, overlay, receipt)
            return text, usage
        if explicit_model or not (chosen.backend in ("litellm", "native") and exc.fallback_eligible):
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

    from jarvis import gpu_scheduler

    options = dict(kwargs.get("options") or {})
    with gpu_scheduler.admit_ollama(model, options) as job:
        if job.options:
            kwargs["options"] = {**options, **job.options}
        response = (_ollama_client_chat(job) if job.host else chat)(model=model, messages=messages, tools=tools, **kwargs)
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
    _note_overlay(receipt, model, chosen_model, overlay, route)
    chosen = route or select_route(chosen_model, role=role, messages=messages, lock_model=lock)
    chosen = _authorize(chosen, role, receipt)
    chosen, cloud = _admit_cloud(chosen, role, receipt, messages, kwargs)
    _trace(chosen, hardware, overlay, stream=False)

    def run(target: InferenceRoute) -> tuple[dict, dict]:
        boundary.check_capabilities(target.model, {"tools"})
        if target.backend == "native":
            native, usage = _native_call(target, cloud, kwargs, receipt, tools=tools)
            return (
                {
                    "content": native.text,
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments}
                        for c in native.tool_calls
                    ],
                },
                usage,
            )
        attempt = receipt.attempt(target.model)
        token = None
        try:
            if target.backend == "litellm":
                sent = messages
                if cloud is not None:
                    from jarvis.inference import cloud_policy

                    cloud_policy.record_disclosure(
                        cloud.disclosure, receipt_id=receipt.id, provider=cloud.provider,
                        model=target.model, role=receipt.role,
                        authorization_id=cloud.reservation.authorization_id,
                    )
                    sent = cloud.disclosure.messages
                    token = cloud_policy.activate(cloud.reservation)
                try:
                    result, usage = _litellm_tools(target.model, sent, tools)
                finally:
                    if token is not None:
                        cloud_policy.deactivate(token)
            else:
                result, usage = _ollama_tools(target.model, messages, tools)
        except boundary.InferenceError as exc:
            attempt.finish("failed", error=str(exc))
            if target.backend == "litellm" and cloud is not None:
                _settle(cloud, receipt, attempt, "failed")
            raise
        except Exception as exc:  # noqa: BLE001
            attempt.finish("failed", error=f"{type(exc).__name__}: {exc}")
            if target.backend == "litellm" and cloud is not None:
                _settle(cloud, receipt, attempt, "failed")
            raise boundary.ProviderUnavailable(f"{target.model!r} failed: {exc}") from exc
        attempt.prompt_tokens = usage.get("prompt_tokens")
        attempt.completion_tokens = usage.get("completion_tokens")
        attempt.finish("completed")
        if target.backend == "litellm" and cloud is not None:
            _settle(cloud, receipt, attempt, "completed")
        return result, usage

    try:
        try:
            result, usage = run(chosen)
        except boundary.ProviderUnavailable:
            if chosen.backend not in ("litellm", "native"):
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
    cloud: _CloudCall | None = None,
) -> Iterator[str]:
    """One streaming attempt. Failure before output → ProviderUnavailable;
    failure after output → StreamInterrupted (never continued elsewhere)."""
    if chosen.backend == "native":
        yield from _native_stream(chosen, cloud, kwargs, receipt, usage, cancel_check)
        return
    attempt = receipt.attempt(chosen.model)
    produced = 0
    token = None
    try:
        if chosen.backend == "litellm":
            if cloud is not None:
                from jarvis.inference import cloud_policy

                cloud_policy.record_disclosure(
                    cloud.disclosure, receipt_id=receipt.id, provider=cloud.provider,
                    model=chosen.model, role=receipt.role,
                    authorization_id=cloud.reservation.authorization_id,
                )
                messages = cloud.disclosure.messages
                token = cloud_policy.activate(cloud.reservation)
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
        if cloud is not None:
            _settle(cloud, receipt, attempt, "failed")
        raise
    except Exception as exc:  # noqa: BLE001 - classified below
        if cloud is not None:
            _settle(cloud, receipt, attempt, "interrupted" if produced else "failed")
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
    finally:
        if token is not None:
            from jarvis.inference import cloud_policy

            cloud_policy.deactivate(token)
    if usage is not None:
        attempt.prompt_tokens = usage.get("prompt_tokens")
        attempt.completion_tokens = usage.get("completion_tokens")
    attempt.finish("completed")
    if cloud is not None:
        _settle(cloud, receipt, attempt, "completed")


def _native_stream(
    chosen: InferenceRoute,
    cloud: _CloudCall,
    kwargs: dict,
    receipt: boundary.Receipt,
    usage: dict | None,
    cancel_check,
) -> Iterator[str]:
    """A native provider stream with the same pre/post-output rules."""
    from jarvis.inference import cloud_policy
    from jarvis.inference.providers import adapter_for

    adapter = adapter_for(cloud.provider)
    attempt = receipt.attempt(chosen.model)
    cloud_policy.record_disclosure(
        cloud.disclosure,
        receipt_id=receipt.id,
        provider=cloud.provider,
        model=chosen.model,
        role=receipt.role,
        authorization_id=cloud.reservation.authorization_id,
    )
    produced = 0
    token = cloud_policy.activate(cloud.reservation)
    try:
        events = adapter.stream(_native_request(cloud, kwargs, cancel_check=cancel_check))
        for event in events:
            if event.type == "text" and event.text:
                if attempt.first_token_ms is None:
                    attempt.first_token_ms = round((time.time() - attempt.started_at) * 1000, 1)
                produced += len(event.text)
                attempt.output_chars = produced
                yield event.text
            elif event.type == "usage" and event.usage is not None:
                attempt.prompt_tokens = event.usage.input_tokens
                attempt.completion_tokens = event.usage.output_tokens
            elif event.type == "done":
                if event.finish in ("length", "filtered"):
                    receipt.policy.append(f"provider finished with {event.finish!r}")
    except boundary.InferenceCancelled:
        attempt.finish("cancelled")
        _settle(cloud, receipt, attempt, "cancelled")
        return
    except boundary.InferenceError as exc:
        status = "interrupted" if produced else "failed"
        attempt.finish(status, error=str(exc))
        _settle(cloud, receipt, attempt, status)
        if produced:
            raise boundary.StreamInterrupted(
                f"The {attempt.provider} response was interrupted after {produced} characters. "
                "The partial answer is incomplete and was not continued by another model.",
                provider=attempt.provider,
                model=chosen.model,
                partial_chars=produced,
            ) from exc
        raise
    finally:
        cloud_policy.deactivate(token)
    if usage is not None:
        usage["prompt_tokens"] = attempt.prompt_tokens
        usage["completion_tokens"] = attempt.completion_tokens
    attempt.finish("completed")
    _settle(cloud, receipt, attempt, "completed")


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
    explicit_model = bool(kwargs.get("explicit_model", False))
    overlay, chosen_model, hardware, lock = _prepare(model, role, kwargs)
    receipt = boundary.Receipt(
        role=role,
        requested_model=model,
        privacy=boundary.privacy_class(messages, privacy),
        stream=True,
    )
    _note_overlay(receipt, model, chosen_model, overlay, route)
    chosen = route or select_route(chosen_model, role=role, messages=messages, lock_model=lock)
    _require_selected_model(chosen, model, explicit_model, receipt)
    chosen = _authorize(chosen, role, receipt)
    _require_selected_model(chosen, model, explicit_model, receipt)
    boundary.check_capabilities(chosen.model, boundary.requirements_from_kwargs(kwargs, messages))
    chosen, cloud = _admit_cloud(chosen, role, receipt, messages, kwargs, explicit_model=explicit_model)
    _utility_defaults(role, chosen, kwargs)
    _trace(chosen, hardware, overlay, stream=True)
    if usage is not None:
        _usage_fields(usage, chosen, hardware, overlay, receipt)
    status = "failed"
    try:
        try:
            yield from _attempt_stream(chosen, messages, kwargs, receipt, usage, cancel_check, cloud)
        except boundary.ProviderUnavailable as exc:
            if chosen.backend == "ollama":
                last: boundary.ProviderUnavailable = exc
                for step in _local_recovery_routes(
                    chosen, exc, role=role, explicit_model=explicit_model, receipt=receipt,
                    kwargs=kwargs, messages=messages, cancel_check=cancel_check,
                ):
                    chosen = step
                    try:
                        yield from _attempt_stream(chosen, messages, kwargs, receipt, usage, cancel_check)
                        break
                    except boundary.ProviderUnavailable as again:
                        last = again
                else:
                    receipt.failure_category = receipt.failure_category or boundary.classify_failure(last)
                    raise last
                final = receipt.final
                status = final.status if final else "failed"
                return
            if explicit_model or chosen.backend not in ("litellm", "native"):
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
