"""Family medical history — recorded facts only; educational context, never prediction."""

from __future__ import annotations

from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

RELATIONS = (
    "mother",
    "father",
    "sister",
    "brother",
    "sibling",
    "maternal_grandmother",
    "maternal_grandfather",
    "paternal_grandmother",
    "paternal_grandfather",
    "grandmother",
    "grandfather",
    "daughter",
    "son",
    "child",
    "aunt",
    "uncle",
    "cousin",
    "other",
)

CONDITION_CATALOG = {
    "heart disease": "cardiac",
    "heart attack": "cardiac",
    "stroke": "neuro",
    "high blood pressure": "cardiac",
    "hypertension": "cardiac",
    "high cholesterol": "metabolic",
    "diabetes": "metabolic",
    "cancer": "oncologic",
    "alzheimer": "neuro",
    "alzheimer's": "neuro",
    "parkinson": "neuro",
    "parkinson's": "neuro",
    "kidney disease": "renal",
    "autoimmune": "autoimmune",
    "depression": "psych",
    "anxiety": "psych",
    "mental health": "psych",
}

_BOUNDARY = (
    "Family history is recorded context only. Aria does not diagnose, predict disease, "
    "or imply that you will develop any condition because a relative had it."
)


def _side_for(relation: str) -> str:
    r = (relation or "").lower()
    if r.startswith("maternal_") or r in ("mother",):
        return "maternal"
    if r.startswith("paternal_") or r in ("father",):
        return "paternal"
    if "grandmother" in r or "grandfather" in r or "aunt" in r or "uncle" in r:
        return "unknown"
    return "other"


def _category_for(condition: str) -> str:
    c = (condition or "").lower()
    for key, cat in CONDITION_CATALOG.items():
        if key in c:
            return cat
    return "other"


def save_entry(rec: dict[str, Any], *, provenance: str = "manual", confirmed: bool = False) -> dict[str, Any]:
    relation = str(rec.get("relation") or "other").lower().replace(" ", "_")
    condition = str(rec.get("condition") or "").strip()
    if not condition:
        raise ValueError("condition required")
    payload = {
        **rec,
        "relation": relation,
        "relation_side": rec.get("relation_side") or _side_for(relation),
        "condition": condition,
        "condition_category": rec.get("condition_category") or _category_for(condition),
        "hereditary": rec.get("hereditary", True),
        "provenance": provenance,
        "confidence": "user_confirmed" if confirmed else "user_entered",
        "confirmed": 1 if confirmed else 0,
    }
    return store.upsert_family_history(payload)


def family_summary() -> dict[str, Any]:
    rows = store.list_table("family_history", limit=300)
    by_side: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        side = str(r.get("relation_side") or "other")
        by_side.setdefault(side, []).append(r)
    lines = ["**Family medical history**", "", _BOUNDARY, ""]
    if not rows:
        lines.append("Nothing recorded yet.")
    else:
        for side in ("maternal", "paternal", "other", "unknown"):
            group = by_side.get(side) or []
            if not group:
                continue
            lines.append(f"**{side.title()}**")
            for r in group:
                bits = [f"{r.get('relation')}: {r.get('condition')}"]
                if r.get("age_at_diagnosis"):
                    bits.append(f"age {r['age_at_diagnosis']}")
                if r.get("cause_of_death"):
                    bits.append(f"cause of death: {r['cause_of_death']}")
                if r.get("notes"):
                    bits.append(str(r["notes"])[:120])
                lines.append("• " + " — ".join(bits))
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "family_history",
        "entries": rows,
        "by_side": by_side,
        "boundary": _BOUNDARY,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
        "educational": True,
    }


def hereditary_flags() -> list[str]:
    """Recorded condition names only — never risk predictions."""
    rows = store.list_table("family_history", limit=200)
    out = []
    for r in rows:
        name = str(r.get("condition") or "").strip()
        if name and name.lower() not in {x.lower() for x in out}:
            out.append(name)
    return out


def doctor_prep_section() -> list[str]:
    rows = store.list_table("family_history", limit=40)
    if not rows:
        return []
    lines = ["**Family history on file** (recorded facts — not predictions)"]
    for r in rows[:12]:
        lines.append(f"• {r.get('relation')}: {r.get('condition')}" + (f" (age {r['age_at_diagnosis']})" if r.get("age_at_diagnosis") else ""))
    lines.append(_BOUNDARY)
    return lines
