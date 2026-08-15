"""Guided Repair product boundaries — expert diagnosis, never silent mutation."""

SCHEMA_VERSION = "2"

TERMINOLOGY = {
    "product": "Guided Repair",
    "operator_name": "Repair",
    "home": "Repair Center",
    "engine": "Guided Repair Engine",
}

DISCLAIMER = (
    "Repairs never claim success without verification. "
    "Jeff always approves before a repair executes. "
    "Truth is more important than optimism. "
    "Confidence is justified by evidence and history — never certainty."
)

BOUNDARIES = {
    "philosophy": (
        "Aria diagnoses problems with evidence, proposes a repair plan with risk and rollback, "
        "waits for Jeff's approval, executes, verifies, monitors stability, records history, and learns. "
        "A Fix button that only retries is not a repair. Trust is the objective — not autonomy."
    ),
    "owns": [
        "issue_detection",
        "diagnosis",
        "evidence",
        "repair_plans",
        "approval_gates",
        "repair_execution",
        "verification",
        "post_repair_monitoring",
        "repair_history",
        "repair_learning",
        "repair_knowledge",
        "maintenance_mode",
        "diagnostic_export",
    ],
    "does_not_own": [
        "automatic_destructive_changes",
        "silent_success_claims",
        "blind_retries_as_repairs",
        "unjustified_certainty",
    ],
}

MENTAL_MODEL = (
    "Problem → Diagnosis → Evidence → Confidence(+reasons) → Impact → Dependencies → "
    "Plan → Preview → Risk → Time → Rollback → User Approval → Multi-step Repair → "
    "Verification → Monitoring → History → Knowledge → Learning"
)

# Lifecycle states (canonical)
STATES = (
    "detected",
    "investigating",
    "diagnosis_complete",
    "repair_ready",
    "awaiting_approval",
    "repairing",
    "verifying",
    "repair_successful",
    "repair_failed",
    "needs_user",
    "unsafe_to_repair",
    "monitoring",
)

RISK_LEVELS = ("very_low", "low", "medium", "high", "critical")
PRIORITIES = ("critical", "high", "medium", "low", "informational")
ROLLBACK_KINDS = ("available", "unavailable", "partial")

# Approval classes
APPROVAL_SAFE = "safe"  # still requires Jeff click unless auto-approved list
APPROVAL_SEMI = "semi"
APPROVAL_MANUAL = "manual"
