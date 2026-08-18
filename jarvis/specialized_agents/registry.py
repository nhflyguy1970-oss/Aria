"""Specialized agent registry — registration, lookup, and explainable selection.

Built-ins are rebuilt from the immutable definitions on every reset, so tests
are order-independent: nothing a test registers can leak into the next one.
Selection is deterministic metadata matching, and it says so — the result
carries the signals that produced it rather than implying semantic reasoning
the framework does not perform.
"""

from __future__ import annotations

import threading
from typing import Any

from jarvis.specialized_agents.definitions import (
    BUILTIN_AGENTS,
    FALLBACK_AGENT_ID,
    AgentDefinition,
    AgentDefinitionError,
    validate,
)

_lock = threading.RLock()
_agents: dict[str, AgentDefinition] = {}

# Task keywords -> capability. Deterministic and inspectable on purpose: this
# is metadata matching, not semantic routing, and the milestone requires the
# distinction to be explicit rather than dressed up.
CAPABILITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "coding": ("code", "coding", "bug", "debug", "refactor", "function", "compile", "stack trace"),
    "debugging": ("debug", "traceback", "exception", "crash", "failing test"),
    "testing": ("test", "tests", "pytest", "unit test", "regression"),
    "repository": ("repo", "repository", "git", "branch", "commit", "diff"),
    "research": ("research", "investigate", "find out", "look up", "sources", "literature"),
    "search": ("search", "web", "google", "browse"),
    "evidence": ("evidence", "citation", "cite", "verify", "corroborate"),
    "analysis": ("analyse", "analyze", "analysis", "compare", "evaluate", "assess", "trade-off"),
    "comparison": ("compare", "versus", " vs ", "difference between"),
    "data": ("data", "csv", "dataset", "statistics", "metrics"),
    "summarization": ("summarize", "summarise", "summary", "tl;dr"),
}


def reset(agents: list[AgentDefinition] | None = None) -> None:
    """Restore the registry to the built-ins (or an explicit set, for tests)."""
    with _lock:
        _agents.clear()
        for definition in agents if agents is not None else BUILTIN_AGENTS:
            _agents[definition.id] = validate(definition)


def _ensure_loaded() -> None:
    if not _agents:
        reset()


def register(definition: AgentDefinition, *, replace_existing: bool = False) -> AgentDefinition:
    """Add a specialist. Duplicate ids are rejected unless replacing explicitly."""
    _ensure_loaded()
    validate(definition)
    with _lock:
        if definition.id in _agents and not replace_existing:
            raise AgentDefinitionError(f"Agent already registered: {definition.id}")
        _agents[definition.id] = definition
    return definition


def unregister(agent_id: str) -> bool:
    _ensure_loaded()
    with _lock:
        return _agents.pop(agent_id, None) is not None


def set_enabled(agent_id: str, enabled: bool) -> AgentDefinition | None:
    _ensure_loaded()
    with _lock:
        current = _agents.get(agent_id)
        if not current:
            return None
        updated = current.with_enabled(enabled)
        _agents[agent_id] = updated
        return updated


def get(agent_id: str) -> AgentDefinition | None:
    _ensure_loaded()
    with _lock:
        return _agents.get((agent_id or "").strip())


def list_agents(*, include_disabled: bool = False) -> list[AgentDefinition]:
    _ensure_loaded()
    with _lock:
        items = list(_agents.values())
    items.sort(key=lambda a: a.id)  # deterministic ordering
    return [a for a in items if include_disabled or a.enabled]


def find_by_capability(capability: str) -> list[AgentDefinition]:
    return [a for a in list_agents() if a.matches(capability)]


def capabilities() -> dict[str, list[str]]:
    """Capability -> agent ids offering it."""
    out: dict[str, list[str]] = {}
    for agent in list_agents():
        for cap in agent.capabilities:
            out.setdefault(cap, []).append(agent.id)
    return {k: sorted(v) for k, v in sorted(out.items())}


def detect_capabilities(task: str) -> list[str]:
    """Capabilities implied by a task string, most specific first."""
    text = f" {(task or '').lower()} "
    hits: list[tuple[int, str]] = []
    for capability, keywords in CAPABILITY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score:
            hits.append((score, capability))
    hits.sort(key=lambda pair: (-pair[0], pair[1]))
    return [capability for _, capability in hits]


def select(task: str, *, required_capability: str = "") -> dict[str, Any]:
    """Choose a specialist for a task and explain the choice.

    Always returns a selection: when nothing matches, the fallback specialist is
    chosen and the result says the match was a fallback, not a real match.
    """
    _ensure_loaded()
    if required_capability:
        candidates = find_by_capability(required_capability)
        if not candidates:
            return {
                "agent_id": None,
                "agent": None,
                "matched": False,
                "reason": f"No enabled agent provides capability {required_capability!r}",
                "requested_capabilities": [required_capability],
                "matched_capabilities": [],
                "candidates": [],
            }
        chosen = candidates[0]
        return {
            "agent_id": chosen.id,
            "agent": chosen.to_dict(),
            "matched": True,
            "reason": f"Explicitly required capability {required_capability!r}",
            "requested_capabilities": [required_capability],
            "matched_capabilities": [required_capability],
            "candidates": [c.id for c in candidates],
            "selection_method": "explicit_capability",
        }

    detected = detect_capabilities(task)
    scored: list[tuple[int, list[str], AgentDefinition]] = []
    for agent in list_agents():
        matched = [c for c in detected if agent.matches(c)]
        if matched:
            scored.append((len(matched), matched, agent))
    # Highest number of matched capabilities wins; ties break on id for determinism.
    scored.sort(key=lambda row: (-row[0], row[2].id))

    if not scored:
        fallback = get(FALLBACK_AGENT_ID)
        return {
            "agent_id": fallback.id if fallback else None,
            "agent": fallback.to_dict() if fallback else None,
            "matched": False,
            "reason": "No capability keywords matched; using the fallback general assistant",
            "requested_capabilities": detected,
            "matched_capabilities": [],
            "candidates": [],
            "selection_method": "fallback",
        }

    _, matched, chosen = scored[0]
    return {
        "agent_id": chosen.id,
        "agent": chosen.to_dict(),
        "matched": True,
        "reason": (
            f"Task signals {matched} matched {chosen.name}'s capabilities (role: {chosen.role})"
        ),
        "requested_capabilities": detected,
        "matched_capabilities": matched,
        "candidates": [a.id for _, _, a in scored],
        "selection_method": "keyword_capability_match",
    }
