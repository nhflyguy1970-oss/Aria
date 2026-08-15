"""Mission Control bridge — Health status only; PHR stays in Health."""

from __future__ import annotations

from datetime import date
from typing import Any


def health_mission_panel() -> dict[str, Any]:
    from jarvis.health_product import store
    from jarvis.health_product.terminology import DISCLAIMER, TERMINOLOGY

    today = date.today().isoformat()
    checkin = store.get_checkin(today)
    meds = store.list_table("medications", "status=?", ("current",), limit=50)
    reminders = store.list_table("reminders", "enabled=?", (1,), limit=20)
    questions = store.list_table("doctor_questions", "status=?", ("open",), limit=20)
    pending = store.latest_pending()
    return {
        "product": TERMINOLOGY["product"],
        "operator_name": TERMINOLOGY["operator_name"],
        "state": "attention" if pending or not checkin else "ready",
        "detail": (
            f"{'check-in done' if checkin else 'no check-in today'} · "
            f"{len(meds)} current meds · {len(reminders)} reminders · "
            f"{len(questions)} doctor questions"
            + (" · pending confirmation" if pending else "")
        ),
        "checkin_today": bool(checkin),
        "current_medications": len(meds),
        "reminders": len(reminders),
        "doctor_questions": len(questions),
        "pending": bool(pending),
        "deep_links": {
            "home": "#health",
            "status": "/api/health/product",
            "mission": "/api/health/mission",
            "emergency": "/api/health/emergency",
        },
        "disclaimer": DISCLAIMER,
        "note": "Mission Control shows Health status. The Personal Health Record lives in Health.",
    }
