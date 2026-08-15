"""Health dashboard — summary only; Health remains the record owner."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER


def medication_adherence(*, days: int = 7) -> dict[str, Any]:
    """Gentle adherence history — never shaming."""
    meds = store.list_table("medications", "status=?", ("current",), limit=40)
    supps = store.list_table("supplements", "status=?", ("current",), limit=40)
    if not meds and not supps:
        return {
            "current_meds": 0,
            "current_supps": 0,
            "taken_today": [],
            "missed_today": [],
            "estimate_pct": None,
            "weekly_pct": None,
            "monthly_pct": None,
            "explain": "No current medications or supplements on file.",
        }
    today = date.today().isoformat()
    week_since = (date.today() - timedelta(days=days)).isoformat()
    month_since = (date.today() - timedelta(days=30)).isoformat()
    logs = store.list_table("dose_logs", limit=800)
    taken_today = [d for d in logs if d.get("day") == today and d.get("status") == "taken"]
    missed_today = [d for d in logs if d.get("day") == today and d.get("status") == "missed"]
    # Also count legacy missed_doses without dose_logs duplicates
    for m in store.list_table("missed_doses", limit=200):
        if m.get("day") == today and not any(x.get("name") == m.get("name") for x in missed_today):
            missed_today.append(m)

    def _pct(since: str, window_days: int) -> float | None:
        expected = max(1, len(meds) * window_days)
        missed = [d for d in logs if str(d.get("day") or "") >= since and d.get("status") == "missed" and d.get("kind") != "supplement"]
        legacy = [m for m in store.list_table("missed_doses", limit=200) if str(m.get("day") or "") >= since and m.get("kind") != "supplement"]
        miss_n = len({(m.get("day"), m.get("name")) for m in (missed + legacy)})
        return round(max(0.0, min(100.0, 100.0 * (expected - miss_n) / expected)), 0)

    weekly = _pct(week_since, days)
    monthly = _pct(month_since, 30)
    due_names = [m.get("name") for m in meds if m.get("name")]
    taken_names = {str(t.get("name") or "").lower() for t in taken_today}
    still_due = [n for n in due_names if str(n).lower() not in taken_names]
    return {
        "current_meds": len(meds),
        "current_supps": len(supps),
        "taken_today": taken_today,
        "missed_today": missed_today,
        "due_today": still_due,
        "estimate_pct": weekly,
        "weekly_pct": weekly,
        "monthly_pct": monthly,
        "explain": (
            f"About {weekly:.0f}% of expected medication days logged without a missed note over {days} days. "
            "This is a gentle history reminder — not a judgment."
            if weekly is not None
            else "Start logging taken/missed doses to see adherence history."
        ),
    }


def _adherence() -> dict[str, Any] | None:
    adh = medication_adherence(days=7)
    if adh.get("current_meds", 0) == 0 and adh.get("current_supps", 0) == 0:
        return None
    return {
        "current_meds": adh["current_meds"],
        "missed_7d": len([m for m in store.list_table("missed_doses", limit=80) if str(m.get("day") or "") >= (date.today() - timedelta(days=7)).isoformat()]),
        "estimate_pct": adh.get("estimate_pct"),
        "weekly_pct": adh.get("weekly_pct"),
        "monthly_pct": adh.get("monthly_pct"),
        "taken_today": adh.get("taken_today") or [],
        "missed_today": adh.get("missed_today") or [],
        "due_today": adh.get("due_today") or [],
        "explain": adh.get("explain"),
    }


def _goal_progress(goal: dict[str, Any]) -> dict[str, Any]:
    kind = str(goal.get("kind") or "").lower()
    target = goal.get("target_value")
    per_week = goal.get("per_week")
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    since = (today - timedelta(days=28)).isoformat()
    current = None
    note = ""
    pct = None
    on_track = None
    if kind in ("weight",):
        rows = store.list_vitals(kind="weight", limit=20)
        if rows:
            current = rows[-1].get("value")
            note = f"latest {current}"
            if target is not None and current is not None:
                try:
                    start = float(rows[0]["value"]) if rows else float(current)
                    t = float(target)
                    c = float(current)
                    if start != t:
                        pct = max(0.0, min(100.0, 100.0 * (start - c) / (start - t))) if start > t else max(0.0, min(100.0, 100.0 * (c - start) / (t - start)))
                        on_track = c <= t if start > t else c >= t
                except Exception:
                    pct = None
    elif kind in ("steps", "walk", "walking"):
        acts = [a for a in store.list_table("activities", limit=80) if str(a.get("day") or "") >= week_start]
        current = sum(float(a["steps"]) for a in acts if a.get("steps") is not None)
        note = f"{current:.0f} steps this week"
        if target:
            try:
                pct = max(0.0, min(100.0, 100.0 * float(current) / float(target)))
                on_track = float(current) >= float(target)
            except Exception:
                pass
    elif kind in ("exercise", "workout", "activity", "strength"):
        days = {a.get("day") for a in store.list_table("activities", limit=80) if str(a.get("day") or "") >= week_start}
        days |= {w.get("day") for w in store.list_table("workouts", limit=40) if str(w.get("day") or "") >= week_start}
        current = len(days)
        note = f"{current} active day(s) this week"
        target = per_week or target
        if target:
            try:
                pct = max(0.0, min(100.0, 100.0 * float(current) / float(target)))
                on_track = float(current) >= float(target)
            except Exception:
                pass
    elif kind in ("sleep",):
        chks = store.list_checkins(limit=14, since=since)
        vals = [float(c["sleep_hours"]) for c in chks if c.get("sleep_hours") is not None]
        current = round(sum(vals) / len(vals), 1) if vals else None
        note = f"avg {current}h" if current is not None else "no sleep logs"
        if target and current is not None:
            try:
                pct = max(0.0, min(100.0, 100.0 * float(current) / float(target)))
                on_track = float(current) >= float(target)
            except Exception:
                pass
    elif kind in ("water", "hydration"):
        chks = [c for c in store.list_checkins(limit=14) if str(c.get("day") or "") >= week_start and str(c.get("water") or "").strip()]
        current = len(chks)
        note = f"water logged {current} day(s) this week"
        target = per_week or target or 7
        try:
            pct = max(0.0, min(100.0, 100.0 * float(current) / float(target)))
            on_track = float(current) >= float(target)
        except Exception:
            pass
    elif kind in ("stress",):
        chks = store.list_checkins(limit=14, since=since)
        vals = [float(c["stress"]) for c in chks if c.get("stress") is not None]
        current = round(sum(vals) / len(vals), 1) if vals else None
        note = f"avg stress {current}" if current is not None else ""
        if target and current is not None:
            try:
                on_track = float(current) <= float(target)
                pct = max(0.0, min(100.0, 100.0 * (10 - float(current)) / max(0.1, 10 - float(target))))
            except Exception:
                pass
    elif kind in ("stretch", "stretching", "mobility"):
        acts = [a for a in store.list_table("activities", limit=80) if a.get("kind") in ("stretching", "yoga", "mobility") and str(a.get("day") or "") >= week_start]
        current = len({a.get("day") for a in acts})
        note = f"{current} stretch/mobility day(s) this week"
        target = per_week or target
        if target:
            try:
                pct = max(0.0, min(100.0, 100.0 * float(current) / float(target)))
                on_track = float(current) >= float(target)
            except Exception:
                pass
    elif kind in ("blood_pressure", "bp"):
        rows = store.list_vitals(kind="blood_pressure", limit=10)
        if rows:
            current = rows[-1].get("value")
            note = f"latest systolic {current}"
            if target and current is not None:
                try:
                    on_track = float(current) <= float(target)
                    pct = 100.0 if on_track else max(0.0, 100.0 - abs(float(current) - float(target)))
                except Exception:
                    pass
    elif kind in ("blood_sugar", "sugar", "glucose"):
        rows = store.list_vitals(kind="blood_sugar", limit=10)
        if rows:
            current = rows[-1].get("value")
            note = f"latest {current}"
            if target and current is not None:
                try:
                    on_track = float(current) <= float(target)
                    pct = 100.0 if on_track else max(0.0, 100.0 - abs(float(current) - float(target)) / 2)
                except Exception:
                    pass
    elif kind in ("medication", "meds", "adherence", "supplement"):
        adh = medication_adherence(days=7)
        current = adh.get("weekly_pct")
        note = adh.get("explain") or ""
        target = target or 90
        if current is not None:
            try:
                pct = float(current)
                on_track = float(current) >= float(target)
            except Exception:
                pass
    elif kind in ("appointment",):
        note = "Tracked via reminders / calendar"
        providers = [p for p in store.list_table("providers", limit=20) if p.get("next_visit")]
        current = len(providers)
        on_track = current > 0
        pct = 100.0 if providers else 0.0
    return {
        **goal,
        "current": current,
        "progress_note": note,
        "target": target,
        "progress_pct": round(pct, 0) if pct is not None else None,
        "on_track": on_track,
        "needs_work": on_track is False,
    }


def dashboard_payload() -> dict[str, Any]:
    from jarvis.health_product.engine import home_payload, observations
    from jarvis.health_product.milestones import discover_milestones
    from jarvis.health_product.reminders import due_reminders, related_calendar_appointments
    from jarvis.health_product.scorecard import build_scorecard
    from jarvis.health_product.trends import build_trends
    from jarvis.health_product.workouts import progression

    home = home_payload()
    today = date.today().isoformat()
    month_start = (date.today().replace(day=1)).isoformat()
    acts = [a for a in store.list_table("activities", limit=40) if a.get("day") == today]
    wos = [w for w in store.list_table("workouts", limit=20) if w.get("day") == today]
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    week_acts = [a for a in store.list_table("activities", limit=80) if str(a.get("day") or "") >= week_start]
    week_wos = [w for w in store.list_table("workouts", limit=40) if str(w.get("day") or "") >= week_start]
    goals = [_goal_progress(g) for g in store.list_table("goals", "status=?", ("active",), limit=30)]
    on_track = [g for g in goals if g.get("on_track") is True]
    needs_work = [g for g in goals if g.get("needs_work") is True]
    prog = progression(days=28)
    trends = build_trends(days=45)
    scorecard = build_scorecard(days=28)
    milestones = discover_milestones(persist=True)
    adh = _adherence()
    preventive_due = []
    nutrition_counts = {"meals": 0, "water": 0, "alcohol": 0}
    try:
        from jarvis.health_product.preventive import list_due

        preventive_due = list_due().get("due") or []
    except Exception:
        preventive_due = []
    try:
        from jarvis.health_product.nutrition import habits

        nutrition_counts = habits(days=14).get("counts") or nutrition_counts
    except Exception:
        pass
    attention = [t for t in (trends.get("trends") or []) if t.get("status") == "needs_attention"]
    month_changes = []
    for kind, label in (("weight", "Weight"), ("blood_pressure", "BP"), ("blood_sugar", "Sugar"), ("sleep_hours", "Sleep")):
        rows = store.list_vitals(kind=kind, since=month_start, limit=40)
        vals = [r.get("value") for r in rows if r.get("value") is not None]
        if len(vals) >= 2:
            try:
                month_changes.append(f"{label}: {vals[0]} → {vals[-1]} ({float(vals[-1]) - float(vals[0]):+.1f})")
            except Exception:
                pass

    def _trend(kind: str) -> str | None:
        rows = store.list_vitals(kind=kind, limit=8)
        vals = [r.get("value") for r in rows if r.get("value") is not None]
        if len(vals) < 2:
            return None
        try:
            delta = float(vals[-1]) - float(vals[0])
        except Exception:
            return None
        return f"{vals[0]} → {vals[-1]} ({delta:+.1f})"

    visits = store.list_table("visits", order="day DESC", limit=5)
    payload = {
        "ok": True,
        "product": "Health",
        "disclaimer": DISCLAIMER,
        "today": today,
        "checkin": home.get("checkin"),
        "today_activity": acts,
        "today_workouts": wos,
        "weekly": {
            "activity_sessions": len(week_acts),
            "workouts": len(week_wos),
            "active_days": len({*(a.get("day") for a in week_acts), *(w.get("day") for w in week_wos)}),
        },
        "adherence": adh,
        "weight_trend": _trend("weight"),
        "bp_trend": _trend("blood_pressure"),
        "sugar_trend": _trend("blood_sugar"),
        "sleep_trend": _trend("sleep_hours"),
        "workout_streak": prog.get("streak_days"),
        "goals": goals,
        "goals_on_track": on_track,
        "goals_need_work": needs_work,
        "trends": (trends.get("trends") or [])[:8],
        "attention": attention,
        "month_changes": month_changes,
        "scorecard": scorecard,
        "milestones": (milestones.get("milestones") or [])[:8],
        "observations": observations(limit=4),
        "appointments": related_calendar_appointments(days=21),
        "reminders_due": due_reminders(),
        "providers_next": [p for p in store.list_table("providers", limit=20) if p.get("next_visit")],
        "recent_visits": visits,
        "preventive_due": preventive_due,
        "nutrition_counts": nutrition_counts,
        "open_view": "health",
    }
    lines = ["**How am I doing?**", ""]
    if scorecard.get("overall") is not None:
        lines.append(f"Wellness habit summary: {scorecard['overall']}/100 (not a medical score).")
    chk = payload.get("checkin")
    lines.append("Today's check-in: " + ("on file" if chk else "not yet"))
    lines.append(f"Today's activity: {len(acts)} session(s), {len(wos)} workout(s)")
    if month_changes:
        lines.append("**What changed this month?**")
        lines.extend(f"• {c}" for c in month_changes)
    if attention:
        lines.append("**What should I pay attention to?**")
        lines.extend(f"• {t['topic']}: {t['detail']}" for t in attention[:5])
    if payload.get("appointments") or payload.get("providers_next"):
        lines.append("**Upcoming appointments**")
        for a in (payload.get("appointments") or [])[:4]:
            lines.append(f"• {a.get('day')} {a.get('time') or ''} — {a.get('title')}".strip())
        for p in (payload.get("providers_next") or [])[:3]:
            lines.append(f"• {p.get('next_visit')}: {p.get('specialty')} {p.get('name')}")
    if adh:
        lines.append("**Medications**")
        lines.append(adh.get("explain") or f"Adherence estimate {adh.get('estimate_pct')}%")
        if adh.get("due_today"):
            lines.append("Still to log today: " + ", ".join(str(x) for x in adh["due_today"][:6]))
    if preventive_due:
        lines.append("**Preventive care due**")
        for d in preventive_due[:5]:
            lines.append(f"• {d.get('name')}: {d.get('status')} (next {d.get('next_due') or '—'})")
    nc = nutrition_counts or {}
    if any(nc.get(k) for k in ("meals", "water", "alcohol")):
        lines.append(
            "**Nutrition (14 days)** — "
            f"{nc.get('meals', 0)} meal note(s), {nc.get('water', 0)} water note(s), {nc.get('alcohol', 0)} alcohol note(s)"
        )
    if on_track or needs_work:
        lines.append("**Goals**")
        for g in on_track[:4]:
            lines.append(f"• On track: {g.get('title')} ({g.get('progress_note')})")
        for g in needs_work[:4]:
            lines.append(f"• Needs work: {g.get('title')} ({g.get('progress_note')})")
    ms = payload.get("milestones") or []
    if ms:
        lines.append("**Milestones**")
        lines.extend(f"• {m.get('title')}" for m in ms[:5])
    lines += ["", "_" + DISCLAIMER + "_"]
    payload["message"] = "\n".join(lines)
    payload["intent"] = "dashboard"
    return payload
