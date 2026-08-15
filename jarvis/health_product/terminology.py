"""Health product boundaries — Personal Health Record, not EMR."""

TERMINOLOGY = {
    "product": "Health",
    "operator_name": "Health",
    "home": "Health",
    "record": "Personal Health Record",
    "engine": "Health Engine",
}

DISCLAIMER = (
    "Aria is not a physician and does not diagnose or prescribe. "
    "Health insights are informational only. Consult a qualified healthcare professional "
    "for medical advice."
)

BOUNDARIES = {
    "philosophy": (
        "Health is Jeff's local Personal Health Record. It owns daily check-ins, "
        "medical history, medications, supplements, vitals, labs, symptoms, documents, "
        "and printable summaries. Chat must retrieve health facts from Health — never invent them. "
        "Observations are patterns in recorded data, never diagnoses."
    ),
    "owns": [
        "daily_health_reports",
        "medical_history",
        "conditions",
        "medications",
        "supplements",
        "vital_signs",
        "laboratory_values",
        "symptoms",
        "allergies",
        "physicians",
        "health_documents",
        "health_reminders",
        "health_timeline",
        "doctor_questions",
        "doctor_summaries",
        "emergency_medical_information",
        "ai_consultation_history",
        "wellness_coach_suggestions",
        "health_export",
        "activities",
        "workouts",
        "activity_goals",
        "health_trends",
        "health_journal",
        "health_knowledge",
        "providers",
        "procedures",
        "medication_safety_education",
        "health_milestones",
        "wellness_scorecard",
        "medication_adherence",
        "recovery_tracking",
        "doctor_visit_history",
        "family_history",
        "preventive_care",
        "nutrition_habits",
        "health_observations",
        "health_backups",
    ],
    "does_not_own": [
        "emr",
        "hospital_systems",
        "fhir",
        "apple_health",
        "fitbit",
        "cgm_apis",
        "insurance_apis",
        "diagnosis",
        "prescriptions_as_treatment",
        "journal_wellness_mood_only",
        "planner_tasks",
        "calendar_appointments_storage",
    ],
}

MENTAL_MODEL = {
    "health": "Local Personal Health Record — single source of truth for Jeff's medical information",
    "journal": "Notes and reflections — not medical history",
    "planner": "Actionable work — not medication schedules (Health may remind)",
    "calendar": "Scheduled commitments including appointments",
    "documents": "General document index — Health owns medical documents",
    "acm": "Remembered facts — Health is authoritative for medical data",
}
