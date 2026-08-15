"""Optional external AI consultation — Health stays local; cloud is consultant only."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_REDACT_PROFILE = {
    "name",
    "dob",
    "emergency_contacts",
    "insurance",
    "primary_physician",
    "specialists",
    "address",
    "phone",
    "email",
    "emergency_notes",
}


def _vitals_series(kind: str, days: int = 180) -> list[dict[str, Any]]:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = store.list_vitals(kind=kind, since=since, limit=400)
    out = []
    for r in rows:
        out.append({"day": r.get("day"), "value": r.get("value"), "value2": r.get("value2"), "units": r.get("units")})
    return out


def build_shared_payload(level: str, *, include_docs: bool = False) -> dict[str, Any]:
    level = (level or "sanitized").lower()
    if level in ("1", "local", "local_only"):
        level = "local_only"
    elif level in ("3", "full", "full_consultation"):
        level = "full"
    else:
        level = "sanitized"

    meds = store.list_table("medications", "status=?", ("current",), limit=80)
    past_meds = store.list_table("medications", "status!=?", ("current",), limit=80)
    supps = store.list_table("supplements", limit=80)
    conds = store.list_table("conditions", limit=80)
    allergies = store.list_table("allergies", limit=80)
    labs = store.list_labs(limit=200)
    symptoms = store.list_table("symptoms", order="recorded_at DESC", limit=80)
    questions = store.list_table("doctor_questions", "status=?", ("open",), order="created_at DESC", limit=40)

    def _med(m: dict[str, Any], full: bool) -> dict[str, Any]:
        row = {
            "name": m.get("name"),
            "brand_name": m.get("brand_name"),
            "generic_name": m.get("generic_name"),
            "strength": m.get("strength"),
            "dose": m.get("dose"),
            "units": m.get("units"),
            "frequency": m.get("frequency"),
            "purpose": m.get("purpose"),
            "status": m.get("status"),
            "start_date": m.get("start_date"),
            "stop_date": m.get("stop_date"),
        }
        if full:
            row.update({"physician": m.get("physician"), "pharmacy": m.get("pharmacy"), "instructions": m.get("instructions"), "notes": m.get("notes")})
        return row

    payload: dict[str, Any] = {
        "privacy_level": level,
        "disclaimer": DISCLAIMER,
        "note": "Consultant only. Health Record remains local and is not owned by the cloud model.",
        "current_medications": [_med(m, level == "full") for m in meds],
        "past_medications": [_med(m, level == "full") for m in past_meds] if level == "full" else [],
        "supplements": [{"name": s.get("name"), "dose": s.get("dose"), "frequency": s.get("frequency"), "status": s.get("status")} for s in supps],
        "conditions": [{"name": c.get("name"), "kind": c.get("kind"), "status": c.get("status")} for c in conds],
        "allergies": [{"kind": a.get("kind"), "name": a.get("name"), "reaction": a.get("reaction") if level == "full" else None} for a in allergies],
        "labs": [
            {"name": r.get("name"), "day": r.get("day"), "value": r.get("value"), "value_text": r.get("value_text"), "units": r.get("units")}
            for r in labs
        ],
        "vitals": {
            "blood_pressure": _vitals_series("blood_pressure"),
            "blood_sugar": _vitals_series("blood_sugar"),
            "weight": _vitals_series("weight"),
            "sleep_hours": _vitals_series("sleep_hours"),
            "heart_rate": _vitals_series("heart_rate"),
        },
        "symptoms": [{"name": s.get("name"), "day": s.get("day"), "duration": s.get("duration")} for s in symptoms],
        "open_doctor_questions": [q.get("text") for q in questions],
    }
    if level == "full":
        profile = store.get_profile()
        payload["profile"] = dict(profile)
        if include_docs:
            docs = store.list_table("documents", order="created_at DESC", limit=20)
            payload["documents"] = [
                {"title": d.get("title"), "kind": d.get("kind"), "day": d.get("day"), "extracted_text": (d.get("extracted_text") or "")[:8000]}
                for d in docs
            ]
    else:
        payload["profile"] = {k: v for k, v in store.get_profile().items() if k not in _REDACT_PROFILE and k == "blood_type"}
        payload["redacted"] = sorted(_REDACT_PROFILE)
        payload["documents"] = []
    return payload


def preview_consultation(question: str, *, level: str = "sanitized", include_docs: bool = False) -> dict[str, Any]:
    shared = build_shared_payload(level, include_docs=include_docs)
    if shared["privacy_level"] == "local_only":
        provider, model = "local", os.getenv("JARVIS_HEALTH_LOCAL_MODEL") or os.getenv("JARVIS_CHAT_MODEL") or "local"
        leaves = False
    else:
        provider = os.getenv("JARVIS_HEALTH_CONSULT_PROVIDER") or ("litellm" if os.getenv("JARVIS_CLOUD_MODEL") else "unset")
        model = os.getenv("JARVIS_HEALTH_CONSULT_MODEL") or os.getenv("JARVIS_CLOUD_MODEL") or ""
        leaves = True
    rec = store.add_consultation(
        {
            "level": shared["privacy_level"],
            "provider": provider,
            "model": model,
            "question": question,
            "shared": shared,
            "status": "preview",
            "approved": False,
        }
    )
    lines = [
        "**Health consultation preview — nothing has been sent.**",
        "",
        f"Privacy level: **{shared['privacy_level']}**",
        f"Provider: **{provider or 'not configured'}**",
        f"Model: **{model or 'not configured'}**",
        f"Leaves this computer: **{'yes, only after you confirm' if leaves else 'no (local only)'}**",
        "",
        f"Question: {question}",
        "",
        "Exact information that would be shared:",
        "```json",
        json.dumps(shared, indent=2)[:6000],
        "```",
        "",
        "Reply **send consultation** / confirm this preview, or **cancel consultation**.",
        "",
        "_" + DISCLAIMER + "_",
    ]
    return {
        "ok": True,
        "intent": "consult_preview",
        "consultation_id": rec["id"],
        "shared": shared,
        "provider": provider,
        "model": model,
        "leaves_device": leaves,
        "confirm_required": True,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
        "open_view": "health",
    }


def run_consultation(consultation_id: str, *, store_response: bool = True) -> dict[str, Any]:
    rec = store.get_by_id("consultations", consultation_id)
    if not rec:
        return {"ok": False, "message": "Consultation preview not found.", "disclaimer": DISCLAIMER}
    try:
        shared = json.loads(rec.get("shared_json") or "{}")
    except Exception:
        shared = {}
    level = rec.get("level") or shared.get("privacy_level") or "sanitized"
    question = rec.get("question") or ""
    if level == "local_only":
        text, meta = _run_local(question, shared)
    else:
        text, meta = _run_cloud(question, shared)
    store.update_consultation(
        consultation_id,
        {
            "response": text,
            "approved": 1,
            "stored": 1 if store_response else 0,
            "status": "complete",
            "provider": meta.get("provider") or rec.get("provider"),
            "model": meta.get("model") or rec.get("model"),
        },
    )
    if store_response:
        store.add_note("AI consultation", f"Q: {question}\n\nA: {text[:4000]}")
    lines = [
        "**Consultation response** (consultant only — not part of your medical chart unless you keep it)",
        "",
        f"Provider: {meta.get('provider')}",
        f"Model: {meta.get('model')}",
        f"Level: {level}",
        "",
        text,
        "",
        "_" + DISCLAIMER + "_",
    ]
    return {
        "ok": True,
        "intent": "consult_result",
        "consultation_id": consultation_id,
        "message": "\n".join(lines),
        "response": text,
        "meta": meta,
        "disclaimer": DISCLAIMER,
        "open_view": "health",
    }


def cancel_consultation(consultation_id: str) -> dict[str, Any]:
    rec = store.update_consultation(consultation_id, {"status": "cancelled", "approved": 0})
    return {"ok": True, "intent": "consult_cancel", "message": "Consultation cancelled. Nothing was sent.\n\n_" + DISCLAIMER + "_", "consultation": rec, "disclaimer": DISCLAIMER}


def latest_preview() -> dict[str, Any] | None:
    rows = store.list_table("consultations", "status=?", ("preview",), order="created_at DESC", limit=1)
    return rows[0] if rows else None


def _system_prompt() -> str:
    return (
        "You are an optional health-information consultant. You are NOT a physician. "
        "Do not diagnose. Do not prescribe. Do not tell the user to stop prescription medications. "
        "Use only the provided Health Record excerpt plus general public-health education. "
        "Present observations and questions for a qualified clinician. Be explicit about uncertainty."
    )


def _run_local(question: str, shared: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    from jarvis.inference.gateway import chat_with_usage
    from jarvis.llm import get_chat_model

    model = os.getenv("JARVIS_HEALTH_LOCAL_MODEL") or get_chat_model()
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": f"Question: {question}\n\nHealth excerpt:\n{json.dumps(shared)[:12000]}"},
    ]
    text, usage = chat_with_usage(model, messages, role="general")
    return text, {"provider": "ollama/local", "model": usage.get("execution_model") or model, "cloud": False}


def _run_cloud(question: str, shared: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    model = os.getenv("JARVIS_HEALTH_CONSULT_MODEL") or os.getenv("JARVIS_CLOUD_MODEL") or ""
    if not model:
        return (
            "Cloud consultation is not configured (set JARVIS_HEALTH_CONSULT_MODEL or JARVIS_CLOUD_MODEL). Nothing was sent.",
            {"provider": "none", "model": "", "cloud": False},
        )
    from jarvis.inference.gateway import chat_with_usage

    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": f"Question: {question}\n\nHealth excerpt:\n{json.dumps(shared)[:18000]}"},
    ]
    text, usage = chat_with_usage(model, messages, role="general")
    return text, {
        "provider": usage.get("execution_provider") or "cloud",
        "model": usage.get("execution_model") or model,
        "cloud": True,
    }
