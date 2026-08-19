"""Routed model invocation with bounded, honest fallback.

The rule that shapes this module: falling back is only ever a response to a
model or provider fault. A cancellation and a policy denial are decisions, and
quietly running somebody else's model instead would override them. And when
fallback does happen, the result says so — a second model's success is never
presented as though the first had worked.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from jarvis.model_routing import failures, health, profiles, store
from jarvis.model_routing.decision import FALLBACK, RoutingDecision
from jarvis.model_routing.request import RoutingRequest
from jarvis.model_routing.router import route

log = logging.getLogger("jarvis.model_routing.execute")

SUCCESS = "success"
FAILED = "failed"
CANCELLED = "cancelled"
UNROUTABLE = "unroutable"
DENIED = "denied"
STATUSES = (SUCCESS, FAILED, CANCELLED, UNROUTABLE, DENIED)


class RoutingCancelled(RuntimeError):
    """The caller stopped the work. Never a reason to try another model."""


class PolicyDenied(RuntimeError):
    """ARIA refused. A different model would not make it allowed."""


class ExecutedElsewhere(RuntimeError):
    """The call ran on a different model than the router chose."""

    def __init__(self, requested: str, executed: str) -> None:
        super().__init__(
            f"routing selected {requested!r} but the inference gateway executed {executed!r}"
        )
        self.requested = requested
        self.executed = executed


def default_invoker(model: str, payload: dict[str, Any]) -> Any:
    """Invoke through ARIA's existing model interface — no second chat engine.

    The inference gateway applies its own policy overlay and can substitute a
    different model. For a routed call that would make the decision advisory
    and the audit trail wrong, so the chosen model is pinned with an explicit
    route, and the model the gateway reports having executed is checked against
    the one that was asked for.
    """
    from jarvis.inference.gateway import chat_with_usage
    from jarvis.inference.policy import InferenceRoute

    system = payload.get("system") or ""
    role = payload.get("role") or "conversation"
    messages = payload.get("messages")
    if not messages:
        messages = [{"role": "user", "content": payload.get("prompt") or ""}]
    if system:
        messages = [{"role": "system", "content": system}, *messages]

    pinned = InferenceRoute(
        backend="ollama", model=model, reason="model_routing_decision", local=True
    )
    text, usage = chat_with_usage(
        model, messages, role=role, route=pinned, **(payload.get("options") or {})
    )
    executed = str((usage or {}).get("execution_model") or model)
    if executed and executed != model:
        # Never record somebody else's model as though it were the choice.
        raise ExecutedElsewhere(model, executed)
    return text


def _call_bounded(
    call: Callable[[str, dict[str, Any]], Any],
    model: str,
    body: dict[str, Any],
    timeout_s: float,
    cancel_check: Callable[[], bool] | None,
) -> Any:
    """Invoke with a wall-clock bound ARIA controls.

    A model that never answers must not hold a request open forever, and a
    cancellation must be noticed while the call is still in flight rather than
    only at the boundaries around it. The provider call cannot be interrupted,
    so the worker is left to finish on its own — ARIA simply stops waiting, and
    says which of the two happened.
    """
    from concurrent.futures import ThreadPoolExecutor
    from concurrent.futures import TimeoutError as FutureTimeout

    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"aria-model-{model[:16]}")
    future = pool.submit(call, model, body)
    try:
        deadline = time.monotonic() + max(0.001, float(timeout_s))
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"model {model} exceeded {timeout_s}s; ARIA stopped waiting")
            try:
                return future.result(timeout=min(0.25, remaining))
            except FutureTimeout:
                if cancel_check is not None and cancel_check():
                    raise RoutingCancelled(f"cancelled while {model} was still working") from None
    finally:
        # Do not block shutdown on a model that is still generating.
        pool.shutdown(wait=False, cancel_futures=True)


def _attempt_record(model: str, ok: bool, ms: float, kind: str = "", error: str = "") -> dict:
    record = {"model": model, "ok": ok, "duration_ms": round(ms, 2)}
    if not ok:
        record["failure_kind"] = kind
        record["error"] = str(error)[:1000]
        record["fallback_eligible"] = failures.may_fallback(kind)
    return record


def execute(
    request: RoutingRequest,
    payload: dict[str, Any] | None = None,
    *,
    invoker: Callable[[str, dict[str, Any]], Any] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    validator: Callable[[Any], bool] | None = None,
    decision: RoutingDecision | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Route, invoke, and fall back within bounds. Returns a truthful envelope."""
    started = time.time()
    invocation_id = store.new_id()
    call = invoker or default_invoker
    body = dict(payload or {})

    decision = decision or route(request)
    envelope: dict[str, Any] = {
        "invocation_id": invocation_id,
        "status": FAILED,
        "requester": request.requester,
        "agent_id": request.agent_id,
        "skill_id": request.skill_id,
        "mission_id": request.mission_id,
        "decision": decision.to_dict(),
        "selected_model": decision.selected_model,
        "final_model": "",
        "provider": decision.provider,
        "attempts": [],
        "fallback_chain": [],
        "fallback_count": 0,
        "fallback_active": False,
        "result": None,
        "error": None,
        "failure_kind": "",
        "started_at": started,
    }

    def finish(**updates: Any) -> dict[str, Any]:
        envelope.update(updates)
        envelope["duration_ms"] = round((time.time() - started) * 1000, 2)
        envelope["ok"] = envelope["status"] == SUCCESS
        if persist:
            try:
                envelope["invocation_id"] = store.record(envelope)
            except Exception:  # noqa: BLE001 - audit must not mask the outcome
                log.warning("could not persist routing invocation", exc_info=True)
        return envelope

    if not decision.ok:
        return finish(
            status=UNROUTABLE,
            failure_kind=failures.CAPABILITY_MISMATCH,
            error=decision.reason,
        )

    if cancel_check is not None and cancel_check():
        return finish(
            status=CANCELLED,
            failure_kind=failures.CANCELLED,
            error="cancelled before any model was invoked",
        )

    # The ordered list of models to try: the choice, then the next best
    # compatible candidates. Only models that already passed hard filtering
    # appear here, so a fallback can never violate a requirement.
    # Next-best first. decision.candidates is in name order for readability, so
    # sorting by score here is what makes a fallback the *next best* model
    # rather than merely the next one alphabetically — which is how a "fast"
    # request ended up falling back onto the slowest models available.
    ranked = sorted(decision.accepted(), key=lambda c: (-c.score, c.model_id))
    ordered = [c.model_id for c in ranked]
    if decision.selected_model in ordered:
        ordered.remove(decision.selected_model)
    chain = [decision.selected_model, *ordered][: 1 + max(0, request.max_fallbacks)]

    last_kind = ""
    last_error: Any = None
    for index, model in enumerate(chain):
        if cancel_check is not None and cancel_check():
            return finish(
                status=CANCELLED,
                failure_kind=failures.CANCELLED,
                error="cancelled before invoking " + model,
                final_model="",
            )

        attempt_started = time.time()
        try:
            result = _call_bounded(call, model, body, request.timeout_s, cancel_check)
            elapsed = (time.time() - attempt_started) * 1000

            if validator is not None and not validator(result):
                kind = failures.STRUCTURED_OUTPUT_FAILED
                health.record_failure(model, kind=kind, error="output failed validation")
                envelope["attempts"].append(
                    _attempt_record(model, False, elapsed, kind, "output failed validation")
                )
                last_kind, last_error = kind, "output failed validation"
                if not failures.may_fallback(kind) or index >= len(chain) - 1:
                    break
                continue

            health.record_success(model, latency_ms=elapsed)
            envelope["attempts"].append(_attempt_record(model, True, elapsed))
            fallback_count = index
            return finish(
                status=SUCCESS,
                result=result,
                final_model=model,
                provider=_provider_of(model, decision),
                fallback_count=fallback_count,
                fallback_active=fallback_count > 0,
                fallback_chain=chain[: index + 1],
                # A later model's success is recorded as a fallback, never as
                # though the first choice had worked.
                decision={
                    **decision.to_dict(),
                    "selection_method": (FALLBACK if fallback_count else decision.selection_method),
                },
            )

        except RoutingCancelled as exc:
            return finish(
                status=CANCELLED,
                failure_kind=failures.CANCELLED,
                error=str(exc),
                fallback_chain=chain[: index + 1],
            )
        except PolicyDenied as exc:
            return finish(
                status=DENIED,
                failure_kind=failures.POLICY_DENIED,
                error=str(exc),
                fallback_chain=chain[: index + 1],
            )
        except Exception as exc:  # noqa: BLE001 - classified, never swallowed
            elapsed = (time.time() - attempt_started) * 1000
            kind = failures.classify(exc)
            envelope["attempts"].append(_attempt_record(model, False, elapsed, kind, exc))
            last_kind, last_error = kind, exc

            if kind in failures.NEVER_FALLBACK:
                status = (
                    CANCELLED
                    if kind == failures.CANCELLED
                    else (DENIED if kind == failures.POLICY_DENIED else FAILED)
                )
                return finish(
                    status=status,
                    failure_kind=kind,
                    error=str(exc),
                    fallback_chain=chain[: index + 1],
                )

            health.record_failure(model, kind=kind, error=str(exc))
            if not failures.may_fallback(kind):
                break

    exhausted = len(chain) > 1
    return finish(
        status=FAILED,
        failure_kind=last_kind or failures.PROVIDER_ERROR,
        error=(f"all {len(chain)} candidate model(s) failed" if exhausted else "model failed")
        + f": {last_error}",
        final_model="",
        fallback_count=max(0, len(envelope["attempts"]) - 1),
        fallback_active=len(envelope["attempts"]) > 1,
        fallback_chain=chain[: len(envelope["attempts"])],
    )


def _provider_of(model: str, decision: RoutingDecision) -> str:
    for candidate in decision.candidates:
        if candidate.model_id == model:
            return candidate.provider
    profile = profiles.get_profile(model)
    return profile.provider if profile else decision.provider
