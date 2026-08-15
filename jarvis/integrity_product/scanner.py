"""Production Integrity scanner — lightweight, cached, never deletes."""

from __future__ import annotations

import time
from typing import Any

from jarvis.integrity_product import checks, store
from jarvis.integrity_product.terminology import (
    DISCLAIMER,
    STATUS_ATTENTION,
    STATUS_CLEAN,
    STATUS_WARNING,
    TERMINOLOGY,
)

_CACHE: dict[str, Any] = {"at": 0.0, "value": None}
_CACHE_TTL_S = 30.0


def _status_for(findings: list[dict[str, Any]]) -> str:
    actionable = [f for f in findings if f.get("safe_to_remove")]
    if not actionable:
        return STATUS_WARNING if findings else STATUS_CLEAN
    health = [f for f in actionable if f.get("category") == "health"]
    if health or len(actionable) >= 5:
        return STATUS_ATTENTION
    return STATUS_WARNING


def run_scan(*, force: bool = False, trigger: str = "manual") -> dict[str, Any]:
    """Scan live workspace for development artifacts. Read-only."""
    now = time.monotonic()
    if not force and _CACHE.get("value") and now - float(_CACHE.get("at") or 0) < _CACHE_TTL_S:
        cached = dict(_CACHE["value"])
        cached["cached"] = True
        return cached

    findings: list[dict[str, Any]] = []
    errors: list[str] = []
    for fn in checks.ALL_CHECKS:
        try:
            findings.extend(fn() or [])
        except Exception as exc:
            errors.append(f"{fn.__name__}: {exc}")

    findings = checks._dedupe_findings(findings)

    by_category: dict[str, int] = {}
    for f in findings:
        cat = str(f.get("category") or "other")
        by_category[cat] = by_category.get(cat, 0) + 1

    status = _status_for(findings)
    from jarvis.integrity_product.score import compute_score

    payload = {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "status": status,
        "state": "ready" if status == STATUS_CLEAN else ("critical" if status == STATUS_ATTENTION else "attention"),
        "clean": status == STATUS_CLEAN and not any(f.get("safe_to_remove") for f in findings),
        "findings": findings,
        "counts": {
            "total": len(findings),
            "actionable": sum(1 for f in findings if f.get("safe_to_remove")),
            "by_category": by_category,
            "safe_to_remove": sum(1 for f in findings if f.get("safe_to_remove")),
            "uncertain": sum(1 for f in findings if f.get("uncertain")),
        },
        "scanned_at": time.time(),
        "trigger": trigger,
        "errors": errors,
        "disclaimer": DISCLAIMER,
        "cached": False,
        "auto_delete": False,
        "note": "Scans never delete. Approve Guided Repair to remove known-safe development artifacts.",
    }
    payload["score"] = compute_score(payload)
    store.save_last_scan(payload)
    store.append_history(
        {
            "event": "scan",
            "trigger": trigger,
            "status": status,
            "count": len(findings),
            "by_category": by_category,
            "score": (payload.get("score") or {}).get("overall"),
        }
    )
    _CACHE["at"] = now
    _CACHE["value"] = payload
    return payload


def invalidate_cache() -> None:
    _CACHE["at"] = 0.0
    _CACHE["value"] = None


def home_payload() -> dict[str, Any]:
    last = store.load_last_scan()
    if not last or (time.time() - float(last.get("scanned_at") or 0)) > 3600:
        last = run_scan(force=False, trigger="home")
    hist = store.list_history(limit=12)
    repairs = [h for h in hist if h.get("event") in ("repair", "repair_verified")]
    from jarvis.integrity_product.score import compute_score

    score = last.get("score") or compute_score(last)
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "status": last.get("status") or STATUS_CLEAN,
        "state": last.get("state") or "ready",
        "score": score,
        "last_scan": last,
        "findings": last.get("findings") or [],
        "artifacts_found": (last.get("counts") or {}).get("total", 0),
        "pending_repairs": sum(1 for h in hist if h.get("event") == "scan" and (h.get("count") or 0) > 0),
        "last_repair": repairs[0] if repairs else None,
        "last_successful_cleanup": next((h for h in repairs if h.get("ok") or h.get("event") == "repair_verified"), None),
        "history": hist,
        "disclaimer": DISCLAIMER,
        "deep_links": {
            "scan": "/api/integrity/scan",
            "mission": "/api/integrity/mission",
            "score": "/api/integrity/score",
            "guided_repair": "mc:recovery",
        },
    }


def product_status() -> dict[str, Any]:
    last = store.load_last_scan() or {}
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "status": last.get("status") or "unknown",
        "clean": bool(last.get("clean")) if last else None,
        "last_scan_at": last.get("scanned_at"),
        "artifacts_found": (last.get("counts") or {}).get("total"),
        "disclaimer": DISCLAIMER,
    }
