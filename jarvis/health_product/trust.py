"""Trust levels and write protection for the Personal Health Record."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jarvis.health_product.terminology import DISCLAIMER

TRUST_LEVELS = {
    "highest": [
        "current_medications",
        "allergies",
        "medical_conditions",
        "blood_type",
        "emergency_contacts",
        "physicians",
        "lab_values",
        "vaccinations",
        "family_history",
        "preventive_care",
    ],
    "high": [
        "blood_pressure",
        "blood_sugar",
        "weight",
        "sleep",
        "heart_rate",
        "temperature",
        "pulse_oximeter",
        "exercise",
        "mood",
        "pain",
        "energy",
        "nutrition",
    ],
    "medium": ["symptoms", "journal_entries", "lifestyle_notes", "ai_observations", "doctor_questions"],
    "low": ["ai_suggestions", "educational_content", "lifestyle_recommendations", "external_ai_consultations", "derived_patterns"],
}

# Chat/NL must confirm before applying these mutations.
CONFIRM_KINDS = frozenset(
    {
        "medication",
        "condition",
        "allergy",
        "vaccination",
        "blood_type",
        "emergency_contacts",
        "physician",
        "physicians",
        "profile_identity",
        "family_history",
    }
)

PROFILE_CONFIRM_KEYS = frozenset(
    {"blood_type", "emergency_contacts", "primary_physician", "specialists", "name", "dob", "insurance"}
)


class HealthWriteBlocked(PermissionError):
    """Raised when a test/smoke/readonly path tries to mutate the live PHR."""


def _looks_ephemeral(path: Path) -> bool:
    text = str(path).lower()
    parts = {p.lower() for p in path.parts}
    return "pytest" in text or "tmp" in parts or "temp" in parts or text.startswith("/tmp")


def is_live_record(db_path: Path | None = None) -> bool:
    from jarvis.config import DATA_DIR, _DATA_DEFAULT
    from jarvis.health_product import store

    path = Path(db_path or store.DB_PATH).resolve()
    if _looks_ephemeral(path):
        return False
    candidates = {
        (Path(_DATA_DEFAULT) / "health_product" / "health.db").resolve(),
        (Path(DATA_DIR) / "health_product" / "health.db").resolve(),
    }
    return path in candidates


def writes_blocked_reason(*, force: bool = False) -> str | None:
    if force:
        return None
    smoke = os.getenv("JARVIS_SMOKE", "").lower() in ("1", "true", "yes", "on")
    readonly = os.getenv("JARVIS_HEALTH_READONLY", "").lower() in ("1", "true", "yes", "on")
    pytest_running = bool(os.getenv("PYTEST_CURRENT_TEST"))
    live = is_live_record()
    if readonly:
        return "Health Record is read-only (JARVIS_HEALTH_READONLY)."
    if smoke and live:
        return "Smoke/QA must not write the live Health Record."
    if pytest_running and live:
        return "pytest must not write the live Health Record — patch DB_PATH to a temp store."
    return None


def assert_writable(*, force: bool = False) -> None:
    reason = writes_blocked_reason(force=force)
    if reason:
        raise HealthWriteBlocked(reason)


def confirm_prompt(kind: str, summary: str) -> str:
    label = {
        "medication": "medication",
        "condition": "medical condition",
        "allergy": "allergy",
        "vaccination": "vaccination",
        "blood_type": "blood type",
        "emergency_contacts": "emergency contacts",
        "physician": "physician",
        "physicians": "physician",
        "profile_identity": "identity / physician profile field",
        "family_history": "family medical history",
    }.get(kind, kind)
    return (
        f"I understood: {summary}\n\n"
        f"This would change a highest-trust {label} in your Health Record.\n"
        f"Would you like me to add/update it? Reply **yes** to confirm or **no** to cancel.\n\n"
        f"_{DISCLAIMER}_"
    )


def trust_for_source(source: str) -> str:
    src = (source or "").lower()
    mapping = {
        "medications": "highest",
        "allergies": "highest",
        "conditions": "highest",
        "labs": "highest",
        "vaccinations": "highest",
        "profile": "highest",
        "vitals": "high",
        "checkins": "high",
        "symptoms": "medium",
        "medical_notes": "medium",
        "doctor_questions": "medium",
        "documents": "highest",
        "consultations": "low",
        "reminders": "medium",
        "supplements": "high",
        "activities": "high",
        "workouts": "high",
        "goals": "medium",
        "health_journal": "medium",
        "knowledge": "low",
        "providers": "highest",
        "procedures": "highest",
        "milestones": "medium",
        "recovery": "high",
        "recovery_events": "high",
        "dose_logs": "high",
        "visits": "highest",
        "family_history": "highest",
        "preventive_care": "highest",
        "nutrition_log": "medium",
        "health_observations": "low",
        "backups": "highest",
    }
    return mapping.get(src, "medium")


def product_trust_payload() -> dict[str, Any]:
    return {
        "levels": TRUST_LEVELS,
        "confirm_kinds": sorted(CONFIRM_KINDS),
        "disclaimer": DISCLAIMER,
        "default_privacy": "local_only",
    }
