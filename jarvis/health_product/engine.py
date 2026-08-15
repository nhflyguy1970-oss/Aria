"""Health engine — PHR operations, observations, doctor/emergency summaries."""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.parser import parse_health_utterance
from jarvis.health_product.terminology import BOUNDARIES, DISCLAIMER, MENTAL_MODEL, TERMINOLOGY
from jarvis.health_product.trust import HealthWriteBlocked, confirm_prompt, product_trust_payload

_KIND_ALIASES = {
    "pressure": "blood_pressure",
    "blood pressure": "blood_pressure",
    "bp": "blood_pressure",
    "sugar": "blood_sugar",
    "glucose": "blood_sugar",
    "sleep": "sleep_hours",
    "pulse": "heart_rate",
    "hr": "heart_rate",
    "o2": "spo2",
    "oxygen": "spo2",
}


def product_status() -> dict[str, Any]:
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "record": TERMINOLOGY["record"],
        "disclaimer": DISCLAIMER,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "local": True,
        "cloud": False,
        "privacy_default": "local_only",
        "trust": product_trust_payload(),
    }


def home_payload() -> dict[str, Any]:
    today = date.today().isoformat()
    checkin = store.get_checkin(today)
    meds = [m for m in store.list_table("medications", "status=?", ("current",), limit=50)]
    supps = [s for s in store.list_table("supplements", "status=?", ("current",), limit=50)]
    allergies = store.list_table("allergies", limit=40)
    conditions = store.list_table("conditions", "status=?", ("active",), limit=40)
    recent_vitals = store.list_vitals(since=(date.today() - timedelta(days=14)).isoformat(), limit=200)
    latest: dict[str, Any] = {}
    for v in reversed(recent_vitals):
        latest.setdefault(v["kind"], v)
    return {
        "ok": True,
        "product": "Health",
        "disclaimer": DISCLAIMER,
        "today": today,
        "checkin": checkin,
        "profile": store.get_profile(),
        "medications": meds,
        "supplements": supps,
        "allergies": allergies,
        "conditions": conditions,
        "latest_vitals": latest,
        "observations": observations(limit=6),
        "reminders": store.list_table("reminders", "enabled=?", (1,), limit=20),
        "doctor_questions": store.list_table("doctor_questions", "status=?", ("open",), order="created_at DESC", limit=30),
        "vaccinations": store.list_table("vaccinations", order="day DESC", limit=40),
        "pending": store.latest_pending(),
        "consultations": store.list_table("consultations", order="created_at DESC", limit=20),
        "trust": product_trust_payload(),
    }


def _apply_medication(med: dict[str, Any]) -> str:
    existing = store.find_medication(med["name"])
    rec = dict(existing or {})
    rec.update({k: val for k, val in med.items() if k != "action" and val not in (None, "")})
    rec["name"] = med["name"]
    if med.get("action") == "stop":
        rec["status"] = "stopped"
        rec["stop_date"] = rec.get("stop_date") or date.today().isoformat()
    elif med.get("action") == "pause":
        rec["status"] = "paused"
    else:
        rec["status"] = med.get("status") or "current"
        rec.setdefault("start_date", date.today().isoformat())
    store.upsert_medication(rec)
    return f"medication {rec['name']} → {rec['status']}"


def _apply_condition(cond: dict[str, Any]) -> str:
    store.upsert_condition(cond)
    return f"condition {cond.get('name')} saved"


def _apply_allergy(allergy: dict[str, Any]) -> str:
    store.upsert_allergy(allergy)
    return f"allergy {allergy.get('name')} saved"


def apply_parsed(parsed: dict[str, Any], *, confirm: bool = False) -> dict[str, Any]:
    applied: list[str] = []
    pending: list[dict[str, Any]] = []
    checkin_bits = dict(parsed.get("checkin") or {})
    for v in parsed.get("vitals") or []:
        store.add_vital(v["kind"], v.get("value"), value2=v.get("value2"), units=v.get("units") or "", notes=v.get("notes") or "")
        applied.append(f"{v['kind']} recorded")
    for lab in parsed.get("labs") or []:
        store.add_lab(lab)
        applied.append(f"lab {lab['name']} recorded")
    for med in parsed.get("medications") or []:
        summary = f"you {med.get('action') or 'updated'} {med.get('name')}"
        if not confirm:
            rec = store.add_pending_mutation("medication", summary, {"medications": [med]})
            pending.append(rec)
        else:
            applied.append(_apply_medication(med))
    for supp in parsed.get("supplements") or []:
        existing = store.find_supplement(supp["name"])
        rec = dict(existing or {})
        rec.update({k: val for k, val in supp.items() if k != "action" and val not in (None, "")})
        rec["name"] = supp["name"]
        if supp.get("action") == "stop":
            rec["status"] = "stopped"
            rec["stop_date"] = date.today().isoformat()
        else:
            rec["status"] = supp.get("status") or "current"
            rec.setdefault("start_date", date.today().isoformat())
        store.upsert_supplement(rec)
        applied.append(f"supplement {rec['name']} → {rec['status']}")
    for cond in parsed.get("conditions") or []:
        summary = f"add condition {cond.get('name')}"
        if not confirm:
            rec = store.add_pending_mutation("condition", summary, {"conditions": [cond]})
            pending.append(rec)
        else:
            applied.append(_apply_condition(cond))
    for allergy in parsed.get("allergies") or []:
        summary = f"add allergy {allergy.get('name')}"
        if not confirm:
            rec = store.add_pending_mutation("allergy", summary, {"allergies": [allergy]})
            pending.append(rec)
        else:
            applied.append(_apply_allergy(allergy))
    for vax in parsed.get("vaccinations") or []:
        summary = f"add vaccination {vax.get('name')}"
        if not confirm:
            rec = store.add_pending_mutation("vaccination", summary, {"vaccinations": [vax]})
            pending.append(rec)
        else:
            store.upsert_vaccination(vax)
            applied.append(f"vaccination {vax.get('name')} saved")
    for miss in parsed.get("missed_doses") or []:
        store.add_missed_dose(miss.get("name") or "medication", kind=miss.get("kind") or "medication", notes=miss.get("notes") or "")
        applied.append(f"missed dose noted: {miss.get('name')}")
    for taken in parsed.get("taken_doses") or []:
        store.log_dose(taken.get("name") or "medication", status="taken", kind=taken.get("kind") or "medication", notes=taken.get("notes") or "")
        applied.append(f"dose taken: {taken.get('name')}")
    for rec in parsed.get("recovery") or []:
        store.add_recovery(rec)
        applied.append(f"recovery noted: {rec.get('title') or rec.get('kind')}")
    for act in parsed.get("activities") or []:
        if act.get("calories") in (None, "") and act.get("duration_min"):
            from jarvis.health_product.workouts import estimate_calories

            act["calories"] = estimate_calories(act.get("kind") or "custom", act.get("duration_min"), act.get("intensity") or "")
        store.add_activity(act)
        applied.append(f"activity {act.get('kind')} recorded")
        checkin_bits.setdefault("exercise", act.get("title") or act.get("kind"))
    for wo in parsed.get("workouts") or []:
        store.add_workout(wo, wo.get("sets"))
        applied.append(f"workout {wo.get('title') or wo.get('template')} recorded")
        checkin_bits.setdefault("exercise", wo.get("title") or "workout")
    for j in parsed.get("journal") or []:
        store.add_health_journal(j.get("body") or "", mood=j.get("mood") or "")
        applied.append("health journal entry saved")
    for g in parsed.get("goals") or []:
        store.upsert_goal({"title": g.get("title") or "Goal", "kind": g.get("kind") or "custom", "status": "active"})
        applied.append(f"goal saved: {g.get('title')}")
    for q in parsed.get("doctor_questions") or []:
        store.add_doctor_question(q if isinstance(q, str) else str(q.get("text") or ""))
        applied.append("doctor question saved")
    for sym in parsed.get("symptoms") or []:
        store.add_symptom(sym)
        applied.append(f"symptom {sym['name']} noted")
        checkin_bits.setdefault("symptoms", sym["name"])
    if parsed.get("nutrition"):
        from jarvis.health_product.nutrition import log_entries

        saved = log_entries(parsed["nutrition"], provenance="chat_nl")
        for s in saved:
            applied.append(f"nutrition logged: {s.get('description') or s.get('kind')}")
    for fh in parsed.get("family_history") or []:
        summary = f"add family history: {fh.get('relation')} — {fh.get('condition')}"
        if not confirm:
            rec = store.add_pending_mutation("family_history", summary, {"family_history": [fh]})
            pending.append(rec)
        else:
            from jarvis.health_product.family_history import save_entry

            save_entry(fh, provenance="chat_nl", confirmed=True)
            applied.append(f"family history saved: {fh.get('relation')} — {fh.get('condition')}")
    for prev in parsed.get("preventive") or []:
        from jarvis.health_product.preventive import complete, save

        if prev.get("action") == "complete" and prev.get("id"):
            complete(str(prev["id"]), day=prev.get("last_done"))
            applied.append(f"preventive care completed: {prev.get('name') or prev.get('slug')}")
        else:
            rec = save(prev, provenance="chat_nl")
            if prev.get("action") == "complete" and rec.get("id"):
                complete(str(rec["id"]), day=prev.get("last_done"))
            applied.append(f"preventive care saved: {rec.get('name') or prev.get('slug') or prev.get('name')}")
    if checkin_bits:
        merged = store.upsert_checkin(checkin_bits)
        applied.append(f"daily check-in updated for {merged.get('day')}")
    out: dict[str, Any] = {"ok": True, "applied": applied, "disclaimer": DISCLAIMER, "pending": pending}
    if pending:
        first = pending[0]
        out["confirm_required"] = True
        out["confirm_id"] = first["id"]
        out["message"] = confirm_prompt(first["kind"], first["summary"])
        if applied:
            out["message"] = "Recorded lower-trust updates, and held highest-trust changes for confirmation:\n\n" + "\n".join(f"• {a}" for a in applied) + "\n\n" + out["message"]
        return out
    out["message"] = _format_applied(applied)
    return out


def confirm_latest(confirm: bool = True) -> dict[str, Any]:
    try:
        return _confirm_latest(confirm)
    except HealthWriteBlocked as exc:
        return {
            "ok": False,
            "write_blocked": True,
            "message": f"{exc}\n\n_{DISCLAIMER}_",
            "disclaimer": DISCLAIMER,
        }


def _confirm_latest(confirm: bool = True) -> dict[str, Any]:
    pending = store.latest_pending()
    if not pending:
        return {"ok": True, "message": "No Health change is waiting for confirmation.\n\n_" + DISCLAIMER + "_", "disclaimer": DISCLAIMER}
    if not confirm:
        store.set_pending_status(pending["id"], "cancelled")
        return {"ok": True, "message": "Cancelled. Your Health Record was not changed.\n\n_" + DISCLAIMER + "_", "disclaimer": DISCLAIMER}
    payload = pending.get("payload_obj") or {}
    result = apply_parsed(payload, confirm=True)
    store.set_pending_status(pending["id"], "confirmed")
    result["intent"] = "confirm"
    result["confirmed_id"] = pending["id"]
    return result


def ingest_message(message: str) -> dict[str, Any]:
    try:
        return _ingest_message(message)
    except HealthWriteBlocked as exc:
        return {
            "ok": False,
            "write_blocked": True,
            "message": f"{exc}\n\n_{DISCLAIMER}_",
            "disclaimer": DISCLAIMER,
        }


def _ingest_message(message: str) -> dict[str, Any]:
    parsed = parse_health_utterance(message)
    intent = parsed.get("intent")
    if intent == "confirm":
        return confirm_latest(True)
    if intent == "reject":
        return confirm_latest(False)
    if intent == "doctor_question":
        q = parsed.get("query") or message
        store.add_doctor_question(q)
        return {
            "ok": True,
            "intent": "doctor_question",
            "message": f"Saved a question for your doctor: {q}\n\n_{DISCLAIMER}_",
            "disclaimer": DISCLAIMER,
            "open_view": "health",
        }
    if intent == "timeline":
        from jarvis.health_product.timeline import build_timeline

        return build_timeline(category=str(parsed.get("query") or ""))
    if intent == "coach":
        from jarvis.health_product.coach import wellness_coach

        return wellness_coach()
    if intent == "dashboard":
        from jarvis.health_product.dashboard import dashboard_payload

        return dashboard_payload()
    if intent == "scorecard":
        from jarvis.health_product.scorecard import build_scorecard

        return build_scorecard()
    if intent == "milestones":
        from jarvis.health_product.milestones import discover_milestones

        return discover_milestones(persist=True)
    if intent == "adherence":
        from jarvis.health_product.dashboard import medication_adherence
        from jarvis.health_product.terminology import DISCLAIMER as _D

        adh = medication_adherence(days=7)
        lines = ["**Medication adherence** (gentle history — not a judgment)", ""]
        lines.append(adh.get("explain") or "No adherence data yet.")
        if adh.get("taken_today"):
            lines.append("Taken today: " + ", ".join(str(x.get("name")) for x in adh["taken_today"][:8]))
        if adh.get("missed_today"):
            lines.append("Missed today: " + ", ".join(str(x.get("name")) for x in adh["missed_today"][:8]))
        if adh.get("due_today"):
            lines.append("Still to log today: " + ", ".join(str(x) for x in adh["due_today"][:8]))
        if adh.get("weekly_pct") is not None:
            lines.append(f"Weekly estimate: {adh['weekly_pct']}%")
        if adh.get("monthly_pct") is not None:
            lines.append(f"Monthly estimate: {adh['monthly_pct']}%")
        lines += ["", "_" + _D + "_"]
        return {"ok": True, "intent": "adherence", **adh, "message": "\n".join(lines), "disclaimer": _D}
    if intent == "last_visit":
        visits = store.list_table("visits", order="day DESC", limit=5)
        lines = ["**Doctor appointment history**", ""]
        if not visits:
            lines.append("No doctor visits recorded yet. Log them in Health → Providers / Visits.")
        else:
            for v in visits:
                lines.append(
                    f"• {v.get('day')}: {v.get('title') or v.get('reason') or 'Visit'} — {v.get('physician') or ''}"
                )
                if v.get("summary"):
                    lines.append(f"  Summary: {v['summary']}")
                if v.get("next_appointment"):
                    lines.append(f"  Next: {v['next_appointment']}")
        lines += ["", "_" + DISCLAIMER + "_"]
        return {"ok": True, "intent": "last_visit", "visits": visits, "message": "\n".join(lines), "disclaimer": DISCLAIMER}
    if intent == "trends":
        from jarvis.health_product.trends import build_trends

        return build_trends()
    if intent == "safety":
        from jarvis.health_product.safety import scan_interactions

        return scan_interactions()
    if intent == "activity":
        from jarvis.health_product.workouts import activity_summary

        return activity_summary()
    if intent == "workouts":
        from jarvis.health_product.workouts import workout_summary

        return workout_summary()
    if intent == "second_opinion":
        from jarvis.health_product.second_opinion import preview_second_opinion

        return preview_second_opinion(parsed.get("query") or message, level=str(parsed.get("level") or "sanitized"))
    if intent == "consult":
        from jarvis.health_product.consult import preview_consultation

        level = str(parsed.get("level") or "sanitized")
        return preview_consultation(parsed.get("query") or message, level=level, include_docs=level == "full")
    if intent == "consult_send":
        from jarvis.health_product.consult import latest_preview, run_consultation

        prev = latest_preview()
        if not prev:
            return {"ok": True, "message": "No consultation preview is waiting.\n\n_" + DISCLAIMER + "_", "disclaimer": DISCLAIMER}
        if str(prev.get("question") or "").startswith("[second-opinion]"):
            from jarvis.health_product.second_opinion import run_second_opinion

            return run_second_opinion(prev["id"])
        return run_consultation(prev["id"])
    if intent == "consult_cancel":
        from jarvis.health_product.consult import cancel_consultation, latest_preview

        prev = latest_preview()
        if not prev:
            return {"ok": True, "message": "No consultation preview is waiting.\n\n_" + DISCLAIMER + "_", "disclaimer": DISCLAIMER}
        return cancel_consultation(prev["id"])
    if intent == "export":
        return export_summary()
    if intent == "reminders":
        from jarvis.health_product.reminders import reminder_message

        return reminder_message()
    if intent == "doctor_visit":
        return doctor_visit_summary()
    if intent == "visit_prep":
        from jarvis.health_product.visit_prep import build_visit_prep

        return build_visit_prep()
    if intent == "family_history":
        from jarvis.health_product.family_history import family_summary

        q = str(parsed.get("query") or "").strip().lower()
        summary = family_summary()
        if q:
            hits = [e for e in summary.get("entries") or [] if q in str(e.get("condition") or "").lower()]
            if hits:
                lines = [f"**Family history — “{parsed.get('query')}”**", ""]
                lines.extend(f"• {h.get('relation')}: {h.get('condition')}" for h in hits)
                lines += ["", "_" + DISCLAIMER + "_"]
                summary = {**summary, "matches": hits, "message": "\n".join(lines)}
            else:
                summary = {
                    **summary,
                    "message": (
                        f"No recorded family history entry matches “{parsed.get('query')}”. "
                        f"I will not invent one.\n\n_{DISCLAIMER}_"
                    ),
                }
        return summary
    if intent == "preventive":
        from jarvis.health_product.preventive import answer_last, list_due

        q = str(parsed.get("query") or "").strip().lower()
        if q == "due" or "due for" in (message or "").lower():
            return list_due(include_catalog=True)
        if q:
            return answer_last(q)
        return list_due()
    if intent == "nutrition":
        from jarvis.health_product.nutrition import habits

        return habits()
    if intent == "insights":
        from jarvis.health_product.patterns import build_insights

        return build_insights()
    if intent == "backup":
        from jarvis.health_product.backup import history

        return history()
    if intent == "restore":
        return {
            "ok": True,
            "intent": "restore",
            "message": (
                "Health restore requires an encrypted backup file and password in Health → Backups. "
                "Preview first, then confirm explicitly.\n\n_" + DISCLAIMER + "_"
            ),
            "disclaimer": DISCLAIMER,
            "open_view": "health",
        }
    if intent == "integrity":
        from jarvis.health_product.backup import integrity_report

        return integrity_report()
    if intent == "emergency":
        return emergency_summary()
    if intent == "medications":
        return medications_summary()
    if intent == "supplements":
        return supplements_summary()
    if intent == "today":
        return today_summary()
    if intent == "labs":
        return labs_summary(parsed.get("query"))
    if intent == "graph":
        return graph_summary(parsed.get("query") or "weight")
    if intent == "search":
        return search_summary(parsed.get("query") or message)
    if intent == "log" or (
        parsed.get("vitals")
        or parsed.get("checkin")
        or parsed.get("medications")
        or parsed.get("supplements")
        or parsed.get("symptoms")
        or parsed.get("labs")
        or parsed.get("conditions")
        or parsed.get("allergies")
        or parsed.get("missed_doses")
        or parsed.get("taken_doses")
        or parsed.get("recovery")
        or parsed.get("vaccinations")
        or parsed.get("doctor_questions")
        or parsed.get("activities")
        or parsed.get("workouts")
        or parsed.get("journal")
        or parsed.get("goals")
        or parsed.get("family_history")
        or parsed.get("preventive")
        or parsed.get("nutrition")
    ):
        result = apply_parsed(parsed)
        result["intent"] = "log"
        if not result.get("message"):
            result["message"] = _format_applied(result.get("applied") or [])
        return result
    return search_summary(message)


def export_summary() -> dict[str, Any]:
    bundle = store.export_bundle()
    return {
        "ok": True,
        "intent": "export",
        "bundle": bundle,
        "message": "Health export is ready (local JSON). Open Health → Print / Export to download.\n\n_" + DISCLAIMER + "_",
        "disclaimer": DISCLAIMER,
        "open_view": "health",
    }


def _format_applied(applied: list[str]) -> str:
    if not applied:
        return "I didn't find a health update to record.\n\n_" + DISCLAIMER + "_"
    lines = ["Updated your Health record:"] + [f"• {a}" for a in applied]
    lines.append("")
    lines.append("_" + DISCLAIMER + "_")
    return "\n".join(lines)


def today_summary() -> dict[str, Any]:
    day = date.today().isoformat()
    chk = store.get_checkin(day)
    if not chk:
        return {
            "ok": True,
            "intent": "today",
            "message": f"No daily health check-in for {day} yet.\n\n_{DISCLAIMER}_",
            "checkin": None,
            "disclaimer": DISCLAIMER,
        }
    lines = [f"**Daily health — {day}**"]
    for key in (
        "overall",
        "energy",
        "mood",
        "stress",
        "pain",
        "sleep_hours",
        "sleep_quality",
        "weight",
        "bp_systolic",
        "bp_diastolic",
        "heart_rate",
        "blood_sugar",
        "temperature",
        "spo2",
        "exercise",
        "water",
        "meals",
        "alcohol",
        "tobacco",
        "symptoms",
        "notes",
    ):
        if chk.get(key) not in (None, ""):
            label = key.replace("_", " ")
            if key == "bp_systolic" and chk.get("bp_diastolic") is not None:
                continue
            if key == "bp_diastolic" and chk.get("bp_systolic") is not None:
                lines.append(f"• Blood pressure: {chk['bp_systolic']}/{chk['bp_diastolic']}")
                continue
            lines.append(f"• {label.title()}: {chk[key]}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "today", "message": "\n".join(lines), "checkin": chk, "disclaimer": DISCLAIMER}


def medications_summary(status: str = "current") -> dict[str, Any]:
    rows = store.list_table("medications", "status=?" if status else "", (status,) if status else (), limit=80)
    if not rows:
        return {
            "ok": True,
            "intent": "medications",
            "message": f"No {status} medications in Health.\n\n_{DISCLAIMER}_",
            "medications": [],
            "disclaimer": DISCLAIMER,
        }
    lines = [f"**{status.title()} medications**"]
    for m in rows:
        bits = [m.get("name") or ""]
        if m.get("strength"):
            bits.append(str(m["strength"]))
        if m.get("dose"):
            bits.append(str(m["dose"]))
        if m.get("frequency"):
            bits.append(str(m["frequency"]))
        if m.get("purpose"):
            bits.append(f"— {m['purpose']}")
        lines.append("• " + " ".join(bits))
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "medications", "message": "\n".join(lines), "medications": rows, "disclaimer": DISCLAIMER}


def supplements_summary(status: str = "current") -> dict[str, Any]:
    rows = store.list_table("supplements", "status=?" if status else "", (status,) if status else (), limit=80)
    if not rows:
        return {
            "ok": True,
            "intent": "supplements",
            "message": f"No {status} supplements in Health.\n\n_{DISCLAIMER}_",
            "supplements": [],
            "disclaimer": DISCLAIMER,
        }
    lines = [f"**{status.title()} supplements**"]
    for s in rows:
        bits = [s.get("name") or ""]
        if s.get("dose"):
            bits.append(str(s["dose"]))
        if s.get("frequency"):
            bits.append(str(s["frequency"]))
        lines.append("• " + " ".join(bits))
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "supplements", "message": "\n".join(lines), "supplements": rows, "disclaimer": DISCLAIMER}


def labs_summary(name: str | None = None) -> dict[str, Any]:
    rows = store.list_labs(name=name, limit=40)
    if not rows:
        return {
            "ok": True,
            "intent": "labs",
            "message": "No laboratory results saved in Health yet.\n\n_" + DISCLAIMER + "_",
            "labs": [],
            "disclaimer": DISCLAIMER,
        }
    # latest per name
    latest: dict[str, dict] = {}
    for r in rows:
        latest[str(r.get("name"))] = r
    lines = ["**Latest lab values**"]
    for r in latest.values():
        val = r.get("value") if r.get("value") is not None else r.get("value_text")
        unit = r.get("units") or ""
        lines.append(f"• {r.get('name')} ({r.get('day')}): {val} {unit}".strip())
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "labs", "message": "\n".join(lines), "labs": rows, "disclaimer": DISCLAIMER}


def _normalize_kind(kind: str) -> str:
    k = (kind or "").strip().lower()
    return _KIND_ALIASES.get(k, k.replace(" ", "_"))


def graph_summary(kind: str, days: int = 90) -> dict[str, Any]:
    kind = _normalize_kind(kind)
    since = (date.today() - timedelta(days=max(7, days))).isoformat()
    if kind in ("a1c", "cholesterol", "hdl", "ldl", "triglycerides", "vitamin_d", "vitamin d"):
        lab_name = {
            "a1c": "A1C",
            "cholesterol": "Cholesterol",
            "hdl": "HDL",
            "ldl": "LDL",
            "triglycerides": "Triglycerides",
            "vitamin_d": "Vitamin D",
            "vitamin d": "Vitamin D",
        }.get(kind, kind)
        rows = store.list_labs(name=lab_name, since=since, limit=200)
        series = [{"day": r["day"], "value": r.get("value"), "label": lab_name} for r in rows if r.get("value") is not None]
        title = lab_name
    else:
        rows = store.list_vitals(kind=kind, since=since, limit=400)
        series = []
        for r in rows:
            if kind == "blood_pressure":
                series.append({"day": r["day"], "value": r.get("value"), "value2": r.get("value2"), "label": "BP"})
            elif r.get("value") is not None:
                series.append({"day": r["day"], "value": r.get("value"), "label": kind})
        title = kind.replace("_", " ")
    if not series:
        return {
            "ok": True,
            "intent": "graph",
            "kind": kind,
            "series": [],
            "message": f"No {title} history in Health yet.\n\n_{DISCLAIMER}_",
            "disclaimer": DISCLAIMER,
        }
    vals = [float(p["value"]) for p in series if p.get("value") is not None]
    trend = ""
    if len(vals) >= 2:
        delta = vals[-1] - vals[0]
        if abs(delta) < 1e-6:
            trend = "flat"
        elif delta > 0:
            trend = f"up {delta:.1f} from first to last reading"
        else:
            trend = f"down {abs(delta):.1f} from first to last reading"
    last = series[-1]
    last_txt = str(last.get("value"))
    if last.get("value2") is not None:
        last_txt = f"{last.get('value')}/{last.get('value2')}"
    lines = [
        f"**{title.title()} — last {days} days**",
        f"• Readings: {len(series)}",
        f"• Latest ({last.get('day')}): {last_txt}",
    ]
    if vals:
        lines.append(f"• Range: {min(vals):.1f} – {max(vals):.1f}")
    if trend:
        lines.append(f"• Observation: {trend}.")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "graph",
        "kind": kind,
        "series": series,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }


def search_summary(query: str) -> dict[str, Any]:
    hits = store.search_all(query, limit=20)
    if not hits:
        return {
            "ok": True,
            "intent": "search",
            "message": f"Nothing in Health matched “{query}”.\n\n_{DISCLAIMER}_",
            "hits": [],
            "disclaimer": DISCLAIMER,
        }
    lines = [f"**Health search — {query}**"]
    for h in hits[:12]:
        rec = h.get("record") or {}
        extra = rec.get("status") or rec.get("day") or rec.get("kind") or ""
        lines.append(f"• [{h.get('source')}] {h.get('title')} {extra}".strip())
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "search", "message": "\n".join(lines), "hits": hits, "disclaimer": DISCLAIMER}


def observations(limit: int = 8) -> list[str]:
    """Informational patterns only — never diagnoses."""
    notes: list[str] = []
    since = (date.today() - timedelta(days=90)).isoformat()
    checkins = store.list_checkins(limit=90, since=since)
    if len(checkins) >= 5:
        sleep_bp: list[tuple[float, float]] = []
        for c in checkins:
            sh = c.get("sleep_hours")
            sys = c.get("bp_systolic")
            if sh is not None and sys is not None:
                try:
                    sleep_bp.append((float(sh), float(sys)))
                except Exception:
                    pass
        if len(sleep_bp) >= 6:
            low = [bp for s, bp in sleep_bp if s < 6.5]
            high = [bp for s, bp in sleep_bp if s >= 7]
            if low and high and statistics.mean(low) > statistics.mean(high) + 3:
                notes.append(
                    "Observation: systolic pressure readings tend to be higher on days with under 6.5 hours of sleep."
                )
        sugars_wd: list[float] = []
        sugars_we: list[float] = []
        for c in checkins:
            sg = c.get("blood_sugar")
            if sg is None:
                continue
            try:
                d = date.fromisoformat(str(c.get("day")))
            except Exception:
                continue
            (sugars_we if d.weekday() >= 5 else sugars_wd).append(float(sg))
        if len(sugars_wd) >= 4 and len(sugars_we) >= 2 and statistics.mean(sugars_we) > statistics.mean(sugars_wd) + 8:
            notes.append("Observation: blood sugar readings tend to run higher on weekends than weekdays.")
        pains = []
        moods = []
        for c in checkins:
            if c.get("pain") is not None:
                try:
                    pains.append(float(c["pain"]))
                except Exception:
                    pass
            if c.get("mood") is not None:
                try:
                    moods.append(float(c["mood"]))
                except Exception:
                    pass
        if len(pains) >= 6 and pains[-1] > statistics.mean(pains[:-1]) + 1.5:
            notes.append("Observation: recent pain scores are higher than the prior average.")
        if len(moods) >= 6 and moods[-1] < statistics.mean(moods[:-1]) - 1.5:
            notes.append("Observation: recent mood scores are lower than the prior average.")
        weights = []
        for c in reversed(checkins):
            if c.get("weight") is not None:
                try:
                    weights.append(float(c["weight"]))
                except Exception:
                    pass
        if len(weights) >= 4 and weights[-1] < weights[0] - 2:
            notes.append("Observation: recorded weight has declined over the recent check-in window.")
        elif len(weights) >= 4 and weights[-1] > weights[0] + 2:
            notes.append("Observation: recorded weight has increased over the recent check-in window.")
        sleep_vals = [float(c["sleep_hours"]) for c in checkins if c.get("sleep_hours") is not None]
        if len(sleep_vals) >= 5 and statistics.mean(sleep_vals[:3]) < 6 and statistics.mean(sleep_vals) < 6.5:
            notes.append("Observation: recent sleep duration has been consistently under 6.5 hours.")
    bp = store.list_vitals(kind="blood_pressure", since=since, limit=60)
    if len(bp) >= 4:
        sys_vals = [float(v["value"]) for v in bp if v.get("value") is not None]
        if len(sys_vals) >= 4 and sys_vals[-1] > sys_vals[0] + 8:
            notes.append("Observation: systolic blood pressure readings have been climbing over the saved series.")
    sugar = store.list_vitals(kind="blood_sugar", since=since, limit=60)
    if len(sugar) >= 4:
        vals = [float(v["value"]) for v in sugar if v.get("value") is not None]
        if len(vals) >= 4 and vals[-1] > vals[0] + 15:
            notes.append("Observation: blood sugar readings have been rising over the saved series.")
    return notes[:limit]


def observations_message() -> dict[str, Any]:
    notes = observations()
    if not notes:
        msg = "No strong patterns in the recorded Health data yet.\n\n_" + DISCLAIMER + "_"
    else:
        msg = "**Health observations** (not a diagnosis)\n\n" + "\n".join(f"• {n}" for n in notes) + "\n\n_" + DISCLAIMER + "_"
    return {"ok": True, "intent": "observations", "message": msg, "observations": notes, "disclaimer": DISCLAIMER}


def doctor_visit_summary() -> dict[str, Any]:
    from jarvis.health_product.visit_prep import build_visit_prep

    result = build_visit_prep()
    result["intent"] = "doctor_visit"
    result["report"] = "doctor_visit"
    return result


def emergency_summary() -> dict[str, Any]:
    profile = store.get_profile()
    meds = store.list_table("medications", "status=?", ("current",), limit=40)
    supps = store.list_table("supplements", "status=?", ("current",), limit=40)
    allergies = store.list_table("allergies", limit=40)
    conditions = store.list_table("conditions", "status=?", ("active",), limit=40)
    lines = ["**Emergency medical summary**", ""]
    lines.append(f"• Name: {profile.get('name') or '—'}")
    lines.append(f"• Date of birth: {profile.get('dob') or '—'}")
    lines.append(f"• Blood type: {profile.get('blood_type') or '—'}")
    lines.append(f"• Primary physician: {profile.get('primary_physician') or '—'}")
    lines.append(f"• Emergency contacts: {profile.get('emergency_contacts') or '—'}")
    if profile.get("insurance"):
        lines.append(f"• Insurance: {profile.get('insurance')}")
    lines.append("")
    lines.append("**Conditions**")
    lines.extend(f"• {c.get('name')}" for c in conditions) if conditions else lines.append("• None recorded")
    lines.append("")
    lines.append("**Allergies**")
    if allergies:
        lines.extend(f"• {a.get('kind')}: {a.get('name')} ({a.get('reaction') or 'reaction not recorded'})" for a in allergies)
    else:
        lines.append("• None recorded")
    lines.append("")
    lines.append("**Current medications**")
    if meds:
        lines.extend(f"• {m.get('name')} {m.get('strength') or ''} {m.get('dose') or ''} {m.get('frequency') or ''}".strip() for m in meds)
    else:
        lines.append("• None recorded")
    lines.append("")
    lines.append("**Current supplements**")
    if supps:
        lines.extend(f"• {s.get('name')} {s.get('dose') or ''}".strip() for s in supps)
    else:
        lines.append("• None recorded")
    if profile.get("emergency_notes"):
        lines += ["", f"**Notes:** {profile.get('emergency_notes')}"]
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "emergency",
        "message": "\n".join(lines),
        "open_view": "health",
        "disclaimer": DISCLAIMER,
        "report": "emergency",
    }


def bmi_for_profile(weight_lb: float | None = None) -> float | None:
    profile = store.get_profile()
    height_in = profile.get("height_in") or profile.get("height_inches")
    w = weight_lb
    if w is None:
        latest = store.list_vitals(kind="weight", limit=5)
        if latest:
            w = latest[-1].get("value")
    try:
        if not height_in or not w:
            return None
        return round(703.0 * float(w) / (float(height_in) ** 2), 1)
    except Exception:
        return None
