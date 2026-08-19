"""Reusable workflow templates.

Small and deliberate: a handful of validated, versioned definitions that
compose ARIA's own subsystems. A template is a starting point for a run, not a
plugin — instantiating one produces an ordinary workflow that is validated like
any other.
"""

from __future__ import annotations

from typing import Any

TEMPLATE_VERSION = "1.0.0"


def _template(template_id: str, name: str, description: str, steps: list[dict]) -> dict:
    return {
        "template_id": template_id,
        "template_version": TEMPLATE_VERSION,
        "name": name,
        "description": description,
        "steps": steps,
    }


# research → evidence → verification → synthesis, all through existing systems.
RESEARCH_WITH_EVIDENCE = _template(
    "research_with_evidence",
    "Research with evidence",
    "Run deep research, read back its evidence, and verify a claim from it.",
    [
        {
            "step_id": "research",
            "action": "research_create",
            "agent_id": "research_specialist",
            "params": {"objective": "${input.objective}"},
            "outputs": ("research_id",),
        },
        {
            "step_id": "run_research",
            "action": "research_run",
            "agent_id": "research_specialist",
            "depends_on": ("research",),
            "params": {"research_id": "${steps.research.output.research_id}"},
            "timeout_s": 900.0,
        },
        {
            "step_id": "evidence",
            "action": "evidence_list_claims",
            "agent_id": "research_specialist",
            "depends_on": ("run_research",),
            "params": {"context_id": "${steps.research.output.research_id}"},
        },
        {
            "step_id": "report",
            "action": "research_report",
            "agent_id": "research_specialist",
            "depends_on": ("run_research",),
            "params": {"research_id": "${steps.research.output.research_id}"},
        },
    ],
)

# A safe, bounded coding workflow over an existing coding task.
CODING_TASK = _template(
    "coding_task",
    "Coding task",
    "Inspect a repository, run its tests, and diagnose failures via skills.",
    [
        {
            "step_id": "inspect",
            "action": "skill_invoke",
            "agent_id": "coding_specialist",
            "params": {
                "skill_id": "repository_inspect",
                "inputs": {"task_id": "${input.task_id}"},
            },
        },
        {
            "step_id": "diagnose",
            "action": "skill_invoke",
            "agent_id": "coding_specialist",
            "depends_on": ("inspect",),
            "params": {
                "skill_id": "analyze_test_failure",
                "inputs": {"task_id": "${input.task_id}"},
            },
            "timeout_s": 600.0,
        },
    ],
)

# A model-routed question, recorded with its routing provenance.
ROUTED_ANSWER = _template(
    "routed_answer",
    "Routed answer",
    "Answer a question on a model chosen by the router, preserving provenance.",
    [
        {
            "step_id": "route",
            "action": "model_route",
            "agent_id": "general_specialist",
            "params": {"task_type": "general"},
        },
        {
            "step_id": "answer",
            "action": "model_execute",
            "agent_id": "general_specialist",
            "depends_on": ("route",),
            "params": {"prompt": "${input.question}", "latency_preference": "fast"},
            "timeout_s": 600.0,
        },
    ],
)

TEMPLATES = {t["template_id"]: t for t in (RESEARCH_WITH_EVIDENCE, CODING_TASK, ROUTED_ANSWER)}


def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "template_id": t["template_id"],
            "name": t["name"],
            "description": t["description"],
            "version": t["template_version"],
            "steps": len(t["steps"]),
        }
        for t in sorted(TEMPLATES.values(), key=lambda x: x["template_id"])
    ]


def get_template(template_id: str) -> dict[str, Any] | None:
    template = TEMPLATES.get(template_id)
    # A copy: a running workflow must never share structure with the template
    # it came from.
    return _deep_copy(template) if template else None


def instantiate(
    template_id: str, inputs: dict[str, Any] | None = None, *, requester: str = ""
) -> dict[str, Any]:
    """Build a concrete workflow definition from a template."""
    template = get_template(template_id)
    if not template:
        raise KeyError(f"No such workflow template: {template_id}")
    definition = dict(template)
    definition["inputs"] = dict(inputs or {})
    definition["requester"] = requester
    return definition


def _deep_copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_deep_copy(v) for v in value]
    return value
