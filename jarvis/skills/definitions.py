"""Skill definitions — the declarative contract for a reusable capability.

A skill sits above the action registry and below agents and missions: it names
a meaningful operation, declares what authority it needs, and composes existing
ARIA actions and subsystems. It is deliberately data, not behaviour, so the
same definition can be validated, discovered and explained without executing
anything.

Not to be confused with jarvis.skill_database, which stores human-facing
procedure playbooks (shell steps for install/repair runbooks). Those are
exposed through this system as PROCEDURE-category skills rather than
reimplemented here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1

# Impact classification. Ordered: a composed skill takes the highest impact in
# its execution graph, so a wrapper can never look safer than what it calls.
READ = "read"
LOW_IMPACT = "low_impact"
MODIFY = "modify"
HIGH_IMPACT = "high_impact"
IMPACTS = (READ, LOW_IMPACT, MODIFY, HIGH_IMPACT)
_IMPACT_RANK = {name: i for i, name in enumerate(IMPACTS)}

# Categories the built-in catalog spans.
RESEARCH = "research"
EVIDENCE = "evidence"
BROWSER = "browser"
CODING = "coding"
ANALYSIS = "analysis"
REPOSITORY = "repository"
PROCEDURE = "procedure"
CATEGORIES = (RESEARCH, EVIDENCE, BROWSER, CODING, ANALYSIS, REPOSITORY, PROCEDURE)

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

_JSON_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


class SkillDefinitionError(ValueError):
    """A definition that must never reach the registry."""


def parse_version(text: str) -> tuple[int, int, int]:
    m = _VERSION_RE.match((text or "").strip())
    if not m:
        raise SkillDefinitionError(f"Invalid version {text!r}; expected MAJOR.MINOR.PATCH")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def version_key(text: str) -> tuple[int, int, int]:
    return parse_version(text)


def compatible(requested: str, candidate: str) -> bool:
    """Same major, and at least the requested minor.patch.

    A different major is an incompatible contract, never a silent substitute.
    """
    r = parse_version(requested)
    c = parse_version(candidate)
    return r[0] == c[0] and c >= r


def max_impact(*impacts: str) -> str:
    """The most consequential impact present. Risk never gets downgraded."""
    best = READ
    for impact in impacts:
        if impact and _IMPACT_RANK.get(impact, 0) > _IMPACT_RANK[best]:
            best = impact
    return best


def impact_rank(impact: str) -> int:
    return _IMPACT_RANK.get(impact, 0)


@dataclass(frozen=True)
class SkillDefinition:
    """An immutable skill contract.

    Frozen on purpose: an executing skill must not be able to edit its own
    declared authority, impact or dependencies part-way through a run.
    """

    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = ANALYSIS
    purpose: str = ""
    author: str = "aria"
    source: str = "builtin"
    tags: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    dependencies: tuple[tuple[str, str], ...] = ()  # (skill_id, minimum version)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    impact: str = READ
    required_permissions: tuple[str, ...] = ()
    allowed_agents: tuple[str, ...] = ()  # empty means "any agent that holds the actions"
    denied_agents: tuple[str, ...] = ()
    composable: bool = True
    model_requirements: tuple[str, ...] = ()
    timeout_s: float = 120.0
    max_depth: int = 4
    enabled: bool = True
    implementation: str = ""
    schema_version: int = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def gate_action(self) -> str:
        """The registry action an agent must hold to run a skill of this impact."""
        return HIGH_IMPACT_GATE if self.impact == HIGH_IMPACT else SKILL_GATE

    def permits_agent(self, agent_id: str) -> bool:
        """Deny beats allow, and beats an empty (open) allow list."""
        name = (agent_id or "").strip()
        if not name:
            return False
        if name in self.denied_agents:
            return False
        if not self.allowed_agents:
            return True
        return name in self.allowed_agents

    def matches_capability(self, capability: str) -> bool:
        return (capability or "").strip().lower() in {c.lower() for c in self.capabilities}

    def ref(self) -> str:
        return f"{self.skill_id}@{self.version}"

    def to_dict(self, *, include_schema: bool = True) -> dict[str, Any]:
        data = {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "purpose": self.purpose,
            "author": self.author,
            "source": self.source,
            "tags": list(self.tags),
            "capabilities": list(self.capabilities),
            "required_actions": list(self.required_actions),
            "dependencies": [list(d) for d in self.dependencies],
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
            "side_effects": list(self.side_effects),
            "impact": self.impact,
            "required_permissions": list(self.required_permissions),
            "allowed_agents": list(self.allowed_agents),
            "denied_agents": list(self.denied_agents),
            "composable": self.composable,
            "model_requirements": list(self.model_requirements),
            "timeout_s": self.timeout_s,
            "max_depth": self.max_depth,
            "enabled": self.enabled,
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
        }
        if include_schema:
            data["input_schema"] = dict(self.input_schema)
            data["output_schema"] = dict(self.output_schema)
        return data


# Gate actions live in the existing action registry, so skill authority is
# expressed in the one permission system ARIA already has.
SKILL_GATE = "skill_invoke"
HIGH_IMPACT_GATE = "skill_invoke_high_impact"


def _check_schema(schema: dict[str, Any], label: str, skill_id: str) -> None:
    if not isinstance(schema, dict):
        raise SkillDefinitionError(f"{skill_id}: {label} must be an object")
    for prop, spec in (schema.get("properties") or {}).items():
        if not isinstance(spec, dict):
            raise SkillDefinitionError(f"{skill_id}: {label} property {prop!r} must be an object")
        declared = spec.get("type")
        if declared and declared not in _JSON_TYPES:
            raise SkillDefinitionError(
                f"{skill_id}: {label} property {prop!r} has unknown type {declared!r}"
            )
    required = schema.get("required") or []
    if not isinstance(required, list):
        raise SkillDefinitionError(f"{skill_id}: {label} 'required' must be a list")
    props = schema.get("properties") or {}
    for name in required:
        if props and name not in props:
            raise SkillDefinitionError(
                f"{skill_id}: {label} requires {name!r} which it does not declare"
            )


def validate(defn: SkillDefinition) -> SkillDefinition:
    """Reject a definition before it can ever be registered or executed."""
    if not isinstance(defn, SkillDefinition):
        raise SkillDefinitionError("Not a SkillDefinition")
    if not _ID_RE.match(defn.skill_id or ""):
        raise SkillDefinitionError(
            f"Invalid skill_id {defn.skill_id!r}: lowercase, digits and underscores, 3-64 chars"
        )
    if not (defn.name or "").strip():
        raise SkillDefinitionError(f"{defn.skill_id}: name is required")
    if not (defn.description or "").strip():
        raise SkillDefinitionError(f"{defn.skill_id}: description is required")
    parse_version(defn.version)
    if defn.category not in CATEGORIES:
        raise SkillDefinitionError(f"{defn.skill_id}: unknown category {defn.category!r}")
    if defn.impact not in IMPACTS:
        raise SkillDefinitionError(f"{defn.skill_id}: unknown impact {defn.impact!r}")
    if defn.schema_version != SCHEMA_VERSION:
        raise SkillDefinitionError(
            f"{defn.skill_id}: schema_version {defn.schema_version} != {SCHEMA_VERSION}"
        )
    if defn.timeout_s <= 0:
        raise SkillDefinitionError(f"{defn.skill_id}: timeout_s must be positive")
    if defn.max_depth < 1:
        raise SkillDefinitionError(f"{defn.skill_id}: max_depth must be at least 1")

    _check_schema(defn.input_schema, "input_schema", defn.skill_id)
    _check_schema(defn.output_schema, "output_schema", defn.skill_id)

    overlap = set(defn.allowed_agents) & set(defn.denied_agents)
    if overlap:
        raise SkillDefinitionError(
            f"{defn.skill_id}: contradictory permissions, agent(s) both allowed and denied: "
            f"{sorted(overlap)}"
        )
    for dep_id, dep_version in defn.dependencies:
        if not _ID_RE.match(dep_id or ""):
            raise SkillDefinitionError(f"{defn.skill_id}: invalid dependency id {dep_id!r}")
        parse_version(dep_version)
        if dep_id == defn.skill_id:
            raise SkillDefinitionError(f"{defn.skill_id}: cannot depend on itself")
    if defn.dependencies and not defn.composable:
        raise SkillDefinitionError(
            f"{defn.skill_id}: declares dependencies but is marked non-composable"
        )
    return defn
