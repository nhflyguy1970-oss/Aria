"""Restart and replay safety for general autonomous missions."""

from jarvis.missions import engine, store


def test_unknown_external_outcome_stops_without_replay(data_dir):
    calls = []
    mission_id = engine.create_mission("two actions", [
        {"name": "external", "action": "fixture_external", "params": {}},
        {"name": "followup", "action": "fixture_followup", "params": {}},
    ])

    def crash(step, context):
        calls.append(context["operation_id"])
        raise SystemExit("process died after external request")

    try:
        engine.run(mission_id, crash)
    except SystemExit:
        pass
    assert calls == [store.operation_id(mission_id, 0)]
    assert store.get(mission_id)["state"] == store.RUNNING
    assert store.recover_interrupted() == [mission_id]
    assert store.get(mission_id)["error_kind"] == "uncertain_effect"
    assert store.get(mission_id)["state"] == store.PAUSED
    assert engine.resume(mission_id, crash)["state"] == store.PAUSED
    assert len(calls) == 1

    store.reconcile_operation(mission_id, 0, outcome="completed",
                              evidence="fixture provider ledger records one accepted effect",
                              result={"ok": True, "external_id": "effect-1"})
    def finish(step, context):
        calls.append(context["operation_id"])
        return {"ok": True}
    result = engine.run(mission_id, finish)
    assert result["state"] == store.COMPLETED
    assert calls == [store.operation_id(mission_id, 0), store.operation_id(mission_id, 1)]
    assert store.latest_checkpoint(mission_id)["step_index"] == 2


def test_owner_verified_nonexecution_allows_one_retry(data_dir):
    mission_id = engine.create_mission("external", [{"name": "external", "action": "fixture", "params": {}}])
    store.transition(mission_id, store.RUNNING)
    claim = store.begin_operation(mission_id, 0)
    assert claim["claimed"]
    store.recover_interrupted()
    store.reconcile_operation(mission_id, 0, outcome="not_executed",
                              evidence="provider ledger confirms request ID was absent")
    calls = []
    result = engine.run(mission_id, lambda step, ctx: calls.append(ctx["operation_id"]) or {"ok": True})
    assert result["state"] == store.COMPLETED
    assert calls == [store.operation_id(mission_id, 0)]


def test_finished_operation_replays_result_only(data_dir):
    mission_id = engine.create_mission("external", [{"name": "external", "action": "fixture", "params": {}}])
    store.transition(mission_id, store.RUNNING)
    store.begin_operation(mission_id, 0)
    store.finish_operation(mission_id, 0, {"ok": True, "external_id": "effect-1"})
    store.recover_interrupted()
    assert store.get(mission_id)["error_kind"] is None
    assert engine.resume(mission_id, lambda *_: (_ for _ in ()).throw(AssertionError("duplicate")))["state"] == store.COMPLETED


def test_pause_is_observed_at_boundary(data_dir):
    mission_id = engine.create_mission("pause", [
        {"name": "first", "action": "fixture", "params": {}},
        {"name": "second", "action": "fixture", "params": {}},
    ])
    calls = []
    def runner(step, context):
        calls.append(step["name"])
        engine.pause(mission_id)
        return {"ok": True}
    assert engine.run(mission_id, runner)["state"] == store.PAUSED
    assert calls == ["first"]
    assert engine.resume(mission_id, lambda step, ctx: {"ok": True})["state"] == store.COMPLETED
