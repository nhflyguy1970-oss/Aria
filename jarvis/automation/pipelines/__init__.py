"""Automation Pipelines (DAG Workflow Engine) — subsystem of Automation, not a separate product.

Pipelines = multi-step execution DAGs.
Automation Rules decide *when* they run.
Activity records events. Job Center tracks live work.
"""

from __future__ import annotations

from jarvis.automation.pipelines.engine import explain_pipeline, run_pipeline
from jarvis.automation.pipelines.storage import (
    create_from_template,
    delete_pipeline,
    duplicate_pipeline,
    export_pipelines,
    get_pipeline,
    list_pipelines,
    list_templates,
    rename_pipeline,
    save_pipeline,
    search_pipelines,
)

__all__ = [
    "run_pipeline",
    "explain_pipeline",
    "list_pipelines",
    "list_templates",
    "get_pipeline",
    "create_from_template",
    "save_pipeline",
    "rename_pipeline",
    "delete_pipeline",
    "duplicate_pipeline",
    "export_pipelines",
    "search_pipelines",
]
