"""Skill execution — the envelope, the bounds, and the authority boundary.

Every action a skill performs goes through the existing action registry under
the *requester's* permissions, and every child skill inherits that same
requester. There is no second permission system here and no way for a skill to
widen the authority it was invoked with.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any

from jarvis.skills import registry, store
from jarvis.skills.contracts import ContractError, apply_defaults, validate_payload
from jarvis.skills.definitions import HIGH_IMPACT, SkillDefinition, impact_rank

log = logging.getLogger("jarvis.skills")

# Execution statuses. A run that did not do what was asked never reports success.
SUCCESS = "success"
PARTIAL = "partial"
FAILED = "failed"
DENIED = "denied"
UNAVAILABLE = "unavailable"
INVALID = "invalid"
CANCELLED = "cancelled"
TIMED_OUT = "timed_out"
BOUNDED = "bounded"
STATUSES = (SUCCESS, PARTIAL, FAILED, DENIED, UNAVAILABLE, INVALID, CANCELLED, TIMED_OUT, BOUNDED)
UNSUCCESSFUL = (FAILED, DENIED, UNAVAILABLE, INVALID, CANCELLED, TIMED_OUT, BOUNDED)

BOUNDS = {
    "max_depth": 4,
    "max_children": 8,
    "max_actions": 40,
    "max_output_bytes": 262144,
    "max_retries": 2,
    "max_concurrent_children": 1,
}


class SkillError(RuntimeError):
    pass


class SkillDenied(SkillError):
    """Authority refused. Never converted into a soft failure."""


class SkillCancelled(SkillError):
    pass


class SkillBounded(SkillError):
    pass


class SkillTimeout(SkillError):
    pass


def _agent(requester: str):
    from jarvis import specialized_agents as agents

    return agents.get(requester) if requester else None


def check_authority(defn: SkillDefinition, requester: str) -> None:
    """The whole permission story, in one place.

    A skill is runnable by an agent only if the agent holds the gate action for
    the skill's *effective* impact and every action the skill can reach,
    including through its dependencies. That is what stops a harmless-looking
    wrapper from being a privilege ladder.
    """
    if not requester:
        # No agent context: system/operator invocation, still subject to the
        # skill's own allow/deny list.
        return
    agent = _agent(requester)
    if agent is None:
        raise SkillDenied(f"No such agent: {requester}")
    if not agent.enabled:
        raise SkillDenied(f"Agent disabled: {requester}")
    if not defn.permits_agent(requester):
        raise SkillDenied(f"Skill {defn.skill_id} denies agent {requester}")

    effective = registry.effective_impact(defn)
    gate = "skill_invoke_high_impact" if effective == HIGH_IMPACT else "skill_invoke"
    if not agent.permits(gate):
        raise SkillDenied(
            f"Agent {requester} may not invoke {effective}-impact skills (missing {gate})"
        )
    for action in registry.effective_actions(defn):
        if not agent.permits(action):
            raise SkillDenied(
                f"Agent {requester} may not use action {action!r}, required by {defn.ref()}"
            )
    for permission in defn.required_permissions:
        if not agent.permits(permission):
            raise SkillDenied(
                f"Agent {requester} lacks required permission {permission!r} for {defn.ref()}"
            )


class SkillContext:
    """What a skill implementation is handed.

    Deliberately the only route to actions and to other skills, so provenance,
    bounds and permissions cannot be sidestepped by a skill doing its own
    imports.
    """

    def __init__(
        self,
        defn: SkillDefinition,
        *,
        invocation_id: str,
        requester: str = "",
        parent_id: str = "",
        root_id: str = "",
        mission_id: str = "",
        depth: int = 0,
        assistant: Any = None,
        cancel_check: Callable[[], bool] | None = None,
        deadline: float | None = None,
        budget: dict[str, Any] | None = None,
    ):
        self.definition = defn
        self.invocation_id = invocation_id
        self.requester = requester
        self.parent_id = parent_id
        self.root_id = root_id or invocation_id
        self.mission_id = mission_id
        self.depth = depth
        self.assistant = assistant
        self.cancel_check = cancel_check
        self.deadline = deadline
        # Shared across the whole tree so bounds are global, not per-node.
        self.budget = budget if budget is not None else {"actions": 0, "children": 0}
        self.actions: list[dict[str, Any]] = []
        self.children: list[dict[str, Any]] = []
        self.side_effects: list[str] = []
        self.notes: list[str] = []

    # -- guards ---------------------------------------------------------

    def checkpoint(self) -> None:
        """Cancellation and timeout are checked between every unit of work."""
        if self.cancel_check is not None and self.cancel_check():
            raise SkillCancelled(f"{self.definition.ref()} cancelled")
        if self.deadline is not None and time.monotonic() > self.deadline:
            raise SkillTimeout(f"{self.definition.ref()} exceeded {self.definition.timeout_s}s")

    # -- capability access ----------------------------------------------

    def call_action(
        self, action: str, params: dict[str, Any] | None = None, message: str = ""
    ) -> dict[str, Any]:
        """Run an ARIA action under the requester's authority."""
        self.checkpoint()
        if action not in self.definition.required_actions:
            raise SkillDenied(
                f"{self.definition.ref()} did not declare action {action!r}; "
                "undeclared actions are refused"
            )
        if self.budget["actions"] >= BOUNDS["max_actions"]:
            raise SkillBounded(f"max_actions ({BOUNDS['max_actions']}) reached")
        self.budget["actions"] += 1

        agent = _agent(self.requester)
        if agent is not None and not agent.permits(action):
            raise SkillDenied(f"Agent {self.requester} may not use action {action!r}")

        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import call_action as registry_call

        ensure_handlers_loaded()
        started = time.perf_counter()
        result = registry_call(self.assistant, action, dict(params or {}), message or action)
        record = {
            "action": action,
            "ok": bool(isinstance(result, dict) and result.get("ok", True)),
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }
        self.actions.append(record)
        return result if isinstance(result, dict) else {"ok": True, "result": result}

    def call_skill(
        self,
        skill_id: str,
        inputs: dict[str, Any] | None = None,
        *,
        version: str = "",
        strategy: str = "compatible",
    ) -> dict[str, Any]:
        """Invoke a child skill, inheriting this invocation's authority."""
        self.checkpoint()
        if self.budget["children"] >= BOUNDS["max_children"]:
            raise SkillBounded(f"max_children ({BOUNDS['max_children']}) reached")
        self.budget["children"] += 1

        envelope = execute(
            skill_id,
            inputs or {},
            version=version,
            strategy=strategy,
            requester=self.requester,
            assistant=self.assistant,
            parent_id=self.invocation_id,
            root_id=self.root_id,
            mission_id=self.mission_id,
            depth=self.depth + 1,
            cancel_check=self.cancel_check,
            deadline=self.deadline,
            budget=self.budget,
        )
        self.children.append(
            {
                "skill_id": envelope["skill_id"],
                "version": envelope["version"],
                "invocation_id": envelope["invocation_id"],
                "status": envelope["status"],
            }
        )
        # Denial and cancellation propagate upward: a parent cannot quietly
        # succeed on top of a child that was refused.
        if envelope["status"] == DENIED:
            raise SkillDenied(envelope.get("error") or f"child skill {skill_id} denied")
        if envelope["status"] == CANCELLED:
            raise SkillCancelled(envelope.get("error") or f"child skill {skill_id} cancelled")
        if envelope["status"] == BOUNDED:
            raise SkillBounded(envelope.get("error") or f"child skill {skill_id} bounded")
        return envelope

    def record_side_effect(self, description: str) -> None:
        self.side_effects.append(description)


def _envelope(defn: SkillDefinition, invocation_id: str, **kw: Any) -> dict[str, Any]:
    base = {
        "skill_id": defn.skill_id,
        "version": defn.version,
        "name": defn.name,
        "invocation_id": invocation_id,
        "parent_invocation": kw.get("parent_id", ""),
        "root_invocation": kw.get("root_id", invocation_id),
        "mission_id": kw.get("mission_id", ""),
        "requester": kw.get("requester", ""),
        "depth": kw.get("depth", 0),
        "status": kw.get("status", FAILED),
        "impact": kw.get("impact", defn.impact),
        "input": kw.get("input", {}),
        "output": kw.get("output"),
        "error": kw.get("error"),
        "error_kind": kw.get("error_kind", ""),
        "actions": kw.get("actions", []),
        "children": kw.get("children", []),
        "side_effects": kw.get("side_effects", []),
        "provenance": kw.get("provenance", {}),
        "verification": kw.get("verification", "none"),
        "started_at": kw.get("started_at", time.time()),
        "duration_ms": kw.get("duration_ms", 0.0),
    }
    base["ok"] = base["status"] == SUCCESS
    return base


def execute(
    skill_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    version: str = "",
    strategy: str = "compatible",
    requester: str = "",
    assistant: Any = None,
    parent_id: str = "",
    root_id: str = "",
    mission_id: str = "",
    depth: int = 0,
    cancel_check: Callable[[], bool] | None = None,
    deadline: float | None = None,
    budget: dict[str, Any] | None = None,
    authorized_high_impact: bool = False,
) -> dict[str, Any]:
    """Run a skill and return a structured envelope. Never raises for control flow."""
    started = time.time()
    invocation_id = store.new_id()

    # --- resolve -------------------------------------------------------
    try:
        defn = registry.resolve(skill_id, version, strategy=strategy)
    except registry.SkillNotFound as exc:
        return _envelope(
            _placeholder(skill_id, version),
            invocation_id,
            status=UNAVAILABLE,
            error=str(exc),
            error_kind="not_found",
            requester=requester,
            parent_id=parent_id,
            root_id=root_id,
            depth=depth,
            started_at=started,
        )
    except registry.VersionUnavailable as exc:
        return _envelope(
            _placeholder(skill_id, version),
            invocation_id,
            status=UNAVAILABLE,
            error=str(exc),
            error_kind="version_unavailable",
            requester=requester,
            parent_id=parent_id,
            root_id=root_id,
            depth=depth,
            started_at=started,
        )

    effective_impact = registry.effective_impact(defn)
    common = {
        "requester": requester,
        "parent_id": parent_id,
        "root_id": root_id or invocation_id,
        "mission_id": mission_id,
        "depth": depth,
        "impact": effective_impact,
        "started_at": started,
    }

    def fail(status: str, error: str, kind: str, **extra: Any) -> dict[str, Any]:
        env = _envelope(
            defn,
            invocation_id,
            status=status,
            error=error,
            error_kind=kind,
            input=dict(inputs or {}),
            **common,
            **extra,
        )
        env["duration_ms"] = round((time.time() - started) * 1000, 2)
        try:
            store.start(
                invocation_id,
                defn.skill_id,
                defn.version,
                requester=requester,
                parent_id=parent_id,
                root_id=common["root_id"],
                mission_id=mission_id,
                depth=depth,
                impact=effective_impact,
                inputs=dict(inputs or {}),
            )
            store.finish(invocation_id, env)
        except Exception:  # noqa: BLE001 - audit must not mask the real outcome
            log.warning("could not persist skill invocation %s", invocation_id, exc_info=True)
        return env

    # --- availability --------------------------------------------------
    if not defn.enabled:
        return fail(UNAVAILABLE, f"Skill {defn.ref()} is disabled", "disabled")
    if depth >= min(BOUNDS["max_depth"], defn.max_depth):
        return fail(
            BOUNDED,
            f"max_depth ({min(BOUNDS['max_depth'], defn.max_depth)}) reached at {defn.ref()}",
            "bounded",
        )

    # --- dependency integrity -----------------------------------------
    try:
        registry.validate_dependencies(defn)
    except registry.SkillRegistryError as exc:
        return fail(INVALID, str(exc), "dependencies")

    # --- authority -----------------------------------------------------
    try:
        check_authority(defn, requester)
    except SkillDenied as exc:
        return fail(DENIED, str(exc), "permission_denied")

    if effective_impact == HIGH_IMPACT and not authorized_high_impact:
        return fail(
            DENIED,
            f"{defn.ref()} is {effective_impact} and needs explicit authorization",
            "high_impact_unauthorized",
        )

    # --- input contract ------------------------------------------------
    try:
        payload = apply_defaults(dict(inputs or {}), defn.input_schema)
        payload = validate_payload(payload, defn.input_schema, label="input")
    except ContractError as exc:
        return fail(INVALID, str(exc), "input_contract")

    # --- run -----------------------------------------------------------
    impl = registry.implementation(defn.skill_id, defn.version)
    if impl is None:
        return fail(UNAVAILABLE, f"{defn.ref()} has no implementation", "no_implementation")

    store.start(
        invocation_id,
        defn.skill_id,
        defn.version,
        requester=requester,
        parent_id=parent_id,
        root_id=common["root_id"],
        mission_id=mission_id,
        depth=depth,
        impact=effective_impact,
        inputs=payload,
    )

    own_deadline = time.monotonic() + max(0.001, float(defn.timeout_s))
    ctx = SkillContext(
        defn,
        invocation_id=invocation_id,
        requester=requester,
        parent_id=parent_id,
        root_id=common["root_id"],
        mission_id=mission_id,
        depth=depth,
        assistant=assistant,
        cancel_check=cancel_check,
        deadline=own_deadline if deadline is None else min(deadline, own_deadline),
        budget=budget,
    )

    status, output, error, kind = SUCCESS, None, None, ""
    attempts = 0
    max_retries = min(BOUNDS["max_retries"], 2)
    while True:
        attempts += 1
        try:
            ctx.checkpoint()
            output = impl(ctx, payload)
            break
        except SkillDenied as exc:
            status, error, kind = DENIED, str(exc), "permission_denied"
            break
        except SkillCancelled as exc:
            status, error, kind = CANCELLED, str(exc), "cancelled"
            break
        except SkillTimeout as exc:
            status, error, kind = TIMED_OUT, str(exc), "timeout"
            break
        except SkillBounded as exc:
            status, error, kind = BOUNDED, str(exc), "bounded"
            break
        except ContractError as exc:
            status, error, kind = INVALID, str(exc), "contract"
            break
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            if attempts <= max_retries and _retryable(exc):
                log.info("retrying %s after %s", defn.ref(), exc)
                continue
            log.exception("skill %s failed", defn.ref())
            status, error, kind = FAILED, f"{type(exc).__name__}: {exc}", "execution"
            break

    # --- output contract -----------------------------------------------
    verification = "none"
    provenance = {
        "skill": defn.ref(),
        "requester": requester,
        "parent_invocation": parent_id,
        "root_invocation": common["root_id"],
        "mission_id": mission_id,
        "actions": [a["action"] for a in ctx.actions],
        "children": [c["skill_id"] for c in ctx.children],
    }
    if status == SUCCESS:
        if not isinstance(output, dict):
            status, error, kind = FAILED, "Skill returned a non-object result", "output_contract"
        else:
            verification = str(output.get("verification") or "none")
            extra_prov = output.get("provenance")
            if isinstance(extra_prov, dict):
                provenance = {**provenance, **extra_prov}
            try:
                validate_payload(output, defn.output_schema, label="output", allow_extra=True)
            except ContractError as exc:
                status, error, kind = FAILED, str(exc), "output_contract"

    if status == SUCCESS and output is not None:
        try:
            size = len(json.dumps(output, default=str))
            if size > BOUNDS["max_output_bytes"]:
                status = BOUNDED
                error = f"output {size} bytes exceeds max_output_bytes"
                kind = "bounded"
        except (TypeError, ValueError):
            status, error, kind = FAILED, "Skill output is not serialisable", "output_contract"

    env = _envelope(
        defn,
        invocation_id,
        status=status,
        output=output if status in (SUCCESS, PARTIAL) else None,
        error=error,
        error_kind=kind,
        input=payload,
        actions=ctx.actions,
        children=ctx.children,
        side_effects=ctx.side_effects,
        provenance=provenance,
        verification=verification if status == SUCCESS else "none",
        **common,
    )
    env["duration_ms"] = round((time.time() - started) * 1000, 2)
    env["attempts"] = attempts
    store.finish(invocation_id, env)
    return env


def _retryable(exc: Exception) -> bool:
    """Only transient-looking failures are retried; logic errors are not."""
    from jarvis.missions.engine import RetryableError

    return isinstance(exc, (RetryableError, TimeoutError, ConnectionError))


def _placeholder(skill_id: str, version: str) -> SkillDefinition:
    """A stand-in so an unresolvable skill still returns a well-formed envelope."""
    return SkillDefinition(
        skill_id=skill_id if len(skill_id or "") >= 3 else "unknown_skill",
        name=skill_id or "unknown",
        description="unresolved",
        version=version if version else "0.0.0",
    )


def status_of(invocation_id: str) -> dict[str, Any] | None:
    """Operational history for one invocation, with its children."""
    record = store.get(invocation_id)
    if not record:
        return None
    record["child_invocations"] = store.children_of(invocation_id)
    return record


def impact_at_least(impact: str, threshold: str) -> bool:
    return impact_rank(impact) >= impact_rank(threshold)
