"""Canonical Coding product terminology and boundaries."""

from __future__ import annotations

TERMINOLOGY: dict[str, str] = {
    "Coding": "Aria's software-development product (propose → review → apply → undo → verify).",
    "Developer": "Sidebar tools drawer for LSP, Git helpers, and quick actions — not a separate product.",
    "Project": "Workspace identity owned by Projects (coding root, namespaces, git path).",
    "Coding root": "Filesystem directory where Coding proposes and applies file changes.",
    "Proposal": "A pending patch (diff) awaiting operator Apply or Reject.",
    "Apply": "Write proposal files to disk after operator confirmation.",
    "Undo": "Restore files from the last apply backup.",
    "Verify": "Operator-approved post-apply checks (syntax, lint, tests, build).",
    "Coding job": "Long-running agent work tracked in Job Center (execution), owned by Coding for results.",
    "Quality brief": "Pre-apply summary of risk, files, and suggested verification.",
}

BOUNDARIES: dict[str, list[str] | str] = {
    "owns": [
        "propose",
        "review",
        "apply",
        "undo",
        "verify",
        "lsp_helpers",
        "git_helpers",
        "coding_jobs_execution",
        "proposal_history",
        "coding_home",
        "coding_root_guardrails",
    ],
    "does_not_own": [
        "projects_workspace_identity",
        "job_center_queue_ux",
        "activity_center_history",
        "mission_control_health",
        "models_configuration",
    ],
    "projects_deep_link": "projects",
    "job_center_deep_link": "jobs",
    "models_deep_link": "models",
    "activity_deep_link": "activity",
    "philosophy": "Coding proposes. Projects identify. Job Center tracks. Activity records. Models configure. Mission Control monitors.",
}
