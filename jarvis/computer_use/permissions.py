"""Browser permission mapping onto the Milestone 5 agent model.

Each impact class maps to a registry action, so browser authority is granted by
the same definitions and the same deny-beats-allow rule as everything else. No
second permission framework.
"""

from __future__ import annotations

from jarvis.computer_use.actions import HIGH_IMPACT, INTERACT, READ, impact_of

# Registry actions that gate each impact class.
READ_ACTION = "browser_use_read"
INTERACT_ACTION = "browser_use_interact"
HIGH_IMPACT_ACTION = "browser_use_high_impact"

GATE = {READ: READ_ACTION, INTERACT: INTERACT_ACTION, HIGH_IMPACT: HIGH_IMPACT_ACTION}


class BrowserPermissionDenied(PermissionError):
    """The agent may not perform this class of browser action."""


def gate_for(action: str) -> str:
    return GATE[impact_of(action)]


def agent_may(agent_id: str, action: str) -> bool:
    from jarvis import specialized_agents as agents

    agent = agents.get(agent_id)
    if not agent or not agent.enabled:
        return False
    return agent.permits(gate_for(action))


def check_agent_action(agent_id: str, action: str) -> None:
    if not agent_may(agent_id, action):
        raise BrowserPermissionDenied(
            f"Agent {agent_id!r} is not permitted {impact_of(action)} browser actions "
            f"(needs {gate_for(action)!r} for {action!r})"
        )
