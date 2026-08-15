"""Printable Health reports — clean HTML for physicians and hospitals."""

from __future__ import annotations

import html
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.engine import bmi_for_profile, doctor_visit_summary, emergency_summary, observations
from jarvis.health_product.terminology import DISCLAIMER

_CSS = """
@page { margin: 0.7in; }
body { font-family: Georgia, "Times New Roman", serif; color: #111; font-size: 12pt; line-height: 1.35; }
h1 { font-size: 18pt; margin: 0 0 0.2rem; }
h2 { font-size: 13pt; border-bottom: 1px solid #333; margin: 1rem 0 0.4rem; }
h3 { font-size: 11pt; margin: 0.7rem 0 0.25rem; }
p, li { margin: 0.15rem 0; }
.meta { color: #444; font-size: 10pt; margin-bottom: 0.8rem; }
table { width: 100%; border-collapse: collapse; font-size: 10.5pt; margin: 0.3rem 0 0.8rem; }
th, td { text-align: left; border-bottom: 1px solid #ccc; padding: 0.22rem 0.35rem; vertical-align: top; }
th { font-weight: 700; }
.disclaimer { margin-top: 1.4rem; font-size: 9pt; color: #555; border-top: 1px solid #999; padding-top: 0.5rem; }
.small { font-size: 10pt; color: #444; }
"""


def _esc(v: Any) -> str:
    if v is None:
        return ""
    return html.escape(str(v))


def wrap_html(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<title>{_esc(title)}</title><style>{_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )


def _header(title: str) -> str:
    profile = store.get_profile()
    name = profile.get("name") or "Personal Health Record"
    dob = profile.get("dob") or ""
    bits = [f"<h1>{_esc(title)}</h1>", f"<p class='meta'>{_esc(name)}"]
    if dob:
        bits.append(f" · DOB {_esc(dob)}")
    bits.append(f" · Printed {date.today().isoformat()}</p>")
    return "".join(bits)


def _disclaimer() -> str:
    return f"<p class='disclaimer'>{_esc(DISCLAIMER)}</p>"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "<p class='small'>None recorded.</p>"
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def daily_report_html(day: str | None = None) -> str:
    day = day or date.today().isoformat()
    chk = store.get_checkin(day) or {}
    rows = []
    labels = [
        ("overall", "Overall (1–10)"),
        ("energy", "Energy"),
        ("mood", "Mood"),
        ("stress", "Stress"),
        ("pain", "Pain"),
        ("sleep_hours", "Hours slept"),
        ("sleep_quality", "Sleep quality"),
        ("weight", "Weight"),
        ("heart_rate", "Heart rate"),
        ("blood_sugar", "Blood sugar"),
        ("temperature", "Temperature"),
        ("spo2", "Pulse ox"),
        ("exercise", "Exercise"),
        ("water", "Water"),
        ("meals", "Meals"),
        ("alcohol", "Alcohol"),
        ("tobacco", "Tobacco"),
        ("symptoms", "Symptoms"),
        ("notes", "Notes"),
        ("comments", "Comments"),
    ]
    if chk.get("bp_systolic") is not None:
        rows.append(["Blood pressure", f"{chk.get('bp_systolic')}/{chk.get('bp_diastolic')}"])
    for key, label in labels:
        if chk.get(key) not in (None, ""):
            rows.append([label, chk.get(key)])
    body = _header(f"Daily Health Report — {day}") + _table(["Metric", "Value"], rows) + _disclaimer()
    return wrap_html(f"Daily Health — {day}", body)


def _range_days(kind: str, start: str | None, end: str | None) -> tuple[str, str]:
    end = end or date.today().isoformat()
    if start:
        return start, end
    days = {"week": 7, "month": 30, "3m": 90, "6m": 180, "year": 365, "all": 3650}.get(kind, 30)
    start = (date.fromisoformat(end) - timedelta(days=days)).isoformat()
    return start, end


def summary_html(*, kind: str = "week", start: str | None = None, end: str | None = None) -> str:
    start, end = _range_days(kind, start, end)
    checkins = [c for c in store.list_checkins(limit=400) if start <= str(c.get("day") or "") <= end]
    checkins.sort(key=lambda c: str(c.get("day") or ""))
    rows = []
    for c in checkins:
        bp = ""
        if c.get("bp_systolic") is not None:
            bp = f"{c.get('bp_systolic')}/{c.get('bp_diastolic')}"
        rows.append(
            [
                c.get("day"),
                c.get("overall"),
                c.get("energy"),
                c.get("mood"),
                c.get("pain"),
                c.get("sleep_hours"),
                c.get("weight"),
                bp,
                c.get("blood_sugar"),
                c.get("symptoms") or "",
            ]
        )
    obs = observations(limit=8)
    body = (
        _header(f"Health Summary — {start} to {end}")
        + _table(
            ["Date", "Overall", "Energy", "Mood", "Pain", "Sleep", "Weight", "BP", "Sugar", "Symptoms"],
            rows,
        )
        + "<h2>Observations</h2>"
        + (
            "<ul>" + "".join(f"<li>{_esc(o)}</li>" for o in obs) + "</ul>"
            if obs
            else "<p class='small'>No strong patterns in this window.</p>"
        )
        + _disclaimer()
    )
    return wrap_html(f"Health Summary {start}–{end}", body)


def medication_list_html(*, history: bool = False) -> str:
    where = "" if history else "status=?"
    args = () if history else ("current",)
    rows = store.list_table("medications", where, args, limit=200)
    table = _table(
        ["Name", "Strength", "Dose", "Frequency", "Purpose", "Physician", "Status", "Start", "Stop"],
        [
            [
                r.get("name"),
                r.get("strength"),
                r.get("dose"),
                r.get("frequency"),
                r.get("purpose"),
                r.get("physician"),
                r.get("status"),
                r.get("start_date"),
                r.get("stop_date"),
            ]
            for r in rows
        ],
    )
    title = "Medication History" if history else "Current Medications"
    return wrap_html(title, _header(title) + table + _disclaimer())


def supplement_list_html(*, history: bool = False) -> str:
    where = "" if history else "status=?"
    args = () if history else ("current",)
    rows = store.list_table("supplements", where, args, limit=200)
    table = _table(
        ["Name", "Dose", "Frequency", "Purpose", "Status", "Start", "Stop"],
        [
            [r.get("name"), r.get("dose"), r.get("frequency"), r.get("purpose"), r.get("status"), r.get("start_date"), r.get("stop_date")]
            for r in rows
        ],
    )
    title = "Supplement History" if history else "Current Supplements"
    return wrap_html(title, _header(title) + table + _disclaimer())


def vital_log_html(kind: str, *, start: str | None = None, end: str | None = None, window: str = "month") -> str:
    start, end = _range_days(window, start, end)
    rows = [v for v in store.list_vitals(kind=kind, since=start, limit=800) if str(v.get("day") or "") <= end]
    title = {
        "blood_pressure": "Blood Pressure Log",
        "blood_sugar": "Blood Sugar Log",
        "weight": "Weight Log",
        "sleep_hours": "Sleep Report",
        "heart_rate": "Heart Rate Log",
    }.get(kind, f"{kind.replace('_', ' ').title()} Log")
    bmi = bmi_for_profile() if kind == "weight" else None
    extra = f"<p class='small'>Latest calculated BMI: {bmi}</p>" if bmi is not None else ""
    table_rows = []
    for r in rows:
        val = r.get("value")
        if r.get("value2") is not None:
            val = f"{r.get('value')}/{r.get('value2')}"
        table_rows.append([r.get("day"), val, r.get("units") or "", r.get("notes") or ""])
    return wrap_html(title, _header(f"{title} — {start} to {end}") + extra + _table(["Date", "Value", "Units", "Notes"], table_rows) + _disclaimer())


def lab_report_html(name: str | None = None) -> str:
    rows = store.list_labs(name=name, limit=300)
    title = f"Lab Report — {name}" if name else "Laboratory Report"
    table = _table(
        ["Date", "Test", "Value", "Units", "Ref low", "Ref high", "Physician", "Notes"],
        [
            [r.get("day"), r.get("name"), r.get("value") if r.get("value") is not None else r.get("value_text"), r.get("units"), r.get("ref_low"), r.get("ref_high"), r.get("physician"), r.get("notes")]
            for r in rows
        ],
    )
    return wrap_html(title, _header(title) + table + _disclaimer())


def vaccination_report_html() -> str:
    rows = store.list_table("vaccinations", order="day DESC", limit=200)
    table = _table(
        ["Date", "Vaccine", "Dose", "Notes"],
        [[r.get("day"), r.get("name"), r.get("dose_number"), r.get("notes")] for r in rows],
    )
    return wrap_html("Vaccination Report", _header("Vaccination Report") + table + _disclaimer())


def doctor_visit_html() -> str:
    summary = doctor_visit_summary()
    body = _header("Doctor Visit Summary") + f"<pre style='white-space:pre-wrap;font-family:Georgia,serif'>{_esc(summary.get('message','').replace('**',''))}</pre>" + _disclaimer()
    return wrap_html("Doctor Visit Summary", body)


def visit_prep_html() -> str:
    from jarvis.health_product.visit_prep import build_visit_prep

    summary = build_visit_prep()
    body = _header("Doctor Visit Preparation") + f"<pre style='white-space:pre-wrap;font-family:Georgia,serif'>{_esc(summary.get('message','').replace('**',''))}</pre>" + _disclaimer()
    return wrap_html("Doctor Visit Preparation", body)


def emergency_html() -> str:
    summary = emergency_summary()
    body = _header("Emergency Medical Summary") + f"<pre style='white-space:pre-wrap;font-family:Georgia,serif'>{_esc(summary.get('message','').replace('**',''))}</pre>" + _disclaimer()
    return wrap_html("Emergency Medical Summary", body)


def report_html(kind: str, **kwargs: Any) -> str:
    k = (kind or "daily").lower().replace("-", "_")
    if k in ("daily", "today", "checkin"):
        return daily_report_html(kwargs.get("day"))
    if k in ("week", "weekly", "month", "monthly", "3m", "6m", "year", "all", "custom", "summary"):
        window = "week" if k in ("week", "weekly") else "month" if k in ("month", "monthly", "summary") else k
        if k == "custom":
            window = "all"
        return summary_html(kind=window, start=kwargs.get("start"), end=kwargs.get("end"))
    if k in ("meds", "medications", "current_meds"):
        return medication_list_html(history=False)
    if k in ("med_history", "medication_history"):
        return medication_list_html(history=True)
    if k in ("supps", "supplements"):
        return supplement_list_html(history=False)
    if k in ("supp_history", "supplement_history"):
        return supplement_list_html(history=True)
    if k in ("bp", "blood_pressure"):
        return vital_log_html("blood_pressure", start=kwargs.get("start"), end=kwargs.get("end"), window=kwargs.get("window") or "month")
    if k in ("sugar", "blood_sugar", "glucose"):
        return vital_log_html("blood_sugar", start=kwargs.get("start"), end=kwargs.get("end"), window=kwargs.get("window") or "month")
    if k in ("weight",):
        return vital_log_html("weight", start=kwargs.get("start"), end=kwargs.get("end"), window=kwargs.get("window") or "month")
    if k in ("sleep",):
        return vital_log_html("sleep_hours", start=kwargs.get("start"), end=kwargs.get("end"), window=kwargs.get("window") or "month")
    if k in ("labs", "lab", "laboratory"):
        return lab_report_html(kwargs.get("name"))
    if k in ("vax", "vaccination", "vaccinations"):
        return vaccination_report_html()
    if k in ("doctor", "doctor_visit", "appointment"):
        return doctor_visit_html()
    if k in ("visit_prep", "visit-prep", "visit_preparation"):
        return visit_prep_html()
    if k in ("emergency", "ice"):
        return emergency_html()
    return daily_report_html()
