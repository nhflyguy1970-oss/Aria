"""Exact-plan approval and owner control for the mission-backed task surface."""

from jarvis.missions import engine, store, tasks
import time
import pytest


class Owner:
    stepped = False

    def authorize(self, capability, *, room):
        assert room == "automation"
        if capability == "automation.modify" and not self.stepped:
            return {"ok": False, "reason": "Step-up authentication required"}
        return {"ok": True}


def owner(monkeypatch):
    from jarvis.security.owner import provider_credentials

    identity = Owner()
    monkeypatch.setattr(provider_credentials, "bound_owner_service", lambda: identity)
    return identity


def test_exact_plan_approval_survives_restart_and_rechecks_privilege(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    steps = [
        {"name": "inspect", "action": "mission_list", "params": {}},
        {"name": "delegate", "action": "specialists_run", "params": {"goal": "inspect", "confirm": True}},
    ]
    task = tasks.create("inspect safely", steps, project="aria")
    mid = task["id"]
    assert task["state"] == store.PAUSED and task["approval"] == "proposed"
    try:
        tasks.approve(mid)
        assert False, "step-up was bypassed"
    except tasks.TaskApprovalError:
        pass
    identity.stepped = True
    assert tasks.approve(mid)["approval"] == "approved"
    assert tasks.status(mid)["approval"] == "approved"  # durable DB read
    identity.stepped = False
    calls = []
    result = engine.run(mid, lambda step, ctx: calls.append(step["action"]) or {"ok": True})
    assert result["state"] == store.PAUSED
    assert result["error_kind"] == "awaiting_approval"
    assert calls == ["mission_list"]
    identity.stepped = True
    tasks.resume(mid)
    result = engine.run(mid, lambda step, ctx: calls.append(step["action"]) or {"ok": True})
    assert result["state"] == store.COMPLETED
    assert calls == ["mission_list", "specialists_run"]


def test_plan_tamper_fails_at_execution_boundary(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    task = tasks.create("inspect", [{"name": "inspect", "action": "mission_list", "params": {}}])
    mid = task["id"]
    tasks.approve(mid)
    store.set_steps(mid, [{"name": "changed", "action": "mission_list", "params": {}}])
    calls = []
    result = engine.run(mid, lambda *_: calls.append(1) or {"ok": True})
    assert result["state"] == store.PAUSED
    assert result["error_kind"] == "awaiting_approval" and not calls


def test_redirect_preserves_completed_steps_and_requires_new_approval(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    first = {"name": "first", "action": "mission_list", "params": {}}
    second = {"name": "second", "action": "mission_list", "params": {}}
    task = tasks.create("original", [first, second])
    mid = task["id"]
    tasks.approve(mid)
    def pause_after_first(step, ctx):
        engine.pause(mid)
        return {"ok": True}
    assert engine.run(mid, pause_after_first)["state"] == store.PAUSED
    redirected = tasks.redirect(mid, objective="updated goal", steps=[first, second])
    assert redirected["objective"] == "updated goal"
    assert redirected["approval"] == "proposed"
    try:
        tasks.redirect(mid, objective="bad", steps=[second, second])
        assert False, "completed prefix changed"
    except tasks.TaskApprovalError:
        pass
    tasks.approve(mid)
    called = []
    assert engine.run(mid, lambda step, ctx: called.append(step["name"]) or {"ok": True})["state"] == store.COMPLETED
    assert called == ["second"]


def test_scheduled_task_waits_and_dependencies_are_ordered(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    steps = [
        {"step_id": "second", "name": "second", "action": "mission_list", "params": {}, "depends_on": ["first"]},
        {"step_id": "first", "name": "first", "action": "mission_list", "params": {}},
    ]
    task = tasks.create("scheduled", steps, scheduled_at=time.time() + 60)
    mid = task["id"]
    assert [s["step_id"] for s in task["steps"]] == ["first", "second"]
    assert tasks.approve(mid)["display_state"] == "scheduled"
    assert store.next_pending() is None
    with store._conn() as conn:
        conn.execute("UPDATE agent_task_plans SET scheduled_at=? WHERE mission_id=?", (time.time() - 1, mid))
    assert store.next_pending()["id"] == mid


def test_dependency_cycle_and_embedded_credentials_are_rejected(data_dir):
    with pytest.raises(ValueError, match="cycle"):
        tasks.create("cycle", [
            {"step_id": "first", "action": "mission_list", "depends_on": ["second"], "params": {}},
            {"step_id": "second", "action": "mission_list", "depends_on": ["first"], "params": {}},
        ])
    with pytest.raises(ValueError, match="credentials"):
        tasks.create("secret", [{"action": "mission_list", "params": {"api_key": "value"}}])


def test_completed_task_publishes_one_verified_artifact(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    task = tasks.create("summarize missions", [{"name": "list", "action": "mission_list", "params": {}}],
                        project="aria", session_ref="chat:main")
    mid = task["id"]
    tasks.approve(mid)
    done = engine.run(mid, lambda step, ctx: {"ok": True, "missions": 3})
    assert done["state"] == store.COMPLETED
    path = tasks.artifact_path(mid)
    assert path and path.parent.name == mid and oct(path.stat().st_mode)[-3:] == "600"
    body = __import__("json").loads(path.read_text())
    assert body["task_id"] == mid and body["objective"] == "summarize missions"
    assert tasks.status(mid)["artifact_url"] == f"/api/agent-tasks/{mid}/artifact"
    tasks.save_artifact(store.get(mid))  # idempotent republish of the same result
    changed = {**store.get(mid), "result": {"forged": True}}
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        tasks.save_artifact(changed)
    path.write_text(path.read_text().replace("summarize", "tampered"))
    with pytest.raises(RuntimeError, match="hash mismatch"):
        tasks.artifact_path(mid)


def test_artifact_ids_are_validated(data_dir):
    with pytest.raises(ValueError):
        tasks.artifact_path("../../etc/passwd")
    assert tasks.artifact_path("0123456789ab") is None


def test_task_context_is_durable_and_searchable_across_sessions(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    mid = tasks.create("audit fly tying inventory", [{"name": "list", "action": "mission_list", "params": {}}],
                       project="flytying", session_ref="chat:session-a")["id"]
    found = tasks.list_tasks(project="flytying", query="inventory")
    assert [t["id"] for t in found] == [mid] and found[0]["session_ref"] == "chat:session-a"
    assert tasks.list_tasks(project="aria", query="inventory") == []


def test_queued_scheduled_task_can_be_paused_redirected_and_reapproved(data_dir, monkeypatch):
    """Live-acceptance regression: pausing an approved task that has not started yet."""
    identity = owner(monkeypatch)
    identity.stepped = True
    mid = tasks.create("original goal", [{"name": "list", "action": "mission_list", "params": {}}],
                       scheduled_at=time.time() + 120)["id"]
    tasks.approve(mid)
    assert store.get(mid)["state"] == store.PENDING
    assert tasks.pause(mid)["state"] == store.PAUSED
    assert store.next_pending() is None
    redirected = tasks.redirect(mid, objective="redirected goal",
                                steps=[{"name": "health", "action": "model_health", "params": {}}])
    assert redirected["approval"] == "proposed" and redirected["objective"] == "redirected goal"
    assert tasks.approve(mid)["approval"] == "approved"
    kinds = [e["kind"] for e in store.history(mid)]
    assert kinds.count("approval:approved") == 2 and "task:redirected" in kinds  # history kept


def test_pause_flag_never_leaves_a_claimable_spinning_mission(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    mid = tasks.create("x", [{"name": "list", "action": "mission_list", "params": {}}])["id"]
    tasks.approve(mid)
    with store._conn() as conn:  # the state Task 5 was left in before the fix
        conn.execute("UPDATE missions SET pause_requested=1 WHERE id=?", (mid,))
    assert store.next_pending() is None


def test_cancel_of_finished_task_is_reported_not_silently_accepted(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    mid = tasks.create("quick", [{"name": "list", "action": "mission_list", "params": {}}])["id"]
    tasks.approve(mid)
    engine.run(mid, lambda step, ctx: {"ok": True})
    with pytest.raises(tasks.TaskApprovalError, match="already finished"):
        tasks.cancel(mid)


def test_cancel_during_a_step_stops_before_the_next_one(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    steps = [{"name": f"essay {i}", "action": "mission_list", "params": {}} for i in range(3)]
    mid = tasks.create("three long steps", steps)["id"]
    tasks.approve(mid)
    calls = []

    def runner(step, ctx):
        calls.append(step["name"])
        if len(calls) == 1:
            tasks.cancel(mid)  # owner cancels while step 0 is executing
        return {"ok": True}

    assert engine.run(mid, runner)["state"] == store.CANCELLED
    assert calls == ["essay 0"]
    assert [o["state"] for o in [store.operation(mid, i) for i in range(3)] if o] == ["finished"]


def test_finished_tasks_show_no_current_step(data_dir, monkeypatch):
    identity = owner(monkeypatch)
    identity.stepped = True
    steps = [{"name": f"s{i}", "action": "mission_list", "params": {}} for i in range(3)]
    mid = tasks.create("cancel me", steps)["id"]
    tasks.approve(mid)
    engine.run(mid, lambda step, ctx: tasks.cancel(mid) and {"ok": True} or {"ok": True})
    shown = tasks.status(mid)
    assert shown["state"] == store.CANCELLED and shown["current_step"] == []
