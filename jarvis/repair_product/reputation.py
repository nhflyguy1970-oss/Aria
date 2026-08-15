"""Repair module reputation — reliability earned from verified outcomes."""

from __future__ import annotations

from typing import Any

from jarvis.repair_product import store
from jarvis.repair_product.registry import all_modules


def _stars(rate: float, attempts: int) -> str:
    if attempts == 0:
        return "☆☆☆☆☆"
    if rate >= 0.95 and attempts >= 5:
        return "★★★★★"
    if rate >= 0.85:
        return "★★★★☆"
    if rate >= 0.7:
        return "★★★☆☆"
    if rate >= 0.5:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def for_module(module_id: str) -> dict[str, Any]:
    learn = store.learning_stats()
    # Aggregate across codes for this module
    ok = 0
    fail = 0
    durs: list[float] = []
    confs: list[float] = []
    last_fail = 0
    for key, n in (learn.get("successful_repairs") or {}).items():
        if str(key).startswith(module_id + ":"):
            ok += int(n)
    for key, n in (learn.get("failed_repairs") or {}).items():
        if str(key).startswith(module_id + ":"):
            fail += int(n)
    for key, v in (learn.get("avg_duration") or {}).items():
        if str(key).startswith(module_id + ":"):
            try:
                durs.append(float(v))
            except (TypeError, ValueError):
                pass
    for key, v in (learn.get("avg_confidence") or {}).items():
        if str(key).startswith(module_id + ":"):
            try:
                confs.append(float(v))
            except (TypeError, ValueError):
                pass
    attempts = ok + fail
    rate = (ok / attempts) if attempts else 0.0
    # Repeat failures = consecutive-ish fail count signal
    repeat = int((learn.get("repeat_failures") or {}).get(module_id) or 0)
    trend = "stable"
    if attempts >= 3:
        if rate >= 0.9:
            trend = "improving"
        elif rate < 0.6:
            trend = "declining"
    desc = ""
    try:
        from jarvis.repair_product.registry import get_module

        mod = get_module(module_id)
        desc = mod.description() if mod else module_id
    except Exception:
        desc = module_id
    return {
        "module_id": module_id,
        "description": desc,
        "reliability_stars": _stars(rate, attempts),
        "reliability_rate": round(rate, 3),
        "executed": attempts,
        "succeeded": ok,
        "failed": fail,
        "average_repair_time": round(sum(durs) / len(durs), 2) if durs else None,
        "average_confidence": round(sum(confs) / len(confs), 3) if confs else None,
        "repeat_failures": repeat,
        "trend": trend,
    }


def all_reputations() -> list[dict[str, Any]]:
    from jarvis.repair_product import modules

    modules.register_all()
    rows = [for_module(m.id) for m in all_modules()]
    rows.sort(key=lambda r: (-(r.get("executed") or 0), r.get("module_id") or ""))
    return rows
