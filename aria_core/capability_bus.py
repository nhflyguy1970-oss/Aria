"""Aria Core Capability Bus (Phase 3).

Applications will request capabilities here. Each verb delegates to today's
implementation via Aria Core modules or soft-imports. No organ moves.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aria_core._delegate import soft_import
from aria_core.capability_contracts import get_contract, list_contracts, validate_contracts
from aria_core.capability_registry import (
    CAPABILITY_VERSION,
    all_capability_ids,
    dependency_graph,
    get_capability,
    list_capabilities,
    validate_registry,
)
from aria_core.ownership import module_ownership

OWNER = module_ownership("capabilities")
BUS_VERSION = CAPABILITY_VERSION


def _orchestrate(capability: str, fn, *, meta: dict[str, Any] | None = None):
    """Cap Bus → Cognitive Orchestrator → existing organ work."""
    from aria_core.cognitive_orchestrator import run as _run

    return _run(capability, fn, meta=meta)


def _emit(name: str, **payload: Any) -> None:
    """Best-effort Event Bus publish — never changes capability behavior."""
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(name, source="aria_core.capability_bus", **payload)
    except Exception:
        pass


def _probe_import(module_path: str) -> dict[str, Any]:
    mod = soft_import(module_path)
    if mod is None:
        return {"ok": False, "module": module_path, "status": "unavailable"}
    return {"ok": True, "module": module_path, "status": "ok"}


def health(capability_id: str | None = None) -> dict[str, Any]:
    """Probe provider importability without executing side-effect verbs."""
    probes = {
        "remember": "aria_core.memory_manager",
        "recall": "aria_core.memory_manager",
        "learn": "aria_core.learning_manager",
        "reason": "jarvis.assistant",
        "plan": "jarvis.agents.coordinator",
        "reference": "jarvis.reference_engine",
        "search": "jarvis.knowledge",
        "infer": "jarvis.llm",
        "execute_tool": "jarvis.handlers.registry",
        "schedule": "jarvis.handlers.registry",
        "observe": "aiplatform.mission_control.aggregator",
        "notify": "aiplatform.mission_control.notifications",
        "diagnose": "aiplatform.workstation.operations",
        "repair": "aiplatform.workstation.operations",
        "backup": "jarvis",
        "recover": "aiplatform.workstation.operations",
    }
    if capability_id:
        if capability_id not in probes:
            return {"ok": False, "id": capability_id, "status": "unknown"}
        result = _probe_import(probes[capability_id])
        result["id"] = capability_id
        meta = get_capability(capability_id) or {}
        result["owner"] = meta.get("owner")
        result["provider"] = meta.get("provider")
        result["current_implementation"] = meta.get("current_implementation")
        return result

    items = []
    for cid in all_capability_ids():
        items.append(health(cid))
    healthy = sum(1 for i in items if i.get("ok"))
    return {
        "ok": healthy == len(items),
        "version": BUS_VERSION,
        "healthy": healthy,
        "total": len(items),
        "capabilities": items,
    }


def remember(
    content: str,
    *,
    entry_type: str = "fact",
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> Any:
    """Persist memory — Cap Bus → Core Memory Manager → organ."""

    def _body() -> Any:
        from aria_core.memory import remember as core_remember

        return core_remember(content, entry_type=entry_type, tags=tags, namespace=namespace)

    return _orchestrate("remember", _body)


def recall(
    query: str | None = None,
    *,
    entry_id: str | None = None,
    limit: int = 10,
    **kwargs: Any,
) -> Any:
    """Retrieve memory — Cap Bus → Core Memory Manager → organ."""

    def _body() -> Any:
        from aria_core.memory import get_memory, search_memory

        if entry_id:
            return get_memory(entry_id)
        if query is None:
            return []
        return search_memory(query, limit=limit, namespace=kwargs.get("namespace"))

    return _orchestrate("recall", _body)


def learn(
    *,
    kind: str,
    payload: dict[str, Any] | None = None,
    source: str = "",
    apply=None,
) -> Any:
    """Learning Governor propose (and optional commit)."""

    def _body() -> Any:
        from aria_core import learning

        proposal = learning.propose(kind=kind, payload=payload, source=source)
        if apply is None:
            return proposal
        return learning.commit(proposal, apply)

    return _orchestrate("learn", _body, meta={"kind": kind})


def reason(message: str, **kwargs: Any) -> Any:
    """Conversational reasoning — delegates to aria_core.reasoning.chat."""

    def _body() -> Any:
        from aria_core import reasoning

        _emit("ReasoningStarted", message_len=len(message or ""))
        try:
            result = reasoning.chat(message, **kwargs)
        except Exception as exc:
            _emit("ReasoningFinished", ok=False, error=type(exc).__name__)
            raise
        _emit("ReasoningFinished", ok=True)
        return result

    return _orchestrate("reason", _body, meta={"query_len": len(message or "")})


def plan(*, action: str = "status", **kwargs: Any) -> dict[str, Any]:
    """Planning surface — status / coordinator access (no new planner)."""

    def _body() -> dict[str, Any]:
        from aria_core import planning

        _emit("PlanStarted", action=action)
        available = planning.coordinator_available()
        if action == "status":
            out = {
                "ok": True,
                "available": available,
                "planner_store": planning.planner_store_path(),
                "owner": OWNER["owner"],
            }
            _emit("PlanCompleted", action=action, ok=True)
            return out
        if action == "coordinator":
            if not available:
                out = {"ok": False, "available": False, "error": "coordinator unavailable"}
                _emit("PlanCompleted", action=action, ok=False)
                return out
            out = {"ok": True, "available": True, "coordinator": planning.get_coordinator()}
            _emit("PlanCompleted", action=action, ok=True)
            return out
        out = {"ok": False, "error": f"unknown plan action: {action}", **kwargs}
        _emit("PlanCompleted", action=action, ok=False)
        return out

    return _orchestrate("plan", _body, meta={"action": action})


def reference(query: str, *, subject: str = "") -> dict[str, Any]:
    def _body() -> dict[str, Any]:
        from aria_core import reference as reference_mod

        result = reference_mod.search_reference(query, subject=subject)
        _emit("ReferenceLookup", query=query, subject=subject)
        return result

    return _orchestrate("reference", _body, meta={"query_len": len(query or "")})


def search(query: str, **kwargs: Any) -> Any:
    def _body() -> Any:
        from aria_core import knowledge

        return knowledge.search(query, **kwargs)

    return _orchestrate("search", _body, meta={"query_len": len(query or "")})


def infer(prompt: str, *, model: str | None = None, **kwargs: Any) -> Any:
    """LLM inference — delegates to jarvis.llm.generate_text when present."""

    def _body() -> Any:
        _emit("InferenceStarted", prompt_len=len(prompt or ""))
        try:
            llm = soft_import("jarvis.llm")
            if llm is not None and hasattr(llm, "generate_text"):
                use_model = model or (
                    llm.general_model() if hasattr(llm, "general_model") else None
                )
                if use_model:
                    result = llm.generate_text(use_model, prompt, **kwargs)
                else:
                    result = llm.generate_text(prompt, **kwargs)  # type: ignore[misc]
                _emit("InferenceFinished", ok=True)
                return result
            # Fall back to reasoning chat (same organ stack) — reason() emits its own pair.
            return reason(prompt, **kwargs)
        except Exception as exc:
            _emit("InferenceFinished", ok=False, error=type(exc).__name__)
            raise

    return _orchestrate("infer", _body, meta={"query_len": len(prompt or "")})


def list_tools() -> list[dict[str, Any]]:
    try:
        from jarvis.handlers.registry import all_actions

        return list(all_actions())
    except Exception:
        return []


def execute_tool(assistant: Any, action: str, params: dict | None = None, message: str = "") -> Any:
    """Dispatch registered handler — existing call_action semantics."""

    def _body() -> Any:
        from jarvis.handlers.registry import call_action

        _emit("ToolStarted", action=action)
        try:
            result = call_action(assistant, action, params or {}, message)
        except Exception as exc:
            _emit("ToolCompleted", action=action, ok=False, error=type(exc).__name__)
            raise
        _emit("ToolCompleted", action=action, ok=True)
        return result

    return _orchestrate("execute_tool", _body, meta={"action": action})


def schedule(*, op: str = "status", **kwargs: Any) -> dict[str, Any]:
    """Job/queue observation — does not invent a new scheduler."""

    def _body() -> dict[str, Any]:
        detail: dict[str, Any] = {"ok": True, "op": op, "queues": []}
        if kwargs:
            detail["extra_keys"] = sorted(kwargs.keys())
        try:
            from jarvis.handlers.registry import all_actions

            queues = sorted({a.get("queue") for a in all_actions() if a.get("queue")})
            detail["queues"] = queues
        except Exception as exc:
            detail["queues_error"] = str(exc)
        try:
            from jarvis.runtime_introspection import _jobs

            detail["jobs"] = _jobs()
        except Exception as exc:
            detail["jobs"] = {"any_busy": False, "recent": [], "error": str(exc)}
        return detail

    return _orchestrate("schedule", _body, meta={"action": op})


def observe(**kwargs: Any) -> dict[str, Any]:
    def _body() -> dict[str, Any]:
        from aria_core import operations

        return operations.collect_overview(**kwargs)

    return _orchestrate("observe", _body)


def notify(message: str, *, detail: str = "", **kwargs: Any) -> dict[str, Any]:
    def _body() -> dict[str, Any]:
        mod = soft_import("aiplatform.mission_control.notifications")
        if mod is None or not hasattr(mod, "notify"):
            return {"ok": False, "error": "notifications unavailable"}
        mod.notify(message, detail=detail, **kwargs)
        return {"ok": True}

    return _orchestrate("notify", _body)


def diagnose(*, force: bool = False) -> dict[str, Any]:
    def _body() -> dict[str, Any]:
        mod = soft_import("aiplatform.workstation.operations")
        if mod is None:
            return {"ok": False, "error": "workstation.operations unavailable"}
        return dict(mod.diagnose(force=force))

    return _orchestrate("diagnose", _body)


def repair(*, mode: str = "safe") -> dict[str, Any]:
    """Safe repair only — delegates to recover_safe (existing semantics)."""

    def _body() -> dict[str, Any]:
        _emit("RepairStarted", mode=mode)
        result = recover()
        _emit("RepairCompleted", ok=bool(result.get("ok")))
        return result

    return _orchestrate("repair", _body, meta={"action": mode})


def latest_backup_hint() -> dict[str, Any]:
    """Describe backup script / latest archive without running backup."""
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "backup-data.sh"
    backups = root / "backups"
    latest = None
    if backups.is_dir():
        archives = sorted(backups.glob("*.tar.gz"), reverse=True)
        if archives:
            latest = archives[0].name
    return {
        "ok": True,
        "script_available": script.is_file(),
        "script": str(script) if script.is_file() else None,
        "latest": latest,
    }


def backup(*, op: str = "hint") -> dict[str, Any]:
    """Phase 3: hint/status only — does not run backup scripts."""

    def _body() -> dict[str, Any]:
        if op in ("hint", "status"):
            return latest_backup_hint()
        return {"ok": False, "error": f"backup op not enabled in Phase 3: {op}"}

    return _orchestrate("backup", _body, meta={"action": op})


def recover() -> dict[str, Any]:
    def _body() -> dict[str, Any]:
        mod = soft_import("aiplatform.workstation.operations")
        if mod is None:
            out = {"ok": False, "error": "workstation.operations unavailable"}
            _emit("RecoveryStarted")
            _emit("RecoveryCompleted", ok=False)
            return out
        _emit("RecoveryStarted")
        result = dict(mod.recover_safe())
        _emit("RecoveryCompleted", ok=bool(result.get("ok")))
        return result

    # When called from repair(), nested orchestrate is suppressed.
    return _orchestrate("recover", _body)


def invoke(capability_id: str, *args: Any, **kwargs: Any) -> Any:
    """Generic dispatch by capability id."""
    fn = globals().get(capability_id)
    if not callable(fn) or capability_id.startswith("_"):
        raise KeyError(f"unknown capability: {capability_id}")
    if capability_id in {
        "health",
        "invoke",
        "mission_control_panel",
        "list_tools",
        "latest_backup_hint",
    }:
        raise KeyError(f"not a bus verb: {capability_id}")
    return fn(*args, **kwargs)


def mission_control_panel() -> dict[str, Any]:
    """Operational visibility payload for Mission Control Capabilities tab."""
    reg_errors = validate_registry()
    contract_errors = validate_contracts()
    health_snap = health()
    caps = []
    for rec in list_capabilities():
        cid = rec["id"]
        h = next((x for x in health_snap.get("capabilities") or [] if x.get("id") == cid), {})
        caps.append(
            {
                "id": cid,
                "purpose": rec.get("purpose"),
                "owner": rec.get("owner"),
                "provider": rec.get("provider"),
                "implementation": rec.get("current_implementation"),
                "consumers": rec.get("consumers"),
                "dependencies": rec.get("dependencies"),
                "health": "ok" if h.get("ok") else "degraded",
                "health_detail": h,
                "version": rec.get("version"),
                "public_api": rec.get("public_api"),
                "permission_requirements": rec.get("permission_requirements"),
                "learning_effects": rec.get("learning_effects"),
                "memory_effects": rec.get("memory_effects"),
                "recovery_behavior": rec.get("recovery_behavior"),
                "contract": get_contract(cid),
                "future_implementation_owner": rec.get("future_implementation_owner"),
            }
        )
    return {
        "ok": not reg_errors and not contract_errors,
        "title": "Aria Core Capability Bus",
        "version": BUS_VERSION,
        "owner": OWNER["owner"],
        "summary": {
            "total": health_snap.get("total"),
            "healthy": health_snap.get("healthy"),
            "registry_errors": reg_errors,
            "contract_errors": contract_errors,
        },
        "capabilities": caps,
        "dependency_graph": dependency_graph(),
        "contracts": list_contracts(),
        "note": "Visibility only — organs unchanged; verbs delegate to existing implementations.",
    }


__all__ = [
    "BUS_VERSION",
    "OWNER",
    "backup",
    "diagnose",
    "execute_tool",
    "health",
    "infer",
    "invoke",
    "latest_backup_hint",
    "learn",
    "list_tools",
    "mission_control_panel",
    "notify",
    "observe",
    "plan",
    "reason",
    "recall",
    "recover",
    "reference",
    "remember",
    "repair",
    "schedule",
    "search",
]
