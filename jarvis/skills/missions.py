"""Mission integration — durable, resumable skill execution.

There is no skills worker, queue or checkpoint system here: a long-running
skill becomes an ordinary mission whose steps dispatch the existing skill_step
action, so persistence, checkpointing, cancellation, retry and recovery all
come from the mission engine that already does those things.
"""

from __future__ import annotations

from typing import Any

from jarvis.skills import registry


def plan_steps(
    skill_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    version: str = "",
    requester: str = "",
) -> list[dict[str, Any]]:
    """One mission step per skill in dependency order, dependencies first."""
    defn = registry.resolve(skill_id, version, strategy="compatible" if version else "latest")
    order = registry.dependency_order(defn)
    steps = []
    for dep_id in order:
        if dep_id == defn.skill_id:
            continue
        child = registry.get(dep_id)
        if child:
            steps.append(
                {
                    "name": f"skill:{child.skill_id}",
                    "action": "skill_step",
                    "params": {
                        "skill_id": child.skill_id,
                        "version": child.version,
                        "requester": requester,
                        "inputs": dict(inputs or {}),
                        "dependency_of": defn.skill_id,
                    },
                }
            )
    steps.append(
        {
            "name": f"skill:{defn.skill_id}",
            "action": "skill_step",
            "params": {
                "skill_id": defn.skill_id,
                "version": defn.version,
                "requester": requester,
                "inputs": dict(inputs or {}),
            },
        }
    )
    return steps


def create_skill_mission(
    skill_id: str,
    inputs: dict[str, Any] | None = None,
    *,
    version: str = "",
    requester: str = "",
    objective: str = "",
) -> str:
    """Create a durable mission that executes a skill through the mission engine."""
    from jarvis import missions

    defn = registry.resolve(skill_id, version, strategy="compatible" if version else "latest")
    steps = plan_steps(skill_id, inputs, version=version, requester=requester)
    mission_id = missions.create_mission(
        objective or f"Run skill {defn.ref()}", steps=steps, kind="skill"
    )
    # Each step has to know which mission owns it: that is how the running
    # skill sees a cancellation request mid-flight, and how an invocation is
    # linked back to its mission afterwards. The id only exists now.
    from jarvis.missions import store as mission_store

    for step in steps:
        step["params"]["mission_id"] = mission_id
    mission_store.set_steps(mission_id, steps)
    return mission_id
