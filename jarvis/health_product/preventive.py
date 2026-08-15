"""Preventive care tracking — educational scheduling from recorded dates only."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_BOUNDARY = (
    "Preventive care dates are from your Health Record. Recommended intervals are general education "
    "from common public-health guidance — your physician decides what is right for you."
)

CATALOG: list[dict[str, Any]] = [
    {"slug": "physical", "name": "Physical exam", "category": "exam", "interval_months": 12},
    {"slug": "dental", "name": "Dental cleaning", "category": "dental", "interval_months": 6},
    {"slug": "eye", "name": "Eye exam", "category": "vision", "interval_months": 24},
    {"slug": "hearing", "name": "Hearing test", "category": "exam", "interval_months": 36},
    {"slug": "colonoscopy", "name": "Colonoscopy", "category": "screening", "interval_months": 120},
    {"slug": "mammogram", "name": "Mammogram", "category": "screening", "interval_months": 12},
    {"slug": "pap", "name": "Pap test", "category": "screening", "interval_months": 36},
    {"slug": "psa", "name": "PSA", "category": "screening", "interval_months": 12},
    {"slug": "bone_density", "name": "Bone density", "category": "screening", "interval_months": 24},
    {"slug": "skin", "name": "Skin exam", "category": "screening", "interval_months": 12},
    {"slug": "vaccination", "name": "Vaccination", "category": "immunization", "interval_months": None},
]


def catalog() -> list[dict[str, Any]]:
    return [dict(c, source_kind="catalog_suggestion") for c in CATALOG]


def _add_months(day: str, months: float | None) -> str | None:
    if not day or not months:
        return None
    try:
        d = date.fromisoformat(str(day)[:10])
        # Approximate month add
        y = d.year + int((d.month - 1 + int(months)) // 12)
        m = (d.month - 1 + int(months)) % 12 + 1
        day_n = min(d.day, 28)
        return date(y, m, day_n).isoformat()
    except Exception:
        return None


def due_status(row: dict[str, Any]) -> str:
    status = str(row.get("status") or "planned")
    if status in ("completed", "declined", "not_applicable"):
        return status
    next_due = row.get("next_due") or ""
    if not next_due and row.get("last_done") and row.get("interval_months"):
        next_due = _add_months(str(row["last_done"]), float(row["interval_months"])) or ""
    if not next_due:
        return status or "planned"
    try:
        due = date.fromisoformat(str(next_due)[:10])
    except Exception:
        return status
    today = date.today()
    if due < today:
        return "overdue"
    if due <= today + timedelta(days=60):
        return "due"
    if row.get("scheduled_for"):
        return "scheduled"
    return "planned"


def save(rec: dict[str, Any], *, provenance: str = "manual") -> dict[str, Any]:
    slug = str(rec.get("slug") or "").lower()
    if not rec.get("name") and slug:
        for c in CATALOG:
            if c["slug"] == slug:
                rec = {**c, **rec}
                break
    if rec.get("last_done") and not rec.get("next_due") and rec.get("interval_months"):
        rec["next_due"] = _add_months(str(rec["last_done"]), float(rec["interval_months"]))
    rec["status"] = due_status(rec)
    rec["provenance"] = provenance
    return store.upsert_preventive(rec)


def complete(item_id: str, *, day: str | None = None, result: str = "", physician: str = "") -> dict[str, Any]:
    row = store.get_by_id("preventive_care", item_id)
    if not row:
        raise ValueError("Preventive care item not found")
    day = day or date.today().isoformat()
    row["last_done"] = day
    row["result"] = result or row.get("result") or ""
    row["result_day"] = day
    if physician:
        row["physician"] = physician
    if row.get("interval_months"):
        row["next_due"] = _add_months(day, float(row["interval_months"]))
    row["status"] = "completed"
    saved = store.upsert_preventive(row)
    # Soft reminder for next due
    if saved.get("next_due"):
        try:
            rem = store.upsert_reminder(
                {
                    "kind": "preventive",
                    "title": f"Preventive care: {saved.get('name')}",
                    "schedule": saved["next_due"],
                    "enabled": 1,
                    "notes": f"Next recommended around {saved['next_due']} — confirm with your physician.",
                }
            )
            saved["reminder_id"] = rem.get("id")
            store.upsert_preventive(saved)
        except Exception:
            pass
    return saved


def list_due(*, include_catalog: bool = False) -> dict[str, Any]:
    rows = store.list_table("preventive_care", limit=200)
    for r in rows:
        r["status"] = due_status(r)
    due = [r for r in rows if r.get("status") in ("due", "overdue", "scheduled")]
    lines = ["**Preventive care**", "", _BOUNDARY, ""]
    if due:
        lines.append("**Coming due / overdue**")
        for r in due[:20]:
            lines.append(f"• {r.get('name')}: {r.get('status')} — next {r.get('next_due') or '—'} (last {r.get('last_done') or '—'})")
    elif rows:
        lines.append("No items currently marked due. Recorded screenings:")
        for r in rows[:12]:
            lines.append(f"• {r.get('name')}: last {r.get('last_done') or '—'} · next {r.get('next_due') or '—'}")
    else:
        lines.append("No preventive care recorded yet.")
        if include_catalog:
            lines.append("Catalog suggestions (educational only — not prescriptions):")
            for c in CATALOG[:8]:
                lines.append(f"• {c['name']}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "preventive",
        "items": rows,
        "due": due,
        "catalog": catalog() if include_catalog else [],
        "boundary": _BOUNDARY,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }


def answer_last(name_or_slug: str) -> dict[str, Any]:
    needle = (name_or_slug or "").strip().lower()
    rows = store.list_table("preventive_care", limit=200)
    hits = [r for r in rows if needle in str(r.get("name") or "").lower() or needle == str(r.get("slug") or "").lower()]
    # Also check vaccinations / procedures for colonoscopy etc.
    if not hits and "colonoscop" in needle:
        procs = [p for p in store.list_table("procedures", limit=50) if "colonoscop" in str(p.get("name") or "").lower() or "colonoscop" in str(p.get("kind") or "").lower()]
        if procs:
            p = procs[0]
            msg = f"Last recorded colonoscopy-related procedure: {p.get('day') or '—'} — {p.get('name')} at {p.get('location') or '—'}.\n\n_{DISCLAIMER}_"
            return {"ok": True, "intent": "preventive", "message": msg, "disclaimer": DISCLAIMER, "items": procs}
    if not hits:
        msg = f"No recorded date for “{name_or_slug}” in Preventive Care. I will not invent one.\n\n_{DISCLAIMER}_"
        return {"ok": True, "intent": "preventive", "message": msg, "disclaimer": DISCLAIMER, "items": []}
    r = sorted(hits, key=lambda x: str(x.get("last_done") or ""), reverse=True)[0]
    msg = (
        f"**{r.get('name')}**\n"
        f"• Last completed: {r.get('last_done') or 'not recorded'}\n"
        f"• Next recommended (from your record): {r.get('next_due') or 'not set'}\n"
        f"• Physician: {r.get('physician') or '—'}\n"
        f"• Location: {r.get('facility') or '—'}\n\n"
        f"{_BOUNDARY}\n\n_{DISCLAIMER}_"
    )
    return {"ok": True, "intent": "preventive", "item": r, "message": msg, "disclaimer": DISCLAIMER}
