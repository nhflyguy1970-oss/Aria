"""Automation product storage paths — isolated namespaces (no shared folders)."""

from __future__ import annotations

from jarvis.config import DATA_DIR

# Product root
AUTOMATION_ROOT = DATA_DIR / "automation_product"

# Isolated stores
RULES_FILE = AUTOMATION_ROOT / "rules.json"
# Read once by migration only; runtime rules live in RULES_FILE.
LEGACY_RULES_FILE = DATA_DIR / "user_automations.json"

WORKFLOW_DAGS_DIR = AUTOMATION_ROOT / "workflow_dags"
LEGACY_WORKFLOWS_DIR = DATA_DIR / "workflows"  # was shared — migrate carefully

LEARNED_WORKFLOWS_DIR = AUTOMATION_ROOT / "learned_workflows"
LEARNED_INDEX_FILE = LEARNED_WORKFLOWS_DIR / "index.json"
LEARNED_WATCH_FILE = LEARNED_WORKFLOWS_DIR / "_watch_state.json"

TEMPLATES_DIR = AUTOMATION_ROOT / "templates"
RUN_HISTORY_FILE = AUTOMATION_ROOT / "run_history.json"
SUGGESTIONS_FILE = AUTOMATION_ROOT / "suggestions.json"
MUTED_FILE = AUTOMATION_ROOT / "muted.json"
EXPORT_DIR = AUTOMATION_ROOT / "exports"

# View Paths stay client-side (AriaUiPrefs) — documented only
VIEW_PATHS_NOTE = "browser:AriaUiPrefs.recordedWorkflows|viewPaths"

# Ops maintenance (existing)
OPS_DIR = DATA_DIR / "automation"


def ensure_dirs() -> None:
    for d in (
        AUTOMATION_ROOT,
        WORKFLOW_DAGS_DIR,
        LEARNED_WORKFLOWS_DIR,
        TEMPLATES_DIR,
        EXPORT_DIR,
        OPS_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
