"""Guided Repair module — Production Integrity (Jeff must approve; never auto-deletes)."""

from __future__ import annotations

from typing import Any, Callable

from jarvis.repair_product.modules import BaseModule
from jarvis.repair_product.registry import (
    DetectedIssue,
    Diagnosis,
    RepairOutcome,
    RepairPlan,
    StepResult,
    VerifyResult,
)
from jarvis.repair_product.terminology import APPROVAL_SEMI


class ProductionIntegrityModule(BaseModule):
    id = "production_integrity"
    subsystem = "integrity"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Remove development / QA / smoke / certification artifacts from the live workspace"

    def detect(self) -> list[DetectedIssue]:
        from jarvis.integrity_product.scanner import run_scan

        scan = run_scan(force=False, trigger="guided_repair_detect")
        findings = scan.get("findings") or []
        if not findings:
            return []
        counts = scan.get("counts") or {}
        by = counts.get("by_category") or {}
        evidence_bits = [f"{k}: {v}" for k, v in sorted(by.items())]
        return [
            DetectedIssue(
                module_id=self.id,
                subsystem=self.subsystem,
                title="Development artifacts detected in production",
                summary=(
                    f"{counts.get('total', len(findings))} development artifact(s) found in the live workspace. "
                    + "; ".join(evidence_bits)
                ),
                severity="critical" if scan.get("status") == "attention" else "warning",
                code="dev_artifacts",
                context={
                    "component": "production_integrity",
                    "status": scan.get("status"),
                    "counts": counts,
                    "finding_titles": [f.get("title") for f in findings[:20]],
                    "findings": findings,
                },
            )
        ]

    def collect_evidence(self, issue: DetectedIssue) -> list[str]:
        findings = (issue.context or {}).get("findings") or []
        ev = [issue.summary] if issue.summary else []
        for f in findings[:25]:
            bits = [str(f.get("title") or "")]
            for e in (f.get("evidence") or [])[:3]:
                bits.append(str(e))
            conf = f.get("confidence")
            if conf is not None:
                bits.append(f"confidence={conf}")
            ev.append(" | ".join(bits))
        return ev

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        findings = (issue.context or {}).get("findings") or []
        return Diagnosis(
            root_cause="QA / smoke / certification / demo artifacts leaked into the live workspace",
            explanation=(
                "Automated tests, certification suites, or development probes wrote artifacts "
                "into Jeff's production DATA_DIR. Production Integrity detected them. "
                "Scans never auto-delete — Jeff approves Guided Repair to remove only known-safe leftovers."
            ),
            confidence=0.99 if findings else 0.7,
            why="Artifact titles/paths/metadata match development patterns or qa_artifact tags",
            evidence=self.collect_evidence(issue),
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        findings = (issue.context or {}).get("findings") or []
        n = len(findings)
        return RepairPlan(
            steps=[
                "Re-scan and list verified development artifacts",
                "Remove only allow-listed QA/smoke/cert/demo leftovers",
                "Preserve all user Health, ACM, Projects, Journal, Planner, Calendar, Gallery data",
                "Re-scan and verify production is clean",
                "Record repair history",
            ],
            expected_result="No development artifacts remain in the live workspace",
            risk="very_low",
            risk_why="Only removes known-safe development artifacts with metadata/path allow-lists; user data is out of scope",
            estimated_seconds=max(8.0, min(60.0, 3.0 + n * 0.5)),
            rollback_available=False,
            rollback_description="Project/file deletions are not auto-rolled-back; Health can use encrypted backup restore if a row was wrong",
            approval_class=APPROVAL_SEMI,
            destructive=False,
        )

    def repair(
        self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None
    ) -> RepairOutcome:
        self._prog(progress, "Removing development artifacts…")
        from jarvis.integrity_product.remediate import apply_safe_remediations
        from jarvis.integrity_product.scanner import run_scan

        # Always re-scan at execution time — never trust a stale issue context.
        live = run_scan(force=True, trigger="guided_repair_execute")
        findings = live.get("findings") or []
        result = apply_safe_remediations(findings)
        steps = [
            StepResult(
                id=str(a.get("kind") or "action"),
                ok=bool(a.get("ok", True)),
                detail=str(a)[:240],
            )
            for a in (result.get("actions") or [])
        ]
        remaining = int(result.get("remaining_artifacts") or 0)
        ok = remaining == 0
        return RepairOutcome(
            ok=ok,
            executed=True,
            steps=steps,
            message=(
                "Production clean"
                if ok
                else f"Repair finished with {remaining} artifact(s) still present — review Mission Control"
            ),
        )

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        from jarvis.integrity_product.scanner import run_scan

        scan = run_scan(force=True, trigger="guided_repair_verify")
        remaining = int((scan.get("counts") or {}).get("actionable") or (scan.get("counts") or {}).get("safe_to_remove") or 0)
        ok = remaining == 0
        return VerifyResult(
            ok=ok,
            checks=[{"id": "integrity_scan", "ok": ok, "detail": scan.get("status")}],
            message="Production clean" if ok else f"{remaining} development artifact(s) remain",
        )

    def risk_level(self, issue: DetectedIssue) -> str:
        return "very_low"

    def confidence(self, issue: DetectedIssue, diagnosis: Diagnosis) -> float:
        return float(diagnosis.confidence or 0.95)

    def estimated_time(self, issue: DetectedIssue) -> float:
        n = len((issue.context or {}).get("findings") or [])
        return max(8.0, min(60.0, 3.0 + n * 0.5))
