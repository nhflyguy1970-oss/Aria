"""Skill registry — registration, versioned lookup, dependencies, discovery.

Selection here is deterministic: every discovery result carries the reasons it
matched, so nothing has to be taken on trust and nothing pretends to be
semantic understanding.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from jarvis.skills.definitions import (
    SkillDefinition,
    SkillDefinitionError,
    compatible,
    impact_rank,
    parse_version,
    validate,
    version_key,
)

# skill_id -> version -> (definition, implementation)
_SKILLS: dict[str, dict[str, tuple[SkillDefinition, Callable[..., Any]]]] = {}
_lock = threading.RLock()


class SkillRegistryError(RuntimeError):
    """Registration or lookup that must fail loudly."""


class SkillNotFound(SkillRegistryError):
    pass


class VersionUnavailable(SkillRegistryError):
    """A requested version exists in no compatible form. Never substituted."""


def reset() -> None:
    """Drop every registration. Used by tests and by catalog reload."""
    with _lock:
        _SKILLS.clear()


def register(
    defn: SkillDefinition,
    implementation: Callable[..., Any],
    *,
    replace: bool = False,
) -> SkillDefinition:
    """Validate and register a skill. Fails closed on anything malformed."""
    validate(defn)
    if not callable(implementation):
        raise SkillDefinitionError(f"{defn.skill_id}: implementation is not callable")
    with _lock:
        versions = _SKILLS.setdefault(defn.skill_id, {})
        if defn.version in versions and not replace:
            raise SkillRegistryError(
                f"Skill {defn.ref()} is already registered; bump the version to publish a change"
            )
        versions[defn.version] = (defn, implementation)
        try:
            # A registration that breaks the graph must not be left behind.
            validate_dependencies(defn)
        except SkillRegistryError:
            del versions[defn.version]
            if not versions:
                _SKILLS.pop(defn.skill_id, None)
            raise
    return defn


def unregister(skill_id: str, version: str = "") -> bool:
    """Remove one version, or every version when no version is given."""
    with _lock:
        versions = _SKILLS.get(skill_id)
        if not versions:
            return False
        if version:
            if version not in versions:
                return False
            del versions[version]
            if not versions:
                _SKILLS.pop(skill_id, None)
            return True
        _SKILLS.pop(skill_id, None)
        return True


def versions(skill_id: str) -> list[str]:
    with _lock:
        return sorted((_SKILLS.get(skill_id) or {}), key=version_key)


def get(skill_id: str, version: str = "") -> SkillDefinition | None:
    """Resolve a definition. Without a version, the latest registered one."""
    entry = _entry(skill_id, version)
    return entry[0] if entry else None


def implementation(skill_id: str, version: str = "") -> Callable[..., Any] | None:
    entry = _entry(skill_id, version)
    return entry[1] if entry else None


def _entry(skill_id: str, version: str = "") -> tuple[SkillDefinition, Callable[..., Any]] | None:
    with _lock:
        available = _SKILLS.get(skill_id)
        if not available:
            return None
        if not version:
            latest = max(available, key=version_key)
            return available[latest]
        return available.get(version)


def resolve(skill_id: str, version: str = "", *, strategy: str = "compatible") -> SkillDefinition:
    """Deterministic version selection.

    strategy 'exact'      — that version or nothing
    strategy 'compatible' — same major, >= requested; highest such version
    strategy 'latest'     — the newest registered version

    An incompatible version is never silently substituted.
    """
    with _lock:
        available = _SKILLS.get(skill_id)
        if not available:
            raise SkillNotFound(f"No such skill: {skill_id}")
        names = sorted(available, key=version_key)

        if strategy == "latest" or (not version and strategy != "exact"):
            return available[names[-1]][0]
        if not version:
            raise VersionUnavailable(f"{skill_id}: an exact lookup needs a version")
        parse_version(version)
        if strategy == "exact":
            if version not in available:
                raise VersionUnavailable(
                    f"{skill_id}: version {version} is not registered "
                    f"(have {', '.join(names)}); refusing to substitute"
                )
            return available[version][0]
        if strategy != "compatible":
            raise SkillRegistryError(f"Unknown version strategy: {strategy!r}")
        matches = [n for n in names if compatible(version, n)]
        if not matches:
            raise VersionUnavailable(
                f"{skill_id}: no version compatible with {version} "
                f"(have {', '.join(names)}); refusing to substitute across a major version"
            )
        return available[matches[-1]][0]


def list_skills(*, include_disabled: bool = True) -> list[SkillDefinition]:
    with _lock:
        out = []
        for available in _SKILLS.values():
            for version in sorted(available, key=version_key):
                defn = available[version][0]
                if include_disabled or defn.enabled:
                    out.append(defn)
    return sorted(out, key=lambda d: (d.skill_id, version_key(d.version)))


def set_enabled(skill_id: str, enabled: bool, version: str = "") -> SkillDefinition:
    """Enable or disable in place, without mutating the frozen definition."""
    from dataclasses import replace as dc_replace

    with _lock:
        available = _SKILLS.get(skill_id) or {}
        target = version or (max(available, key=version_key) if available else "")
        entry = available.get(target)
        if not entry:
            raise SkillNotFound(f"No such skill: {skill_id}{'@' + version if version else ''}")
        defn, impl = entry
        updated = dc_replace(defn, enabled=enabled)
        available[target] = (updated, impl)
        return updated


# ------------------------------------------------------------------ dependencies


def dependency_edges(defn: SkillDefinition) -> dict[str, list[str]]:
    """Full transitive edge map reachable from defn, by skill_id.

    Iterative on purpose: a deep chain must not depend on interpreter stack
    depth to be validated.
    """
    edges: dict[str, list[str]] = {}
    stack = [defn]
    seen_defs = {defn.skill_id}
    while stack:
        current = stack.pop()
        deps = [dep_id for dep_id, _ in current.dependencies]
        edges.setdefault(current.skill_id, [])
        for dep_id in deps:
            if dep_id not in edges[current.skill_id]:
                edges[current.skill_id].append(dep_id)
        for dep_id, dep_version in current.dependencies:
            child = _resolve_dependency(current, dep_id, dep_version)
            if child.skill_id not in seen_defs:
                seen_defs.add(child.skill_id)
                stack.append(child)
            else:
                edges.setdefault(child.skill_id, [])
    return edges


def _resolve_dependency(parent: SkillDefinition, dep_id: str, dep_version: str) -> SkillDefinition:
    try:
        return resolve(dep_id, dep_version, strategy="compatible")
    except SkillNotFound as exc:
        raise SkillRegistryError(
            f"{parent.ref()} depends on missing skill {dep_id}@{dep_version}"
        ) from exc
    except VersionUnavailable as exc:
        raise SkillRegistryError(f"{parent.ref()} dependency unsatisfiable: {exc}") from exc


def detect_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """Return a cycle path if one exists, else None.

    Iterative DFS with an explicit stack, matching the collaboration graph, so
    a deeply nested skill graph cannot overflow the call stack.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour = dict.fromkeys(edges, WHITE)
    for node in edges:
        for dep in edges[node]:
            colour.setdefault(dep, WHITE)

    for start in list(colour):
        if colour[start] != WHITE:
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        path: list[str] = []
        colour[start] = GREY
        path.append(start)
        while stack:
            node, index = stack[-1]
            children = edges.get(node) or []
            if index < len(children):
                stack[-1] = (node, index + 1)
                child = children[index]
                state = colour.get(child, WHITE)
                if state == GREY:
                    return [*path[path.index(child) :], child]
                if state == WHITE:
                    colour[child] = GREY
                    path.append(child)
                    stack.append((child, 0))
            else:
                colour[node] = BLACK
                stack.pop()
                if path:
                    path.pop()
    return None


def validate_dependencies(defn: SkillDefinition) -> dict[str, list[str]]:
    """Reject missing, unsatisfiable or circular dependencies."""
    edges = dependency_edges(defn)
    cycle = detect_cycle(edges)
    if cycle:
        raise SkillRegistryError(f"{defn.skill_id}: dependency cycle {' -> '.join(cycle)}")
    return edges


def dependency_order(defn: SkillDefinition) -> list[str]:
    """Dependencies first, deterministic, so a chain executes in a known order."""
    edges = validate_dependencies(defn)
    order: list[str] = []
    seen: set[str] = set()
    stack: list[tuple[str, bool]] = [(defn.skill_id, False)]
    while stack:
        node, expanded = stack.pop()
        if expanded:
            if node not in seen:
                seen.add(node)
                order.append(node)
            continue
        if node in seen:
            continue
        stack.append((node, True))
        for child in sorted(edges.get(node) or [], reverse=True):
            if child not in seen:
                stack.append((child, False))
    return order


def effective_actions(defn: SkillDefinition) -> list[str]:
    """Every action this skill can reach, including through dependencies."""
    actions = set(defn.required_actions)
    for dep_id in dependency_order(defn):
        if dep_id == defn.skill_id:
            continue
        child = get(dep_id)
        if child:
            actions.update(child.required_actions)
    return sorted(actions)


def effective_impact(defn: SkillDefinition) -> str:
    """The highest impact anywhere in the graph. A wrapper cannot look safe."""
    from jarvis.skills.definitions import max_impact

    impacts = [defn.impact]
    for dep_id in dependency_order(defn):
        if dep_id == defn.skill_id:
            continue
        child = get(dep_id)
        if child:
            impacts.append(child.impact)
    return max_impact(*impacts)


# -------------------------------------------------------------------- discovery


def discover(
    *,
    query: str = "",
    skill_id: str = "",
    category: str = "",
    tag: str = "",
    capability: str = "",
    action: str = "",
    agent_id: str = "",
    impact_at_most: str = "",
    include_disabled: bool = False,
) -> list[dict[str, Any]]:
    """Deterministic filtered discovery. Each hit says why it matched."""
    results = []
    for defn in list_skills(include_disabled=True):
        reasons: list[str] = []
        if skill_id and defn.skill_id != skill_id:
            continue
        if skill_id:
            reasons.append(f"skill_id == {skill_id}")
        if category:
            if defn.category != category:
                continue
            reasons.append(f"category == {category}")
        if tag:
            if tag.lower() not in {t.lower() for t in defn.tags}:
                continue
            reasons.append(f"tag {tag!r}")
        if capability:
            if not defn.matches_capability(capability):
                continue
            reasons.append(f"capability {capability!r}")
        if action:
            if action not in effective_actions(defn):
                continue
            reasons.append(f"uses action {action!r}")
        if agent_id:
            if not defn.permits_agent(agent_id):
                continue
            reasons.append(f"agent {agent_id} not denied")
        if impact_at_most:
            if impact_rank(effective_impact(defn)) > impact_rank(impact_at_most):
                continue
            reasons.append(f"effective impact <= {impact_at_most}")
        if query:
            text = " ".join(
                [defn.skill_id, defn.name, defn.description, defn.purpose, " ".join(defn.tags)]
            ).lower()
            needle = query.strip().lower()
            if needle not in text:
                continue
            reasons.append(f"text match on {query.strip()!r}")

        if not defn.enabled:
            if not include_disabled:
                continue
            reasons.append("DISABLED — cannot be executed")
        if not reasons:
            reasons.append("listed (no filters applied)")

        results.append(
            {
                "skill_id": defn.skill_id,
                "version": defn.version,
                "name": defn.name,
                "description": defn.description,
                "category": defn.category,
                "tags": list(defn.tags),
                "capabilities": list(defn.capabilities),
                "impact": defn.impact,
                "effective_impact": effective_impact(defn),
                "enabled": defn.enabled,
                "available": defn.enabled,
                "dependencies": [list(d) for d in defn.dependencies],
                "required_actions": list(defn.required_actions),
                "effective_actions": effective_actions(defn),
                "match_reasons": reasons,
            }
        )
    return results


def explain(skill_id: str, version: str = "") -> dict[str, Any] | None:
    """Everything an operator needs to judge a skill before running it."""
    defn = get(skill_id, version)
    if not defn:
        return None
    return {
        **defn.to_dict(),
        "ref": defn.ref(),
        "versions": versions(skill_id),
        "effective_actions": effective_actions(defn),
        "effective_impact": effective_impact(defn),
        "dependency_order": dependency_order(defn),
        "gate_action": defn.gate_action(),
    }
