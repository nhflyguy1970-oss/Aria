"""Health milestones — only from recorded PHR data; never fabricated."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER


def _weights() -> list[tuple[str, float]]:
    out = []
    for v in store.list_vitals(kind="weight", limit=500):
        if v.get("value") is None:
            continue
        try:
            out.append((str(v.get("day") or ""), float(v["value"])))
        except Exception:
            pass
    return out


def discover_milestones(*, persist: bool = True) -> dict[str, Any]:
    found: list[dict[str, Any]] = []
    today = date.today().isoformat()

    def claim(key: str, title: str, detail: str, day: str | None = None):
        row = {"key": key, "title": title, "detail": detail, "day": day or today}
        if persist:
            try:
                saved = store.remember_milestone(key, title, detail, day=day or today)
                if saved:
                    row = saved
            except Exception:
                pass
        found.append(row)

    weights = _weights()
    if len(weights) >= 2:
        start_w = weights[0][1]
        latest_w = weights[-1][1]
        lost = start_w - latest_w
        for threshold in (10, 20, 30, 50):
            if lost >= threshold:
                claim(f"weight_lost_{threshold}", f"Lost first {threshold} pounds (from recorded series)", f"{start_w:.1f} → {latest_w:.1f}", weights[-1][0])
        for g in store.list_table("goals", "status=? AND kind=?", ("active", "weight"), limit=20):
            target = g.get("target_value")
            if target is None:
                continue
            try:
                if latest_w <= float(target):
                    claim(f"weight_goal_{g.get('id')}", "Weight goal achieved", f"{g.get('title')}: {latest_w} ≤ {target}", weights[-1][0])
            except Exception:
                pass

    bp = store.list_vitals(kind="blood_pressure", limit=120)
    target = 130.0
    for g in store.list_table("goals", "kind=?", ("blood_pressure",), limit=5):
        if g.get("target_value") is not None:
            try:
                target = float(g["target_value"])
            except Exception:
                pass
    under = []
    for v in bp:
        try:
            if float(v["value"]) < target:
                under.append(str(v.get("day") or ""))
        except Exception:
            pass
    under_set = set(under)
    streak = 0
    d = date.today()
    while d.isoformat() in under_set:
        streak += 1
        d -= timedelta(days=1)
    if streak >= 30:
        claim("bp_under_30", "Blood pressure under target for 30 days", f"Systolic under {target:.0f} for {streak} consecutive logged days")

    a1c = store.list_labs(name="A1C", limit=20)
    a1c_vals = [(r.get("day"), r.get("value")) for r in a1c if r.get("value") is not None]
    if len(a1c_vals) >= 2:
        try:
            if float(a1c_vals[-1][1]) < float(a1c_vals[0][1]):
                claim("a1c_improved", "A1C improved (recorded)", f"{a1c_vals[0][1]} → {a1c_vals[-1][1]}", str(a1c_vals[-1][0] or today))
        except Exception:
            pass

    workouts = store.list_table("workouts", limit=500)
    for n in (25, 50, 100, 250, 500):
        if len(workouts) >= n:
            claim(f"workouts_{n}", f"Completed {n} workouts", f"{len(workouts)} workouts on record")

    acts = store.list_table("activities", limit=2000)
    miles = 0.0
    for a in acts:
        try:
            dist = float(a.get("distance") or 0)
        except Exception:
            dist = 0.0
        units = str(a.get("distance_units") or "mi").lower()
        if units in ("km", "kilometers"):
            dist *= 0.621371
        miles += dist
    for n in (100, 250, 500, 1000):
        if miles >= n:
            claim(f"miles_{n}", f"Walked/cycled {n} miles (logged distance)", f"{miles:.1f} miles across activity logs")

    for med in store.list_table("medications", "status=?", ("current",), limit=40):
        start = med.get("start_date")
        if not start:
            continue
        try:
            years = (date.today() - date.fromisoformat(str(start)[:10])).days / 365.25
        except Exception:
            continue
        if years >= 1:
            claim(
                f"med_anniv_{str(med.get('name') or '').lower()}",
                f"Medication anniversary — {med.get('name')}",
                f"On record since {start} (~{years:.1f} years)",
                today,
            )

    profile = store.get_profile()
    smoke_free = profile.get("smoke_free_since") or profile.get("tobacco_quit_date")
    if smoke_free:
        try:
            days = (date.today() - date.fromisoformat(str(smoke_free)[:10])).days
            if days >= 365:
                claim("smoke_free_1y", "One year smoke-free", f"Quit date on record: {smoke_free} ({days} days)")
        except Exception:
            pass

    # Deduplicate by key for response
    by_key = {}
    for m in found:
        by_key[m.get("key") or m.get("title")] = m
    items = list(by_key.values())
    stored = store.list_table("milestones", limit=100)
    lines = ["**Health milestones** (from recorded data only)", ""]
    if not items and not stored:
        lines.append("No milestones yet — keep logging weight, workouts, BP, and labs.")
    else:
        for m in (items or stored)[:20]:
            lines.append(f"• {m.get('day')}: {m.get('title')} — {m.get('detail') or ''}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "milestones", "milestones": items or stored, "message": "\n".join(lines), "disclaimer": DISCLAIMER}
