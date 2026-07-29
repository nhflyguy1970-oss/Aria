"""Smart Home product boundaries."""

TERMINOLOGY = {
    "product": "Smart Home",
    "pipeline": "shared_smarthome_pipeline",
    "engine": "Smart Home Engine",
    "home": "Smart Home Home",
}

BOUNDARIES = {
    "philosophy": (
        "Smart Home is Aria's dedicated Home Assistant product. It owns connectivity, "
        "device control, scenes, rooms, favorites, entity search, home status, profiles, "
        "history, HA orchestration, and the Smart Home dashboard. Home Assistant owns "
        "devices, entities, automations, Lovelace, and integrations. Aria owns natural "
        "language, permissions, cross-product orchestration, operator workflows, and "
        "context. Never duplicate Home Assistant or Lovelace."
    ),
    "owns": [
        "ha_connectivity",
        "device_control",
        "scenes",
        "rooms",
        "favorites",
        "entity_search",
        "home_status",
        "home_profiles",
        "home_history",
        "ha_orchestration",
        "ha_integrations",
        "smart_home_dashboard",
    ],
    "does_not_own": [
        "home_assistant_automations",
        "lovelace",
        "vision",
        "voice",
        "planner",
        "calendar",
        "automation_engine",
        "browser",
        "coding",
        "gallery",
        "second_ha_implementation",
        "cloud_smart_home_hub",
        "marketplace",
        "separate_home_llm",
        "always_on_cameras",
        "emotion_lighting",
        "silent_memory_ingestion",
        "auto_buy_devices",
    ],
    "home_assistant_owns": [
        "devices",
        "entities",
        "automations",
        "lovelace",
        "integrations",
    ],
    "aria_owns": [
        "natural_language",
        "permissions",
        "cross_product_orchestration",
        "operator_workflows",
        "context",
    ],
}
