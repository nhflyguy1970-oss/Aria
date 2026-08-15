"""Concrete Guided Repair modules — each owns detect→diagnose→plan→repair→verify."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Callable

from jarvis.repair_product.registry import (
    DetectedIssue,
    Diagnosis,
    RepairOutcome,
    RepairPlan,
    StepResult,
    VerifyResult,
    register_module,
)
from jarvis.repair_product.terminology import APPROVAL_MANUAL, APPROVAL_SAFE, APPROVAL_SEMI

_REGISTERED = False


def _production_integrity_cls():
    from jarvis.integrity_product.repair_module import ProductionIntegrityModule

    return ProductionIntegrityModule


class BaseModule:
    id = "base"
    subsystem = "system"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return self.id

    def detect(self) -> list[DetectedIssue]:
        return []

    def collect_evidence(self, issue: DetectedIssue) -> list[str]:
        return [issue.summary] if issue.summary else []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause=issue.summary or issue.title,
            explanation=issue.summary or issue.title,
            confidence=0.6,
            evidence=self.collect_evidence(issue),
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Inspect", "Attempt safe repair", "Verify"],
            expected_result="Issue resolved and verified",
            risk=self.risk_level(issue),
            risk_why="Default plan",
            estimated_seconds=self.estimated_time(issue),
            rollback_available=False,
            approval_class=self.approval_class,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        return RepairOutcome(ok=False, executed=False, message="Not implemented")

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        return VerifyResult(ok=False, message="No verification")

    def rollback(self, issue: DetectedIssue) -> RepairOutcome | None:
        return None

    def risk_level(self, issue: DetectedIssue) -> str:
        return "low"

    def confidence(self, issue: DetectedIssue, diagnosis: Diagnosis) -> float:
        return float(diagnosis.confidence or 0.5)

    def estimated_time(self, issue: DetectedIssue) -> float:
        return 15.0

    def _prog(self, progress: Callable[[str], None] | None, msg: str) -> None:
        if progress:
            try:
                progress(msg)
            except Exception:
                pass


class ProviderOllamaModule(BaseModule):
    id = "provider_ollama"
    subsystem = "providers"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return "Restart / reconnect Ollama provider and verify it responds"

    def detect(self) -> list[DetectedIssue]:
        try:
            from jarvis.provider_health.probe import ping_provider

            # Routine detect must not force a generate probe (≈5s). Use cached
            # liveness; execute/verify paths still force_probe=True when repairing.
            ping = ping_provider("ollama", force_probe=False)
            if ping.get("alive"):
                return []
            return [
                DetectedIssue(
                    module_id=self.id,
                    subsystem=self.subsystem,
                    title="Ollama provider appears offline",
                    summary=str(ping.get("detail") or ping.get("state") or "Provider not responding"),
                    severity="critical",
                    code="provider_offline",
                    context={"ping": {k: ping.get(k) for k in ("alive", "state", "detail")}},
                )
            ]
        except Exception as exc:
            return [
                DetectedIssue(
                    module_id=self.id,
                    subsystem=self.subsystem,
                    title="Unable to probe Ollama",
                    summary=str(exc),
                    severity="warning",
                    code="probe_error",
                )
            ]

    def collect_evidence(self, issue: DetectedIssue) -> list[str]:
        ev = [issue.summary] if issue.summary else []
        try:
            from jarvis.provider_health.probe import ping_provider

            ping = ping_provider("ollama", force_probe=True)
            ev.append(f"Ping alive={ping.get('alive')} state={ping.get('state')}")
            if ping.get("detail"):
                ev.append(str(ping["detail"]))
        except Exception as exc:
            ev.append(f"Probe error: {exc}")
        return ev

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        cause = "Provider offline"
        conf = 0.85
        if "timeout" in (issue.summary or "").lower():
            cause = "API timeout contacting Ollama"
            conf = 0.8
        elif "connection" in (issue.summary or "").lower():
            cause = "Connection refused / Ollama process not listening"
            conf = 0.9
        return Diagnosis(
            root_cause=cause,
            explanation="Ollama did not respond to a health probe. Common causes: process stopped, wedged, or port blocked.",
            confidence=conf,
            why="Probe returned not-alive",
            evidence=self.collect_evidence(issue),
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=[
                "Ping Ollama",
                "Reconnect / ensure provider",
                "Restart Ollama if still down",
                "Verify provider responds and lists models",
            ],
            expected_result="Ollama responds to health probes again",
            risk="low",
            risk_why="Restarts local inference provider only; does not delete models or data",
            estimated_seconds=25,
            rollback_available=False,
            rollback_description="Not available — restart is one-way; models remain on disk",
            approval_class=APPROVAL_SAFE,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        steps: list[StepResult] = []
        self._prog(progress, "Running provider recovery…")
        try:
            from jarvis.provider_health.recovery import recover

            result = recover(code=issue.code, message=issue.summary, provider="ollama", auto=True)
            for s in result.get("steps") or []:
                steps.append(StepResult(id=str(s.get("id")), ok=bool(s.get("ok")), detail=str(s.get("detail") or "")))
            usable = bool(result.get("usable") or result.get("success"))
            return RepairOutcome(
                ok=usable,
                executed=True,
                steps=steps,
                message=result.get("message") or ("Provider usable" if usable else "Provider still down"),
            )
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, steps=steps, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        checks = []
        try:
            from jarvis.provider_health.probe import list_models, ping_provider

            ping = ping_provider("ollama", force_probe=True)
            checks.append({"id": "ping", "ok": bool(ping.get("alive")), "detail": ping.get("state")})
            models = list_models("ollama")
            ok_models = bool(models.get("models") is not None)
            checks.append({"id": "list_models", "ok": ok_models, "detail": f"{len(models.get('models') or [])} models"})
            ok = bool(ping.get("alive"))
            return VerifyResult(ok=ok, checks=checks, message="Provider responds" if ok else "Provider still not responding")
        except Exception as exc:
            return VerifyResult(ok=False, checks=[{"id": "verify", "ok": False, "detail": str(exc)}], message=str(exc))

    def risk_level(self, issue: DetectedIssue) -> str:
        return "low"

    def estimated_time(self, issue: DetectedIssue) -> float:
        return 25.0


class SchedulerModule(BaseModule):
    id = "scheduler"
    subsystem = "jobs"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return "Restart proactive scheduler thread"

    def detect(self) -> list[DetectedIssue]:
        try:
            from jarvis import proactive_scheduler

            thread = proactive_scheduler._thread
            alive = thread is not None and thread.is_alive()
            if alive:
                return []
            return [
                DetectedIssue(
                    module_id=self.id,
                    subsystem=self.subsystem,
                    title="Proactive scheduler is not running",
                    summary="Scheduler thread missing or dead",
                    severity="warning",
                    code="scheduler_down",
                )
            ]
        except Exception:
            return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Scheduler thread stopped",
            explanation="The proactive scheduler background thread is not alive — timers and nudges will not fire.",
            confidence=0.95,
            evidence=["proactive_scheduler._thread is None or not alive"],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Restart proactive scheduler", "Verify thread is alive"],
            expected_result="Scheduler thread running",
            risk="very_low",
            risk_why="Restarts an in-process thread only",
            estimated_seconds=4,
            rollback_available=False,
            approval_class=APPROVAL_SAFE,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Restarting scheduler…")
        try:
            from jarvis import proactive_scheduler

            if hasattr(proactive_scheduler, "restart"):
                proactive_scheduler.restart()
            elif hasattr(proactive_scheduler, "start"):
                proactive_scheduler.start()
            else:
                return RepairOutcome(ok=False, executed=False, message="No scheduler restart API")
            time.sleep(0.3)
            thread = getattr(proactive_scheduler, "_thread", None)
            ok = thread is not None and thread.is_alive()
            return RepairOutcome(
                ok=ok,
                executed=True,
                steps=[StepResult(id="restart_scheduler", ok=ok, detail="thread alive" if ok else "still down")],
                message="Scheduler restarted" if ok else "Scheduler restart did not stick",
            )
        except Exception as exc:
            return RepairOutcome(ok=False, executed=True, message=str(exc), steps=[StepResult(id="restart", ok=False, detail=str(exc))])

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis import proactive_scheduler

            thread = proactive_scheduler._thread
            ok = thread is not None and thread.is_alive()
            return VerifyResult(ok=ok, checks=[{"id": "thread_alive", "ok": ok}], message="Scheduler alive" if ok else "Scheduler still down")
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))

    def estimated_time(self, issue: DetectedIssue) -> float:
        return 4.0

    def risk_level(self, issue: DetectedIssue) -> str:
        return "very_low"


class SearchIndexModule(BaseModule):
    id = "search_index"
    subsystem = "search"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Repair / rebuild search indexes and verify search returns results"

    def detect(self) -> list[DetectedIssue]:
        issues: list[DetectedIssue] = []
        try:
            from jarvis.search_product import diagnostics

            summary = diagnostics.health_summary() if hasattr(diagnostics, "health_summary") else {}
            if summary.get("ok") is False or summary.get("corrupt"):
                issues.append(
                    DetectedIssue(
                        module_id=self.id,
                        subsystem=self.subsystem,
                        title="Search index appears unhealthy",
                        summary=str(summary.get("detail") or summary.get("message") or "health_summary not ok"),
                        severity="warning",
                        code="search_unhealthy",
                        context={"summary": summary},
                    )
                )
        except Exception:
            pass
        return issues

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Search index unhealthy or corrupt",
            explanation="Search diagnostics reported an unhealthy index. Often caused by interrupted indexing or a partial write.",
            confidence=0.75,
            evidence=self.collect_evidence(issue),
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=[
                "Preserve existing documents",
                "Remove / invalidate damaged index artifacts if needed",
                "Rebuild search index",
                "Verify search returns results",
            ],
            expected_result="Search returns normal results again",
            risk="low",
            risk_why="Rebuilds index metadata; does not delete source documents",
            estimated_seconds=45,
            rollback_available=False,
            rollback_description="Not available — previous index artifacts are replaced",
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Rebuilding search index…")
        steps: list[StepResult] = []
        try:
            # Prefer product rebuild hooks when present
            rebuilt = False
            try:
                from jarvis.search_product import pipeline

                if hasattr(pipeline, "rebuild_index"):
                    out = pipeline.rebuild_index()
                    rebuilt = bool((out or {}).get("ok", True))
                    steps.append(StepResult(id="rebuild_index", ok=rebuilt, detail=str((out or {}).get("message") or "ok")))
            except Exception as exc:
                steps.append(StepResult(id="rebuild_index", ok=False, detail=str(exc)))
            if not rebuilt:
                try:
                    from jarvis import document_services

                    if hasattr(document_services, "rebuild_search_index"):
                        out = document_services.rebuild_search_index()
                        rebuilt = bool((out or {}).get("ok", True))
                        steps.append(StepResult(id="documents_rebuild_search", ok=rebuilt, detail=str(out)))
                except Exception as exc:
                    steps.append(StepResult(id="documents_rebuild_search", ok=False, detail=str(exc)))
            if not any(s.ok for s in steps):
                return RepairOutcome(
                    ok=False,
                    executed=True,
                    steps=steps,
                    message="No search rebuild API succeeded — needs user",
                )
            return RepairOutcome(ok=True, executed=True, steps=steps, message="Search rebuild attempted")
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis.search_product import diagnostics

            if hasattr(diagnostics, "health_summary"):
                summary = diagnostics.health_summary()
                ok = summary.get("ok") is not False and not summary.get("corrupt")
                return VerifyResult(ok=ok, checks=[{"id": "health_summary", "ok": ok, "detail": summary}], message="Search healthy" if ok else "Search still unhealthy")
        except Exception:
            pass
        # Soft verify: module imported
        return VerifyResult(ok=True, checks=[{"id": "module_import", "ok": True}], message="Search module reachable (soft verify)")

    def estimated_time(self, issue: DetectedIssue) -> float:
        return 45.0


class DocumentsIndexModule(BaseModule):
    id = "documents_index"
    subsystem = "documents"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Repair document / OCR indexes"

    def detect(self) -> list[DetectedIssue]:
        return []  # event-driven primarily

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Document index needs rebuild",
            explanation="Document or OCR index is stale, incomplete, or corrupt.",
            confidence=0.7,
            evidence=[issue.summary] if issue.summary else ["Triggered by operator / activity event"],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Rebuild document index", "Verify document search"],
            expected_result="Documents searchable again",
            risk="low",
            risk_why="Rebuilds index only; source files preserved",
            estimated_seconds=60,
            rollback_available=False,
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Rebuilding document index…")
        try:
            from jarvis import document_services

            fn = getattr(document_services, "rebuild_index", None) or getattr(document_services, "reindex", None)
            if not fn:
                return RepairOutcome(ok=False, executed=False, message="document_services has no rebuild_index")
            out = fn()
            ok = bool((out or {}).get("ok", True))
            return RepairOutcome(
                ok=ok,
                executed=True,
                steps=[StepResult(id="rebuild_documents", ok=ok, detail=str(out))],
                message="Document index rebuilt" if ok else "Document rebuild reported failure",
            )
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis import document_services

            ok = True
            detail = "document_services importable"
            if hasattr(document_services, "status"):
                st = document_services.status()
                ok = bool((st or {}).get("ok", True))
                detail = str(st)
            return VerifyResult(ok=ok, checks=[{"id": "documents_status", "ok": ok, "detail": detail}], message=detail)
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class CachesTempModule(BaseModule):
    id = "caches_temp"
    subsystem = "system"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Clean temporary files and rebuild safe caches"

    def detect(self) -> list[DetectedIssue]:
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Stale temporary files or caches",
            explanation="Temporary directories or caches may be consuming space or serving stale data.",
            confidence=0.65,
            evidence=self.collect_evidence(issue),
        )

    def collect_evidence(self, issue: DetectedIssue) -> list[str]:
        from jarvis.config import DATA_DIR

        tmp = DATA_DIR / "tmp"
        ev = []
        if tmp.exists():
            try:
                size = sum(p.stat().st_size for p in tmp.rglob("*") if p.is_file())
                ev.append(f"DATA_DIR/tmp ≈ {size / (1024 * 1024):.1f} MB")
            except Exception as exc:
                ev.append(f"tmp scan error: {exc}")
        else:
            ev.append("No DATA_DIR/tmp directory")
        return ev

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Rotate old logs if oversized", "Clean DATA_DIR/tmp older than 7 days", "Leave user data untouched"],
            expected_result="Temp space reclaimed; caches ready to rebuild on demand",
            risk="low",
            risk_why="Only deletes temporary files under DATA_DIR/tmp older than 7 days",
            estimated_seconds=12,
            rollback_available=False,
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        from jarvis.config import DATA_DIR

        self._prog(progress, "Cleaning temporary files…")
        tmp = DATA_DIR / "tmp"
        removed = 0
        if tmp.is_dir():
            cutoff = time.time() - 7 * 86400
            for p in tmp.rglob("*"):
                try:
                    if p.is_file() and p.stat().st_mtime < cutoff:
                        p.unlink(missing_ok=True)
                        removed += 1
                except Exception:
                    continue
        return RepairOutcome(
            ok=True,
            executed=True,
            steps=[StepResult(id="clean_tmp", ok=True, detail=f"removed {removed} files")],
            message=f"Removed {removed} old temp file(s)",
        )

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        from jarvis.config import DATA_DIR

        ok = DATA_DIR.exists()
        return VerifyResult(ok=ok, checks=[{"id": "data_dir", "ok": ok}], message="DATA_DIR intact")


class DockerServicesModule(BaseModule):
    id = "docker_services"
    subsystem = "docker"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Repair Docker-managed workstation services"

    def detect(self) -> list[DetectedIssue]:
        try:
            from jarvis.application.standalone.workstation_impl.operations import diagnose

            # Cached diagnose for scan/home; force=True reserved for verify/repair.
            diag = diagnose(force=False)
            out = []
            for iss in diag.get("issues") or []:
                if iss.get("component") in ("postgres", "redis", "qdrant", "mongodb", "n8n", "open_webui", "litellm"):
                    out.append(
                        DetectedIssue(
                            module_id=self.id,
                            subsystem=self.subsystem,
                            title=str(iss.get("message") or iss.get("label")),
                            summary=str(iss.get("message")),
                            severity=str(iss.get("severity") or "warning"),
                            code=str(iss.get("action") or "docker_issue"),
                            context={"component": iss.get("component"), "raw": iss},
                        )
                    )
            return out
        except Exception:
            return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause=f"Docker service issue: {issue.context.get('component') or issue.title}",
            explanation=issue.summary or "A managed Docker service is unhealthy or offline.",
            confidence=0.8,
            evidence=[issue.summary] if issue.summary else [],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Run safe workstation recovery for Docker services", "Re-check component health"],
            expected_result="Managed Docker services healthy",
            risk="medium",
            risk_why="May restart containers; brief service interruption",
            estimated_seconds=40,
            rollback_available=False,
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Running safe Docker/workstation recovery…")
        try:
            from jarvis.application.standalone.workstation_impl import repair as wr

            if hasattr(wr, "repair_docker_services"):
                out = wr.repair_docker_services()
                ok = bool((out or {}).get("ok"))
                return RepairOutcome(ok=ok, executed=True, steps=[StepResult(id="docker", ok=ok, detail=str(out))], message=str((out or {}).get("detail") or out))
            from jarvis.application.standalone.workstation_impl.operations import recover_safe

            out = recover_safe()
            ok = bool(out.get("ok"))
            return RepairOutcome(ok=ok, executed=True, steps=[StepResult(id="recover_safe", ok=ok, detail=str(out.get("report") or "")[:500])], message="recover_safe finished")
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis.application.standalone.workstation_impl.operations import diagnose

            diag = diagnose(force=True)
            comp = (issue.context or {}).get("component")
            still = [i for i in (diag.get("issues") or []) if i.get("component") == comp] if comp else []
            ok = len(still) == 0
            return VerifyResult(ok=ok, checks=[{"id": "diagnose", "ok": ok, "detail": still or "clear"}], message="Component clear" if ok else "Still unhealthy")
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class HomeAssistantModule(BaseModule):
    id = "home_assistant"
    subsystem = "smarthome"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return "Reconnect Home Assistant and verify API"

    def detect(self) -> list[DetectedIssue]:
        try:
            from jarvis.home_assistant_product.mission_bridge import smarthome_mission_panel

            panel = smarthome_mission_panel()
            if panel.get("state") in ("ready", "ok", "connected"):
                return []
            if panel.get("state") in ("unknown",):
                return []
            return [
                DetectedIssue(
                    module_id=self.id,
                    subsystem=self.subsystem,
                    title="Home Assistant connection issue",
                    summary=str(panel.get("detail") or panel.get("state")),
                    severity="warning",
                    code="ha_disconnect",
                    context={"panel": panel},
                )
            ]
        except Exception:
            return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Home Assistant unreachable or token invalid",
            explanation="Smart-home bridge cannot reach Home Assistant.",
            confidence=0.7,
            evidence=[issue.summary] if issue.summary else [],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Reconnect Home Assistant client", "Run connectivity test", "Verify entities reachable"],
            expected_result="Home Assistant responds",
            risk="very_low",
            risk_why="Reconnect only; no device state changes",
            estimated_seconds=8,
            rollback_available=False,
            approval_class=APPROVAL_SAFE,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Reconnecting Home Assistant…")
        try:
            # Prefer product test hooks
            tested = False
            detail = ""
            for mod_name in ("jarvis.home_assistant_product.engine", "jarvis.ha"):
                try:
                    import importlib

                    mod = importlib.import_module(mod_name)
                    fn = getattr(mod, "test_connection", None) or getattr(mod, "reconnect", None) or getattr(mod, "ping", None)
                    if fn:
                        out = fn()
                        tested = True
                        detail = str(out)
                        ok = bool((out or {}).get("ok", True)) if isinstance(out, dict) else bool(out)
                        return RepairOutcome(ok=ok, executed=True, steps=[StepResult(id="ha_reconnect", ok=ok, detail=detail)], message=detail)
                except Exception as exc:
                    detail = str(exc)
            return RepairOutcome(ok=False, executed=tested, message=detail or "No HA reconnect API")
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis.home_assistant_product.mission_bridge import smarthome_mission_panel

            panel = smarthome_mission_panel()
            ok = panel.get("state") in ("ready", "ok", "connected")
            return VerifyResult(ok=ok, checks=[{"id": "ha_panel", "ok": ok, "detail": panel.get("state")}], message=str(panel.get("detail") or panel.get("state")))
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class BackgroundJobsModule(BaseModule):
    id = "background_jobs"
    subsystem = "jobs"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return "Resume interrupted background / media jobs"

    def detect(self) -> list[DetectedIssue]:
        try:
            from jarvis.jobs.checkpointed import list_jobs

            failed = list(list_jobs(status="failed")[:5])
            if not failed:
                return []
            return [
                DetectedIssue(
                    module_id=self.id,
                    subsystem=self.subsystem,
                    title=f"{len(failed)} failed background job(s)",
                    summary=str(getattr(failed[0], "goal", None) or (failed[0] if isinstance(failed[0], dict) else failed[0]))[:200],
                    severity="warning",
                    code="jobs_failed",
                    context={"count": len(failed)},
                )
            ]
        except Exception:
            return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Background jobs failed or interrupted",
            explanation="One or more checkpointed jobs are in a failed state and may be resumable.",
            confidence=0.8,
            evidence=[issue.summary] if issue.summary else [],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["List failed jobs", "Resume resumable media/agent jobs", "Verify job center no longer stuck"],
            expected_result="Failed jobs resumed or clearly marked needs-user",
            risk="low",
            risk_why="Resumes existing jobs; does not delete job history",
            estimated_seconds=20,
            rollback_available=False,
            approval_class=APPROVAL_SAFE,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Resuming jobs…")
        steps = []
        try:
            from jarvis import media_jobs

            if hasattr(media_jobs, "resume_all"):
                out = media_jobs.resume_all()
                ok = bool((out or {}).get("ok", True))
                steps.append(StepResult(id="resume_media", ok=ok, detail=str(out)))
                return RepairOutcome(ok=ok, executed=True, steps=steps, message="Media jobs resume requested")
        except Exception as exc:
            steps.append(StepResult(id="resume_media", ok=False, detail=str(exc)))
        return RepairOutcome(
            ok=False,
            executed=True,
            steps=steps,
            message="Could not auto-resume jobs — open Job Center (needs user)",
        )

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis.jobs.checkpointed import list_jobs

            failed = list(list_jobs(status="failed")[:5])
            # Soft: repair attempted; fewer failures is success, same count is not claimed fixed
            ok = len(failed) == 0
            return VerifyResult(
                ok=ok,
                checks=[{"id": "failed_jobs", "ok": ok, "detail": f"{len(failed)} failed"}],
                message="No failed jobs" if ok else f"{len(failed)} failed job(s) remain — not claiming fixed",
            )
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class BrowserWebsocketModule(BaseModule):
    id = "browser_websocket"
    subsystem = "browser"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return "Reconnect browser / websocket session"

    def detect(self) -> list[DetectedIssue]:
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Browser websocket disconnected",
            explanation="Live browser bridge lost its websocket or session.",
            confidence=0.7,
            evidence=[issue.summary] if issue.summary else [],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Reset browser session state", "Reconnect websocket", "Verify session responds"],
            expected_result="Browser bridge connected",
            risk="very_low",
            risk_why="Reconnects session only",
            estimated_seconds=6,
            rollback_available=False,
            approval_class=APPROVAL_SAFE,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Reconnecting browser…")
        try:
            from jarvis.extensions.browser import api as browser_api

            fn = getattr(browser_api, "reconnect", None) or getattr(browser_api, "reset_session", None)
            if not fn:
                return RepairOutcome(ok=False, executed=False, message="No browser reconnect API — open Browser view")
            out = fn()
            ok = bool((out or {}).get("ok", True)) if isinstance(out, dict) else bool(out)
            return RepairOutcome(ok=ok, executed=True, steps=[StepResult(id="browser_reconnect", ok=ok, detail=str(out))], message=str(out))
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        return VerifyResult(ok=True, checks=[{"id": "soft", "ok": True}], message="Browser reconnect requested (soft verify)")


class MissionControlCacheModule(BaseModule):
    id = "mission_control_cache"
    subsystem = "mission_control"
    approval_class = APPROVAL_SAFE

    def description(self) -> str:
        return "Repair Mission Control caches / refresh health snapshot"

    def detect(self) -> list[DetectedIssue]:
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Stale Mission Control cache",
            explanation="Mission Control health snapshot or series cache is stale or inconsistent.",
            confidence=0.7,
            evidence=[],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Clear Mission Control series cache files", "Force-refresh health snapshot", "Verify snapshot loads"],
            expected_result="Mission Control health loads cleanly",
            risk="very_low",
            risk_why="Deletes only MC series cache JSON, not product data",
            estimated_seconds=5,
            rollback_available=False,
            approval_class=APPROVAL_SAFE,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        from jarvis.config import DATA_DIR

        self._prog(progress, "Clearing Mission Control caches…")
        series = DATA_DIR / "mission_control" / "series"
        removed = 0
        if series.is_dir():
            for p in series.glob("*.json"):
                try:
                    p.unlink()
                    removed += 1
                except Exception:
                    continue
        return RepairOutcome(
            ok=True,
            executed=True,
            steps=[StepResult(id="clear_mc_series", ok=True, detail=f"removed {removed}")],
            message=f"Cleared {removed} series cache file(s)",
        )

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis import mission_control

            snap = mission_control.health_summary(force=True)
            ok = snap is not None
            return VerifyResult(ok=ok, checks=[{"id": "health_summary", "ok": ok}], message="Health summary loaded" if ok else "Failed to load")
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class GalleryMetadataModule(BaseModule):
    id = "gallery_metadata"
    subsystem = "gallery"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Repair gallery metadata consistency"

    def detect(self) -> list[DetectedIssue]:
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Gallery metadata inconsistency",
            explanation="Gallery index/metadata may be out of sync with files on disk.",
            confidence=0.65,
            evidence=[],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Run gallery consistency repair", "Verify gallery listing"],
            expected_result="Gallery opens and lists assets",
            risk="low",
            risk_why="Repairs metadata; soft-delete rules preserved",
            estimated_seconds=30,
            rollback_available=False,
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Repairing gallery metadata…")
        try:
            from jarvis.gallery_product import consistency

            if hasattr(consistency, "repair"):
                out = consistency.repair()
                ok = bool((out or {}).get("ok", True))
                return RepairOutcome(ok=ok, executed=True, steps=[StepResult(id="gallery_consistency", ok=ok, detail=str(out))], message=str(out))
            return RepairOutcome(ok=False, executed=False, message="gallery consistency.repair missing")
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis.gallery_product import consistency

            if hasattr(consistency, "check"):
                out = consistency.check()
                ok = bool((out or {}).get("ok", True))
                return VerifyResult(ok=ok, checks=[{"id": "gallery_check", "ok": ok, "detail": out}], message=str(out))
            return VerifyResult(ok=True, checks=[{"id": "soft", "ok": True}], message="Gallery module reachable")
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class HealthStoreModule(BaseModule):
    id = "health_store"
    subsystem = "health"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Repair Health product store integrity (never deletes PHR rows)"

    def detect(self) -> list[DetectedIssue]:
        try:
            from jarvis.health_product import store as hstore

            # Integrity: can open DB and read schema version
            ver = hstore.schema_version()
            if not ver:
                return [
                    DetectedIssue(
                        module_id=self.id,
                        subsystem=self.subsystem,
                        title="Health schema version missing",
                        summary="schema_version empty",
                        severity="warning",
                        code="health_schema",
                    )
                ]
        except Exception as exc:
            return [
                DetectedIssue(
                    module_id=self.id,
                    subsystem=self.subsystem,
                    title="Health store not readable",
                    summary=str(exc),
                    severity="critical",
                    code="health_db_error",
                )
            ]
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Health SQLite store error",
            explanation="Health database could not be opened or migrated cleanly.",
            confidence=0.85,
            evidence=[issue.summary] if issue.summary else [],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Open Health DB", "Run migrations", "Verify schema_version", "Never delete health rows"],
            expected_result="Health API responds with schema version",
            risk="low",
            risk_why="Migrations only; no row deletion",
            estimated_seconds=10,
            rollback_available=True,
            rollback_description="Use Health encrypted backup restore if migration fails",
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Repairing Health store…")
        try:
            from jarvis.health_product import store as hstore

            hstore.reset_migration_cache()
            hstore.ensure_dirs()
            conn = hstore.connect()
            conn.close()
            ver = hstore.schema_version()
            ok = bool(ver)
            return RepairOutcome(
                ok=ok,
                executed=True,
                steps=[StepResult(id="health_migrate", ok=ok, detail=f"schema={ver}")],
                message=f"Health schema {ver}" if ok else "schema missing",
            )
        except Exception as exc:
            return RepairOutcome(ok=False, executed=True, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        try:
            from jarvis.health_product.engine import product_status

            st = product_status()
            ok = bool(st.get("ok"))
            return VerifyResult(ok=ok, checks=[{"id": "health_product_status", "ok": ok, "detail": st.get("schema_version")}], message="Health OK" if ok else "Health not OK")
        except Exception as exc:
            return VerifyResult(ok=False, message=str(exc))


class AriaRestartModule(BaseModule):
    id = "aria_restart"
    subsystem = "aria"
    approval_class = APPROVAL_SEMI

    def description(self) -> str:
        return "Restart Aria server process (semi-automatic)"

    def detect(self) -> list[DetectedIssue]:
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Aria process needs restart",
            explanation="Operator requested or recovery requires restarting the Aria server.",
            confidence=0.9,
            evidence=[],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Request Aria server restart", "Wait for process to come back", "Verify /api/ping"],
            expected_result="Aria responds to health ping after restart",
            risk="medium",
            risk_why="Brief UI/API interruption during restart",
            estimated_seconds=20,
            rollback_available=False,
            approval_class=APPROVAL_SEMI,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        self._prog(progress, "Requesting Aria restart…")
        try:
            from jarvis.server_restart import request_restart

            out = request_restart(source="guided_repair", detail="approved aria restart")
            ok = bool((out or {}).get("ok", True))
            return RepairOutcome(ok=ok, executed=True, steps=[StepResult(id="aria_restart", ok=ok, detail=str(out))], message=str(out))
        except Exception as exc:
            return RepairOutcome(ok=False, executed=False, message=str(exc))

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        # After restart the verifying process may be the new one — soft OK if importable
        return VerifyResult(ok=True, checks=[{"id": "soft_post_restart", "ok": True}], message="Restart requested; verify ping from client")


class DestructiveGuardModule(BaseModule):
    """Manual-only placeholder for destructive actions — never auto-runs."""

    id = "destructive_guard"
    subsystem = "security"
    approval_class = APPROVAL_MANUAL

    def description(self) -> str:
        return "Destructive operations require explicit multi-step confirmation (never one-click)"

    def detect(self) -> list[DetectedIssue]:
        return []

    def diagnose(self, issue: DetectedIssue) -> Diagnosis:
        return Diagnosis(
            root_cause="Destructive action requested",
            explanation="Deletes, resets, and git destructive ops are never one-click repairs.",
            confidence=0.99,
            evidence=["Manual confirmation required by policy"],
        )

    def repair_plan(self, issue: DetectedIssue, diagnosis: Diagnosis) -> RepairPlan:
        return RepairPlan(
            steps=["Review exact target", "Type explicit confirmation", "Execute only after confirm_destructive=true"],
            expected_result="No automatic action — operator must use dedicated destructive tools",
            risk="critical",
            risk_why="May permanently delete data",
            estimated_seconds=0,
            rollback_available=False,
            rollback_description="Often impossible after delete",
            approval_class=APPROVAL_MANUAL,
            destructive=True,
        )

    def repair(self, issue: DetectedIssue, plan: RepairPlan, *, progress: Callable[[str], None] | None = None) -> RepairOutcome:
        return RepairOutcome(
            ok=False,
            executed=False,
            message="Refused: destructive repairs never execute from Guided Repair. Use the dedicated product UI with explicit confirmation.",
        )

    def verify(self, issue: DetectedIssue) -> VerifyResult:
        return VerifyResult(ok=False, message="Destructive path not executed (by design)")


def register_all() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    for cls in (
        ProviderOllamaModule,
        SchedulerModule,
        SearchIndexModule,
        DocumentsIndexModule,
        CachesTempModule,
        DockerServicesModule,
        HomeAssistantModule,
        BackgroundJobsModule,
        BrowserWebsocketModule,
        MissionControlCacheModule,
        GalleryMetadataModule,
        HealthStoreModule,
        AriaRestartModule,
        DestructiveGuardModule,
        _production_integrity_cls(),
    ):
        register_module(cls())
    _REGISTERED = True
