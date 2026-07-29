"""Integrations product boundaries — credentials & provider health, not product behavior."""

TERMINOLOGY = {
    "product": "Integrations",
    "architecture_term": "External APIs",
    "pipeline": "shared_integrations_pipeline",
    "engine": "Integrations Engine",
    "home": "Integrations Home",
}

BOUNDARIES = {
    "philosophy": (
        "Integrations is Aria's unified management system for providers, API keys, secrets, "
        "connection tests, provider health, unlock matrices, and inbound webhook visibility. "
        "'External APIs' is the architectural term for the connector/runtime layer. "
        "Voice owns Cloud Live behavior; Models owns inference; Smart Home owns Home Assistant; "
        "Engineering owns Meshy functionality; Automation owns inbound webhook execution. "
        "Integrations supplies credentials, health, diagnostics, and provider services only."
    ),
    "owns": [
        "provider_registry",
        "api_keys",
        "secrets_lifecycle",
        "connection_testing",
        "provider_health",
        "unlock_matrix",
        "secret_hygiene",
        "usage_log_redacted",
        "connector_registry_projection",
        "inbound_webhook_visibility",
        "integrations_diagnostics",
        "integrations_recovery",
    ],
    "does_not_own": [
        "voice_cloud_live_behavior",
        "model_inference",
        "home_assistant_control",
        "meshy_generation",
        "browser_agent",
        "automation_execution",
        "planner",
        "calendar",
        "gallery",
        "vision_analysis",
        "public_api_marketplace",
        "zapier_clone",
    ],
}

CATEGORIES = (
    "Cloud AI",
    "Local AI",
    "Gateway",
    "Engineering",
    "Smart Home",
    "Automation",
    "Search",
    "Host",
    "Experimental",
)
