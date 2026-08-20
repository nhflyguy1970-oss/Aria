"""Live certification: a mission must never report success for failed work.

ARIA actions signal failure by returning ok: False. The mission engine only
treated exceptions as failures, so a mission whose step failed finished as
"completed" at 100%, with the failure buried inside its result context.
"""

from __future__ import annotations

import pytest

from jarvis import missions
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("cert_step_fails", module="general", description="probe")
def _fails(assistant, params, message):
    return err("the step genuinely failed", module="general", error_kind="probe_failure")


@register_action("cert_step_works", module="general", description="probe")
def _works(assistant, params, message):
    return ok("fine", module="general")


@pytest.fixture
def runner():
    return missions.ActionStepRunner(assistant=None)


def test_a_failing_step_fails_the_mission(data_dir, runner):
    mission_id = missions.create_mission(
        "failure", steps=[{"name": "boom", "action": "cert_step_fails", "params": {}}]
    )
    missions.run(mission_id, runner=runner)

    snapshot = missions.status(mission_id)
    assert snapshot["state"] == missions.FAILED
    assert "genuinely failed" in (snapshot["error"] or "")
    assert snapshot["progress"]["completed_steps"] == 0


def test_progress_does_not_claim_completed_steps_that_failed(data_dir, runner):
    mission_id = missions.create_mission(
        "partial",
        steps=[
            {"name": "good", "action": "cert_step_works", "params": {}},
            {"name": "bad", "action": "cert_step_fails", "params": {}},
            {"name": "never", "action": "cert_step_works", "params": {}},
        ],
    )
    missions.run(mission_id, runner=runner)

    snapshot = missions.status(mission_id)
    assert snapshot["state"] == missions.FAILED
    assert snapshot["progress"]["completed_steps"] == 1
    assert snapshot["progress"]["percent"] < 100


def test_a_succeeding_mission_still_completes(data_dir, runner):
    mission_id = missions.create_mission(
        "success", steps=[{"name": "good", "action": "cert_step_works", "params": {}}] * 2
    )
    missions.run(mission_id, runner=runner)
    assert missions.status(mission_id)["state"] == missions.COMPLETED


def test_a_step_that_returns_no_ok_field_is_not_treated_as_failure(data_dir):
    """Runners may return plain data; absence of `ok` is not a failure signal."""

    def plain_runner(step, context):
        return {"data": "some value"}

    mission_id = missions.create_mission(
        "plain", steps=[{"name": "plain", "action": "irrelevant", "params": {}}]
    )
    missions.run(mission_id, runner=plain_runner)
    assert missions.status(mission_id)["state"] == missions.COMPLETED


def test_the_failure_names_the_step(data_dir, runner):
    mission_id = missions.create_mission(
        "named", steps=[{"name": "fetch prices", "action": "cert_step_fails", "params": {}}]
    )
    missions.run(mission_id, runner=runner)
    assert "fetch prices" in (missions.status(mission_id)["error"] or "")
