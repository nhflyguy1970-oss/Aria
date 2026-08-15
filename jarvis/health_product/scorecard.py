"""Personal wellness scorecard — educational summary, not a medical score."""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_BOUNDARY = (
    "This wellness scorecard summarizes your recorded Health habits. "
    "It is not a medical score, diagnosis, or risk calculator."
)


def _clamp(n: float) -> int:
    return int(max(0, min(100, round(n))))


def build_scorecard(*, days: int = 28) -> dict[str, Any]:
    since = (date.today() - timedelta(days=days)).isoformat()
    checkins = store.list_checkins(limit=90, since=since)
    scores: list[dict[str, Any]] = []

    sleep = [float(c["sleep_hours"]) for c in checkins if c.get("sleep_hours") is not None]
    if sleep:
        avg = statistics.mean(sleep)
        consistency = 100 - min(40, statistics.pstdev(sleep) * 25) if len(sleep) >= 2 else 70
        near = 100 - min(50, abs(avg - 7.5) * 20)
        score = _clamp(0.55 * near + 0.45 * consistency)
        scores.append({"key": "sleep", "label": "Sleep consistency", "score": score, "explain": f"Avg {avg:.1f}h over {len(sleep)} check-ins; closer to 7.5h with less day-to-day swing scores higher."})
    else:
        scores.append({"key": "sleep", "label": "Sleep consistency", "score": None, "explain": "No sleep hours recorded yet."})

    act_days = {a.get("day") for a in store.list_table("activities", limit=200) if str(a.get("day") or "") >= since}
    act_days |= {w.get("day") for w in store.list_table("workouts", limit=100) if str(w.get("day") or "") >= since}
    exercise_score = _clamp(100.0 * len(act_days) / max(1, min(days, 20)))
    scores.append({"key": "exercise", "label": "Exercise consistency", "score": exercise_score if act_days else None, "explain": f"{len(act_days)} active day(s) in {days} days." if act_days else "No activity/workouts logged in this window."})

    from jarvis.health_product.dashboard import medication_adherence

    adh = medication_adherence(days=7)
    scores.append({"key": "meds", "label": "Medication adherence", "score": adh.get("estimate_pct"), "explain": adh.get("explain") or "No current medications on file."})

    def trend_score(kind: str, *, lower_better: bool) -> dict[str, Any]:
        rows = store.list_vitals(kind=kind, since=since, limit=40)
        vals = [float(r["value"]) for r in rows if r.get("value") is not None]
        if len(vals) < 2:
            return {"score": None, "explain": f"Not enough {kind.replace('_', ' ')} readings."}
        delta = vals[-1] - vals[0]
        good = delta < 0 if lower_better else delta > 0
        base = 70 + (15 if good else -15) - min(20, abs(delta) / max(1.0, abs(vals[0])) * 40)
        return {"score": _clamp(base), "explain": f"{vals[0]:.1f} → {vals[-1]:.1f} ({delta:+.1f})."}

    w = trend_score("weight", lower_better=True)
    scores.append({"key": "weight", "label": "Weight trend", **w})
    bp = trend_score("blood_pressure", lower_better=True)
    scores.append({"key": "bp", "label": "Blood pressure trend", **bp})
    sg = trend_score("blood_sugar", lower_better=True)
    scores.append({"key": "sugar", "label": "Blood sugar trend", **sg})

    water_days = len([c for c in checkins if str(c.get("water") or "").strip()])
    hyd = _clamp(100.0 * water_days / max(1, min(len(checkins), 14))) if checkins else None
    scores.append({"key": "hydration", "label": "Hydration", "score": hyd if water_days else None, "explain": f"Water logged on {water_days} check-in day(s)." if water_days else "No water entries yet."})

    stress = [float(c["stress"]) for c in checkins if c.get("stress") is not None]
    if stress:
        avg = statistics.mean(stress)
        scores.append({"key": "stress", "label": "Stress", "score": _clamp(100 - avg * 10), "explain": f"Average stress {avg:.1f}/10 (lower stress → higher score)."})
    else:
        scores.append({"key": "stress", "label": "Stress", "score": None, "explain": "No stress scores recorded."})

    mood = [float(c["mood"]) for c in checkins if c.get("mood") is not None]
    if mood:
        avg = statistics.mean(mood)
        scores.append({"key": "mood", "label": "Mood", "score": _clamp(avg * 10), "explain": f"Average mood {avg:.1f}/10."})
    else:
        scores.append({"key": "mood", "label": "Mood", "score": None, "explain": "No mood scores recorded."})

    present = [s["score"] for s in scores if s.get("score") is not None]
    overall = _clamp(statistics.mean(present)) if present else None
    lines = ["**Wellness scorecard** (not a medical score)", "", _BOUNDARY, ""]
    if overall is not None:
        lines.append(f"Overall habit summary: **{overall}/100** (average of available dimensions).")
    for s in scores:
        val = "—" if s.get("score") is None else f"{s['score']}/100"
        lines.append(f"• {s['label']}: {val} — {s['explain']}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "scorecard",
        "boundary": _BOUNDARY,
        "overall": overall,
        "scores": scores,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }
