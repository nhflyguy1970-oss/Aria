"""Specialized agent definitions — role, capabilities, permissions, contracts.

A specialized agent is a declarative capability: what it is for, what it may
do, and what it must be given. Definitions are data, not code paths, so a new
specialist is added by declaring one rather than by changing the framework.

Tool permissions are declared here and enforced at invocation. A specialist
never inherits the process's full authority: it may call only the actions its
definition allows, and `denied_actions` always wins over `allowed_actions`.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

SCHEMA_VERSION = 1


class AgentDefinitionError(ValueError):
    """Raised when an agent definition is malformed."""


@dataclass(frozen=True)
class AgentDefinition:
    """An immutable specialist declaration.

    Frozen because a definition is a contract: invocation must not be able to
    quietly widen an agent's permissions by mutating the object it was handed.
    """

    id: str
    name: str
    role: str
    description: str
    capabilities: tuple[str, ...] = ()
    responsibilities: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    system_instructions: str = ""
    allowed_actions: tuple[str, ...] = ()
    denied_actions: tuple[str, ...] = ()
    preferred_model_role: str = "general"
    model_requirements: tuple[str, ...] = ()
    input_contract: tuple[str, ...] = ("task",)
    output_contract: tuple[str, ...] = ("ok", "agent_id", "result")
    version: int = 1
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------------------- access

    def permits(self, action: str) -> bool:
        """Deny wins. A wildcard in allowed_actions still cannot override a deny."""
        name = (action or "").strip()
        if not name:
            return False
        if name in self.denied_actions:
            return False
        if "*" in self.allowed_actions:
            return True
        return name in self.allowed_actions

    def matches(self, capability: str) -> bool:
        return (capability or "").strip().lower() in {c.lower() for c in self.capabilities}

    def to_dict(self, *, include_instructions: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "responsibilities": list(self.responsibilities),
            "limitations": list(self.limitations),
            "allowed_actions": list(self.allowed_actions),
            "denied_actions": list(self.denied_actions),
            "preferred_model_role": self.preferred_model_role,
            "model_requirements": list(self.model_requirements),
            "input_contract": list(self.input_contract),
            "output_contract": list(self.output_contract),
            "version": self.version,
            "enabled": self.enabled,
            "schema_version": SCHEMA_VERSION,
            "metadata": dict(self.metadata),
        }
        if include_instructions:
            data["system_instructions"] = self.system_instructions
        return data

    def with_enabled(self, enabled: bool) -> AgentDefinition:
        return replace(self, enabled=enabled)


def validate(definition: AgentDefinition) -> AgentDefinition:
    """Reject a definition that could not be safely invoked."""
    if not isinstance(definition, AgentDefinition):
        raise AgentDefinitionError("Not an AgentDefinition")
    for required in ("id", "name", "role", "description"):
        if not str(getattr(definition, required) or "").strip():
            raise AgentDefinitionError(f"Agent definition missing {required}")
    if not definition.id.replace("_", "").replace("-", "").isalnum():
        raise AgentDefinitionError(f"Invalid agent id: {definition.id!r}")
    if not definition.capabilities:
        raise AgentDefinitionError(f"Agent {definition.id} declares no capabilities")
    if not definition.allowed_actions:
        raise AgentDefinitionError(f"Agent {definition.id} declares no allowed actions")
    if definition.version < 1:
        raise AgentDefinitionError("Agent version must be >= 1")
    overlap = set(definition.allowed_actions) & set(definition.denied_actions)
    if overlap:
        # Deny would win anyway; an explicit contradiction is a definition bug.
        raise AgentDefinitionError(f"Agent {definition.id} allows and denies: {sorted(overlap)}")
    return definition


# ---------------------------------------------------------------- built-ins
# Actions map to capabilities ARIA already has. Nothing here grants a
# specialist authority the corresponding ARIA action does not already have.

# Requesting work from another specialist is itself a permissioned action, so a
# specialist cannot delegate unless its definition says it may.
DELEGATE_ACTION = "collab_delegate"

# Evidence authority is deliberately split: reading provenance is broad, but
# creating evidence, creating claims and performing verification are separate
# permissions so a specialist cannot mark its own unsupported claim verified.
EVIDENCE_READ = (
    "evidence_claim_get",
    "evidence_provenance",
    "evidence_list_claims",
    "evidence_conflicts",
)
EVIDENCE_WRITE = ("evidence_source_add", "evidence_add", "evidence_claim_add", "evidence_link")
EVIDENCE_VERIFY = ("evidence_verify",)

# Browser authority is granted by impact class, least privilege first. No
# specialist gets high-impact browser actions by default — those cause
# real-world side effects and must be granted deliberately.
BROWSER_READ = ("browser_use_read",)
BROWSER_INTERACT = ("browser_use_interact",)
BROWSER_HIGH_IMPACT = ("browser_use_high_impact",)

# Autonomous development authority. Deliberately excludes deployment, history
# rewriting and force-push: the coding agent may propose and commit its own
# work, never reshape the repository or touch production.
CODING_DEV = (
    "dev_task_create",
    "dev_task_status",
    "dev_task_list",
    "dev_task_run",
    "dev_task_commit",
    "dev_task_cancel",
    "dev_task_recover",
    "dev_step",
    "dev_command",
)
CODING_HIGH_IMPACT = ("dev_force_push", "dev_history_rewrite", "dev_deploy")

# Skills layer. Holding these lets an agent reach the skills system at all; what
# it can actually run is still decided by the underlying action permissions
# above, which stay authoritative. High-impact skill authority and the shell
# playbook runner are denied to every built-in agent.
SKILL_USE = (
    "skill_discover",
    "skill_describe",
    "skill_invoke",
    "skill_cancel",
    "skill_history",
    "skill_catalog",
)
SKILL_HIGH_IMPACT = ("skill_invoke_high_impact", "skill_run")

# MCP is an external authority boundary. Holding these lets an agent reach the
# ecosystem at all; each provider still names which agents it accepts, and a
# provider's own claims never grant an agent anything. High-impact MCP tools
# and trust changes are denied to every built-in agent.
MCP_USE = (
    "mcp_provider_list",
    "mcp_provider_status",
    "mcp_discover",
    "mcp_tools",
    "mcp_invoke",
    "mcp_resource",
    "mcp_prompt",
    "mcp_history",
)
MCP_HIGH_IMPACT = ("mcp_invoke_high_impact", "mcp_set_trust")

_DESTRUCTIVE = (
    "aria_self_fix",
    "self_upgrade_run",
    "mission_cancel",
    "research_cancel",
)

RESEARCH_SPECIALIST = AgentDefinition(
    id="research_specialist",
    name="Research Specialist",
    role="research",
    description="Plans research, gathers sources, weighs evidence and synthesises with citations.",
    capabilities=("research", "search", "evidence", "citations", "synthesis"),
    responsibilities=(
        "Decompose an objective into answerable questions",
        "Gather and deduplicate sources",
        "Attach evidence to claims and preserve disagreement",
        "Synthesise with citations traceable to inspected sources",
    ),
    limitations=(
        "Cannot modify code or repository state",
        "Reports uncertainty rather than resolving contested evidence",
    ),
    system_instructions=(
        "You are ARIA's research specialist. Ground every claim in collected evidence. "
        "Never fabricate a citation. Preserve disagreement between sources instead of "
        "choosing one silently. State what remains unresolved."
    ),
    allowed_actions=(
        "research_create",
        "research_status",
        "research_list",
        "research_report",
        "research_run",
        "research_step",
        "mission_status",
        DELEGATE_ACTION,
        *EVIDENCE_READ,
        *EVIDENCE_WRITE,
        *EVIDENCE_VERIFY,
        *BROWSER_READ,
        *BROWSER_INTERACT,
        *SKILL_USE,
        *MCP_USE,
    ),
    denied_actions=_DESTRUCTIVE
    + BROWSER_HIGH_IMPACT
    + CODING_DEV
    + CODING_HIGH_IMPACT
    + SKILL_HIGH_IMPACT
    + MCP_HIGH_IMPACT,
    preferred_model_role="general",
    model_requirements=("long_context",),
    input_contract=("task",),
    output_contract=("ok", "agent_id", "result"),
    metadata={"delegates_to": "jarvis.research", "catalog_id": "researcher"},
)

CODING_SPECIALIST = AgentDefinition(
    id="coding_specialist",
    name="Coding Specialist",
    role="coding",
    description="Analyses, diagnoses and proposes code changes using ARIA's coding infrastructure.",
    capabilities=("coding", "debugging", "testing", "code_review", "repository"),
    responsibilities=(
        "Reason about the repository",
        "Diagnose defects and propose changes for review",
        "Run tests through existing tooling",
    ),
    limitations=(
        "Proposes changes for approval rather than applying them unreviewed",
        "Cannot run research or web collection",
    ),
    system_instructions=(
        "You are ARIA's coding specialist. Prefer minimal, reviewable changes that match "
        "surrounding code. Diagnose before proposing. Never claim a test passed without running it."
    ),
    allowed_actions=(
        "git_status",
        "run_tests",
        "coding_task_status",
        "code_search",
        "mission_status",
        *CODING_DEV,
        *SKILL_USE,
        *MCP_USE,
    ),
    denied_actions=_DESTRUCTIVE
    + SKILL_HIGH_IMPACT
    + MCP_HIGH_IMPACT
    + ("research_create", "research_run")
    + EVIDENCE_READ
    + EVIDENCE_WRITE
    + EVIDENCE_VERIFY
    + BROWSER_READ
    + BROWSER_INTERACT
    + BROWSER_HIGH_IMPACT
    + CODING_HIGH_IMPACT,
    preferred_model_role="coder",
    model_requirements=("code",),
    metadata={"catalog_id": "coder"},
)

ANALYSIS_SPECIALIST = AgentDefinition(
    id="analysis_specialist",
    name="Analysis Specialist",
    role="analysis",
    description="Structured reasoning, comparison and analysis over supplied information.",
    capabilities=("analysis", "comparison", "reasoning", "data", "summarization"),
    responsibilities=(
        "Analyse supplied material without gathering new sources",
        "Compare options against stated criteria",
        "Make reasoning and assumptions explicit",
    ),
    limitations=(
        "Does not gather new sources — analyses what it is given",
        "Cannot modify code or repository state",
    ),
    system_instructions=(
        "You are ARIA's analysis specialist. Work only from supplied material. "
        "State assumptions explicitly and separate observation from inference."
    ),
    allowed_actions=(
        "data_analyze",
        "document_summarize",
        "mission_status",
        DELEGATE_ACTION,
        *EVIDENCE_READ,
        *EVIDENCE_VERIFY,
        *BROWSER_READ,
        *SKILL_USE,
        *MCP_USE,
    ),
    denied_actions=_DESTRUCTIVE
    + ("research_create", "run_tests")
    + EVIDENCE_WRITE
    + BROWSER_INTERACT
    + BROWSER_HIGH_IMPACT
    + CODING_DEV
    + CODING_HIGH_IMPACT
    + SKILL_HIGH_IMPACT
    + MCP_HIGH_IMPACT,
    preferred_model_role="general",
    metadata={"catalog_id": "synthesizer"},
)

GENERAL_SPECIALIST = AgentDefinition(
    id="general_specialist",
    name="General Assistant",
    role="general",
    description="General-purpose ARIA assistance and the fallback when no specialist fits better.",
    capabilities=("general", "conversation", "explanation", "fallback"),
    responsibilities=(
        "Handle requests with no better-matched specialist",
        "Explain ARIA's capabilities",
    ),
    limitations=("Not a substitute for a domain specialist on specialised work",),
    system_instructions=(
        "You are ARIA's general assistant. Answer directly. If a specialist would serve "
        "the request better, say which one."
    ),
    allowed_actions=(
        "mission_status",
        "mission_list",
        "research_list",
        "agent_list",
        DELEGATE_ACTION,
        *EVIDENCE_READ,
        *SKILL_USE,
        "mcp_provider_list",
        "mcp_provider_status",
        "mcp_tools",
    ),
    denied_actions=_DESTRUCTIVE
    + SKILL_HIGH_IMPACT
    + MCP_HIGH_IMPACT
    + ("mcp_invoke", "mcp_resource", "mcp_prompt", "mcp_discover")
    + BROWSER_READ
    + BROWSER_INTERACT
    + BROWSER_HIGH_IMPACT
    + CODING_DEV
    + CODING_HIGH_IMPACT,
    preferred_model_role="general",
    metadata={"fallback": True},
)

BUILTIN_AGENTS: tuple[AgentDefinition, ...] = (
    RESEARCH_SPECIALIST,
    CODING_SPECIALIST,
    ANALYSIS_SPECIALIST,
    GENERAL_SPECIALIST,
)

FALLBACK_AGENT_ID = GENERAL_SPECIALIST.id
