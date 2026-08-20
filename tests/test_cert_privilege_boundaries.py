"""Live certification: authority must not grow by wrapping the request.

A specialist could reach an action it is explicitly denied by authoring a
workflow whose step named a specialist that holds it. The step's own agent was
checked; nobody asked whether the author was allowed to ask for that work.
"""

from __future__ import annotations

import pytest

from jarvis import autonomous_workflows as wf
from jarvis import specialized_agents as agents


def _step(action: str, agent_id: str) -> dict:
    return {
        "name": "boundary probe",
        "steps": [
            {
                "step_id": "s0",
                "action": action,
                "agent_id": agent_id,
                "params": {"objective": "x", "workspace": "/tmp"},
            }
        ],
    }


@pytest.mark.parametrize("author", ["general_specialist", "research_specialist"])
def test_a_denied_action_cannot_be_reached_through_a_named_agent(author, data_dir):
    assert agents.get(author).denies("dev_task_create"), "test premise changed"
    with pytest.raises(wf.WorkflowDefinitionError) as excinfo:
        wf.create_workflow(_step("dev_task_create", "coding_specialist"), requester=author)
    assert "may not have" in str(excinfo.value) or "may not invoke" in str(excinfo.value)


def test_an_agent_may_still_author_what_it_holds(data_dir):
    created = wf.create_workflow(
        _step("dev_task_create", "coding_specialist"), requester="coding_specialist"
    )
    assert created["id"]


def test_ordinary_delegation_is_not_broken(data_dir):
    """An action merely absent from the author's allow list may be delegated —
    that is what delegation is for."""
    author = agents.get("general_specialist")
    assert not author.denies("research_list")
    created = wf.create_workflow(
        {
            "name": "delegate",
            "steps": [
                {
                    "step_id": "s0",
                    "action": "research_list",
                    "agent_id": "research_specialist",
                    "params": {},
                }
            ],
        },
        requester="general_specialist",
    )
    assert created["id"]


def test_unattributed_workflows_keep_working(data_dir):
    """No requester means no author to check — the step agent check still applies."""
    created = wf.create_workflow(
        {
            "name": "no author",
            "steps": [
                {
                    "step_id": "s0",
                    "action": "mission_list",
                    "agent_id": "general_specialist",
                    "params": {"limit": 1},
                }
            ],
        }
    )
    assert created["id"]


def test_the_author_identity_is_stamped_not_trusted(data_dir, monkeypatch):
    """Otherwise the check is decorative: an agent would just name someone else."""
    import jarvis.handlers.registry as registry
    from jarvis.specialized_agents.invoke import call_action

    seen: dict = {}
    monkeypatch.setattr(
        registry, "call_action", lambda assistant, action, params, message: seen.update(params)
    )
    call_action(
        agents.get("general_specialist"),
        None,
        "workflow_create",
        {"requester": "coding_specialist", "definition": {}},
    )
    assert seen["requester"] == "general_specialist"


def test_denies_is_distinct_from_not_permitted(data_dir):
    agent = agents.get("general_specialist")
    assert agent.denies("dev_task_create") and not agent.permits("dev_task_create")
    # Absent from the allow list, but not forbidden.
    assert not agent.denies("research_create")


def test_a_refused_browser_action_is_reported_as_refused(data_dir):
    """It was classified "internal" — telling the caller ARIA broke when it had
    in fact said no."""
    from jarvis.computer_use import engine, sessions

    session = sessions.create(owner="research_specialist")
    out = engine.perform(
        session["id"],
        "download",
        {"url": "https://example.com/f.zip"},
        agent_id="research_specialist",
    )
    assert out["ok"] is False
    assert out["error_kind"] == engine.ERR_PERMISSION
