"""Calendar ownership — schedule hub only; never owns tasks, notifications, or shell."""

TERMINOLOGY = {
    "product": "Calendar",
    "operator_name": "Calendar",
    "pipeline": "schedule_abstraction",
}

BOUNDARIES = {
    "philosophy": (
        "Calendar is Aria’s unified scheduling hub. It presents commitments from Journal, "
        "Planner, ICS, work schedule, and holidays through a Schedule Abstraction Layer. "
        "Planner is the single write owner for user-created events; Journal contributes "
        "day notes and legacy event projections. Calendar publishes attention signals; "
        "Notifications deliver them. Planner owns tasks and execution."
    ),
    "owns": [
        "events_presentation",
        "calendars_work_schedule",
        "availability_free_windows",
        "scheduling_nl_conflicts_prep",
        "time_zones_local_day",
        "ics_subscribe",
        "recurrence_rrule_basic",
        "schedule_abstraction",
        "calendar_api",
        "calendar_ui",
    ],
    "does_not_own": [
        "tasks",
        "projects",
        "planner_workflows",
        "notifications_delivery",
        "jobs",
        "search_index",
        "settings_database",
        "shell_chrome",
        "mission_control_ops",
    ],
}

MENTAL_MODEL = {
    "calendar": "Scheduled commitments hub",
    "planner": "Actionable work and user event write source",
    "journal": "Notes and legacy day-event projections",
    "ics": "External read-only feed",
    "notifications": "Attention delivery for calendar signals",
}
