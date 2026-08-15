"""Activity + workout history, volume, streaks, and progression — Health-owned."""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

ACTIVITY_KINDS = [
    "walking",
    "running",
    "cycling",
    "swimming",
    "hiking",
    "strength",
    "resistance_bands",
    "weight_lifting",
    "stretching",
    "yoga",
    "mobility",
    "balance",
    "sports",
    "fishing",
    "housework",
    "yardwork",
    "custom",
]

WORKOUT_TEMPLATES = [
    "upper_body",
    "lower_body",
    "full_body",
    "push",
    "pull",
    "legs",
    "core",
    "resistance_band",
    "cardio",
    "mobility",
    "rehabilitation",
    "custom",
]

_METS = {
    "walking": 3.5,
    "running": 8.0,
    "cycling": 6.0,
    "swimming": 7.0,
    "hiking": 6.0,
    "strength": 5.0,
    "resistance_bands": 4.0,
    "weight_lifting": 5.0,
    "stretching": 2.5,
    "yoga": 3.0,
    "mobility": 2.8,
    "balance": 2.5,
    "sports": 6.0,
    "fishing": 3.0,
    "housework": 3.3,
    "yardwork": 4.5,
    "custom": 4.0,
    "cardio": 6.5,
}


def estimate_calories(kind: str, duration_min: float | None, intensity: str = "", weight_lb: float | None = None) -> float | None:
    if not duration_min:
        return None
    profile = store.get_profile()
    w = weight_lb
    if w is None:
        latest = store.list_vitals(kind="weight", limit=5)
        if latest:
            try:
                w = float(latest[-1].get("value"))
            except Exception:
                w = None
        if w is None:
            chk = store.get_checkin() or {}
            try:
                w = float(chk["weight"]) if chk.get("weight") is not None else None
            except Exception:
                w = None
    kg = float(w) * 0.453592 if w else 95.0
    met = _METS.get((kind or "custom").lower(), 4.0)
    mult = {"light": 0.85, "easy": 0.85, "moderate": 1.0, "hard": 1.2, "vigorous": 1.35, "max": 1.45}.get((intensity or "moderate").lower(), 1.0)
    return round(met * 3.5 * kg / 200.0 * float(duration_min) * mult, 0)


def _set_volume(s: dict[str, Any]) -> float:
    try:
        sets = float(s.get("sets") or 1)
        reps = float(s.get("reps") or 0)
        weight = float(s.get("weight") or 0)
        return sets * reps * weight
    except Exception:
        return 0.0


def workout_volume(workout_id: str) -> float:
    return sum(_set_volume(s) for s in store.list_workout_sets(workout_id))


def progression(*, days: int = 28) -> dict[str, Any]:
    since = (date.today() - timedelta(days=days)).isoformat()
    workouts = [w for w in store.list_table("workouts", limit=200) if str(w.get("day") or "") >= since]
    activities = [a for a in store.list_table("activities", limit=400) if str(a.get("day") or "") >= since]
    volumes = []
    for w in workouts:
        vol = workout_volume(w["id"])
        volumes.append({"day": w.get("day"), "title": w.get("title"), "volume": vol, "id": w.get("id")})
    by_ex: dict[str, list[dict[str, Any]]] = {}
    for w in workouts:
        for s in store.list_workout_sets(w["id"]):
            by_ex.setdefault(str(s.get("exercise") or "exercise").lower(), []).append({**s, "day": w.get("day")})
    personal_bests = []
    for ex, rows in by_ex.items():
        best = max(rows, key=lambda r: (float(r.get("weight") or 0), _set_volume(r)))
        personal_bests.append(
            {
                "exercise": ex,
                "weight": best.get("weight"),
                "reps": best.get("reps"),
                "day": best.get("day"),
                "volume": _set_volume(best),
            }
        )
    personal_bests.sort(key=lambda r: r["exercise"])
    days_trained = sorted({str(w.get("day")) for w in workouts} | {str(a.get("day")) for a in activities})
    streak = 0
    d = date.today()
    trained = set(days_trained)
    while d.isoformat() in trained:
        streak += 1
        d -= timedelta(days=1)
    freq_7 = sum(1 for x in days_trained if x >= (date.today() - timedelta(days=7)).isoformat())
    freq_28 = len(days_trained)
    vol_vals = [v["volume"] for v in volumes if v["volume"]]
    vol_trend = "stable"
    if len(vol_vals) >= 4 and vol_vals[-1] > statistics.mean(vol_vals[:-1]) * 1.08:
        vol_trend = "improving"
    elif len(vol_vals) >= 4 and vol_vals[-1] < statistics.mean(vol_vals[:-1]) * 0.92:
        vol_trend = "declining"
    last = workouts[0] if workouts else None
    prev = workouts[1] if len(workouts) > 1 else None
    expected = 3
    goals = [g for g in store.list_table("goals", "status=?", ("active",), limit=40) if g.get("kind") in ("exercise", "workout", "activity")]
    if goals and goals[0].get("per_week"):
        try:
            expected = float(goals[0]["per_week"])
        except Exception:
            expected = 3
    missed = max(0, int(round(expected)) - freq_7)
    recovery = None
    if last and last.get("day"):
        try:
            recovery = (date.today() - date.fromisoformat(str(last["day"]))).days
        except Exception:
            recovery = None
    return {
        "ok": True,
        "days": days,
        "workouts": workouts,
        "activities": activities[:80],
        "last_workout": last,
        "previous_workout": prev,
        "volumes": volumes,
        "volume_trend": vol_trend,
        "personal_bests": personal_bests[:40],
        "frequency_7": freq_7,
        "frequency_28": freq_28,
        "streak_days": streak,
        "missed_workouts_this_week": missed,
        "days_since_last_workout": recovery,
        "disclaimer": DISCLAIMER,
    }


def activity_summary(days: int = 7) -> dict[str, Any]:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = [a for a in store.list_table("activities", limit=300) if str(a.get("day") or "") >= since]
    minutes = sum(float(a["duration_min"]) for a in rows if a.get("duration_min") is not None)
    steps = sum(float(a["steps"]) for a in rows if a.get("steps") is not None)
    cals = sum(float(a["calories"]) for a in rows if a.get("calories") is not None)
    lines = [f"**Activity — last {days} days**", f"• Sessions: {len(rows)}", f"• Minutes: {minutes:.0f}", f"• Steps logged: {steps:.0f}", f"• Estimated calories: {cals:.0f}"]
    for a in rows[:12]:
        lines.append(f"• {a.get('day')} {a.get('kind')}: {a.get('duration_min') or '—'} min {a.get('intensity') or ''}".strip())
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "activity", "activities": rows, "message": "\n".join(lines), "disclaimer": DISCLAIMER}


def workout_summary() -> dict[str, Any]:
    prog = progression()
    last = prog.get("last_workout")
    lines = ["**Workout history**"]
    if not last:
        lines.append("No workouts recorded yet.")
    else:
        lines.append(f"• Last: {last.get('day')} — {last.get('title')} ({last.get('template') or last.get('body_part') or ''})".strip())
        prev = prog.get("previous_workout")
        if prev:
            lines.append(f"• Previous: {prev.get('day')} — {prev.get('title')}")
        lines.append(f"• 7-day sessions: {prog.get('frequency_7')} · 28-day active days: {prog.get('frequency_28')}")
        lines.append(f"• Streak: {prog.get('streak_days')} day(s)")
        lines.append(f"• Volume trend: {prog.get('volume_trend')}")
        if prog.get("days_since_last_workout") is not None:
            lines.append(f"• Days since last workout: {prog.get('days_since_last_workout')}")
        if prog.get("missed_workouts_this_week"):
            lines.append(f"• Missed vs weekly goal estimate: {prog.get('missed_workouts_this_week')}")
        pbs = prog.get("personal_bests") or []
        if pbs:
            lines.append("• Personal bests:")
            for pb in pbs[:8]:
                lines.append(f"  – {pb['exercise']}: {pb.get('weight') or '—'} × {pb.get('reps') or '—'} ({pb.get('day')})")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "workouts", "progression": prog, "message": "\n".join(lines), "disclaimer": DISCLAIMER}
