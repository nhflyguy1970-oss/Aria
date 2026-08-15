"""Chat context from Health — facts only, never invented, never diagnostic."""

from __future__ import annotations

import re

from jarvis.health_product import store
from jarvis.health_product.engine import observations
from jarvis.health_product.terminology import DISCLAIMER

_HEALTH_CUE = re.compile(
    r"\b("
    r"health|blood pressure|blood sugar|glucose|a1c|cholesterol|"
    r"medication|medications|meds?|supplement|vitamin|"
    r"allerg(?:y|ies)|symptom|pain|sleep|weight|"
    r"doctor|physician|lab(?:s|oratory)?|vaccin|wellness coach|health timeline|consultation|"
    r"workout|exercis|blood pressure|sleeping|second opinion|how have i been"
    r")\b",
    re.I,
)


def is_health_chat(message: str) -> bool:
    return bool(_HEALTH_CUE.search(message or ""))


def health_context_for_chat(message: str = "", *, limit: int = 8) -> str:
    """Ground chat in recorded PHR facts when the turn is health-related."""
    if message and not is_health_chat(message):
        return ""
    lines = [
        "Health record context (authoritative local PHR — do not invent medical facts):",
        "Do not store medical facts in ACM as a source of truth. Health owns medications, allergies, conditions, labs, and vitals.",
        f"Disclaimer: {DISCLAIMER}",
    ]
    meds = store.list_table("medications", "status=?", ("current",), limit=20)
    if meds:
        lines.append("Current medications: " + ", ".join(str(m.get("name") or "") for m in meds if m.get("name")))
    else:
        lines.append("Current medications: none recorded.")
    supps = store.list_table("supplements", "status=?", ("current",), limit=20)
    if supps:
        lines.append("Current supplements: " + ", ".join(str(s.get("name") or "") for s in supps if s.get("name")))
    allergies = store.list_table("allergies", limit=20)
    if allergies:
        lines.append("Allergies: " + ", ".join(f"{a.get('kind')}:{a.get('name')}" for a in allergies))
    conditions = store.list_table("conditions", "status=?", ("active",), limit=20)
    if conditions:
        lines.append("Active conditions: " + ", ".join(str(c.get("name") or "") for c in conditions if c.get("name")))
    chk = store.get_checkin()
    if chk:
        bits = []
        if chk.get("bp_systolic") is not None:
            bits.append(f"BP {chk.get('bp_systolic')}/{chk.get('bp_diastolic')}")
        if chk.get("blood_sugar") is not None:
            bits.append(f"sugar {chk.get('blood_sugar')}")
        if chk.get("weight") is not None:
            bits.append(f"weight {chk.get('weight')}")
        if chk.get("sleep_hours") is not None:
            bits.append(f"sleep {chk.get('sleep_hours')}h")
        if bits:
            lines.append(f"Today's check-in: {', '.join(bits)}")
    pending = store.latest_pending()
    if pending:
        lines.append(f"Pending highest-trust confirmation: {pending.get('summary')}. Ask before assuming it was saved.")
    questions = store.list_table("doctor_questions", "status=?", ("open",), order="created_at DESC", limit=6)
    if questions:
        lines.append("Open doctor questions: " + "; ".join(str(q.get("text") or "") for q in questions[:4]))
    obs = observations(limit=3)
    for o in obs:
        lines.append(o)
    return "\n".join(lines[: limit + 8])
