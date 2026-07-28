"""Canonical Browser product terminology and boundaries."""

from __future__ import annotations

TERMINOLOGY: dict[str, str] = {
    "Browser": "Aria's web interaction product — live page automation under operator control.",
    "Browser agent": "Multi-step DOM/Vision automation against a live Playwright page.",
    "Session": "An active Playwright browser context bound to a project profile.",
    "Takeover": "Operator pauses the agent to interact manually, then resumes.",
    "Step log": "Observable record of each browser action (navigate, click, fill, …).",
    "Profile": "Per-project Playwright storage (cookies/localStorage) under browser_session.",
    "Memory Browser": "Unrelated Memory product UI — not this Browser agent.",
}

BOUNDARIES: dict[str, list[str] | str] = {
    "owns": [
        "live_page_automation",
        "navigation",
        "screenshots",
        "dom_interaction",
        "vision_assisted_browsing",
        "safe_browsing_policy",
        "operator_sessions",
        "browser_task_execution",
        "browser_home",
        "bookmarks_history",
    ],
    "does_not_own": [
        "projects_workspace_identity",
        "documents_knowledge_store",
        "memory_remembered_info",
        "automation_orchestration",
        "mission_control_health",
        "chat_conversation",
        "models_configuration",
        "full_chrome_replacement",
    ],
    "philosophy": (
        "Browser interacts with web pages. Documents store knowledge. "
        "Coding edits software. Automation orchestrates. Mission Control monitors."
    ),
}
