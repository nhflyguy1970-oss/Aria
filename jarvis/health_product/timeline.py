"""Chronological Health Timeline — lifelong central view, filterable."""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER
from jarvis.health_product.trust import trust_for_source

FILTERS = [
    ("", "Everything"),
    ("vitals", "Vitals"),
    ("exercise", "Exercise"),
    ("workouts", "Workouts"),
    ("symptoms", "Symptoms"),
    ("medications", "Medications"),
    ("supplements", "Supplements"),
    ("labs", "Labs"),
    ("doctors", "Doctors"),
    ("documents", "Documents"),
    ("journal", "Journal"),
    ("goals", "Goals"),
    ("milestones", "Milestones"),
    ("recovery", "Recovery"),
    ("nutrition", "Nutrition"),
    ("preventive", "Preventive"),
    ("family_history", "Family history"),
]


def _day_from_ts(ts: float | None) -> str:
    if not ts:
        return date.today().isoformat()
    try:
        return datetime.fromtimestamp(float(ts)).date().isoformat()
    except Exception:
        return date.today().isoformat()


def _match(cat: str, source: str, aliases: set[str] | None = None) -> bool:
    if not cat or cat in ("all", "everything"):
        return True
    aliases = aliases or set()
    bucket = {source, source.rstrip("s"), *aliases}
    return cat in bucket or any(cat in a or a in cat for a in bucket)


def build_timeline(*, category: str = "", limit: int = 250) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    cat = (category or "").strip().lower()
    if cat in ("everything",):
        cat = ""

    def add(source: str, title: str, day: str, detail: str = "", ts: float | None = None, record: dict | None = None, aliases: set[str] | None = None):
        if not _match(cat, source, aliases):
            return
        items.append(
            {
                "source": source,
                "category": source,
                "title": title,
                "day": day or _day_from_ts(ts),
                "detail": detail,
                "ts": ts or time.time(),
                "trust": trust_for_source(source),
                "record": record or {},
            }
        )

    if _match(cat, "vitals", {"checkin", "checkins", "sleep", "vital"}):
        for v in store.list_vitals(limit=800):
            val = v.get("value")
            if v.get("value2") is not None:
                val = f"{v.get('value')}/{v.get('value2')}"
            add("vitals", str(v.get("kind")), v.get("day") or "", f"{val} {v.get('units') or ''}".strip(), v.get("recorded_at"), v)
        for c in store.list_checkins(limit=200):
            bits = [f"{k}={c[k]}" for k in ("overall", "sleep_hours", "weight", "blood_sugar", "exercise") if c.get(k) not in (None, "")]
            add("checkins", f"Check-in {c.get('day')}", c.get("day") or "", ", ".join(bits), None, c, {"vitals", "checkin"})

    if _match(cat, "labs", {"lab", "laboratory"}):
        for r in store.list_labs(limit=400):
            add("labs", str(r.get("name")), r.get("day") or "", f"{r.get('value') if r.get('value') is not None else r.get('value_text')} {r.get('units') or ''}".strip(), r.get("recorded_at"), r)

    if _match(cat, "medications", {"meds", "medication", "dose"}):
        for m in store.list_table("medications", limit=200):
            action = "current"
            if m.get("status") == "stopped":
                action = "stopped"
            elif m.get("notes") and "change" in str(m.get("notes")).lower():
                action = "dose change"
            add("medications", f"{action.title()}: {m.get('name')}", m.get("start_date") or m.get("stop_date") or "", f"{m.get('status')} {m.get('dose') or ''} {m.get('frequency') or ''}".strip(), m.get("updated_at"), m)
        for miss in store.list_table("missed_doses", order="created_at DESC", limit=100):
            add("medications", f"Missed {miss.get('name')}", miss.get("day") or "", miss.get("notes") or "", miss.get("created_at"), miss)
        for d in store.list_table("dose_logs", limit=200):
            add("medications", f"{str(d.get('status') or 'dose').title()} {d.get('name')}", d.get("day") or "", d.get("notes") or "", d.get("created_at"), d)

    if _match(cat, "supplements", {"supplement"}):
        for s in store.list_table("supplements", limit=200):
            add("supplements", str(s.get("name")), s.get("start_date") or s.get("stop_date") or "", f"{s.get('status')} {s.get('dose') or ''}".strip(), s.get("updated_at"), s)

    if _match(cat, "symptoms", {"symptom"}):
        for s in store.list_table("symptoms", order="recorded_at DESC", limit=200):
            add("symptoms", str(s.get("name")), s.get("day") or "", s.get("duration") or s.get("notes") or "", s.get("recorded_at"), s)

    if _match(cat, "documents", {"document", "docs"}):
        for d in store.list_table("documents", order="created_at DESC", limit=100):
            add("documents", str(d.get("title")), d.get("day") or "", d.get("kind") or "", d.get("created_at"), {k: d[k] for k in d if k != "extracted_text"})

    if _match(cat, "activities", {"activity", "exercise"}):
        for a in store.list_table("activities", limit=300):
            add("activities", str(a.get("title") or a.get("kind")), a.get("day") or "", f"{a.get('duration_min') or ''} min {a.get('intensity') or ''}".strip(), a.get("created_at"), a, {"exercise"})

    if _match(cat, "workouts", {"workout"}):
        for w in store.list_table("workouts", limit=200):
            add("workouts", str(w.get("title") or "Workout"), w.get("day") or "", w.get("template") or w.get("body_part") or "", w.get("created_at"), w)

    if _match(cat, "visits", {"visit", "doctor", "doctors", "appointment"}):
        for v in store.list_table("visits", order="created_at DESC", limit=100):
            add("visits", str(v.get("title") or v.get("reason") or "Visit"), v.get("day") or "", f"{v.get('physician') or ''} {v.get('summary') or v.get('notes') or ''}".strip(), v.get("created_at"), v, {"doctors"})
        for p in store.list_table("providers", limit=40):
            if p.get("last_visit") or p.get("next_visit"):
                add("providers", f"{p.get('specialty')}: {p.get('name')}", p.get("last_visit") or p.get("next_visit") or "", p.get("notes") or "", p.get("updated_at"), p, {"doctors"})

    if _match(cat, "procedures", {"procedure", "imaging", "hospital"}):
        for p in store.list_table("procedures", limit=200):
            add("procedures", str(p.get("name")), p.get("day") or "", f"{p.get('location') or ''} {p.get('provider') or ''}".strip(), p.get("created_at"), p)

    if _match(cat, "vaccinations", {"vaccination", "vaccine"}):
        for v in store.list_table("vaccinations", limit=100):
            add("vaccinations", str(v.get("name")), v.get("day") or "", v.get("notes") or "", v.get("updated_at"), v)

    if _match(cat, "doctor_questions", {"questions", "question"}):
        for q in store.list_table("doctor_questions", order="created_at DESC", limit=100):
            add("doctor_questions", str(q.get("text")), _day_from_ts(q.get("created_at")), q.get("status") or "", q.get("created_at"), q)

    if _match(cat, "consultations", {"consults", "ai", "consult"}):
        for c in store.list_table("consultations", order="created_at DESC", limit=50):
            add("consultations", str(c.get("question") or "Consultation")[:120], _day_from_ts(c.get("created_at")), f"{c.get('level')} / {c.get('status')}", c.get("created_at"), {k: c[k] for k in c if k != "shared_json"})

    if _match(cat, "health_journal", {"journal", "notes", "medical_notes"}):
        for n in store.list_table("medical_notes", order="created_at DESC", limit=100):
            add("medical_notes", str(n.get("title") or "Note"), n.get("day") or "", (n.get("body") or "")[:160], n.get("created_at"), n, {"journal"})
        for j in store.list_table("health_journal", limit=200):
            add("health_journal", "Health journal", j.get("day") or "", (j.get("body") or "")[:160], j.get("created_at"), j, {"journal"})

    if _match(cat, "goals", {"goal"}):
        for g in store.list_table("goals", limit=100):
            add("goals", str(g.get("title")), g.get("start_date") or g.get("deadline") or _day_from_ts(g.get("updated_at")), f"{g.get('status')} {g.get('kind')}", g.get("updated_at"), g)

    if _match(cat, "milestones", {"milestone"}):
        try:
            from jarvis.health_product.milestones import discover_milestones

            discover_milestones(persist=True)
        except Exception:
            pass
        for m in store.list_table("milestones", limit=100):
            add("milestones", str(m.get("title")), m.get("day") or "", m.get("detail") or "", m.get("created_at"), m)

    if _match(cat, "recovery", {"recovery_events", "injury", "illness", "pt"}):
        for r in store.list_table("recovery_events", limit=200):
            add("recovery", str(r.get("title") or r.get("kind")), r.get("day") or "", f"{r.get('body_part') or ''} pain={r.get('pain') or '—'} {r.get('mobility') or ''}".strip(), r.get("created_at"), r)

    if _match(cat, "nutrition", {"nutrition_log", "meals", "food"}):
        for n in store.list_table("nutrition_log", order="created_at DESC", limit=200):
            add("nutrition", str(n.get("description") or n.get("kind")), n.get("day") or "", f"{n.get('meal_slot') or ''} {n.get('quantity') or ''} {n.get('units') or ''}".strip(), n.get("created_at"), n)

    if _match(cat, "preventive", {"preventive_care", "screening", "screenings"}):
        for p in store.list_table("preventive_care", limit=200):
            add(
                "preventive",
                str(p.get("name") or p.get("slug")),
                p.get("last_done") or p.get("next_due") or "",
                f"{p.get('status') or ''} next={p.get('next_due') or '—'}".strip(),
                p.get("updated_at"),
                p,
            )

    if _match(cat, "family_history", {"family", "hereditary"}):
        for f in store.list_table("family_history", limit=200):
            add(
                "family_history",
                f"{f.get('relation')}: {f.get('condition')}",
                f.get("day") or "",
                f"age={f.get('age_at_diagnosis') or '—'} {f.get('notes') or ''}".strip(),
                f.get("updated_at"),
                f,
            )

    items.sort(key=lambda x: (str(x.get("day") or ""), float(x.get("ts") or 0)), reverse=True)
    items = items[:limit]
    lines = ["**Lifetime Health Timeline**"]
    if cat:
        lines[0] += f" — {cat}"
    if not items:
        lines.append("Nothing recorded yet.")
    else:
        for it in items[:50]:
            lines.append(f"• {it['day']} [{it['source']}] {it['title']}" + (f" — {it['detail']}" if it.get("detail") else ""))
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "timeline",
        "items": items,
        "filters": FILTERS,
        "category": cat or "all",
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }
