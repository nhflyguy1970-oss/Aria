"""Dashboard product boundaries — Home aggregates; products own data."""

TERMINOLOGY = {
    "product": "Dashboard",
    "operator_name": "Home",
    "architecture_term": "Home Aggregate",
    "pipeline": "shared_dashboard_pipeline",
    "engine": "Dashboard Engine",
    "home": "Home",
}

BOUNDARIES = {
    "philosophy": (
        "Dashboard is Aria's Home product. It aggregates product summaries into "
        "honest widgets, deep-links into product Homes, and never duplicates stores. "
        "Operator-facing name is Home. Mission Control remains the ops console. "
        "Chat remains the primary AI workspace. Morning Briefing owns briefing data; "
        "Dashboard indexes it into one Daily Brief card."
    ),
    "owns": [
        "home",
        "widget_catalog",
        "widget_schema",
        "dashboard_aggregate_api",
        "dashboard_routing",
        "layout",
        "dashboard_diagnostics",
        "dashboard_search_registration",
        "dashboard_personalization",
        "home_presentation",
        "dashboard_history",
        "dashboard_api",
        "dashboard_mission_control",
        "attention_strip",
        "daily_brief_presentation",
    ],
    "does_not_own": [
        "planner",
        "calendar",
        "journal",
        "memory",
        "search",
        "mission_control",
        "home_assistant",
        "automation",
        "coding",
        "gallery",
        "voice",
        "vision",
        "morning_briefing",
        "settings_database",
        "monolithic_dashboard_database",
        "duplicate_product_uis",
    ],
}

WIDGET_CATEGORIES = (
    "glance",
    "brief",
    "attention",
    "launcher",
    "health",
    "home",
    "productivity",
    "media",
    "ai",
    "setup",
)

ROLE_LAYOUTS = (
    "default",
    "maker",
    "developer",
    "media",
    "operations",
    "research",
)

MENTAL_MODEL = {
    "home": "What is happening / what next / where to go",
    "mission_control": "Ops detail — Dashboard shows summary only",
    "chat": "Primary AI workspace — not replaced by Home",
    "daily_brief": "One brief card; Morning Briefing owns source data",
    "widgets": "Products own data; Dashboard indexes presentation",
}
