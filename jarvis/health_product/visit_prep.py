"""Doctor visit preparation — aggregates recorded Health facts for physician visits."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_BOUNDARY = (
    "This packet organizes information from your local Personal Health Record for discussion with a clinician. "
    "Aria is not a physician and does not diagnose or prescribe."
)


def _trend(kind: str, *, days: int = 90) -> str:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = store.list_vitals(kind=kind, since=since, limit=40)
    vals = [r.get("value") for r in rows if r.get("value") is not None]
    if len(vals) < 2:
        return "not enough readings"
    try:
        return f"{vals[0]} → {vals[-1]} ({float(vals[-1]) - float(vals[0]):+.1f}) over ~{days}d"
    except Exception:
        return f"{vals[0]} → {vals[-1]}"


def build_visit_prep(*, since: str | None = None) -> dict[str, Any]:
    from jarvis.health_product.engine import home_payload, observations
    from jarvis.health_product.family_history import doctor_prep_section
    from jarvis.health_product.reminders import related_calendar_appointments

    home = home_payload()
    visits = store.list_table("visits", order="day DESC", limit=10)
    last_visit_day = since or (visits[0].get("day") if visits else None)
    if not last_visit_day:
        last_visit_day = (date.today() - timedelta(days=180)).isoformat()

    symptoms = [s for s in store.list_table("symptoms", order="recorded_at DESC", limit=40) if str(s.get("day") or "") >= last_visit_day]
    meds_changed = []
    for m in store.list_table("medications", limit=80):
        if str(m.get("start_date") or "") >= last_visit_day or str(m.get("stop_date") or "") >= last_visit_day or str(m.get("updated_at") or ""):
            # Prefer start/stop dates
            if str(m.get("start_date") or "") >= last_visit_day or str(m.get("stop_date") or "") >= last_visit_day:
                meds_changed.append(m)
    labs = [lab for lab in store.list_labs(limit=40) if str(lab.get("day") or "") >= last_visit_day]
    docs = [d for d in store.list_table("documents", order="created_at DESC", limit=40) if str(d.get("day") or "") >= last_visit_day]
    imaging = [p for p in store.list_table("procedures", limit=40) if str(p.get("day") or "") >= last_visit_day]
    questions = store.list_table("doctor_questions", "status=?", ("open",), order="created_at DESC", limit=40)
    recovery = [r for r in store.list_table("recovery_events", limit=30) if str(r.get("day") or "") >= last_visit_day]
    nutrition = [n for n in store.list_table("nutrition_log", limit=40) if str(n.get("day") or "") >= last_visit_day]

    timeline_bits = []
    for src, rows, title_key in (
        ("symptoms", symptoms, "name"),
        ("labs", labs, "name"),
        ("documents", docs, "title"),
        ("procedures", imaging, "name"),
        ("recovery", recovery, "title"),
        ("nutrition", nutrition[:10], "description"),
    ):
        for r in rows[:8]:
            timeline_bits.append({"day": r.get("day"), "source": src, "title": r.get(title_key) or r.get("id")})
    timeline_bits.sort(key=lambda x: str(x.get("day") or ""), reverse=True)

    lines = [
        "**Doctor visit preparation**",
        "",
        _BOUNDARY,
        "",
        f"Timeline since: {last_visit_day}",
        "",
        "**Current medications**",
    ]
    meds = home.get("medications") or []
    if meds:
        lines.extend(f"• {m.get('name')} {m.get('strength') or ''} {m.get('dose') or ''} {m.get('frequency') or ''}".strip() for m in meds)
    else:
        lines.append("• None on file")
    lines.append("**Current supplements**")
    supps = home.get("supplements") or []
    if supps:
        lines.extend(f"• {s.get('name')} {s.get('dose') or ''}".strip() for s in supps)
    else:
        lines.append("• None on file")
    lines.append("**Conditions**")
    for c in home.get("conditions") or []:
        lines.append(f"• {c.get('name')} ({c.get('status')})")
    if not home.get("conditions"):
        lines.append("• None on file")
    lines += ["", "**Trends**", f"• Blood pressure: {_trend('blood_pressure')}", f"• Blood sugar: {_trend('blood_sugar')}", f"• Weight: {_trend('weight')}", f"• Sleep: {_trend('sleep_hours')}"]
    lines.append("**Recent symptoms**")
    if symptoms:
        lines.extend(f"• {s.get('day')}: {s.get('name')} — {s.get('notes') or s.get('duration') or ''}" for s in symptoms[:10])
    else:
        lines.append("• None since last visit marker")
    if meds_changed:
        lines.append("**Medication changes since last visit**")
        lines.extend(f"• {m.get('name')} — {m.get('status')} (start {m.get('start_date') or '—'} / stop {m.get('stop_date') or '—'})" for m in meds_changed[:10])
    if labs:
        lines.append("**Labs since last visit**")
        lines.extend(f"• {lab.get('day')}: {lab.get('name')} = {lab.get('value') if lab.get('value') is not None else lab.get('value_text')} {lab.get('units') or ''}" for lab in labs[:12])
    if imaging:
        lines.append("**Procedures / imaging since last visit**")
        lines.extend(f"• {p.get('day')}: {p.get('name')} ({p.get('kind')}) — {p.get('result') or ''}" for p in imaging[:8])
    if docs:
        lines.append("**Relevant documents**")
        lines.extend(f"• {d.get('day')}: {d.get('title')} [{d.get('kind')}]" for d in docs[:8])
    lines.append("**Questions for your physician**")
    if questions:
        lines.extend(f"• {q.get('text')}" for q in questions)
    else:
        lines.append("• (none saved — say “remind me to ask my doctor about …”)")
    for section_line in doctor_prep_section():
        lines.append(section_line)
    try:
        from jarvis.health_product.preventive import list_due

        due = list_due().get("due") or []
        if due:
            lines.append("**Preventive care due**")
            lines.extend(f"• {d.get('name')}: {d.get('status')} (next {d.get('next_due') or '—'})" for d in due[:6])
    except Exception:
        pass
    appts = related_calendar_appointments(days=21)
    if appts:
        lines.append("**Upcoming appointments**")
        lines.extend(f"• {a.get('day')} {a.get('time') or ''} — {a.get('title')}" for a in appts[:5])
    obs = observations(limit=4)
    if obs:
        lines.append("**Outstanding concerns / observations**")
        lines.extend(f"• {o}" for o in obs)
    if timeline_bits:
        lines.append("**Timeline highlights since last visit**")
        for t in timeline_bits[:15]:
            lines.append(f"• {t.get('day')} [{t.get('source')}] {t.get('title')}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "visit_prep",
        "since": last_visit_day,
        "medications": meds,
        "supplements": supps,
        "conditions": home.get("conditions") or [],
        "symptoms": symptoms,
        "labs": labs,
        "documents": [{k: d[k] for k in d if k != "extracted_text"} for d in docs],
        "procedures": imaging,
        "questions": questions,
        "timeline": timeline_bits,
        "trends": {
            "blood_pressure": _trend("blood_pressure"),
            "blood_sugar": _trend("blood_sugar"),
            "weight": _trend("weight"),
            "sleep": _trend("sleep_hours"),
        },
        "boundary": _BOUNDARY,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
        "report": "visit_prep",
        "open_view": "health",
    }
