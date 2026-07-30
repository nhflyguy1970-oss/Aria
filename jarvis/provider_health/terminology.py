"""Provider Health ownership boundaries."""

TERMINOLOGY = {
    "product": "Provider Health",
    "operator_name": "Provider Health",
    "pipeline": "stream_watchdog_recovery",
}

BOUNDARIES = {
    "philosophy": (
        "Provider Health owns reliability: monitoring, stream watchdog, timeout classification, "
        "recovery workflows, diagnostics, and health APIs. Providers still own inference. "
        "Models, Chat history, Search, Settings stores, Notifications delivery, and Mission Control "
        "ops remain with their products."
    ),
    "owns": [
        "provider_monitoring",
        "provider_diagnostics",
        "health_state",
        "stream_watchdog",
        "timeout_recovery",
        "retry_policy",
        "capability_detection",
        "provider_statistics",
        "recovery_workflows",
        "health_api",
        "documentation",
        "testing",
    ],
    "does_not_own": [
        "models_catalog",
        "chat_history",
        "search_index",
        "settings_database",
        "notifications_delivery",
        "mission_control_ops",
        "inference_generation",
        "shell_chrome",
    ],
}

MENTAL_MODEL = {
    "healthy": "Provider responding",
    "generating": "Tokens flowing",
    "recovering": "Safe auto-heal in progress",
    "disconnected": "Endpoint unreachable",
    "degraded": "Alive but unreliable",
}

HEALTH_STATES = (
    "healthy",
    "loading",
    "generating",
    "busy",
    "recovering",
    "disconnected",
    "restarting",
    "crashed",
    "degraded",
    "unknown",
)

FAILURE_CLASSES = (
    "provider_disconnected",
    "provider_overloaded",
    "model_loading",
    "model_crashed",
    "oom",
    "context_too_large",
    "gpu_unavailable",
    "cpu_overloaded",
    "network_interruption",
    "provider_unreachable",
    "provider_restarting",
    "stream_stalled",
    "first_token_timeout",
    "unknown_timeout",
)
