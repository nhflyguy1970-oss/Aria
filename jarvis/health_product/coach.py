"""AI Wellness Coach — educational lifestyle suggestions from the local PHR only."""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_COACH_BOUNDARY = (
    "These are educational lifestyle ideas based on your recorded Health data and general public-health guidance. "
    "They are not a diagnosis or prescription. Do not stop prescription medications. Ask your physician before major changes."
)


def wellness_coach(*, limit: int = 8) -> dict[str, Any]:
    suggestions: list[dict[str, str]] = []
    since = (date.today() - timedelta(days=45)).isoformat()
    checkins = store.list_checkins(limit=60, since=since)
    sleep_vals = [float(c["sleep_hours"]) for c in checkins if c.get("sleep_hours") is not None]
    mood_vals = [float(c["mood"]) for c in checkins if c.get("mood") is not None]
    energy_vals = [float(c["energy"]) for c in checkins if c.get("energy") is not None]
    exercise_days = [c for c in checkins if str(c.get("exercise") or "").strip()]
    water_days = [c for c in checkins if str(c.get("water") or "").strip()]
    pain_vals = [float(c["pain"]) for c in checkins if c.get("pain") is not None]
    bp = store.list_vitals(kind="blood_pressure", since=since, limit=40)
    sugar = store.list_vitals(kind="blood_sugar", since=since, limit=40)
    weights = store.list_vitals(kind="weight", since=since, limit=40)

    if len(sleep_vals) >= 4 and statistics.mean(sleep_vals) < 6.5:
        suggestions.append(
            {
                "topic": "Sleep",
                "suggestion": "Protect a consistent sleep window and a wind-down routine.",
                "why": f"Your recent check-ins average {statistics.mean(sleep_vals):.1f} hours of sleep.",
                "trust": "low",
            }
        )
    if len(mood_vals) >= 4 and statistics.mean(mood_vals) <= 5 and len(exercise_days) < max(2, len(checkins) // 4):
        suggestions.append(
            {
                "topic": "Walking / movement",
                "suggestion": "A daily walk or light resistance session is worth discussing as a mood-support habit.",
                "why": f"Mood scores average {statistics.mean(mood_vals):.1f} and exercise is logged on {len(exercise_days)} recent days.",
                "trust": "low",
            }
        )
    if len(energy_vals) >= 4 and statistics.mean(energy_vals) <= 5:
        suggestions.append(
            {
                "topic": "Hydration & routine",
                "suggestion": "Keep water visible and pair it with existing habits (meds, meals).",
                "why": f"Energy averages {statistics.mean(energy_vals):.1f}; hydration was logged on {len(water_days)} days.",
                "trust": "low",
            }
        )
    if len(pain_vals) >= 4 and statistics.mean(pain_vals) >= 4:
        suggestions.append(
            {
                "topic": "Stretching / recovery",
                "suggestion": "Gentle stretching after activity and after poor-sleep days may be worth trying and tracking.",
                "why": f"Recent pain scores average {statistics.mean(pain_vals):.1f}.",
                "trust": "low",
            }
        )
    if len(bp) >= 4:
        sys_vals = [float(v["value"]) for v in bp if v.get("value") is not None]
        if len(sys_vals) >= 4 and (sys_vals[-1] > sys_vals[0] + 6 or statistics.mean(sys_vals[-3:]) > 130):
            suggestions.append(
                {
                    "topic": "Sodium / walking / physician questions",
                    "suggestion": "Consider lower-sodium meals and regular walking, and ask your physician about this blood-pressure trend.",
                    "why": f"Systolic readings moved from {sys_vals[0]:.0f} toward {sys_vals[-1]:.0f} in the saved series.",
                    "trust": "low",
                }
            )
    if len(sugar) >= 4:
        vals = [float(v["value"]) for v in sugar if v.get("value") is not None]
        if len(vals) >= 4 and (vals[-1] > vals[0] + 12 or statistics.mean(vals[-3:]) > 130):
            suggestions.append(
                {
                    "topic": "Fiber / meal pattern / physician questions",
                    "suggestion": "Fiber-forward meals and consistent meal timing are common lifestyle topics to review with your physician.",
                    "why": f"Blood sugar readings moved from {vals[0]:.0f} toward {vals[-1]:.0f}.",
                    "trust": "low",
                }
            )
    if len(weights) >= 4:
        w = [float(v["value"]) for v in weights if v.get("value") is not None]
        if len(w) >= 4 and abs(w[-1] - w[0]) >= 3:
            direction = "down" if w[-1] < w[0] else "up"
            suggestions.append(
                {
                    "topic": "Healthy weight management",
                    "suggestion": "Track meals and activity alongside weight and review the trend with your physician.",
                    "why": f"Recorded weight has moved {direction} from {w[0]:.1f} to {w[-1]:.1f}.",
                    "trust": "low",
                }
            )

    # Long-term pattern observations (educational only — never diagnose)
    for pattern in _long_term_patterns(checkins, bp):
        suggestions.append(pattern)

    meds = store.list_table("medications", "status=?", ("current",), limit=20)
    if meds:
        suggestions.append(
            {
                "topic": "Medication routine consistency",
                "suggestion": "Keep current prescriptions on a visible daily routine. Do not stop prescribed medications.",
                "why": f"Health lists {len(meds)} current medication(s).",
                "trust": "low",
            }
        )
    if any("stress" in (c or {}) and c.get("stress") not in (None, "") and float(c.get("stress") or 0) >= 7 for c in checkins[:10]):
        suggestions.append(
            {
                "topic": "Stress reduction",
                "suggestion": "Short breathing breaks, a walk, or a fixed shutdown time can be useful experiments — not treatment.",
                "why": "Recent check-ins include high stress scores.",
                "trust": "low",
            }
        )

    from jarvis.health_product.engine import observations
    from jarvis.health_product.workouts import progression
    from jarvis.health_product.trends import build_trends
    from jarvis.health_product.dashboard import _adherence, _goal_progress

    prog = progression(days=28)
    if (prog.get("frequency_7") or 0) < 3 and (prog.get("frequency_28") or 0) < 8:
        suggestions.append(
            {
                "topic": "Walking / strength / resistance",
                "suggestion": "Build toward regular walking plus two short resistance or band sessions weekly, if your physician agrees.",
                "why": f"Activity/workout days: {prog.get('frequency_7')} in 7 days and {prog.get('frequency_28')} in 28 days.",
                "trust": "low",
            }
        )
    if (prog.get("days_since_last_workout") or 0) >= 5:
        suggestions.append(
            {
                "topic": "Mobility / return to movement",
                "suggestion": "A light mobility or stretch session can restart consistency after a gap — not a rehab prescription.",
                "why": f"{prog.get('days_since_last_workout')} day(s) since the last recorded workout.",
                "trust": "low",
            }
        )
    adh = _adherence()
    if adh and adh.get("missed_7d", 0) >= 2:
        suggestions.append(
            {
                "topic": "Medication routine consistency",
                "suggestion": "Use a visible daily routine for current prescriptions. Do not stop prescribed medications.",
                "why": f"{adh['missed_7d']} missed-dose notes in 7 days across {adh['current_meds']} current medication(s).",
                "trust": "low",
            }
        )
    for g in store.list_table("goals", "status=?", ("active",), limit=8):
        gp = _goal_progress(g)
        suggestions.append(
            {
                "topic": f"Goal: {g.get('title')}",
                "suggestion": "Keep logging the related metric so this goal stays honest and discuss targets with your physician.",
                "why": gp.get("progress_note") or "No progress data yet.",
                "trust": "low",
            }
        )
    symptoms = store.list_table("symptoms", order="recorded_at DESC", limit=8)
    if symptoms:
        suggestions.append(
            {
                "topic": "Questions for your physician",
                "suggestion": "Bring recent symptoms and trends to your next visit rather than self-diagnosing.",
                "why": f"Recent symptom notes include: {', '.join(str(s.get('name')) for s in symptoms[:4])}.",
                "trust": "low",
            }
        )

    obs = observations(limit=4)
    trend_bits = [t for t in (build_trends().get("trends") or []) if t.get("status") == "needs_attention"]
    lines = ["**Wellness coach** (educational only)", "", _COACH_BOUNDARY, ""]
    if not suggestions:
        lines.append("Not enough recorded trends yet for lifestyle ideas. Keep daily check-ins going.")
    else:
        for s in suggestions[:limit]:
            lines.append(f"• **{s['topic']}:** {s['suggestion']}")
            lines.append(f"  Why: {s['why']}")
    if trend_bits:
        lines += ["", "**Trends needing attention**"] + [f"• {t['topic']}: {t['detail']}" for t in trend_bits[:4]]
    if obs:
        lines += ["", "**Related observations**"] + [f"• {o}" for o in obs]
    lines += ["", "Questions worth asking a physician can live in Health → Questions.", "", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "coach",
        "suggestions": suggestions[:limit],
        "observations": obs,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
        "boundary": _COACH_BOUNDARY,
        "trust": "low",
    }


def _long_term_patterns(checkins: list[dict[str, Any]], bp: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Surface correlational patterns from recorded data only — never fabricated."""
    out: list[dict[str, str]] = []
    if len(checkins) < 8:
        return out

    by_day = {str(c.get("day") or ""): c for c in checkins if c.get("day")}
    walk_days = set()
    for a in store.list_table("activities", limit=200):
        kind = str(a.get("kind") or "").lower()
        if kind in ("walking", "walk", "hike", "hiking") or "walk" in kind:
            walk_days.add(str(a.get("day") or ""))
    for c in checkins:
        if re_search_walk(str(c.get("exercise") or "")):
            walk_days.add(str(c.get("day") or ""))

    sleep_after_walk = []
    sleep_no_walk = []
    for day, c in by_day.items():
        if c.get("sleep_hours") is None:
            continue
        try:
            hrs = float(c["sleep_hours"])
        except Exception:
            continue
        # Sleep logged on day D often reflects prior night — use previous calendar day activity when possible
        prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat() if _iso(day) else day
        if prev in walk_days or day in walk_days:
            sleep_after_walk.append(hrs)
        else:
            sleep_no_walk.append(hrs)
    if len(sleep_after_walk) >= 3 and len(sleep_no_walk) >= 3:
        aw = statistics.mean(sleep_after_walk)
        nw = statistics.mean(sleep_no_walk)
        if aw >= nw + 0.4:
            out.append(
                {
                    "topic": "Sleep after walking",
                    "suggestion": "You usually sleep a bit better after days that include a walk — worth continuing as a lifestyle experiment.",
                    "why": f"Avg sleep {aw:.1f}h on/after walk days vs {nw:.1f}h without (from your check-ins).",
                    "trust": "low",
                }
            )

    stretch_days = set()
    for a in store.list_table("activities", limit=200):
        if "stretch" in str(a.get("kind") or "").lower() or "stretch" in str(a.get("title") or "").lower():
            stretch_days.add(str(a.get("day") or ""))
    for w in store.list_table("workouts", limit=100):
        blob = f"{w.get('template') or ''} {w.get('title') or ''} {w.get('body_part') or ''}".lower()
        if "stretch" in blob or "mobility" in blob:
            stretch_days.add(str(w.get("day") or ""))
    pain_stretch = [float(c["pain"]) for d, c in by_day.items() if d in stretch_days and c.get("pain") is not None]
    pain_other = [float(c["pain"]) for d, c in by_day.items() if d not in stretch_days and c.get("pain") is not None]
    if len(pain_stretch) >= 3 and len(pain_other) >= 3 and statistics.mean(pain_stretch) + 0.8 <= statistics.mean(pain_other):
        out.append(
            {
                "topic": "Stretching and pain notes",
                "suggestion": "Stretching or mobility days appear alongside lower pain scores in your log — track carefully and review with your physician if pain persists.",
                "why": f"Avg pain {statistics.mean(pain_stretch):.1f} on stretch/mobility days vs {statistics.mean(pain_other):.1f} otherwise.",
                "trust": "low",
            }
        )

    morning_wo = set()
    for w in store.list_table("workouts", limit=120):
        notes = f"{w.get('notes') or ''} {w.get('title') or ''}".lower()
        if "morning" in notes or "am " in notes:
            morning_wo.add(str(w.get("day") or ""))
    for a in store.list_table("activities", limit=200):
        notes = f"{a.get('notes') or ''} {a.get('title') or ''}".lower()
        if "morning" in notes:
            morning_wo.add(str(a.get("day") or ""))
    mood_am = [float(c["mood"]) for d, c in by_day.items() if d in morning_wo and c.get("mood") is not None]
    mood_other = [float(c["mood"]) for d, c in by_day.items() if d not in morning_wo and c.get("mood") is not None]
    if len(mood_am) >= 3 and len(mood_other) >= 3 and statistics.mean(mood_am) >= statistics.mean(mood_other) + 0.6:
        out.append(
            {
                "topic": "Morning movement and mood",
                "suggestion": "Morning workouts appear with better mood scores in your record — an educational pattern, not a prescription.",
                "why": f"Avg mood {statistics.mean(mood_am):.1f} on morning-activity days vs {statistics.mean(mood_other):.1f} otherwise.",
                "trust": "low",
            }
        )

    sleep_map = {str(c.get("day") or ""): c.get("sleep_hours") for c in checkins if c.get("sleep_hours") is not None}
    bp_after_good = []
    bp_after_poor = []
    for v in bp:
        day = str(v.get("day") or "")
        if not day or v.get("value") is None:
            continue
        try:
            prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
            sleep = sleep_map.get(prev) or sleep_map.get(day)
            if sleep is None:
                continue
            sys_v = float(v["value"])
            if float(sleep) >= 7:
                bp_after_good.append(sys_v)
            elif float(sleep) <= 5.5:
                bp_after_poor.append(sys_v)
        except Exception:
            continue
    if len(bp_after_good) >= 3 and len(bp_after_poor) >= 3 and statistics.mean(bp_after_good) + 4 <= statistics.mean(bp_after_poor):
        out.append(
            {
                "topic": "Blood pressure after better sleep",
                "suggestion": "Systolic readings look lower after nights with more sleep in your log — a lifestyle observation to discuss with your physician.",
                "why": f"Avg systolic {statistics.mean(bp_after_good):.0f} after ≥7h sleep vs {statistics.mean(bp_after_poor):.0f} after ≤5.5h.",
                "trust": "low",
            }
        )
    return out


def re_search_walk(text: str) -> bool:
    t = (text or "").lower()
    return "walk" in t or "hike" in t


def _iso(day: str) -> bool:
    try:
        date.fromisoformat(day)
        return True
    except Exception:
        return False
