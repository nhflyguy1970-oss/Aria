"""Production Integrity terminology and boundaries."""

TERMINOLOGY = {
    "product": "Production Integrity",
    "operator_name": "Integrity",
    "home": "Production Integrity",
    "architecture_term": "Platform Safeguard",
    "pipeline": "scan_recommend_approve_repair_verify",
}

BOUNDARIES = {
    "philosophy": (
        "Development belongs to developers. Production belongs to Jeff. "
        "Aria must always know the difference between Production, QA, Development, "
        "Smoke, Certification, Demo, Prototype, and Test. "
        "Integrity scans never silently delete — Jeff approves Guided Repair."
    ),
    "owns": [
        "production_integrity_scan",
        "artifact_classification",
        "integrity_history",
        "qa_metadata_helpers",
        "integrity_guided_repair_module",
        "mission_control_integrity_status",
    ],
    "does_not_own": [
        "guided_repair_engine",
        "product_feature_implementations",
        "user_data_content",
        "health_phr_content",
    ],
}

MENTAL_MODEL = {
    "scan": "Lightweight check for development artifacts in the live workspace",
    "finding": "A verified candidate artifact with evidence and confidence",
    "repair": "Jeff-approved removal of known-safe development artifacts only",
    "status": "Clean | Warning | Attention Required",
}

DISCLAIMER = (
    "Production Integrity never auto-deletes. "
    "Only known-safe development artifacts are removable after Jeff approves. "
    "User documents, Health records, ACM memories, Projects, Journal, Planner, "
    "Calendar, Gallery, and coding work are never removed without explicit confirmation."
)

# Mission Control status vocabulary
STATUS_CLEAN = "clean"
STATUS_WARNING = "warning"
STATUS_ATTENTION = "attention"

ARTIFACT_TYPES = (
    "qa",
    "test",
    "demo",
    "sample",
    "prototype",
    "certification",
    "temporary",
    "development",
    "smoke",
    "probe",
)

SCHEMA_VERSION = 1
