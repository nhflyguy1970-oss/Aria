"""Step dispatch — how a workflow step reaches an existing ARIA capability.

There is exactly one route: the action registry. When a step names an agent, it
goes through specialized_agents.invoke, so the agent's own permission check runs
and its identity is stamped for the skills, MCP and routing layers. When it does
not, it runs as an operator action. Either way the workflow adds no authority of
its own — it can only ask for things that were already possible.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from jarvis.autonomous_workflows.definitions import StepDefinition

log = logging.getLogger("jarvis.autonomous_workflows.dispatch")

# Outcome kinds a dispatch can report.
OK = "ok"
FAILED = "failed"
DENIED = "denied"
UNAVAILABLE = "unavailable"
CANCELLED = "cancelled"
TIMED_OUT = "timed_out"

# Failures where trying again cannot change the answer.
TERMINAL_KINDS = frozenset(
    {
        "permission_denied",
        "contract",
        "invalid_provider",
        "input_contract",
        "schema",
        "gate_only",
        "unknown_provider",
        "no_compatible_model",
        "capability_mismatch",
        "not_found",
        "unknown_action",
        "invalid_request",
        "command_form",
        "command_denied",
    }
)


class CapabilityUnavailable(RuntimeError):
    """The step names an action this ARIA does not have."""


def known_action(action: str) -> bool:
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import has_action

    ensure_handlers_loaded()
    return has_action(action)


def _classify(result: dict[str, Any]) -> tuple[str, str]:
    """Turn an action result into a workflow outcome and a failure kind."""
    kind = str(result.get("error_kind") or "")
    if kind in ("permission_denied", "denied"):
        return DENIED, kind
    if kind in ("cancelled",):
        return CANCELLED, kind
    if kind in ("timeout", "timed_out"):
        return TIMED_OUT, kind
    if kind in ("unavailable", "provider_unavailable", "not_found", "unknown_provider"):
        return UNAVAILABLE, kind
    return FAILED, kind or "action_failed"


def _provenance(step: StepDefinition, result: dict[str, Any]) -> dict[str, Any]:
    """Pull identity out of whatever the capability reported.

    Each subsystem already returns its own envelope; this reads them rather than
    inventing provenance. A capability that reports nothing is recorded as
    reporting nothing.
    """
    provenance: dict[str, Any] = {
        "action": step.action,
        "agent": step.agent_id or "",
    }
    envelope = result.get("envelope")
    if isinstance(envelope, dict):
        for key in ("skill_id", "provider_id", "invocation_id", "requester", "status"):
            if envelope.get(key):
                provenance[key] = envelope[key]
        if envelope.get("final_model"):
            provenance["model"] = envelope["final_model"]
            provenance["fallback_count"] = envelope.get("fallback_count", 0)
        if envelope.get("provenance"):
            provenance["capability_provenance"] = envelope["provenance"]
    routing = result.get("model_routing")
    if isinstance(routing, dict) and routing.get("model"):
        provenance["model"] = routing["model"]
        provenance["model_selection"] = routing.get("selection_method", "")
    for key in (
        "research_id",
        "claim_id",
        "task_id",
        "mission_id",
        "collaboration_id",
        "session_id",
        "invocation_id",
    ):
        if result.get(key):
            provenance[key] = result[key]
    if len(provenance) <= 2:
        provenance["note"] = "capability reported no provenance"
    return provenance


def dispatch(
    step: StepDefinition,
    params: dict[str, Any],
    *,
    assistant: Any = None,
    workflow_id: str = "",
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Run one step. Returns a structured outcome; never raises for control flow."""
    started = time.time()
    outcome: dict[str, Any] = {
        "status": FAILED,
        "step_id": step.step_id,
        "action": step.action,
        "agent": step.agent_id or "",
        "output": None,
        "error": None,
        "error_kind": "",
        "retryable": False,
        "provenance": {},
        "duration_ms": 0.0,
    }

    def finish(**updates: Any) -> dict[str, Any]:
        outcome.update(updates)
        outcome["duration_ms"] = round((time.time() - started) * 1000, 2)
        return outcome

    if cancel_check is not None and cancel_check():
        return finish(status=CANCELLED, error="cancelled before dispatch", error_kind="cancelled")

    if not known_action(step.action):
        # An unknown capability is a definition problem: retrying cannot help.
        return finish(
            status=UNAVAILABLE,
            error=f"no such ARIA action: {step.action!r}",
            error_kind="unknown_action",
        )

    payload = dict(params)
    if workflow_id:
        payload.setdefault("workflow_id", workflow_id)

    try:
        if step.agent_id:
            # Through the agent so its permission check and identity stamping run.
            from jarvis import specialized_agents as agents

            invocation = agents.invoke(
                step.agent_id,
                step.name or step.step_id,
                action=step.action,
                params=payload,
                assistant=assistant,
            )
            if not invocation.get("ok"):
                kind = str(invocation.get("error_kind") or "")
                status = DENIED if kind == "permission_denied" else FAILED
                return finish(
                    status=status,
                    error=invocation.get("error") or "agent invocation failed",
                    error_kind=kind or "agent_failed",
                    retryable=status != DENIED and kind not in TERMINAL_KINDS,
                )
            result = invocation.get("result") or {}
            outcome["provenance"] = {
                **_provenance(step, result),
                "agent": step.agent_id,
                "agent_model": invocation.get("model", ""),
                "model_routing": invocation.get("model_routing", {}),
            }
        else:
            from jarvis.handlers import ensure_handlers_loaded
            from jarvis.handlers.registry import call_action

            ensure_handlers_loaded()
            result = call_action(assistant, step.action, payload, step.name or step.action)
            outcome["provenance"] = _provenance(step, result)
    except Exception as exc:  # noqa: BLE001 - a capability fault must not kill the workflow
        log.warning("workflow step %s raised", step.step_id, exc_info=True)
        return finish(
            status=FAILED,
            error=f"{type(exc).__name__}: {exc}",
            error_kind="exception",
            retryable=True,
        )

    if not isinstance(result, dict):
        return finish(
            status=FAILED, error="capability returned a non-object result", error_kind="contract"
        )

    if result.get("ok") is False:
        # An action that ran and reported failure is a failed step, never a
        # success that happens to contain an error message.
        status, kind = _classify(result)
        return finish(
            status=status,
            error=result.get("message") or result.get("error") or "capability failed",
            error_kind=kind,
            retryable=status not in (DENIED, CANCELLED) and kind not in TERMINAL_KINDS,
            output=None,
        )

    payload_out = {k: v for k, v in result.items() if k not in ("ok", "module")}
    return finish(status=OK, output=payload_out)
