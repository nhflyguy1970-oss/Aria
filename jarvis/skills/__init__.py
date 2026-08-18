"""ARIA's skills system — reusable capabilities above actions, below agents.

A skill names a meaningful operation, declares the authority it needs, and
composes existing ARIA subsystems. It deliberately owns none of them: missions
provide persistence, specialized agents provide permissions, and research,
evidence, computer use and the coding agent provide the actual work.
"""

from jarvis.skills.builtin import CATALOG, load_builtin_skills
from jarvis.skills.contracts import ContractError, validate_payload
from jarvis.skills.definitions import (
    ANALYSIS,
    BROWSER,
    CATEGORIES,
    CODING,
    EVIDENCE,
    HIGH_IMPACT,
    IMPACTS,
    LOW_IMPACT,
    MODIFY,
    PROCEDURE,
    READ,
    REPOSITORY,
    RESEARCH,
    SCHEMA_VERSION,
    SkillDefinition,
    SkillDefinitionError,
    compatible,
    max_impact,
    parse_version,
    validate,
)
from jarvis.skills.executor import (
    BOUNDED,
    BOUNDS,
    CANCELLED,
    DENIED,
    FAILED,
    INVALID,
    PARTIAL,
    STATUSES,
    SUCCESS,
    TIMED_OUT,
    UNAVAILABLE,
    UNSUCCESSFUL,
    SkillBounded,
    SkillCancelled,
    SkillContext,
    SkillDenied,
    SkillError,
    SkillTimeout,
    check_authority,
    execute,
    status_of,
)
from jarvis.skills.missions import create_skill_mission, plan_steps
from jarvis.skills.registry import (
    SkillNotFound,
    SkillRegistryError,
    VersionUnavailable,
    dependency_order,
    detect_cycle,
    discover,
    effective_actions,
    effective_impact,
    explain,
    get,
    implementation,
    list_skills,
    register,
    reset,
    resolve,
    set_enabled,
    unregister,
    validate_dependencies,
    versions,
)
from jarvis.skills.store import history

_loaded = False


def ensure_catalog_loaded() -> None:
    """Register the built-in catalog once, idempotently."""
    global _loaded
    if _loaded and list_skills():
        return
    load_builtin_skills(replace=True)
    _loaded = True


__all__ = [
    "ANALYSIS",
    "BOUNDED",
    "BOUNDS",
    "BROWSER",
    "CANCELLED",
    "CATALOG",
    "CATEGORIES",
    "CODING",
    "ContractError",
    "DENIED",
    "EVIDENCE",
    "FAILED",
    "HIGH_IMPACT",
    "IMPACTS",
    "INVALID",
    "LOW_IMPACT",
    "MODIFY",
    "PARTIAL",
    "PROCEDURE",
    "READ",
    "REPOSITORY",
    "RESEARCH",
    "SCHEMA_VERSION",
    "STATUSES",
    "SUCCESS",
    "SkillBounded",
    "SkillCancelled",
    "SkillContext",
    "SkillDefinition",
    "SkillDefinitionError",
    "SkillDenied",
    "SkillError",
    "SkillNotFound",
    "SkillRegistryError",
    "SkillTimeout",
    "TIMED_OUT",
    "UNAVAILABLE",
    "UNSUCCESSFUL",
    "VersionUnavailable",
    "check_authority",
    "compatible",
    "create_skill_mission",
    "dependency_order",
    "detect_cycle",
    "discover",
    "effective_actions",
    "effective_impact",
    "ensure_catalog_loaded",
    "execute",
    "explain",
    "get",
    "history",
    "implementation",
    "list_skills",
    "load_builtin_skills",
    "max_impact",
    "parse_version",
    "plan_steps",
    "register",
    "reset",
    "resolve",
    "set_enabled",
    "status_of",
    "unregister",
    "validate",
    "validate_dependencies",
    "validate_payload",
    "versions",
]
