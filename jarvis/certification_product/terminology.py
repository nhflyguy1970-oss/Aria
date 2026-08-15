"""Certification product — evidence-driven release readiness."""

TERMINOLOGY = {
    "product": "Certification",
    "home": "Certification Dashboard",
    "architecture_term": "Evidence Gate",
    "pipeline": "assert_capture_verify_gate",
}

BOUNDARIES = {
    "philosophy": (
        "Certification is Aria's release center. Every PASS requires objective evidence: "
        "assertions with expected/observed, API traces, filesystem/database checks, "
        "persistence/restart verification, and cross-system agreement. "
        "Toasts and HTTP 200 alone never grant PASS."
    ),
    "owns": [
        "certification_dashboard",
        "evidence_store",
        "assertion_log",
        "replay_scripts",
        "coverage_report",
        "release_gate",
        "false_pass_sampling",
        "mutation_check",
    ],
    "does_not_own": [
        "system_audit_hardware",
        "product_feature_implementations",
        "test_framework_pytest",
    ],
}

MENTAL_MODEL = {
    "dashboard": "Authoritative release readiness — READY TO SHIP only with evidence",
    "run": "A timed certification execution producing an evidence package",
    "assertion": "Expected vs observed with PASS/FAIL and linked evidence",
    "gate": "Binary ship decision from fails, coverage, and evidence completeness",
}

SCHEMA_VERSION = 1

# Gate thresholds — READY_TO_SHIP requires the full required feature set.
# Partial / smoke runs may complete suites but must not mint READY_TO_SHIP.
REQUIRED_COVERAGE_PCT = 100.0
REQUIRED_FEATURES = (
    "chat_clear",
    "image_lifecycle",
    "planner_calendar",
    "journal_calendar",
    "search_federated",
    "settings_appearance",
    "projects_archive",
    "production_integrity",
)
