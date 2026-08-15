"""Guided Repair Engine — full lifecycle with verification and learning."""

from __future__ import annotations

import time
from typing import Any, Callable

from jarvis.repair_product import store
from jarvis.repair_product.registry import (
    DetectedIssue,
    Diagnosis,
    RepairPlan,
    VerifyResult,
    all_modules,
    get_module,
)
from jarvis.repair_product.terminology import (
    APPROVAL_MANUAL,
    APPROVAL_SEMI,
    BOUNDARIES,
    DISCLAIMER,
    MENTAL_MODEL,
    SCHEMA_VERSION,
    STATES,
    TERMINOLOGY,
)


def _ensure_modules() -> None:
    from jarvis.repair_product import modules  # noqa: F401 — registers on import

    modules.register_all()


# Short TTL so /api/repair/home stays warm; Guided Repair POST /scan uses force=True.
_SCAN_TTL_S = 30.0
_SCAN_CACHE: dict[str, Any] = {"at": 0.0, "payload": None}

def product_status() -> dict[str, Any]:
    _ensure_modules()
    from jarvis.repair_product import maintenance, reputation

    issues = store.list_issues(active_only=True)
    hist = store.list_history(limit=5)
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "schema_version": SCHEMA_VERSION,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
        "disclaimer": DISCLAIMER,
        "states": list(STATES),
        "modules": [{"id": m.id, "subsystem": m.subsystem, "description": m.description()} for m in all_modules()],
        "active_issues": len(issues),
        "recent_repairs": hist,
        "maintenance": maintenance.status(),
        "reputations": reputation.all_reputations()[:8],
        "healthy": not any(i.get("severity") == "critical" for i in issues) and not any(i.get("priority") == "critical" for i in issues),
    }


def home_payload() -> dict[str, Any]:
    from jarvis.repair_product import knowledge, maintenance, reputation, root_causes
    from jarvis.repair_product.impact import sort_by_priority

    scan = scan_issues()
    issues = sort_by_priority(scan.get("issues") or [])
    # One product_status() — previously called twice (modules + diagnostics).
    status = product_status()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "note": BOUNDARIES["philosophy"],
        "disclaimer": DISCLAIMER,
        "issues": issues,
        "repair_queue": issues,
        "history": store.list_history(limit=30),
        "learning": store.learning_stats(),
        "auto_approve": store.auto_approve_list(),
        "modules": status["modules"],
        "maintenance": maintenance.status(),
        "reputations": reputation.all_reputations(),
        "knowledge": knowledge.search(limit=20),
        "root_causes": root_causes.list_all()[:20],
        "diagnostics": status,
    }


def _rollback_maturity(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("rollback_available") and plan.get("rollback_partial"):
        kind = "partial"
        label = "Rollback partial"
        why = plan.get("rollback_description") or "Some changes can be undone; others cannot."
    elif plan.get("rollback_available"):
        kind = "available"
        label = "Rollback available"
        why = plan.get("rollback_description") or "Previous state can be restored."
    else:
        kind = "unavailable"
        label = "Rollback unavailable"
        why = plan.get("rollback_description") or "This repair cannot be undone automatically."
    return {"kind": kind, "label": label, "why": why}


def _workflow_steps(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Multi-step repair workflow visibility."""
    raw = list(plan.get("steps") or [])
    # Canonical envelope around module steps
    envelope = [
        ("diagnose", "Diagnose"),
        ("backup", "Backup" if plan.get("rollback_available") else "Backup (skipped — none available)"),
        ("repair", "Repair"),
        ("restart", "Restart" if plan.get("restart_required") else "Restart (not required)"),
        ("verify", "Verify"),
        ("monitor", "Monitor"),
        ("close", "Close"),
    ]
    # Expand repair with concrete steps
    out = []
    for key, title in envelope:
        if key == "repair":
            for i, s in enumerate(raw):
                out.append({"id": f"repair_{i}", "title": s, "phase": "repair", "status": "pending"})
        else:
            out.append({"id": key, "title": title, "phase": key, "status": "pending"})
    return out


def _panel_from_issue(issue: dict[str, Any]) -> dict[str, Any]:
    conf = float(issue.get("confidence") or 0)
    conf_meta = issue.get("confidence_meta") or {}
    conf_label = conf_meta.get("confidence_label") or f"{int(round(conf * 100))}%"
    conf_reasons = conf_meta.get("reasons") or issue.get("confidence_reasons") or []
    plan = issue.get("plan") or {}
    steps = plan.get("steps") or []
    impact = issue.get("impact") or {}
    dependency = issue.get("dependency") or {}
    rollback = _rollback_maturity(plan)
    root = issue.get("root_cause_article") or {}
    reputation = issue.get("reputation") or {}
    return {
        "issue_id": issue.get("id"),
        "state": issue.get("state"),
        "title": issue.get("title"),
        "priority": issue.get("priority") or "medium",
        "confidence": conf,
        "confidence_label": conf_label,
        "confidence_reasons": conf_reasons,
        "diagnosis": issue.get("diagnosis") or {},
        "evidence": issue.get("evidence") or [],
        "plan_steps": steps,
        "workflow": issue.get("workflow") or _workflow_steps(plan),
        "risk": plan.get("risk"),
        "risk_why": plan.get("risk_why"),
        "estimated_seconds": plan.get("estimated_seconds"),
        "estimated_time_label": _fmt_time(plan.get("estimated_seconds")),
        "rollback": rollback,
        "rollback_available": rollback["kind"] != "unavailable",
        "rollback_description": rollback["why"],
        "expected_result": plan.get("expected_result"),
        "approval_class": plan.get("approval_class"),
        "destructive": bool(plan.get("destructive")),
        "impact": impact,
        "dependency": dependency,
        "root_cause": root,
        "reputation": reputation,
        "monitoring": issue.get("monitoring"),
        "message": _human_message(issue, conf_label, plan, conf_reasons, impact, dependency, rollback),
        "disclaimer": DISCLAIMER,
    }


def _fmt_time(seconds: Any) -> str:
    try:
        s = float(seconds or 0)
    except (TypeError, ValueError):
        return "unknown"
    if s < 60:
        return f"{int(round(s))} seconds"
    return f"{s / 60:.1f} minutes"


def _human_message(
    issue: dict[str, Any],
    conf_label: str,
    plan: dict[str, Any],
    conf_reasons: list[str] | None = None,
    impact: dict[str, Any] | None = None,
    dependency: dict[str, Any] | None = None,
    rollback: dict[str, Any] | None = None,
) -> str:
    diag = issue.get("diagnosis") or {}
    evidence = issue.get("evidence") or []
    steps = plan.get("steps") or []
    impact = impact or issue.get("impact") or {}
    dependency = dependency or issue.get("dependency") or {}
    rollback = rollback or _rollback_maturity(plan)
    lines = [
        f"I found a problem: **{issue.get('title') or 'Issue'}**",
        f"**Priority:** {issue.get('priority') or 'medium'}",
        "",
        f"**Confidence:** {conf_label}",
        "**Reason:**",
    ]
    for r in (conf_reasons or [])[:6]:
        lines.append(f"• {r}")
    if not conf_reasons:
        lines.append("• Limited historical signal")
    lines += [
        "",
        f"**Diagnosis:** {diag.get('root_cause') or diag.get('explanation') or '—'}",
        "",
        "**Evidence**",
    ]
    for e in evidence[:8]:
        lines.append(f"• {e}")
    if not evidence:
        lines.append("• (gathering evidence)")
    if dependency.get("display"):
        lines += ["", "**Dependency chain** (repair lowest first)", dependency["display"]]
    if impact:
        lines += [
            "",
            "**Impact**",
            f"• Affected: {', '.join(impact.get('affected') or []) or '—'}",
            f"• Not affected: {', '.join((impact.get('not_affected') or [])[:6]) or '—'}",
            f"• Expected downtime: {impact.get('expected_downtime_label') or '—'}",
            f"• Restart required: {'yes' if impact.get('restart_required') else 'no'}",
            f"• Data risk: {impact.get('data_risk') or '—'}",
            f"• Configuration risk: {impact.get('configuration_risk') or '—'}",
            f"• User interruption: {impact.get('user_interruption') or '—'}",
        ]
    lines += ["", "**Repair plan**"]
    for s in steps:
        lines.append(f"✓ {s}")
    lines += [
        "",
        f"**Risk:** {plan.get('risk') or '—'} — {plan.get('risk_why') or ''}",
        f"**Estimated time:** {_fmt_time(plan.get('estimated_seconds'))}",
        f"**Rollback:** {rollback.get('label')} — {rollback.get('why')}",
        f"**Expected result:** {plan.get('expected_result') or '—'}",
        "",
        "Would you like me to repair it?",
        "",
        f"_{DISCLAIMER}_",
    ]
    return "\n".join(lines)


def scan_issues(*, force: bool = False) -> dict[str, Any]:
    """Detect issues across all modules and prepare repair-ready panels (no execution).

    Routine /home scans reuse a short TTL cache so Mission/Repair panels stay
    responsive. Pass force=True (Guided Repair Scan) for a fresh detect pass.
    """
    from jarvis.repair_product import maintenance
    from jarvis.repair_product.dependencies import order_issues_by_dependency
    from jarvis.repair_product.impact import sort_by_priority
    from jarvis.repair_product.monitoring import tick as monitor_tick

    global _SCAN_CACHE
    now = time.time()
    if (
        not force
        and isinstance(_SCAN_CACHE.get("payload"), dict)
        and now - float(_SCAN_CACHE.get("at") or 0) < _SCAN_TTL_S
    ):
        cached = dict(_SCAN_CACHE["payload"])
        cached["cached"] = True
        return cached

    try:
        monitor_tick()
    except Exception:
        pass

    _ensure_modules()
    prepared: list[dict[str, Any]] = []
    for mod in all_modules():
        try:
            found = mod.detect() or []
        except Exception as exc:
            found = [
                DetectedIssue(
                    module_id=mod.id,
                    subsystem=mod.subsystem,
                    title=f"{mod.subsystem} detection error",
                    summary=str(exc),
                    severity="warning",
                    code="detect_error",
                )
            ]
        for det in found:
            panel = prepare_issue(det)
            if panel.get("ok"):
                prepared.append(panel["issue"])

    # Priority first, then dependency order within priority
    prepared = sort_by_priority(order_issues_by_dependency(prepared))
    maint = maintenance.status()
    if maint.get("enabled"):
        for iss in prepared:
            iss["suppressed_by_maintenance"] = True
            iss["recommendation_delayed"] = True
    payload = {
        "ok": True,
        "issues": prepared,
        "count": len(prepared),
        "critical": sum(1 for i in prepared if i.get("priority") == "critical" or i.get("severity") == "critical"),
        "maintenance": maint,
        "disclaimer": DISCLAIMER,
        "cached": False,
    }
    _SCAN_CACHE["at"] = time.time()
    _SCAN_CACHE["payload"] = dict(payload)
    return payload


def prepare_issue(det: DetectedIssue) -> dict[str, Any]:
    from jarvis.repair_product import confidence as confidence_mod
    from jarvis.repair_product import dependencies, impact, reputation, root_causes

    _ensure_modules()
    mod = get_module(det.module_id)
    if not mod:
        return {"ok": False, "message": f"Unknown repair module: {det.module_id}"}

    # Reuse active issue with same fingerprint (avoid scan spam)
    fp = det.fingerprint()
    for existing in store.list_issues(active_only=True):
        if existing.get("fingerprint") == fp and existing.get("state") not in ("repair_successful",):
            # Refresh context so Production Integrity repairs against the latest scan.
            if det.context:
                updated = store.update_issue(
                    existing["id"],
                    {
                        "context": det.context,
                        "summary": det.summary or existing.get("summary"),
                        "severity": det.severity or existing.get("severity"),
                        "title": det.title or existing.get("title"),
                    },
                )
                existing = updated or store.get_issue(existing["id"]) or existing
            return {"ok": True, "issue": existing, "panel": _panel_from_issue(existing), "disclaimer": DISCLAIMER, "reused": True}

    issue = {
        "id": store.new_id("iss"),
        "created_at": time.time(),
        "module_id": det.module_id,
        "subsystem": det.subsystem,
        "title": det.title,
        "summary": det.summary,
        "severity": det.severity,
        "code": det.code,
        "context": det.context,
        "fingerprint": fp,
        "state": "investigating",
    }
    issue = store.save_issue(issue)

    try:
        evidence = list(mod.collect_evidence(det) or [])
        diagnosis = mod.diagnose(det)
        if not isinstance(diagnosis, Diagnosis):
            diagnosis = Diagnosis(root_cause=str(diagnosis), explanation=str(diagnosis), confidence=0.4, evidence=evidence)
        merged_ev = list(dict.fromkeys([*(diagnosis.evidence or []), *evidence]))
        base_conf = float(mod.confidence(det, diagnosis))
        if base_conf != base_conf:  # NaN
            base_conf = float(diagnosis.confidence or 0.5)
        conf_meta = confidence_mod.justify(
            base_conf,
            module_id=det.module_id,
            code=det.code,
            evidence_count=len(merged_ev),
        )
        conf = float(conf_meta["confidence"])
        plan = mod.repair_plan(det, diagnosis)
        if not isinstance(plan, RepairPlan):
            return {"ok": False, "message": "Module returned invalid repair plan"}
        risk = plan.risk or mod.risk_level(det)
        est = plan.estimated_seconds or mod.estimated_time(det)
        impact_info = impact.build_impact(det.module_id, estimated_seconds=est, risk=risk)
        priority = impact.severity_to_priority(det.severity, det.module_id)
        dep = dependencies.analyze(det.subsystem)
        plan_dict = {
            "steps": list(plan.steps),
            "expected_result": plan.expected_result,
            "risk": risk,
            "risk_why": plan.risk_why,
            "estimated_seconds": est,
            "rollback_available": bool(plan.rollback_available),
            "rollback_description": plan.rollback_description,
            "rollback_partial": bool(getattr(plan, "rollback_partial", False)),
            "approval_class": plan.approval_class,
            "destructive": bool(plan.destructive),
            "restart_required": bool(impact_info.get("restart_required")),
        }
        workflow = _workflow_steps(plan_dict)
        root_article = root_causes.lookup(det.module_id, det.code) or {}
        rep = reputation.for_module(det.module_id)
        state = "unsafe_to_repair" if plan.destructive and plan.approval_class == APPROVAL_MANUAL and conf < 0.5 else "repair_ready"
        if plan.approval_class == APPROVAL_MANUAL:
            state = "needs_user" if state != "unsafe_to_repair" else state
        updated = store.update_issue(
            issue["id"],
            {
                "state": "diagnosis_complete" if state == "repair_ready" else state,
                "evidence": merged_ev,
                "confidence": conf,
                "confidence_meta": conf_meta,
                "confidence_reasons": conf_meta.get("reasons") or [],
                "priority": priority,
                "impact": impact_info,
                "dependency": dep,
                "workflow": workflow,
                "root_cause_article": root_article,
                "reputation": rep,
                "diagnosis": {
                    "root_cause": diagnosis.root_cause,
                    "explanation": diagnosis.explanation,
                    "why": diagnosis.why or diagnosis.explanation,
                    "confidence": conf,
                },
                "plan": plan_dict,
            },
        )
        if updated and updated.get("state") == "diagnosis_complete":
            updated = store.update_issue(issue["id"], {"state": "repair_ready"})
        issue = updated or issue
    except Exception as exc:
        issue = store.update_issue(issue["id"], {"state": "needs_user", "error": str(exc)}) or issue
        return {"ok": False, "issue": issue, "message": f"Diagnosis failed: {exc}", "disclaimer": DISCLAIMER}

    panel = _panel_from_issue(issue)
    return {"ok": True, "issue": issue, "panel": panel, "disclaimer": DISCLAIMER}


def preview_repair(issue_id: str) -> dict[str, Any]:
    """Preview Repair — show everything that would happen; modify nothing."""
    issue = store.get_issue(issue_id)
    if not issue:
        return {"ok": False, "message": "Issue not found", "disclaimer": DISCLAIMER}
    plan = issue.get("plan") or {}
    impact_info = issue.get("impact") or {}
    rollback = _rollback_maturity(plan)
    preview = {
        "ok": True,
        "preview": True,
        "modifies_system": False,
        "issue_id": issue_id,
        "title": issue.get("title"),
        "commands": list(plan.get("steps") or []),
        "workflow": issue.get("workflow") or _workflow_steps(plan),
        "subsystems_affected": impact_info.get("affected") or [],
        "subsystems_not_affected": impact_info.get("not_affected") or [],
        "estimated_duration": _fmt_time(plan.get("estimated_seconds")),
        "estimated_seconds": plan.get("estimated_seconds"),
        "expected_outcome": plan.get("expected_result"),
        "rollback": rollback,
        "risk": plan.get("risk"),
        "priority": issue.get("priority"),
        "confidence": issue.get("confidence"),
        "confidence_reasons": issue.get("confidence_reasons") or [],
        "dependency": issue.get("dependency"),
        "message": (
            "Preview only — no changes will be made.\n\n"
            + (_panel_from_issue(issue).get("message") or "")
        ),
        "disclaimer": DISCLAIMER,
    }
    return preview


def plan_from_event(event: dict[str, Any] | None = None, *, text: str = "") -> dict[str, Any]:
    """Map an Activity Center / free-text event into the best matching repair panel."""
    _ensure_modules()
    hay = f"{text} {(event or {}).get('title') or ''} {(event or {}).get('detail') or ''} {(event or {}).get('category') or ''}".lower()
    scan = scan_issues()
    issues = scan.get("issues") or []
    # Prefer active detected issues that match keywords
    scored: list[tuple[int, dict]] = []
    for iss in issues:
        blob = f"{iss.get('title')} {iss.get('summary')} {iss.get('subsystem')} {iss.get('code')}".lower()
        score = sum(1 for tok in hay.split() if len(tok) > 3 and tok in blob)
        if iss.get("subsystem") and iss["subsystem"] in hay:
            score += 3
        if iss.get("module_id") and iss["module_id"].replace("_", " ") in hay:
            score += 2
        scored.append((score, iss))
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored and scored[0][0] > 0:
        best = scored[0][1]
        return {"ok": True, "matched": True, "panel": _panel_from_issue(best), "issue": best, "disclaimer": DISCLAIMER}

    # Heuristic module hints when nothing currently detected
    hint_map = [
        (("ollama", "provider", "model", "inference", "timeout"), "provider_ollama"),
        (("home assistant", "homeassistant", "ha "), "home_assistant"),
        (("search", "index"), "search_index"),
        (("document", "ocr"), "documents_index"),
        (("scheduler",), "scheduler"),
        (("docker",), "docker_services"),
        (("cache", "temp", "thumbnail"), "caches_temp"),
        (("websocket", "browser"), "browser_websocket"),
        (("job", "media"), "background_jobs"),
        (("gallery",), "gallery_metadata"),
        (("health",), "health_store"),
        (("mission",), "mission_control_cache"),
    ]
    for keys, mid in hint_map:
        if any(k in hay for k in keys):
            mod = get_module(mid)
            if not mod:
                continue
            det = DetectedIssue(
                module_id=mid,
                subsystem=mod.subsystem,
                title=f"Suggested repair: {mod.description()}",
                summary=(event or {}).get("detail") or text or "From activity event",
                severity="warning",
                code="from_event",
                context={"event": event or {}, "text": text},
            )
            return prepare_issue(det)

    return {
        "ok": True,
        "matched": False,
        "message": (
            "I could not map this to a known repair module yet. "
            "Open Mission Control → Recovery for a full scan, or tell me which subsystem is failing."
        ),
        "scan": scan,
        "disclaimer": DISCLAIMER,
    }


def request_approval(issue_id: str) -> dict[str, Any]:
    issue = store.get_issue(issue_id)
    if not issue:
        return {"ok": False, "message": "Issue not found", "disclaimer": DISCLAIMER}
    plan = issue.get("plan") or {}
    if plan.get("approval_class") == APPROVAL_MANUAL and plan.get("destructive"):
        updated = store.update_issue(issue_id, {"state": "needs_user"})
        return {
            "ok": False,
            "needs_explicit_confirmation": True,
            "message": (
                "This repair is destructive and cannot run from a single Repair click. "
                "Confirm explicitly with confirm_destructive=true after reviewing the plan."
            ),
            "panel": _panel_from_issue(updated or issue),
            "disclaimer": DISCLAIMER,
        }
    updated = store.update_issue(issue_id, {"state": "awaiting_approval"})
    return {"ok": True, "issue": updated, "panel": _panel_from_issue(updated or issue), "disclaimer": DISCLAIMER}


def execute_repair(
    issue_id: str,
    *,
    approved: bool = False,
    confirm_destructive: bool = False,
    actor: str = "jeff",
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Execute only after approval. Never claims success without verification."""
    _ensure_modules()
    issue = store.get_issue(issue_id)
    if not issue:
        return {"ok": False, "message": "Issue not found", "disclaimer": DISCLAIMER}

    plan = issue.get("plan") or {}
    approval_class = plan.get("approval_class") or APPROVAL_SEMI
    auto = store.is_auto_approved(issue.get("module_id") or "") and approval_class == "safe" and not plan.get("destructive")

    if not approved and not auto:
        store.update_issue(issue_id, {"state": "awaiting_approval"})
        return {
            "ok": False,
            "approval_required": True,
            "message": "Repair requires Jeff's approval before execution.",
            "panel": _panel_from_issue(store.get_issue(issue_id) or issue),
            "disclaimer": DISCLAIMER,
        }

    if plan.get("destructive") or approval_class == APPROVAL_MANUAL:
        if not confirm_destructive:
            store.update_issue(issue_id, {"state": "needs_user"})
            return {
                "ok": False,
                "needs_explicit_confirmation": True,
                "message": "Destructive/manual repair blocked. Pass confirm_destructive=true after reviewing the plan.",
                "panel": _panel_from_issue(store.get_issue(issue_id) or issue),
                "disclaimer": DISCLAIMER,
            }

    mod = get_module(issue.get("module_id") or "")
    if not mod:
        return {"ok": False, "message": "Repair module missing", "disclaimer": DISCLAIMER}

    det = DetectedIssue(
        module_id=issue["module_id"],
        subsystem=issue.get("subsystem") or mod.subsystem,
        title=issue.get("title") or "",
        summary=issue.get("summary") or "",
        severity=issue.get("severity") or "warning",
        code=issue.get("code") or "",
        context=issue.get("context") or {},
    )
    plan_obj = RepairPlan(
        steps=list(plan.get("steps") or []),
        expected_result=plan.get("expected_result") or "",
        risk=plan.get("risk") or "medium",
        risk_why=plan.get("risk_why") or "",
        estimated_seconds=float(plan.get("estimated_seconds") or 30),
        rollback_available=bool(plan.get("rollback_available")),
        rollback_description=plan.get("rollback_description") or "",
        approval_class=approval_class,
        destructive=bool(plan.get("destructive")),
    )

    store.update_issue(issue_id, {"state": "repairing", "approved_by": actor, "approved_at": time.time()})
    t0 = time.time()
    try:
        outcome = mod.repair(det, plan_obj, progress=progress)
    except Exception as exc:
        outcome_msg = f"Repair raised an exception: {exc}"
        store.update_issue(issue_id, {"state": "repair_failed", "error": str(exc)})
        hist = store.append_history(
            {
                "issue_id": issue_id,
                "module_id": issue.get("module_id"),
                "subsystem": issue.get("subsystem"),
                "title": issue.get("title"),
                "code": issue.get("code"),
                "diagnosis": (issue.get("diagnosis") or {}).get("root_cause"),
                "evidence": issue.get("evidence"),
                "confidence": issue.get("confidence"),
                "plan_steps": " → ".join(plan_obj.steps),
                "user_approved": True,
                "executed": False,
                "verified_ok": False,
                "result": "failed",
                "message": outcome_msg,
                "duration_seconds": round(time.time() - t0, 3),
                "actor": actor,
            }
        )
        return {
            "ok": False,
            "verified": False,
            "success_claimed": False,
            "message": outcome_msg + f"\n\n_{DISCLAIMER}_",
            "history": hist,
            "disclaimer": DISCLAIMER,
        }

    store.update_issue(issue_id, {"state": "verifying", "repair_steps": [s.__dict__ if hasattr(s, "__dict__") else s for s in (outcome.steps or [])]})
    try:
        verify = mod.verify(det)
    except Exception as exc:
        verify = VerifyResult(ok=False, checks=[{"id": "verify_exception", "ok": False, "detail": str(exc)}], message=str(exc))

    duration = round(time.time() - t0, 3)
    verified_ok = bool(outcome.executed and outcome.ok and verify.ok)
    # Truth over optimism
    monitoring = None
    if not outcome.executed:
        state = "repair_failed"
        result = "not_executed"
        msg = outcome.message or "Repair did not execute."
    elif not verify.ok:
        state = "repair_failed"
        result = "executed_unverified"
        msg = (
            f"Repair ran but verification failed. I will NOT claim this is fixed.\n"
            f"Verify: {verify.message}"
        )
    elif not outcome.ok:
        state = "repair_failed"
        result = "failed"
        msg = outcome.message or "Repair reported failure."
    else:
        # Verified — enter post-repair monitoring (does not claim permanently closed yet)
        from jarvis.repair_product.monitoring import start_monitoring

        monitoring = start_monitoring(issue_id, checkpoints=(issue.get("impact") or {}).get("monitor_seconds"))
        state = "monitoring"
        result = "verified_success"
        msg = (
            f"Repair verified successful in {duration}s. Monitoring stability… "
            f"{verify.message or outcome.message or ''}"
        ).strip()

    store.update_issue(
        issue_id,
        {
            "state": state,
            "verify": {"ok": verify.ok, "checks": verify.checks, "message": verify.message},
            "result": result,
            "duration_seconds": duration,
            "workflow_status": "verify_done" if verified_ok else "failed",
        },
    )
    hist = store.append_history(
        {
            "issue_id": issue_id,
            "module_id": issue.get("module_id"),
            "subsystem": issue.get("subsystem"),
            "title": issue.get("title"),
            "code": issue.get("code"),
            "priority": issue.get("priority"),
            "diagnosis": (issue.get("diagnosis") or {}).get("root_cause"),
            "evidence": issue.get("evidence"),
            "confidence": issue.get("confidence"),
            "plan_steps": " → ".join(plan_obj.steps),
            "user_approved": True,
            "executed": bool(outcome.executed),
            "verified_ok": verified_ok,
            "rollback_used": False,
            "result": result,
            "message": msg,
            "duration_seconds": duration,
            "actor": actor,
            "verify_checks": verify.checks,
            "monitoring_started": bool(monitoring and monitoring.get("ok")),
        }
    )

    final = store.get_issue(issue_id)
    return {
        "ok": verified_ok,
        "verified": verified_ok,
        "success_claimed": verified_ok,  # only true when verified
        "monitoring": monitoring,
        "result": result,
        "message": msg + f"\n\n_{DISCLAIMER}_",
        "issue": final,
        "panel": _panel_from_issue(final or issue),
        "outcome": {
            "ok": outcome.ok,
            "executed": outcome.executed,
            "steps": [s.__dict__ if hasattr(s, "__dict__") else s for s in (outcome.steps or [])],
            "message": outcome.message,
        },
        "verify": {"ok": verify.ok, "checks": verify.checks, "message": verify.message},
        "history": hist,
        "disclaimer": DISCLAIMER,
    }


def rollback_issue(issue_id: str, *, approved: bool = False, actor: str = "jeff") -> dict[str, Any]:
    if not approved:
        return {"ok": False, "approval_required": True, "message": "Rollback requires approval.", "disclaimer": DISCLAIMER}
    issue = store.get_issue(issue_id)
    if not issue:
        return {"ok": False, "message": "Issue not found", "disclaimer": DISCLAIMER}
    mod = get_module(issue.get("module_id") or "")
    if not mod:
        return {"ok": False, "message": "Module missing", "disclaimer": DISCLAIMER}
    det = DetectedIssue(
        module_id=issue["module_id"],
        subsystem=issue.get("subsystem") or "",
        title=issue.get("title") or "",
        summary=issue.get("summary") or "",
        severity=issue.get("severity") or "warning",
        code=issue.get("code") or "",
        context=issue.get("context") or {},
    )
    outcome = mod.rollback(det)
    if outcome is None:
        return {"ok": False, "message": "Rollback is not available for this repair.", "disclaimer": DISCLAIMER}
    ok = bool(outcome.ok)
    store.append_history(
        {
            "issue_id": issue_id,
            "module_id": issue.get("module_id"),
            "title": f"Rollback: {issue.get('title')}",
            "user_approved": True,
            "executed": outcome.executed,
            "verified_ok": ok,
            "rollback_used": True,
            "result": "rollback_ok" if ok else "rollback_failed",
            "message": outcome.message,
            "actor": actor,
        }
    )
    return {"ok": ok, "message": outcome.message, "disclaimer": DISCLAIMER}


def issue_panel(issue_id: str) -> dict[str, Any]:
    issue = store.get_issue(issue_id)
    if not issue:
        return {"ok": False, "message": "Issue not found", "disclaimer": DISCLAIMER}
    return {"ok": True, "issue": issue, "panel": _panel_from_issue(issue), "disclaimer": DISCLAIMER}
