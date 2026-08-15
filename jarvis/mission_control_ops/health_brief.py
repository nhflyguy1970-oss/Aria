"""Executive health brief for Mission Control Overview."""

from __future__ import annotations

from typing import Any


def _severity_rank(s: str) -> int:
    return {"ok": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}.get((s or "").lower(), 1)


_CLEAR_SENTINELS = frozenset({"all clear", "no action required", "none", "ok", "healthy"})


def _is_clear_sentinel(text: str) -> bool:
    """True for non-issue placeholders that must never appear as critical_issues (BUG-006)."""
    return (text or "").strip().lower() in _CLEAR_SENTINELS


def build_health_brief(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """Derive an operator-facing brief from a Mission Control snapshot."""
    d = snapshot or {}
    ov = d.get("overview") or {}
    advisor = ov.get("operational_advisor") or d.get("operational_advisor") or {}
    recovery = d.get("recovery") or {}
    health = recovery.get("health") if isinstance(recovery.get("health"), dict) else {}
    attention = list(ov.get("needs_attention") or [])
    recs = list(advisor.get("recommendations") or [])
    platform = str(ov.get("platform_status") or "unknown").lower()
    ok_flag = health.get("ok")
    if ok_flag is None:
        ok_flag = advisor.get("healthy")
    if ok_flag is None:
        ok_flag = platform in ("healthy", "ok", "ready", "up")

    critical_issues: list[str] = []
    severity = "ok"
    for n in attention:
        text = str(n)
        if _is_clear_sentinel(text):
            continue
        critical_issues.append(text)
        severity = "warning"
    for r in recs:
        sev = str((r or {}).get("severity") or "info").lower()
        if _severity_rank(sev) >= _severity_rank("warning"):
            title = (r or {}).get("title") or (r or {}).get("action") or "Issue"
            critical_issues.append(str(title))
        if _severity_rank(sev) > _severity_rank(severity):
            severity = sev if sev in ("info", "warning", "error", "critical") else severity
    if platform in ("degraded", "warning"):
        severity = "warning" if _severity_rank(severity) < _severity_rank("warning") else severity
        critical_issues.append(f"Platform status: {platform}")
    if platform in ("down", "critical", "error", "failed"):
        severity = "critical"
        critical_issues.append(f"Platform status: {platform}")
    if ok_flag is False and _severity_rank(severity) < _severity_rank("error"):
        severity = "error"

    # Deduplicate while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for item in critical_issues:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(item)
    critical_issues = uniq[:8]

    if severity in ("critical", "error"):
        overall = "critical" if severity == "critical" else "degraded"
    elif severity == "warning" or critical_issues:
        overall = "degraded"
    elif ok_flag:
        overall = "healthy"
    else:
        overall = "unknown"

    top = recs[0] if recs else {}
    recommended = (
        str(top.get("action") or top.get("title") or "").strip()
        or (critical_issues[0] if critical_issues else "No action required")
    )
    next_step = str(top.get("reason") or advisor.get("headline") or "").strip()
    if not next_step:
        next_step = (
            "Open Recovery and run an approved repair"
            if overall != "healthy"
            else "Continue monitoring Mission Control"
        )
    impact = str(top.get("impact") or top.get("duration_estimate") or "").strip()
    if not impact:
        impact = "Low — observe only" if overall == "healthy" else "Medium — operator approval required"

    # Primary CTA — never auto-remediate
    if overall in ("critical", "degraded") and (not ok_flag or critical_issues):
        primary_cta = {
            "label": "Open Recovery",
            "action": "mc:recovery",
            "confirm": False,
            "why": "Investigate and approve repair steps",
        }
    elif any("inference" in str(x).lower() or "ollama" in str(x).lower() for x in critical_issues):
        primary_cta = {
            "label": "Open Inference",
            "action": "mc:inference",
            "confirm": False,
            "why": "Check provider and model health",
        }
    elif any("connect" in str(x).lower() or "runtime" in str(x).lower() for x in critical_issues):
        primary_cta = {
            "label": "Open Connection",
            "action": "mc:connection",
            "confirm": False,
            "why": "Diagnose runtime connection",
        }
    else:
        primary_cta = {
            "label": "Refresh health",
            "action": "mc:refresh",
            "confirm": False,
            "why": "Re-check infrastructure snapshot",
        }

    return {
        "overall": overall,
        "severity": severity,
        "headline": advisor.get("headline") or f"Infrastructure {overall}",
        "critical_issues": critical_issues,
        "recommended_action": recommended,
        "next_step": next_step,
        "estimated_impact": impact,
        "primary_cta": primary_cta,
        "healthy": overall == "healthy",
        "source": "mission_control_ops.health_brief",
    }
