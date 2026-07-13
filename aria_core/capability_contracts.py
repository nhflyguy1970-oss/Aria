"""Aria Core Capability Contracts (Phase 3).

Documents inputs/outputs/errors/latency/side-effects for each bus verb.
Contracts are descriptive; behavior remains in existing implementations.
"""

from __future__ import annotations

from typing import Any

from aria_core.capability_registry import CAPABILITY_VERSION, all_capability_ids

CONTRACTS: dict[str, dict[str, Any]] = {
    "remember": {
        "id": "remember",
        "inputs": {"content": "str|dict", "namespace": "str?", "metadata": "dict?"},
        "outputs": {"entry": "dict|Any (MemoryStore.add result)"},
        "errors": ["ImportError", "TypeError", "store-specific write errors"],
        "latency_expectations": "local disk/sqlite; typically <100ms p50 on workstation",
        "side_effects": "Writes memory; may dual-write via existing adapters",
        "observability": "Return value + Learning Governor audit when applicable",
        "interruptibility": "Not interruptible mid-write",
        "recovery": "Retry; store remains source of truth",
        "future_implementation_owner": "aria_core.memory",
        "version": CAPABILITY_VERSION,
    },
    "recall": {
        "id": "recall",
        "inputs": {"query": "str?", "entry_id": "str?", "limit": "int=10"},
        "outputs": {"hits": "list[dict]"},
        "errors": ["ImportError"],
        "latency_expectations": "local search; typically <200ms p50",
        "side_effects": "none (read-only)",
        "observability": "hit count",
        "interruptibility": "safe to abandon",
        "recovery": "empty hits",
        "future_implementation_owner": "aria_core.memory",
        "version": CAPABILITY_VERSION,
    },
    "learn": {
        "id": "learn",
        "inputs": {"kind": "str", "payload": "dict?", "apply": "callable?"},
        "outputs": {"proposal|commit_result": "Any"},
        "errors": ["ImportError"],
        "latency_expectations": "passthrough; sub-ms overhead + apply cost",
        "side_effects": "Governor audit; apply may write corrections/memory",
        "observability": "learning_governor.recent_audit",
        "interruptibility": "do not interrupt during apply",
        "recovery": "passthrough unchanged",
        "future_implementation_owner": "aria_core.learning",
        "version": CAPABILITY_VERSION,
    },
    "reason": {
        "id": "reason",
        "inputs": {"message": "str", "kwargs": "assistant.process kwargs"},
        "outputs": {"response": "Any (assistant process result)"},
        "errors": ["RuntimeError when process unavailable", "LLM errors"],
        "latency_expectations": "model-bound; seconds typical",
        "side_effects": "conversation/history/tool side effects via existing assistant",
        "observability": "existing chat/runtime metrics",
        "interruptibility": "existing cancel paths only",
        "recovery": "surface existing errors",
        "future_implementation_owner": "aria_core.reasoning",
        "version": CAPABILITY_VERSION,
    },
    "plan": {
        "id": "plan",
        "inputs": {"action": "status|coordinator", "payload": "dict?"},
        "outputs": {"available": "bool", "coordinator": "module|None", "detail": "dict"},
        "errors": ["ImportError"],
        "latency_expectations": "import/status <50ms",
        "side_effects": "none for status; coordinator methods may mutate plans",
        "observability": "coordinator_available flag",
        "interruptibility": "status safe",
        "recovery": "available=false",
        "future_implementation_owner": "aria_core.planning",
        "version": CAPABILITY_VERSION,
    },
    "reference": {
        "id": "reference",
        "inputs": {"query": "str", "subject": "str?"},
        "outputs": {"result": "dict (search_reference)"},
        "errors": ["ImportError"],
        "latency_expectations": "local-first; typically <500ms",
        "side_effects": "none",
        "observability": "hits/ok fields",
        "interruptibility": "safe",
        "recovery": "structured error dict",
        "future_implementation_owner": "aria_core.reference",
        "version": CAPABILITY_VERSION,
    },
    "search": {
        "id": "search",
        "inputs": {"query": "str", "kwargs": "knowledge search kwargs"},
        "outputs": {"hits|result": "Any"},
        "errors": ["ImportError", "structured ok=false"],
        "latency_expectations": "vector/RAG bound; varies",
        "side_effects": "none",
        "observability": "hit count / ok",
        "interruptibility": "safe",
        "recovery": "empty hits",
        "future_implementation_owner": "aria_core.knowledge",
        "version": CAPABILITY_VERSION,
    },
    "infer": {
        "id": "infer",
        "inputs": {"prompt": "str", "kwargs": "llm kwargs"},
        "outputs": {"text|result": "Any"},
        "errors": ["ImportError", "LLM client errors"],
        "latency_expectations": "model-bound",
        "side_effects": "GPU/VRAM via existing inference stack",
        "observability": "existing inference metrics",
        "interruptibility": "existing cancel only",
        "recovery": "propagate errors",
        "future_implementation_owner": "aria_core.reasoning",
        "version": CAPABILITY_VERSION,
    },
    "execute_tool": {
        "id": "execute_tool",
        "inputs": {
            "action": "str",
            "assistant": "JarvisAssistant",
            "params": "dict",
            "message": "str",
        },
        "outputs": {"result": "dict"},
        "errors": ["KeyError unknown action", "handler errors"],
        "latency_expectations": "action-dependent",
        "side_effects": "handler-defined",
        "observability": "handler registry + capability_adapter",
        "interruptibility": "queue-dependent",
        "recovery": "existing handler/adapter behavior",
        "future_implementation_owner": "aria_core.capabilities",
        "version": CAPABILITY_VERSION,
    },
    "schedule": {
        "id": "schedule",
        "inputs": {"op": "status|list", "payload": "dict?"},
        "outputs": {"jobs|queues": "dict"},
        "errors": ["ImportError"],
        "latency_expectations": "<100ms for status",
        "side_effects": "none for status/list",
        "observability": "jobs panel fields",
        "interruptibility": "safe for status",
        "recovery": "empty jobs list",
        "future_implementation_owner": "aria_core.runtime",
        "version": CAPABILITY_VERSION,
    },
    "observe": {
        "id": "observe",
        "inputs": {"kwargs": "collect_overview kwargs"},
        "outputs": {"overview": "dict"},
        "errors": ["structured unavailable"],
        "latency_expectations": "overview typically <2s; avoid full MC collect",
        "side_effects": "may record metrics if requested by caller kwargs",
        "observability": "MC overview fields",
        "interruptibility": "safe",
        "recovery": "ok=false payload",
        "future_implementation_owner": "aria_core.operations",
        "version": CAPABILITY_VERSION,
    },
    "notify": {
        "id": "notify",
        "inputs": {"message": "str", "detail": "str?"},
        "outputs": {"ok": "bool"},
        "errors": ["soft fail when platform absent"],
        "latency_expectations": "<50ms",
        "side_effects": "notification store / desktop notify",
        "observability": "MC notifications dock",
        "interruptibility": "safe",
        "recovery": "ok=false",
        "future_implementation_owner": "aria_core.operations",
        "version": CAPABILITY_VERSION,
    },
    "diagnose": {
        "id": "diagnose",
        "inputs": {"force": "bool=False"},
        "outputs": {"report": "dict (diagnose)"},
        "errors": ["ImportError / ok=false"],
        "latency_expectations": "registry snapshot; typically <2s",
        "side_effects": "none (read/probe)",
        "observability": "issues list",
        "interruptibility": "safe",
        "recovery": "issues reported",
        "future_implementation_owner": "aria_core.platform",
        "version": CAPABILITY_VERSION,
    },
    "repair": {
        "id": "repair",
        "inputs": {"mode": "safe (default)"},
        "outputs": {"result": "dict"},
        "errors": ["ImportError"],
        "latency_expectations": "service restart bound; seconds",
        "side_effects": "may restart managed components",
        "observability": "results list",
        "interruptibility": "not safe mid-repair",
        "recovery": "delegates to recover_safe",
        "future_implementation_owner": "aria_core.platform",
        "version": CAPABILITY_VERSION,
    },
    "backup": {
        "id": "backup",
        "inputs": {"op": "hint|status"},
        "outputs": {"available": "bool", "hint": "str|None"},
        "errors": ["none — descriptive only in Phase 3"],
        "latency_expectations": "<50ms for hint",
        "side_effects": "none for hint; script path for future invoke",
        "observability": "latest_backup_hint",
        "interruptibility": "safe for hint",
        "recovery": "available=false",
        "future_implementation_owner": "aria_core.operations",
        "version": CAPABILITY_VERSION,
    },
    "recover": {
        "id": "recover",
        "inputs": {},
        "outputs": {"result": "dict (recover_safe)"},
        "errors": ["ImportError"],
        "latency_expectations": "service restart bound",
        "side_effects": "bootstrap/restart unhealthy managed components",
        "observability": "results + snapshot",
        "interruptibility": "not safe mid-recover",
        "recovery": "existing recover_safe semantics",
        "future_implementation_owner": "aria_core.platform",
        "version": CAPABILITY_VERSION,
    },
}


def get_contract(capability_id: str) -> dict[str, Any] | None:
    rec = CONTRACTS.get(capability_id)
    return dict(rec) if rec else None


def list_contracts() -> list[dict[str, Any]]:
    return [dict(CONTRACTS[k]) for k in sorted(CONTRACTS)]


def validate_contracts() -> list[str]:
    errors: list[str] = []
    for cid in all_capability_ids():
        if cid not in CONTRACTS:
            errors.append(f"missing contract for {cid}")
    for cid in CONTRACTS:
        if cid not in set(all_capability_ids()):
            errors.append(f"orphan contract {cid}")
    required = (
        "inputs",
        "outputs",
        "errors",
        "latency_expectations",
        "side_effects",
        "observability",
        "interruptibility",
        "recovery",
        "future_implementation_owner",
    )
    for cid, rec in CONTRACTS.items():
        for field in required:
            if field not in rec:
                errors.append(f"{cid}: missing {field}")
    return errors
