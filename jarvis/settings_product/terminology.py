"""Settings product boundaries — catalog and navigation; products own stores."""

TERMINOLOGY = {
    "product": "Settings",
    "architecture_term": "Preference Catalog",
    "pipeline": "shared_settings_pipeline",
    "engine": "Settings Engine",
    "home": "Settings Home",
}

BOUNDARIES = {
    "philosophy": (
        "Settings is Aria's preference catalog and navigation layer. "
        "It indexes global/appearance prefs and deep-links into product Homes. "
        "Products continue owning their preference stores. Settings never builds "
        "a monolithic settings database or duplicates secrets/security/product UIs. "
        "Ctrl+, and the Settings button open Settings Home. Voice & Chat is a separate modal."
    ),
    "owns": [
        "settings_home",
        "preference_catalog",
        "preference_search_index",
        "preference_schemas",
        "global_preferences",
        "appearance_preferences",
        "settings_navigation",
        "deep_link_routing",
        "settings_diagnostics",
        "preference_profiles",
        "settings_apis",
        "settings_mission_control",
        "settings_coach",
    ],
    "does_not_own": [
        "voice_settings_store",
        "vision_settings_store",
        "models_settings_store",
        "search_settings_store",
        "integrations_secrets",
        "capabilities_settings_store",
        "smart_home_settings_store",
        "coding_preferences_store",
        "planner_settings",
        "calendar_settings",
        "security_implementation",
        "product_preference_stores",
        "monolithic_settings_database",
        "duplicate_search_engine",
    ],
}

# Canonical IA — no overlapping categories
CATEGORIES = (
    "global",
    "appearance",
    "security",
    "secrets",
    "products",
    "environment",
    "diagnostics",
    "profiles",
)

MENTAL_MODEL = {
    "ctrl_comma": "Opens Settings Home — the preference catalog",
    "voice_chat_modal": "Speak replies + Server Whisper only (not Settings)",
    "products": "Deep prefs live on product Homes; Settings deep-links",
    "secrets": "Integrations owns API keys; Settings only indexes",
    "security": "Security view owns PIN/lock; Settings deep-links",
}
