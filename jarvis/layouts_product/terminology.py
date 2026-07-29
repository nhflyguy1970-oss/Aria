"""Layouts product boundaries — shell presentation profiles only."""

TERMINOLOGY = {
    "product": "Layouts",
    "operator_name": "Layouts",
    "architecture_term": "Shell Presentation Profiles",
    "pipeline": "shared_layouts_pipeline",
    "engine": "Layouts Engine",
    "home": "Layouts",
    "legacy_alias": "workspace_layouts",
}

BOUNDARIES = {
    "philosophy": (
        "Layouts are named shell presentation profiles. They change how Aria looks "
        "and is organized (view, favorites, chrome, split, Home layout, theme hooks). "
        "They never own Projects identity, Chat sessions, Planner/Calendar/Journal data, "
        "Mission Control, Search, Settings stores, secrets, or product databases. "
        "Operator-facing name is Layouts — not Workspaces."
    ),
    "owns": [
        "layout_catalog",
        "layout_schema",
        "snapshot_engine",
        "layout_application_contract",
        "layout_history",
        "restore_engine",
        "layout_diagnostics",
        "layout_api",
        "palette_integration",
        "hotkeys",
        "search_registration",
        "settings_bridge",
        "mission_control_bridge",
        "export_import",
    ],
    "does_not_own": [
        "projects",
        "chat_sessions",
        "planner",
        "calendar",
        "journal",
        "mission_control",
        "search",
        "dashboard_data",
        "favorites_authoritative_store",
        "product_data",
        "secrets",
        "settings_database",
        "virtual_desktops",
        "automatic_ai_layouts",
    ],
}

MENTAL_MODEL = {
    "layouts": "Shell presentation profiles — how Aria looks",
    "projects": "Workspace Identity — what you are working on (Projects owns)",
    "sidebar_surfaces": "Nav group of product views — not Layouts",
    "settings": "Preferences catalog — restore options live there; Layouts applies",
    "home": "Dashboard Home aggregates; Layouts may snapshot Home chrome only",
}

LAYOUT_KINDS = ("builtin", "custom", "starter", "role", "experimental")
