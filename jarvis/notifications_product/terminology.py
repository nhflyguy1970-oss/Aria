"""Notifications product boundaries — delivery only; products publish events."""

TERMINOLOGY = {
    "product": "Notifications",
    "operator_name": "Notifications",
    "inbox": "Activity Center",
    "pipeline": "shared_notifications_pipeline",
    "engine": "Notifications Engine",
    "home": "Notifications",
    "legacy_alias": "activity_center",
}

BOUNDARIES = {
    "philosophy": (
        "Notifications answers one question: what happened that still needs my attention? "
        "Activity Center is the durable inbox. Toasts are transient feedback. "
        "Desktop notifications are OS delivery. Mission Control owns infrastructure health. "
        "Job Center owns running work. Products publish events; Notifications owns delivery."
    ),
    "owns": [
        "notification_pipeline",
        "notification_schema",
        "publish_api",
        "activity_center_inbox",
        "notification_routing",
        "notification_history",
        "notification_preferences",
        "desktop_bridge",
        "toast_bridge",
        "grouping",
        "correlation",
        "digest_engine",
        "diagnostics",
        "settings_bridge",
        "search_registration",
        "mission_control_bridge",
        "dashboard_bridge",
        "outbox_drain",
    ],
    "does_not_own": [
        "jobs",
        "mission_control",
        "planner",
        "calendar",
        "gallery",
        "browser",
        "models",
        "automation",
        "projects",
        "dashboard_data",
        "second_notification_database",
        "slack_clone",
        "auto_dismiss_unread",
        "ai_invented_alerts",
    ],
}

MENTAL_MODEL = {
    "notifications": "Unified delivery product — what still needs attention",
    "activity_center": "Durable inbox UI for Notifications",
    "toasts": "Transient feedback only",
    "desktop": "OS delivery channel gated by preferences",
    "job_center": "Live work — not the inbox",
    "mission_control": "Infrastructure health — may promote critical events",
}
