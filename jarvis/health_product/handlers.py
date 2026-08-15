"""Chat actions — Health is authoritative; chat never invents medical facts."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.health_product import engine
from jarvis.health_product.terminology import DISCLAIMER


def _ok(payload: dict) -> dict:
    payload.setdefault("ok", True)
    payload.setdefault("disclaimer", DISCLAIMER)
    payload.setdefault("open_view", "health")
    payload.setdefault("module", "health")
    return payload


@register_action("health_home", module="health", description="Open Health home / PHR summary", info=True)
def health_home(_assistant, _params: dict, _message: str) -> dict:
    home = engine.home_payload()
    chk = home.get("checkin")
    meds = home.get("medications") or []
    lines = ["**Health** — Personal Health Record", ""]
    if chk:
        lines.append(f"Today's check-in is on file ({chk.get('day')}).")
    else:
        lines.append("No daily check-in yet today.")
    lines.append(f"Current medications: {len(meds)}.")
    pending = home.get("pending")
    if pending:
        lines.append(f"Pending confirmation: {pending.get('summary')}.")
    qs = home.get("doctor_questions") or []
    if qs:
        lines.append(f"Open questions for your doctor: {len(qs)}.")
    obs = home.get("observations") or []
    if obs:
        lines.append("")
        lines.append("**Observations** (not a diagnosis)")
        lines.extend(f"• {o}" for o in obs[:4])
    lines += ["", "_" + DISCLAIMER + "_"]
    return _ok({"message": "\n".join(lines), "data": home})


@register_action("health_log", module="health", description="Record a natural-language health update")
def health_log(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or params.get("message") or message or "").strip()
    return _ok(engine.ingest_message(text))


@register_action("health_confirm", module="health", description="Confirm or cancel a pending Health Record change")
def health_confirm(_assistant, params: dict, message: str) -> dict:
    raw = str(params.get("confirm") if "confirm" in params else message or "yes").strip().lower()
    yes = raw not in ("0", "false", "no", "nope", "cancel", "reject", "n")
    return _ok(engine.confirm_latest(yes))


@register_action("health_today", module="health", description="Today's daily health check-in", info=True)
def health_today(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.today_summary())


@register_action("health_medications", module="health", description="Current or past medications", info=True)
def health_medications(_assistant, params: dict, _message: str) -> dict:
    status = str(params.get("status") or "current")
    return _ok(engine.medications_summary(status=status))


@register_action("health_supplements", module="health", description="Current or past supplements", info=True)
def health_supplements(_assistant, params: dict, _message: str) -> dict:
    status = str(params.get("status") or "current")
    return _ok(engine.supplements_summary(status=status))


@register_action("health_labs", module="health", description="Laboratory results", info=True)
def health_labs(_assistant, params: dict, _message: str) -> dict:
    return _ok(engine.labs_summary(params.get("name")))


@register_action("health_graph", module="health", description="Graph a health metric", info=True)
def health_graph(_assistant, params: dict, message: str) -> dict:
    kind = str(params.get("kind") or params.get("query") or "weight")
    days = int(params.get("days") or 90)
    out = engine.graph_summary(kind, days=days)
    out["open_view"] = "health"
    return _ok(out)


@register_action("health_search", module="health", description="Search the Personal Health Record", info=True)
def health_search(_assistant, params: dict, message: str) -> dict:
    q = str(params.get("query") or params.get("q") or message or "").strip()
    return _ok(engine.search_summary(q))


@register_action("health_timeline", module="health", description="Chronological Health Timeline", info=True)
def health_timeline(_assistant, params: dict, _message: str) -> dict:
    from jarvis.health_product.timeline import build_timeline

    return _ok(build_timeline(category=str(params.get("category") or params.get("query") or "")))


@register_action("health_coach", module="health", description="Educational wellness coach from the local PHR", info=True)
def health_coach(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.coach import wellness_coach

    return _ok(wellness_coach())


@register_action("health_consult", module="health", description="Preview an optional AI health consultation")
def health_consult(_assistant, params: dict, message: str) -> dict:
    from jarvis.health_product.consult import preview_consultation

    question = str(params.get("question") or params.get("text") or message or "").strip()
    level = str(params.get("level") or "sanitized")
    include_docs = bool(params.get("include_docs")) or level in ("full", "3")
    return _ok(preview_consultation(question, level=level, include_docs=include_docs))


@register_action("health_consult_send", module="health", description="Send a previously previewed health consultation")
def health_consult_send(_assistant, params: dict, _message: str) -> dict:
    from jarvis.health_product.consult import latest_preview, run_consultation

    cid = str(params.get("consultation_id") or params.get("id") or "")
    prev = None
    if not cid:
        prev = latest_preview()
        cid = str((prev or {}).get("id") or "")
    else:
        from jarvis.health_product import store

        prev = store.get_by_id("consultations", cid)
    if not cid:
        return _ok({"message": "No consultation preview is waiting.\n\n_" + DISCLAIMER + "_"})
    if str((prev or {}).get("question") or "").startswith("[second-opinion]"):
        from jarvis.health_product.second_opinion import run_second_opinion

        return _ok(run_second_opinion(cid))
    return _ok(run_consultation(cid))


@register_action("health_consult_cancel", module="health", description="Cancel a previewed health consultation")
def health_consult_cancel(_assistant, params: dict, _message: str) -> dict:
    from jarvis.health_product.consult import cancel_consultation, latest_preview

    cid = str(params.get("consultation_id") or params.get("id") or "")
    if not cid:
        prev = latest_preview()
        cid = str((prev or {}).get("id") or "")
    if not cid:
        return _ok({"message": "No consultation preview is waiting.\n\n_" + DISCLAIMER + "_"})
    return _ok(cancel_consultation(cid))


@register_action("health_question", module="health", description="Save a question to ask the doctor")
def health_question(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or params.get("query") or message or "").strip()
    return _ok(engine.ingest_message(f"Remind me to ask my doctor about {text}" if not text.lower().startswith("remind") else text))


@register_action("health_reminders", module="health", description="Health reminders", info=True)
def health_reminders(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.reminders import reminder_message

    return _ok(reminder_message())


@register_action("health_export", module="health", description="Export the local Personal Health Record", info=True)
def health_export(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.export_summary())


@register_action("health_doctor_visit", module="health", description="Prepare doctor visit summary", info=True)
def health_doctor_visit(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.doctor_visit_summary())


@register_action("health_emergency", module="health", description="One-page emergency medical summary", info=True)
def health_emergency(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.emergency_summary())


@register_action("health_observations", module="health", description="Informational health observations", info=True)
def health_observations(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.observations_message())


@register_action("health_dashboard", module="health", description="Health dashboard summary", info=True)
def health_dashboard(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.dashboard import dashboard_payload

    return _ok(dashboard_payload())


@register_action("health_trends", module="health", description="Health trend observations", info=True)
def health_trends(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.trends import build_trends

    return _ok(build_trends())


@register_action("health_safety", module="health", description="Educational medication interaction hints", info=True)
def health_safety(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.safety import scan_interactions

    return _ok(scan_interactions())


@register_action("health_activity", module="health", description="Activity summary or log", info=True)
def health_activity(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or message or "").strip()
    if text and not re_is_query(text):
        return _ok(engine.ingest_message(text))
    from jarvis.health_product.workouts import activity_summary

    return _ok(activity_summary())


@register_action("health_workouts", module="health", description="Workout history and progression", info=True)
def health_workouts(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or message or "").strip()
    if text and not re_is_query(text):
        return _ok(engine.ingest_message(text))
    from jarvis.health_product.workouts import workout_summary

    return _ok(workout_summary())


@register_action("health_second_opinion", module="health", description="Preview a multi-model second opinion")
def health_second_opinion(_assistant, params: dict, message: str) -> dict:
    from jarvis.health_product.second_opinion import preview_second_opinion

    return _ok(preview_second_opinion(str(params.get("question") or message or ""), level=str(params.get("level") or "sanitized")))


@register_action("health_scorecard", module="health", description="Personal wellness scorecard (not medical)", info=True)
def health_scorecard(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.scorecard import build_scorecard

    return _ok(build_scorecard())


@register_action("health_milestones", module="health", description="Health milestones from recorded data", info=True)
def health_milestones(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.milestones import discover_milestones

    return _ok(discover_milestones(persist=True))


@register_action("health_adherence", module="health", description="Gentle medication adherence history", info=True)
def health_adherence(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.ingest_message("medication adherence"))


@register_action("health_last_visit", module="health", description="Last doctor visit history", info=True)
def health_last_visit(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.ingest_message("When was my last doctor visit?"))


@register_action("health_family_history", module="health", description="Family medical history summary", info=True)
def health_family_history(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or message or "").strip()
    if text and not re_is_query(text):
        return _ok(engine.ingest_message(text))
    return _ok(engine.ingest_message("What runs in my family?"))


@register_action("health_preventive", module="health", description="Preventive care due dates and history", info=True)
def health_preventive(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or params.get("query") or message or "").strip()
    if text and not re_is_query(text):
        return _ok(engine.ingest_message(text))
    return _ok(engine.ingest_message("Am I due for screenings?"))


@register_action("health_nutrition", module="health", description="Nutrition habit notes", info=True)
def health_nutrition(_assistant, params: dict, message: str) -> dict:
    text = str(params.get("text") or message or "").strip()
    if text and not re_is_query(text):
        return _ok(engine.ingest_message(text))
    from jarvis.health_product.nutrition import habits

    return _ok(habits())


@register_action("health_insights", module="health", description="Educational health pattern insights", info=True)
def health_insights(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.patterns import build_insights

    return _ok(build_insights())


@register_action("health_visit_prep", module="health", description="Doctor visit preparation packet", info=True)
def health_visit_prep(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.visit_prep import build_visit_prep

    return _ok(build_visit_prep())


@register_action("health_backup", module="health", description="Health backup history", info=True)
def health_backup(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.backup import history

    return _ok(history())


@register_action("health_restore", module="health", description="Health restore guidance", info=True)
def health_restore(_assistant, _params: dict, _message: str) -> dict:
    return _ok(engine.ingest_message("Restore my health backup"))


@register_action("health_integrity", module="health", description="Verify Health backup integrity", info=True)
def health_integrity(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.health_product.backup import integrity_report

    return _ok(integrity_report())


def re_is_query(text: str) -> bool:
    lower = text.lower()
    return lower.endswith("?") or lower.startswith(("how ", "have ", "did ", "what ", "show ", "last "))
