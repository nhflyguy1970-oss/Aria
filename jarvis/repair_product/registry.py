"""Repair module protocol and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from jarvis.repair_product.terminology import APPROVAL_SAFE


@dataclass
class DetectedIssue:
    module_id: str
    subsystem: str
    title: str
    summary: str = ""
    severity: str = "warning"  # info|warning|critical
    code: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        bits = [self.module_id, self.code or self.title, str(self.context.get("component") or "")]
        return "|".join(bits).lower()


@dataclass
class Diagnosis:
    root_cause: str
    explanation: str
    confidence: float  # 0..1
    evidence: list[str] = field(default_factory=list)
    why: str = ""


@dataclass
class RepairPlan:
    steps: list[str]
    expected_result: str
    risk: str  # very_low|low|medium|high|critical
    risk_why: str
    estimated_seconds: float
    rollback_available: bool
    rollback_description: str = ""
    approval_class: str = APPROVAL_SAFE
    destructive: bool = False


@dataclass
class StepResult:
    id: str
    ok: bool
    detail: str = ""


@dataclass
class RepairOutcome:
    ok: bool
    steps: list[StepResult] = field(default_factory=list)
    message: str = ""
    executed: bool = False


@dataclass
class VerifyResult:
    ok: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""


class RepairModule(Protocol):
    id: str
    subsystem: str
    approval_class: str

    def description(self) -> str: ...
    def detect(self) -> list[DetectedIssue]: ...
    def diagnose(self, issue: DetectedIssue) -> Diagnosis: ...
    def collect_evidence(self, issue: DetectedIssue) -> list[str]: ...
    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan: ...
    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome: ...
    def verify(self, issue: DetectedIssue) -> VerifyResult: ...
    def rollback(self, issue: DetectedIssue) -> RepairOutcome | None: ...
    def risk_level(self, issue: DetectedIssue) -> str: ...
    def confidence(self, issue: DetectedIssue, diagnosis: Diagnosis) -> float: ...
    def estimated_time(self, issue: DetectedIssue) -> float: ...


_REGISTRY: dict[str, Any] = {}


def register_module(module: Any) -> None:
    mid = getattr(module, "id", None)
    if not mid:
        raise ValueError("Repair module requires id")
    _REGISTRY[str(mid)] = module


def get_module(module_id: str) -> Any | None:
    return _REGISTRY.get(module_id)


def all_modules() -> list[Any]:
    return list(_REGISTRY.values())


def clear_registry_for_tests() -> None:
    _REGISTRY.clear()
