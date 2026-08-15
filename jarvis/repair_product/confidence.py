"""Justified confidence — never imply certainty without reasons."""

from __future__ import annotations

import time
from typing import Any


def history_key(module_id: str, code: str = "") -> str:
    return f"{module_id}:{code or 'unknown'}"


def stats_for(module_id: str, code: str = "") -> dict[str, Any]:
    from jarvis.repair_product import store

    key = history_key(module_id, code)
    learn = store.learning_stats()
    seen = int((learn.get("common_failures") or {}).get(key) or 0)
    ok_n = int((learn.get("successful_repairs") or {}).get(key) or 0)
    fail_n = int((learn.get("failed_repairs") or {}).get(key) or 0)
    avg = (learn.get("avg_duration") or {}).get(key)
    last_ts = (learn.get("last_success_ts") or {}).get(key)
    return {
        "key": key,
        "seen": seen,
        "succeeded": ok_n,
        "failed": fail_n,
        "avg_seconds": avg,
        "last_success_ts": last_ts,
    }


def justify(base_confidence: float, *, module_id: str, code: str = "", evidence_count: int = 0, first_occurrence: bool | None = None) -> dict[str, Any]:
    """Return confidence 0..1 plus human reasons. Never pretends certainty."""
    st = stats_for(module_id, code)
    reasons: list[str] = []
    conf = max(0.05, min(0.99, float(base_confidence or 0.5)))

    seen = st["seen"]
    ok_n = st["succeeded"]
    fail_n = st["failed"]
    if first_occurrence is None:
        first_occurrence = seen == 0

    if first_occurrence:
        conf = min(conf, 0.55)
        reasons.append("First occurrence (or no prior history for this signature)")
    else:
        reasons.append(f"Seen {seen} time(s)")
        if ok_n:
            reasons.append(f"Successfully repaired {ok_n} time(s)")
            # History boost — evidence-based, capped
            rate = ok_n / max(1, ok_n + fail_n)
            conf = min(0.97, conf + 0.08 * min(1.0, rate) + 0.02 * min(10, ok_n) / 10)
        if fail_n:
            reasons.append(f"Failed previously {fail_n} time(s)")
            conf = max(0.2, conf - 0.05 * min(5, fail_n))
        if st.get("avg_seconds") is not None:
            reasons.append(f"Average repair time {int(round(float(st['avg_seconds'])))} seconds")
        if st.get("last_success_ts"):
            days = max(0, int((time.time() - float(st["last_success_ts"])) / 86400))
            reasons.append(f"Last repaired {days} day(s) ago" if days else "Last repaired today")

    if evidence_count <= 1:
        conf = min(conf, 0.6)
        reasons.append("Limited evidence")
    elif evidence_count >= 3:
        reasons.append(f"{evidence_count} supporting evidence items")
        conf = min(0.97, conf + 0.03)

    if fail_n > ok_n and seen > 2:
        reasons.append("Multiple possible causes / mixed prior outcomes")
        conf = min(conf, 0.45)

    conf = round(max(0.05, min(0.97, conf)), 3)
    pct = int(round(conf * 100))
    if conf < 0.5:
        band = "low — treat as provisional"
    elif conf < 0.75:
        band = "possible"
    elif conf < 0.9:
        band = "likely"
    else:
        band = "known issue pattern"
    return {
        "confidence": conf,
        "confidence_pct": pct,
        "confidence_label": f"{pct}% — {band}",
        "reasons": reasons,
        "stats": st,
        "certainty_claimed": False,
    }
