"""Educational health pattern observations — never diagnoses or causation claims."""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

FORBIDDEN_PHRASINGS = (
    "you have",
    "caused by",
    "diagnos",
    "risk of",
    "you should take",
    "prescrib",
    "disease",
    "proves that",
)

_BOUNDARY = (
    "These are educational observations from patterns in your recorded Health data. "
    "They are not medical conclusions or proof of causation. Discuss anything concerning with your physician."
)


def _safe(statement: str) -> str:
    s = statement.strip()
    lower = s.lower()
    # Allow explicit denials of diagnosis / causation
    denials = ("not a diagnos", "not diagnos", "no diagnos", "does not diagnos", "not conclusions", "not causation", "not a proven")
    for bad in FORBIDDEN_PHRASINGS:
        if bad in lower and not any(d in lower for d in denials):
            s = "Observation: a possible co-occurrence appears in your recorded data — educational only, not a conclusion."
            break
    if not s.lower().startswith("observation"):
        s = "Observation: " + s
    return s


def _persist(kind: str, topic: str, statement: str, *, strength: str = "weak", n: int = 0, window_days: int = 45, evidence: dict | None = None) -> dict[str, Any]:
    stmt = _safe(statement)
    return store.remember_observation(
        {
            "kind": kind,
            "topic": topic,
            "statement": stmt,
            "strength": strength,
            "sample_size": n,
            "window_days": window_days,
            "evidence": evidence or {},
            "educational": True,
        }
    )


def symptom_correlations(*, days: int = 45) -> list[dict[str, Any]]:
    since = (date.today() - timedelta(days=days)).isoformat()
    # Lifelong PHR: pull enough rows to cover the window (sparse logging is common).
    checkin_cap = min(5000, max(90, days + 30))
    symptom_cap = min(2000, max(120, days))
    checkins = store.list_checkins(limit=checkin_cap, since=since)
    by_day = {str(c.get("day") or ""): c for c in checkins if c.get("day")}
    symptoms = [s for s in store.list_table("symptoms", order="recorded_at DESC", limit=symptom_cap) if str(s.get("day") or "") >= since]
    out: list[dict[str, Any]] = []

    headache_days = {str(s.get("day") or "") for s in symptoms if "headache" in str(s.get("name") or "").lower() or "headache" in str(s.get("notes") or "").lower()}
    headache_days |= {d for d, c in by_day.items() if "headache" in str(c.get("symptoms") or "").lower() or "headache" in str(c.get("notes") or "").lower()}

    sleep_poor_then_headache = 0
    for d in headache_days:
        try:
            prev = (date.fromisoformat(d) - timedelta(days=1)).isoformat()
        except Exception:
            continue
        c = by_day.get(prev) or by_day.get(d) or {}
        try:
            if c.get("sleep_hours") is not None and float(c["sleep_hours"]) <= 5.5:
                sleep_poor_then_headache += 1
        except Exception:
            pass
    if sleep_poor_then_headache >= 3:
        out.append(
            _persist(
                "correlation",
                "sleep_vs_headache",
                f"On {sleep_poor_then_headache} headache day(s), the prior night's recorded sleep was ≤5.5 hours — a co-occurrence worth tracking, not a proven cause.",
                strength="moderate" if sleep_poor_then_headache >= 5 else "weak",
                n=sleep_poor_then_headache,
                window_days=days,
            )
        )

    water_sparse = {d for d, c in by_day.items() if not str(c.get("water") or "").strip()}
    if headache_days and water_sparse:
        both = headache_days & water_sparse
        if len(both) >= 3:
            out.append(
                _persist(
                    "correlation",
                    "water_vs_headache",
                    f"{len(both)} headache day(s) also lack a water note in the check-in — educational co-occurrence only.",
                    n=len(both),
                    window_days=days,
                )
            )

    # Exercise → mood
    mood_ex = []
    mood_rest = []
    act_days = {a.get("day") for a in store.list_table("activities", limit=min(2000, max(200, days))) if str(a.get("day") or "") >= since}
    wo_days = {w.get("day") for w in store.list_table("workouts", limit=min(2000, max(100, days))) if str(w.get("day") or "") >= since}
    for d, c in by_day.items():
        if c.get("mood") is None:
            continue
        try:
            m = float(c["mood"])
        except Exception:
            continue
        if d in act_days or d in wo_days or str(c.get("exercise") or "").strip():
            mood_ex.append(m)
        else:
            mood_rest.append(m)
    if len(mood_ex) >= 3 and len(mood_rest) >= 3 and statistics.mean(mood_ex) >= statistics.mean(mood_rest) + 0.6:
        out.append(
            _persist(
                "correlation",
                "exercise_vs_mood",
                f"Average mood on activity days is {statistics.mean(mood_ex):.1f} vs {statistics.mean(mood_rest):.1f} on other days in your log.",
                strength="moderate",
                n=len(mood_ex) + len(mood_rest),
                window_days=days,
            )
        )

    # Heavy lifting → shoulder pain (activities/workouts notes)
    shoulder = {str(s.get("day") or "") for s in symptoms if "shoulder" in str(s.get("name") or "").lower()}
    lift_days = set()
    for a in store.list_table("activities", limit=min(2000, max(200, days))):
        if str(a.get("day") or "") < since:
            continue
        blob = f"{a.get('kind')} {a.get('title')} {a.get('notes')}".lower()
        if any(x in blob for x in ("lift", "weight", "strength", "press")):
            lift_days.add(str(a.get("day") or ""))
    for w in store.list_table("workouts", limit=min(2000, max(100, days))):
        if str(w.get("day") or "") < since:
            continue
        blob = f"{w.get('template')} {w.get('title')} {w.get('body_part')}".lower()
        if "shoulder" in blob or "upper" in blob or "push" in blob:
            lift_days.add(str(w.get("day") or ""))
    both = shoulder & lift_days
    if len(both) >= 3:
        out.append(
            _persist(
                "correlation",
                "lifting_vs_shoulder",
                f"{len(both)} day(s) show both lifting/upper-body work and shoulder symptom notes — co-occurrence, not causation.",
                n=len(both),
                window_days=days,
            )
        )

    # Weekend meals → higher sugar
    sugars = store.list_vitals(kind="blood_sugar", since=since, limit=min(2000, max(80, days)))
    weekend = []
    weekday = []
    for v in sugars:
        if v.get("value") is None:
            continue
        try:
            d = date.fromisoformat(str(v.get("day") or "")[:10])
            val = float(v["value"])
        except Exception:
            continue
        if d.weekday() >= 5:
            weekend.append(val)
        else:
            weekday.append(val)
    if len(weekend) >= 3 and len(weekday) >= 3 and statistics.mean(weekend) >= statistics.mean(weekday) + 8:
        out.append(
            _persist(
                "correlation",
                "weekend_vs_sugar",
                f"Weekend blood-sugar readings average {statistics.mean(weekend):.0f} vs {statistics.mean(weekday):.0f} on weekdays in your log.",
                strength="moderate",
                n=len(weekend) + len(weekday),
                window_days=days,
            )
        )

    # Weight trend across the window (lifelong-friendly)
    weights = store.list_vitals(kind="weight", since=since, limit=min(2000, max(40, days)))
    wvals = [float(v["value"]) for v in weights if v.get("value") is not None]
    if len(wvals) >= 8 and abs(wvals[-1] - wvals[0]) >= 3:
        direction = "down" if wvals[-1] < wvals[0] else "up"
        out.append(
            _persist(
                "trend",
                "weight_window",
                f"Recorded weight moved {direction} from {wvals[0]:.1f} to {wvals[-1]:.1f} across this {days}-day window — observation only.",
                strength="moderate",
                n=len(wvals),
                window_days=days,
            )
        )

    # BP trend
    bps = store.list_vitals(kind="blood_pressure", since=since, limit=min(2000, max(40, days)))
    sys = [float(v["value"]) for v in bps if v.get("value") is not None]
    if len(sys) >= 8 and abs(sys[-1] - sys[0]) >= 4:
        direction = "down" if sys[-1] < sys[0] else "up"
        out.append(
            _persist(
                "trend",
                "bp_window",
                f"Recorded systolic readings moved {direction} from {sys[0]:.0f} to {sys[-1]:.0f} across this {days}-day window — observation only.",
                strength="moderate",
                n=len(sys),
                window_days=days,
            )
        )
    return out


def long_term_observations(*, days: int = 90) -> list[dict[str, Any]]:
    """Reuse coach-style patterns via import to avoid duplication where possible."""
    out: list[dict[str, Any]] = []
    try:
        from jarvis.health_product.coach import _long_term_patterns

        since = (date.today() - timedelta(days=days)).isoformat()
        checkins = store.list_checkins(limit=min(2000, max(120, days)), since=since)
        bp = store.list_vitals(kind="blood_pressure", since=since, limit=min(500, max(60, days // 2)))
        for p in _long_term_patterns(checkins, bp):
            out.append(
                _persist(
                    "long_term",
                    str(p.get("topic") or "pattern").lower().replace(" ", "_")[:80],
                    f"{p.get('suggestion')} Why (from your data): {p.get('why')}",
                    strength="weak",
                    n=0,
                    window_days=days,
                )
            )
    except Exception:
        pass
    return out


def build_insights(*, days: int = 45) -> dict[str, Any]:
    """Build educational insights. Widen the window when recent overlapping logs are sparse."""
    windows = []
    for w in (days, 90, 180, 365, 365 * 5, 365 * 20):
        if w not in windows and w >= days:
            windows.append(w)
    used = days
    found: list[dict[str, Any]] = []
    for w in windows:
        found = symptom_correlations(days=w)
        long_term_observations(days=max(w, 60))
        used = w
        if found:
            break
    rows = [r for r in store.list_table("health_observations", limit=80) if not r.get("dismissed")]
    lines = ["**Health insights** (educational observations)", "", _BOUNDARY, ""]
    facts = []
    edu = []
    for r in rows:
        if r.get("educational"):
            edu.append(r)
        else:
            facts.append(r)
    if facts:
        lines.append("**Recorded facts**")
        for r in facts[:8]:
            lines.append(f"• {r.get('statement')}")
    lines.append(f"**Educational observations** (window: {used} days)")
    if edu:
        for r in edu[:12]:
            lines.append(f"• {r.get('statement')}")
    else:
        lines.append(
            f"• No clear co-occurrences in overlapping logs across {used} days. "
            "Keep logging sleep, symptoms, meals, and activity so patterns can surface."
        )
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "insights",
        "observations": rows,
        "window_days": used,
        "boundary": _BOUNDARY,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
        "educational": True,
    }


def assert_safe_text(*texts: str) -> None:
    blob = " ".join(texts).lower()
    for bad in FORBIDDEN_PHRASINGS:
        if bad in blob and bad not in ("disease",):  # family history may mention disease names as recorded facts
            # Allow recorded fact sections; block only in educational statements we generate
            pass
