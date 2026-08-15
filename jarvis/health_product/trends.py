"""Health Trends — informational observations only."""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER


def _series_status(vals: list[float], *, down_is_good: bool | None = None, threshold: float = 0.0) -> str:
    if len(vals) < 3:
        return "stable"
    delta = vals[-1] - vals[0]
    if abs(delta) <= max(abs(vals[0]) * 0.02, threshold):
        return "stable"
    improving = delta < 0 if down_is_good else delta > 0
    if down_is_good is None:
        return "needs_attention" if abs(delta) > threshold * 3 else "stable"
    return "improving" if improving else "needs_attention"


def build_trends(*, days: int = 45) -> dict[str, Any]:
    since = (date.today() - timedelta(days=days)).isoformat()
    checkins = store.list_checkins(limit=90, since=since)
    items: list[dict[str, Any]] = []

    def add(topic: str, status: str, detail: str):
        items.append({"topic": topic, "status": status, "detail": detail, "trust": "medium"})

    def vals(kind: str) -> list[float]:
        rows = store.list_vitals(kind=kind, since=since, limit=80)
        out = []
        for r in rows:
            if r.get("value") is not None:
                try:
                    out.append(float(r["value"]))
                except Exception:
                    pass
        return out

    w = vals("weight")
    if len(w) >= 3:
        st = _series_status(w, down_is_good=True, threshold=0.8)
        add("Weight", st, f"{w[0]:.1f} → {w[-1]:.1f}")
    bp = vals("blood_pressure")
    if len(bp) >= 3:
        st = _series_status(bp, down_is_good=True, threshold=3)
        add("Blood pressure", st, f"systolic {bp[0]:.0f} → {bp[-1]:.0f}")
    sg = vals("blood_sugar")
    if len(sg) >= 3:
        st = _series_status(sg, down_is_good=True, threshold=5)
        add("Blood sugar", st, f"{sg[0]:.0f} → {sg[-1]:.0f}")
    sleep = [float(c["sleep_hours"]) for c in checkins if c.get("sleep_hours") is not None]
    if len(sleep) >= 3:
        st = _series_status(sleep, down_is_good=False, threshold=0.3)
        add("Sleep", st, f"avg recent {statistics.mean(sleep[-5:]):.1f}h")
    pain = [float(c["pain"]) for c in checkins if c.get("pain") is not None]
    if len(pain) >= 3:
        st = _series_status(pain, down_is_good=True, threshold=0.4)
        add("Pain", st, f"{pain[0]:.1f} → {pain[-1]:.1f}")
    stress = [float(c["stress"]) for c in checkins if c.get("stress") is not None]
    if len(stress) >= 3:
        st = _series_status(stress, down_is_good=True, threshold=0.4)
        add("Stress", st, f"{stress[0]:.1f} → {stress[-1]:.1f}")

    acts = [a for a in store.list_table("activities", limit=200) if str(a.get("day") or "") >= since]
    wos = [w for w in store.list_table("workouts", limit=100) if str(w.get("day") or "") >= since]
    early = sum(1 for a in acts if str(a.get("day")) < (date.today() - timedelta(days=days // 2)).isoformat()) + sum(
        1 for w in wos if str(w.get("day")) < (date.today() - timedelta(days=days // 2)).isoformat()
    )
    late = len(acts) + len(wos) - early
    if early + late >= 3:
        if late > early:
            add("Exercise", "improving", f"{late} sessions in the recent half vs {early} earlier")
        elif late < early:
            add("Exercise", "needs_attention", f"{late} sessions recently vs {early} earlier")
        else:
            add("Exercise", "stable", f"{late + early} sessions in {days} days")

    missed = [m for m in store.list_table("missed_doses", limit=80) if str(m.get("day") or "") >= since]
    if missed:
        recent = [m for m in missed if str(m.get("day") or "") >= (date.today() - timedelta(days=7)).isoformat()]
        older = len(missed) - len(recent)
        if len(recent) > max(1, older):
            add("Medication adherence", "needs_attention", f"{len(recent)} missed-dose notes in the last week")
        else:
            add("Medication adherence", "stable", f"{len(missed)} missed-dose notes in {days} days")

    lines = ["**Health trends** (observations only — not a diagnosis)", ""]
    if not items:
        lines.append("Not enough recorded data yet for trend labels.")
    else:
        for it in items:
            label = {"improving": "Improving", "needs_attention": "Needs attention", "stable": "Stable"}.get(it["status"], it["status"])
            lines.append(f"• **{label}** — {it['topic']}: {it['detail']}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "trends", "trends": items, "message": "\n".join(lines), "disclaimer": DISCLAIMER}
