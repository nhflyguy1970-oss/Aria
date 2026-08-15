"""Post-repair monitoring — verification continues; reopen if issue returns."""

from __future__ import annotations

import time
from typing import Any

from jarvis.repair_product import store
from jarvis.repair_product.terminology import DISCLAIMER


def start_monitoring(issue_id: str, *, checkpoints: list[int] | None = None) -> dict[str, Any]:
    issue = store.get_issue(issue_id)
    if not issue:
        return {"ok": False, "message": "Issue not found", "disclaimer": DISCLAIMER}
    cps = checkpoints or (issue.get("impact") or {}).get("monitor_seconds") or [30, 120, 300]
    now = time.time()
    schedule = [{"at": now + int(s), "seconds": int(s), "status": "pending"} for s in cps if int(s) > 0]
    mon = {
        "started_at": now,
        "checkpoints": schedule,
        "status": "monitoring",
        "stable": False,
        "closed": False,
    }
    store.update_issue(issue_id, {"state": "monitoring", "monitoring": mon})
    store.save_monitor(issue_id, mon)
    return {"ok": True, "issue_id": issue_id, "monitoring": mon, "message": "Verified. Monitoring…", "disclaimer": DISCLAIMER}


def tick(*, now: float | None = None) -> dict[str, Any]:
    """Advance due monitoring checkpoints. Re-open repair if detect() finds same fingerprint."""
    now = now if now is not None else time.time()
    from jarvis.repair_product.registry import get_module
    from jarvis.repair_product import modules

    modules.register_all()
    results = []
    for issue_id, mon in list(store.list_monitors().items()):
        if mon.get("closed"):
            continue
        issue = store.get_issue(issue_id)
        if not issue:
            continue
        changed = False
        for cp in mon.get("checkpoints") or []:
            if cp.get("status") != "pending":
                continue
            if now < float(cp.get("at") or 0):
                continue
            # Run module verify + detect
            mod = get_module(issue.get("module_id") or "")
            ok = True
            detail = "soft ok"
            if mod:
                try:
                    from jarvis.repair_product.registry import DetectedIssue

                    det = DetectedIssue(
                        module_id=issue["module_id"],
                        subsystem=issue.get("subsystem") or "",
                        title=issue.get("title") or "",
                        summary=issue.get("summary") or "",
                        severity=issue.get("severity") or "warning",
                        code=issue.get("code") or "",
                        context=issue.get("context") or {},
                    )
                    v = mod.verify(det)
                    ok = bool(v.ok)
                    detail = v.message
                    # Reopen if detect finds same fingerprint again
                    found = mod.detect() or []
                    fp = issue.get("fingerprint")
                    if any(getattr(f, "fingerprint", lambda: "")() == fp for f in found):
                        ok = False
                        detail = "Issue signature returned during monitoring — reopening"
                        store.update_issue(
                            issue_id,
                            {
                                "state": "repair_ready",
                                "monitoring": {**mon, "status": "reopened", "closed": True},
                                "reopened_at": now,
                                "reopen_reason": detail,
                            },
                        )
                        mon["status"] = "reopened"
                        mon["closed"] = True
                        store.save_monitor(issue_id, mon)
                        results.append({"issue_id": issue_id, "reopened": True, "detail": detail})
                        changed = True
                        break
                except Exception as exc:
                    ok = False
                    detail = str(exc)
            cp["status"] = "passed" if ok else "failed"
            cp["checked_at"] = now
            cp["detail"] = detail
            changed = True
            if not ok:
                store.update_issue(issue_id, {"state": "repair_failed", "monitoring": {**mon, "status": "failed"}})
                mon["status"] = "failed"
                store.save_monitor(issue_id, mon)
                results.append({"issue_id": issue_id, "failed": True, "detail": detail})
                break
        if mon.get("closed"):
            continue
        pending = [c for c in (mon.get("checkpoints") or []) if c.get("status") == "pending"]
        if changed and not pending and mon.get("status") == "monitoring":
            mon["status"] = "stable"
            mon["stable"] = True
            mon["closed"] = True
            mon["closed_at"] = now
            store.update_issue(issue_id, {"state": "repair_successful", "monitoring": mon, "repair_closed": True})
            store.save_monitor(issue_id, mon)
            results.append({"issue_id": issue_id, "stable": True, "message": "Stable — repair closed"})
        elif changed:
            store.update_issue(issue_id, {"monitoring": mon})
            store.save_monitor(issue_id, mon)
    return {"ok": True, "results": results, "disclaimer": DISCLAIMER}


def status(issue_id: str) -> dict[str, Any]:
    mon = store.get_monitor(issue_id) or (store.get_issue(issue_id) or {}).get("monitoring")
    if not mon:
        return {"ok": False, "message": "No monitoring record", "disclaimer": DISCLAIMER}
    label = mon.get("status") or "unknown"
    if label == "monitoring":
        display = "Verified — Monitoring…"
    elif label == "stable":
        display = "Stable — Repair Closed"
    elif label == "reopened":
        display = "Issue returned — Repair reopened"
    elif label == "failed":
        display = "Monitoring failed verification"
    else:
        display = label
    return {"ok": True, "monitoring": mon, "display": display, "disclaimer": DISCLAIMER}
