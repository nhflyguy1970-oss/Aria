"""Capabilities product boundaries and operator terminology."""

TERMINOLOGY = {
    "product": "Capabilities",
    "pipeline": "shared_capabilities_pipeline",
    "engine": "Capabilities Engine",
    "home": "Capabilities Home",
    "item": "capability",
    "registry": "Capabilities Registry",
}

BOUNDARIES = {
    "philosophy": (
        "Capabilities is Aria's unified management system for everything that extends Aria. "
        "It owns registry, discovery, enable/disable, status, permissions, health, trust, "
        "versioning, diagnostics, and third-party capability management. First-class products "
        "(Voice, Vision, Browser, Fly Tying, Smart Home, Planner, Calendar, Gallery, Coding, "
        "Models, Automation, Mission Control, Knowledge Graph) remain product owners. "
        "Capabilities extends them and never duplicates them. Internally multiple extension "
        "layers remain; the operator sees one Capabilities surface."
    ),
    "owns": [
        "capability_registry",
        "discovery",
        "enable_disable_policy",
        "trust_evaluation",
        "permission_review",
        "load_lifecycle",
        "contribution_registration",
        "capability_health",
        "capability_diagnostics",
        "capability_recovery",
        "capability_activity",
        "third_party_capability_management",
        "first_party_capability_visibility",
    ],
    "does_not_own": [
        "voice",
        "vision",
        "browser",
        "fly_tying",
        "smart_home",
        "planner",
        "calendar",
        "gallery",
        "coding",
        "models",
        "automation",
        "mission_control",
        "knowledge_graph",
        "public_marketplace",
        "cloud_plugin_store",
    ],
    "extends": [
        "host_extensions",
        "intelligence_sdk_plugins",
        "acm_plugins",
        "ai_platform_plugins",
    ],
}

CATEGORIES = (
    "AI",
    "Coding",
    "Memory",
    "Voice",
    "Vision",
    "Browser",
    "Planner",
    "Calendar",
    "Automation",
    "Smart Home",
    "Fly Tying",
    "Gallery",
    "Media",
    "System",
    "Security",
    "Utilities",
    "Experimental",
)

LAYER_LABELS = {
    "host": "Host extension",
    "sdk": "Local capability",
    "acm": "Cognitive extension",
    "platform": "Platform module",
}
