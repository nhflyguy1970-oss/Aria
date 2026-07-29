"""Shell ownership — chrome only; products own data."""

TERMINOLOGY = {
    "product": "Shell",
    "operator_name": "Aria Shell",
    "design_system": "Aria Design System",
    "pipeline": "shell_chrome",
}

BOUNDARIES = {
    "philosophy": (
        "The Shell makes Aria feel like one professional operating environment. "
        "It owns navigation, chrome, hotkeys, discoverability, design tokens, and accessibility. "
        "Products own their data and Product Homes. Shell never owns Jobs, Mission Control logic, "
        "Planner, Notifications delivery, Search retrieval, or Settings stores."
    ),
    "owns": [
        "navigation",
        "shell_chrome",
        "breadcrumbs",
        "hotkey_registry",
        "discoverability",
        "sidebar",
        "status_bar",
        "quick_dock",
        "design_system",
        "component_patterns",
        "modal_chrome",
        "theme_tokens",
        "spacing_typography",
        "accessibility_shell",
        "motion_policy",
        "density_prefs_bridge",
        "documentation",
        "testing",
    ],
    "does_not_own": [
        "jobs",
        "mission_control",
        "planner",
        "calendar",
        "notifications_delivery",
        "search_retrieval",
        "settings_database",
        "layouts_snapshots",
        "dashboard_data",
        "product_logic",
        "second_command_palette",
        "movie_hud",
    ],
}

MENTAL_MODEL = {
    "sidebar": "Browse",
    "ctrl_k": "Act",
    "search": "Find",
    "favorites": "Shortcuts",
    "quick_dock": "Current tools",
    "layouts": "Arrange the workspace",
    "notifications": "Attention",
    "mission_control": "Operations",
    "jobs": "Running work",
    "home": "Calm workspace landing",
}
