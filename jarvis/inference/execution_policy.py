"""Benchmark-driven execution routing policy (model + hardware).

Architecture freeze: extends existing inference/policy + placement patterns.
Never hardcodes AMD/NVIDIA winners — winners come from measured benchmarks.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

_POLICY_FILE = DATA_DIR / "execution_routing_policy.json"
_POLICY_VERSION = "1.0"

# Request class → workload profile used for model/hardware selection.
REQUEST_CLASS_WORKLOAD: dict[str, str] = {
    "greeting": "lightweight",
    "reference": "lightweight",
    "search_reference": "lightweight",
    "documentation": "lightweight",
    "runtime": "lightweight",
    "memory": "lightweight",
    "learning": "lightweight",
    "formatting": "lightweight",
    "classification": "lightweight",
    "intent": "lightweight",
    "planning": "reasoning",
    "reasoning": "reasoning",
    "coding": "coding",
    "code": "coding",
    "vision": "vision",
    "voice": "voice",
}

# Paths that normally need no LLM at all (still recorded for Trace/MC).
NON_LLM_PATHS: dict[str, dict[str, Any]] = {
    "greeting": {
        "capability": "greeting",
        "provider": "none",
        "model": None,
        "hardware": "cpu",
        "execution_path": "reflex_or_static_greeting",
        "reason": "Greeting uses static/reflex path — no inference required",
    },
    "reference": {
        "capability": "reference",
        "provider": "local_docs",
        "model": None,
        "hardware": "cpu",
        "execution_path": "reference_engine",
        "reason": "Reference Engine is extractive local docs — no chat model",
    },
    "search_reference": {
        "capability": "reference",
        "provider": "local_docs",
        "model": None,
        "hardware": "cpu",
        "execution_path": "reference_engine",
        "reason": "Reference Engine is extractive local docs — no chat model",
    },
    "documentation": {
        "capability": "reference",
        "provider": "local_docs",
        "model": None,
        "hardware": "cpu",
        "execution_path": "reference_engine",
        "reason": "Documentation requests use Reference Engine — no chat model",
    },
    "runtime": {
        "capability": "runtime",
        "provider": "mission_control",
        "model": None,
        "hardware": "cpu",
        "execution_path": "runtime_client",
        "reason": "Runtime status from Mission Control / introspection — no chat model",
    },
    "memory": {
        "capability": "memory",
        "provider": "acm",
        "model": None,
        "hardware": "cpu",
        "execution_path": "acm_bridge",
        "reason": "Cognitive memory is ACM-authoritative — no chat model",
    },
}


@dataclass(frozen=True)
class ExecutionPlan:
    request_class: str
    capability: str
    provider: str
    model: str | None
    hardware: str
    execution_path: str
    workload: str
    reason: str
    fallback_reason: str = ""
    confidence: float = 1.0
    expected_latency_ms: float | None = None
    benchmark_date: str | None = None
    benchmark_winner: bool = False
    source: str = "policy"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def policy_path() -> Path:
    return _POLICY_FILE


def load_policy() -> dict[str, Any] | None:
    if not _POLICY_FILE.is_file():
        return None
    try:
        data = json.loads(_POLICY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not data.get("workloads"):
        return None
    return data


def save_policy(policy: dict[str, Any]) -> Path:
    _POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    policy = dict(policy)
    policy.setdefault("version", _POLICY_VERSION)
    policy["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    _POLICY_FILE.write_text(
        json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return _POLICY_FILE


def workload_for_request_class(request_class: str) -> str:
    key = (request_class or "greeting").strip().lower()
    return REQUEST_CLASS_WORKLOAD.get(key, "lightweight")


def _role_to_workload(role: str) -> str:
    from jarvis.model_store import canonical_role

    role = canonical_role(role or "conversation")
    if role in ("coding",):
        return "coding"
    if role in ("vision", "image"):
        return "vision"
    if role in ("reasoning", "review", "planning", "reflection", "conversation", "document", "web_research"):
        return "reasoning"
    if role in ("router", "tool_calling", "summarization", "learning", "fast_chat"):
        return "lightweight"
    return "lightweight"


def resolve_execution(
    request_class: str,
    *,
    require_llm: bool | None = None,
) -> ExecutionPlan:
    """Resolve capability/provider/model/hardware for a request class."""
    key = (request_class or "").strip().lower() or "greeting"
    workload = workload_for_request_class(key)

    if require_llm is False or (require_llm is None and key in NON_LLM_PATHS):
        base = NON_LLM_PATHS.get(key) or {
            "capability": key,
            "provider": "none",
            "model": None,
            "hardware": "cpu",
            "execution_path": "non_llm",
            "reason": "No inference required for this request class",
        }
        return ExecutionPlan(
            request_class=key,
            capability=str(base["capability"]),
            provider=str(base["provider"]),
            model=base.get("model"),
            hardware=str(base.get("hardware") or "cpu"),
            execution_path=str(base.get("execution_path") or "non_llm"),
            workload=workload,
            reason=str(base.get("reason") or ""),
            confidence=1.0,
            source="non_llm",
        )

    policy = load_policy()
    wl = (policy or {}).get("workloads", {}).get(workload) if policy else None
    if isinstance(wl, dict) and "model" in wl:
        if not wl.get("model"):
            return ExecutionPlan(
                request_class=key,
                capability=key,
                provider=str(wl.get("provider") or "local"),
                model=None,
                hardware=str(wl.get("hardware") or "cpu"),
                execution_path="benchmark_policy_non_llm",
                workload=workload,
                reason=str(wl.get("selection_reason") or "benchmark_policy"),
                fallback_reason=str(wl.get("fallback_reason") or ""),
                confidence=float(wl.get("confidence") or 0.7),
                expected_latency_ms=wl.get("warm_latency_ms"),
                benchmark_date=(policy or {}).get("benchmark_date"),
                benchmark_winner=True,
                source="benchmark",
            )
        return ExecutionPlan(
            request_class=key,
            capability=key,
            provider=str(wl.get("provider") or "ollama"),
            model=str(wl.get("model")),
            hardware=str(wl.get("hardware") or "cpu"),
            execution_path="benchmark_policy",
            workload=workload,
            reason=str(wl.get("selection_reason") or "benchmark_policy"),
            fallback_reason="",
            confidence=float(wl.get("confidence") or 0.9),
            expected_latency_ms=wl.get("warm_latency_ms"),
            benchmark_date=(policy or {}).get("benchmark_date"),
            benchmark_winner=True,
            source="benchmark",
        )

    # Fallback: model_store defaults on auto-detected compute GPU / CPU.
    from jarvis.model_store import model_for

    role = {
        "lightweight": "router",
        "coding": "coding",
        "reasoning": "conversation",
        "vision": "vision",
        "voice": "conversation",
    }.get(workload, "conversation")
    hardware = _fallback_hardware()
    return ExecutionPlan(
        request_class=key,
        capability=key,
        provider="ollama",
        model=model_for(role),
        hardware=hardware,
        execution_path="model_store_fallback",
        workload=workload,
        reason="No execution benchmark policy yet — using model_store + detected compute device",
        fallback_reason="missing_execution_policy",
        confidence=0.4,
        source="fallback",
    )


def _fallback_hardware() -> str:
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        if gpu.get("nvidia_available") or (gpu.get("compute_vendor") or "").lower() == "nvidia":
            return "nvidia"
        if gpu.get("rocm_available") or (gpu.get("vendor") or "").lower() == "amd":
            return "amd"
    except Exception:
        pass
    return "cpu"


def apply_policy_to_route(
    *,
    model: str,
    role: str = "general",
) -> dict[str, Any]:
    """Overlay benchmark winners onto an inference call (model + device options)."""
    env_force = (os.getenv("JARVIS_EXECUTION_MODEL") or "").strip()
    env_device = (os.getenv("JARVIS_EXECUTION_DEVICE") or "").strip()
    if env_force:
        return {
            "model": env_force,
            "hardware": env_device or _fallback_hardware(),
            "reason": "env JARVIS_EXECUTION_MODEL",
            "source": "env",
            "workload": _role_to_workload(role),
        }

    workload = _role_to_workload(role)
    policy = load_policy()
    wl = (policy or {}).get("workloads", {}).get(workload) if policy else None
    if isinstance(wl, dict) and wl.get("model"):
        return {
            "model": str(wl["model"]),
            "hardware": str(wl.get("hardware") or "cpu"),
            "reason": str(wl.get("selection_reason") or "benchmark_policy"),
            "source": "benchmark",
            "workload": workload,
            "warm_latency_ms": wl.get("warm_latency_ms"),
            "fallback_model": wl.get("fallback_model"),
            "fallback_hardware": wl.get("fallback_hardware"),
        }
    return {
        "model": model,
        "hardware": _fallback_hardware(),
        "reason": "no_policy_passthrough",
        "source": "passthrough",
        "workload": workload,
    }


def mission_control_panel() -> dict[str, Any]:
    """Execution routing visibility for Mission Control."""
    policy = load_policy()
    classes = {}
    for req_class in sorted(REQUEST_CLASS_WORKLOAD):
        plan = resolve_execution(req_class)
        classes[req_class] = plan.to_dict()
    return {
        "ok": True,
        "title": "Execution Routing",
        "policy_loaded": bool(policy),
        "benchmark_date": (policy or {}).get("benchmark_date"),
        "hardware_fingerprint": (policy or {}).get("hardware_fingerprint"),
        "workloads": (policy or {}).get("workloads") or {},
        "request_classes": classes,
        "policy_path": str(_POLICY_FILE),
        "note": "Winners are measured — AMD/NVIDIA/CPU are never hardcoded.",
    }


def routing_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for req_class, workload in sorted(REQUEST_CLASS_WORKLOAD.items()):
        plan = resolve_execution(req_class)
        policy = load_policy() or {}
        wl = (policy.get("workloads") or {}).get(workload) or {}
        rows.append(
            {
                "request_class": req_class,
                "capability": plan.capability,
                "workload": workload,
                "primary_model": plan.model,
                "fallback_model": wl.get("fallback_model"),
                "primary_hardware": plan.hardware,
                "fallback_hardware": wl.get("fallback_hardware") or "cpu",
                "provider": plan.provider,
                "expected_latency_ms": plan.expected_latency_ms,
                "benchmark_winner": plan.benchmark_winner,
                "benchmark_date": plan.benchmark_date,
                "selection_policy": plan.source,
                "selection_reason": plan.reason,
                "execution_path": plan.execution_path,
            }
        )
    return rows
