"""Dashboard/Home bridge — summary only; Health owns the PHR."""

from __future__ import annotations

from datetime import date
from typing import Any


def dashboard_health_summary() -> dict[str, Any]:
    from jarvis.health_product import store
    from jarvis.health_product.engine import observations
    from jarvis.health_product.terminology import DISCLAIMER

    today = date.today().isoformat()
    checkin = store.get_checkin(today)
    meds = store.list_table("medications", "status=?", ("current",), limit=20)
    obs = observations(limit=2)
    latest_bp = None
    bps = store.list_vitals(kind="blood_pressure", limit=5)
    if bps:
        latest_bp = bps[-1]
    return {
        "product": "Health",
        "owner": "Health",
        "checkin_today": bool(checkin),
        "overall": (checkin or {}).get("overall"),
        "current_meds": len(meds),
        "latest_bp": (
            f"{latest_bp.get('value')}/{latest_bp.get('value2')} ({latest_bp.get('day')})"
            if latest_bp
            else None
        ),
        "observation": obs[0] if obs else "",
        "goals_active": len(store.list_table("goals", "status=?", ("active",), limit=20)),
        "disclaimer": DISCLAIMER,
        "open_doctor_questions": len(store.list_table("doctor_questions", "status=?", ("open",), limit=20)),
        "pending": bool(store.latest_pending()),
        "deep_links": [
            {"label": "Open Health", "view": "health"},
            {"label": "Daily check-in", "view": "health", "tab": "checkin"},
            {"label": "Timeline", "view": "health", "tab": "timeline"},
        ],
        "note": "Home displays a summary. Health owns the Personal Health Record.",
    }
