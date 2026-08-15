"""Mission Control bridge — Guided Repair center status."""

from __future__ import annotations

from typing import Any

from jarvis.repair_product.terminology import DISCLAIMER, TERMINOLOGY


def repair_mission_panel() -> dict[str, Any]:
    from jarvis.repair_product import knowledge, maintenance, reputation, root_causes, store
    from jarvis.repair_product.engine import scan_issues
    from jarvis.repair_product.impact import sort_by_priority
    from jarvis.repair_product.monitoring import tick as monitor_tick

    try:
        monitor_tick()
    except Exception:
        pass

    issues = store.list_issues(active_only=True)
    if not issues:
        try:
            scan = scan_issues()
            issues = scan.get("issues") or []
        except Exception:
            issues = []
    issues = sort_by_priority(issues)
    critical = sum(1 for i in issues if i.get("priority") == "critical" or i.get("severity") == "critical")
    ready = [i for i in issues if i.get("state") in ("repair_ready", "awaiting_approval", "diagnosis_complete", "needs_user")]
    monitoring = [i for i in issues if i.get("state") == "monitoring"]
    hist = store.list_history(limit=8)
    learning = store.learning_stats()
    maint = maintenance.status()
    state = "maintenance" if maint.get("enabled") else ("critical" if critical else ("attention" if ready or monitoring else "ready"))
    return {
        "product": TERMINOLOGY["product"],
        "operator_name": TERMINOLOGY["operator_name"],
        "state": state,
        "detail": (
            f"{len(issues)} active · {len(ready)} repair-ready · {len(monitoring)} monitoring · "
            f"{critical} critical · maintenance={'on' if maint.get('enabled') else 'off'}"
        ),
        "active_issues": len(issues),
        "repair_ready": len(ready),
        "monitoring_count": len(monitoring),
        "critical": critical,
        "repair_queue": [
            {
                "id": i.get("id"),
                "title": i.get("title"),
                "state": i.get("state"),
                "priority": i.get("priority"),
                "confidence": i.get("confidence"),
                "confidence_reasons": (i.get("confidence_reasons") or [])[:3],
                "risk": (i.get("plan") or {}).get("risk"),
                "subsystem": i.get("subsystem"),
                "dependency": (i.get("dependency") or {}).get("display"),
                "reputation_stars": (i.get("reputation") or {}).get("reliability_stars"),
            }
            for i in issues[:15]
        ],
        "issues": [
            {
                "id": i.get("id"),
                "title": i.get("title"),
                "state": i.get("state"),
                "priority": i.get("priority"),
                "confidence": i.get("confidence"),
                "risk": (i.get("plan") or {}).get("risk"),
                "subsystem": i.get("subsystem"),
            }
            for i in issues[:12]
        ],
        "recently_repaired": [h for h in hist if h.get("verified_ok")][:5],
        "repeated_issues": sorted(
            (learning.get("common_failures") or {}).items(),
            key=lambda kv: kv[1],
            reverse=True,
        )[:5],
        "history": hist[:5],
        "maintenance": maint,
        "reputations": reputation.all_reputations()[:8],
        "knowledge": knowledge.search(limit=5),
        "root_causes": root_causes.list_all()[:5],
        "learning_top_failures": sorted(
            (learning.get("common_failures") or {}).items(),
            key=lambda kv: kv[1],
            reverse=True,
        )[:5],
        "deep_links": {
            "home": "#workstation",
            "recovery": "mc:recovery",
            "api": "/api/repair/home",
            "scan": "/api/repair/scan",
            "export": "/api/repair/export",
        },
        "disclaimer": DISCLAIMER,
        "note": "Mission Control is the repair center. Trust over autonomy — Jeff always approves.",
    }
