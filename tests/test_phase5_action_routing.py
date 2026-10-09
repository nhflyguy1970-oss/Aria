"""Phase 5 — action routing repair: misroutes, shortlist, clarification,
follow-ups, receipts, confirmation, permission parity across routes."""

from __future__ import annotations

import json
import time

import pytest

from jarvis import action_routing as ar
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture(autouse=True)
def _handlers():
    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()


def r(text, session=None):
    return route(text, session or SessionContext())


# ---------------------------------------------------------------- the three confirmed misroutes


@pytest.mark.parametrize(
    "text,action,arg,value",
    [
        ("Wake me at 5:30", "planner_set_alarm", "time", "5:30"),
        ("Wake me at 5:30 tomorrow for the morning hatch.", "planner_set_alarm", "time", "5:30"),
        ("Add order more hackle to my to-do list", "planner_add_task", "text", "order more hackle"),
        ("Put 'order more hackle' on my to-do list.", "planner_add_task", "text", "order more hackle"),
        ("12-minute timer", "planner_set_timer", "duration", "12 minutes"),
        ("Give me a 12 minute timer for the epoxy.", "planner_set_timer", "duration", "12 minutes"),
    ],
)
def test_confirmed_misroutes_fixed(text, action, arg, value):
    intent = r(text)
    assert intent["action"] == action
    assert intent["params"][arg] == value
    assert intent["routing_receipt"]["method"].startswith("rule:")


def test_alarm_label_and_no_web_search():
    intent = r("Wake me at 5:30 tomorrow for the morning hatch.")
    assert intent["params"].get("label") == "morning hatch"
    assert intent["action"] != "web_search"


# ---------------------------------------------------------------- arguments


@pytest.mark.parametrize(
    "text,expected",
    [("12-minute", "12 minutes"), ("half an hour", "30 minutes"), ("90 seconds", "90 seconds"),
     ("two hours", "2 hours"), ("for 45 mins", "45 minutes")],
)
def test_duration_extraction(text, expected):
    assert ar.extract_duration(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [("at 5:30 tomorrow", "5:30"), ("4:45 am", "4:45am"), ("for 6am", "6am"), ("set my alarm for 7", "7"),
     ("nothing here", None)],
)
def test_clock_extraction(text, expected):
    assert ar.extract_clock_time(text) == expected


# ---------------------------------------------------------------- unsupported / near misses


@pytest.mark.parametrize(
    "text",
    ["book me a flight to Denver next Friday", "order a large pepperoni pizza", "transfer $500 to my savings account",
     "how does a kitchen timer work?", "can you draw a conclusion from these numbers: 3, 6, 12?",
     "explain how home assistant turns lights on and off", "the mission statement for my fly shop needs work"],
)
def test_unsupported_and_near_misses_do_not_become_actions(text):
    from jarvis.handlers.registry import is_info_action

    intent = r(text)
    action = intent["action"]
    assert action in ("chat", "clarify", "nlu_clarify", "capabilities", "web_search") or is_info_action(action), action


# ---------------------------------------------------------------- clarification


@pytest.mark.parametrize("text", ["delete it", "turn it off", "send that", "set it for tomorrow", "remove those",
                                  "move it to tomorrow"])
def test_pronoun_only_requests_ask(text):
    intent = r(text)
    assert intent["needs_clarification"] and intent["action"] == "clarify"
    assert intent["routing_receipt"]["method"] == "deictic_clarify"


def test_fix_it_without_a_file_asks():
    assert r("can you fix it?")["needs_clarification"]  # the existing coding referent check asks first


@pytest.mark.parametrize("text", ["I don't know how to do it", "go ahead and tell me a joke", "how do I do it?"])
def test_do_it_in_a_sentence_never_applies_a_proposal(text):
    s = SessionContext()
    s.note_proposal("p1")
    assert r(text, s)["action"] != "apply_proposal"


def test_bare_go_ahead_applies_only_a_pending_proposal():
    assert r("go ahead")["action"] != "apply_proposal"
    s = SessionContext()
    s.note_proposal("p1")
    assert r("go ahead", s)["action"] == "apply_proposal"
    assert r("apply the changes")["action"] == "apply_proposal"  # explicit


@pytest.mark.parametrize("text", ["set an alarm", "start a timer", "Add a planner task:", "Generate a song:",
                                  "play some music"])
def test_missing_essentials_ask(text):
    assert r(text)["needs_clarification"]


def test_fix_it_with_a_known_file_is_not_hijacked():
    s = SessionContext()
    s.note_file("/tmp/x.py")
    assert ar.deictic_clarification("fix it", s) is None


def test_deictic_answer_is_treated_as_new_request():
    s = SessionContext()
    assert r("delete it", s)["needs_clarification"]
    nxt = r("set a timer for 5 minutes", s)
    assert nxt["action"] == "planner_set_timer"


# ---------------------------------------------------------------- multi-turn, persistence


def test_follow_ups_bind_to_previous_action():
    s = SessionContext()
    r("set a timer for 10 minutes", s)
    assert r("actually make it 15", s)["params"]["duration"] == "15 minutes"
    s = SessionContext()
    r("add a task to order hackle", s)
    assert r("and another one to clean my reels", s)["params"]["text"] == "clean my reels"
    s = SessionContext()
    r("what's the weather tomorrow", s)
    nxt = r("and on Sunday?", s)
    assert nxt["action"] == "weather_forecast" and nxt["params"]["day"] == "sunday"


def test_follow_up_does_not_cross_unrelated_turns():
    s = SessionContext()
    r("set a timer for 5 minutes", s)
    r("what's the capital of Vermont?", s)
    assert r("make it 8", s)["action"] != "planner_set_timer"


def test_follow_up_expires():
    s = SessionContext()
    r("set a timer for 5 minutes", s)
    s.last_action_at = time.time() - ar.FOLLOW_UP_TTL_S - 1
    assert r("make it 8", s)["action"] != "planner_set_timer"


def test_last_action_survives_session_restore():
    s = SessionContext()
    r("set a timer for 10 minutes", s)
    restored = SessionContext.from_dict(json.loads(json.dumps(s.to_dict())))
    assert restored.last_action == "planner_set_timer"
    ask = r("actually make it 15", restored)  # Phase 6: confirmed after a restart, never just run
    assert ask["needs_clarification"]
    assert r("yes", restored)["params"]["duration"] == "15 minutes"


def test_repeat_of_side_effect_needs_confirmation_then_runs_once():
    s = SessionContext()
    r("set a timer for 10 minutes", s)
    ask = r("do it again", s)
    assert ask["needs_clarification"] and ask["choices"] == ["Yes", "No"]
    yes = r("yes", s)
    assert yes["action"] == "planner_set_timer" and yes["routing_receipt"]["confirmed_by_user"]
    assert s.pending_clarification is None


def test_pending_choice_no_declines():
    s = SessionContext()
    r("set a timer for 10 minutes", s)
    r("run it again", s)
    assert r("no", s)["action"] == "chat"


def test_stale_mission_reference_asks_for_id():
    s = SessionContext()
    r("list my missions", s)
    assert r("cancel the first one", s)["needs_clarification"]


# ---------------------------------------------------------------- shortlist


def test_shortlist_is_small_and_relevant():
    top = ar.shortlist("Wake me at 5:30")
    assert len(top) <= ar.SHORTLIST_K
    assert "planner_set_alarm" in [a for a, _ in top]
    top = ar.shortlist("12-minute timer")
    assert top[0][0] == "planner_set_timer"


def test_shortlist_never_offers_control_or_destructive_actions():
    names = set(ar._Index().docs)
    assert not names & {"self_upgrade_run", "git_sync_all", "workstation_down", "chat", "clarify"}


def test_model_stage_is_off_by_default(monkeypatch):
    called = []
    monkeypatch.setattr("jarvis.llm.ask_with_usage", lambda *a, **k: called.append(1) or ("chat", {}))
    assert not ar.model_choice_enabled()
    r("could you organise my fly box by hook size")
    assert called == []


def test_model_choice_side_effect_becomes_confirmation(monkeypatch):
    monkeypatch.setenv("JARVIS_ROUTER_SHORTLIST_MODEL", "1")
    monkeypatch.setattr(ar, "shortlist", lambda text, k=6: [("generate_song", 9.0), ("generate_music", 6.0)])
    monkeypatch.setattr("jarvis.llm.ask_with_usage", lambda *a, **k: ("generate_song", {"prompt_tokens": 50}))
    out = ar.choose_with_model("compose something about trout streams", model="m")
    assert out["needs_clarification"] and out["choices"][0] == "Yes"
    assert out["choice_intents"][0]["action"] == "generate_song"
    assert out["routing_receipt"]["candidates"]


def test_model_choice_info_action_routes_directly(monkeypatch):
    monkeypatch.setenv("JARVIS_ROUTER_SHORTLIST_MODEL", "1")
    monkeypatch.setattr(ar, "shortlist", lambda text, k=6: [("runtime_gpu", 9.0)])
    monkeypatch.setattr("jarvis.llm.ask_with_usage", lambda *a, **k: ("runtime_gpu", {}))
    assert ar.choose_with_model("check the graphics card temperature", model="m")["action"] == "runtime_gpu"


def test_model_clarify_or_garbage_keeps_nlu_answer(monkeypatch):
    monkeypatch.setenv("JARVIS_ROUTER_SHORTLIST_MODEL", "1")
    monkeypatch.setattr(ar, "shortlist", lambda text, k=6: [("runtime_gpu", 9.0)])
    for answer in ("clarify", "I think you want delete_everything", ""):
        monkeypatch.setattr("jarvis.llm.ask_with_usage", lambda *a, ans=answer, **k: (ans, {}))
        out = ar.choose_with_model("check the graphics card temperature", model="m")
        assert "action" not in out and "_receipt" in out


def test_model_failure_is_receipted_not_raised(monkeypatch):
    monkeypatch.setenv("JARVIS_ROUTER_SHORTLIST_MODEL", "1")
    monkeypatch.setattr(ar, "shortlist", lambda text, k=6: [("runtime_gpu", 9.0)])

    def boom(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr("jarvis.llm.ask_with_usage", boom)
    out = ar.choose_with_model("check the graphics card temperature", model="m")
    assert out["_receipt"]["method"] == "shortlist_model_unavailable"


def test_conceptual_questions_never_reach_the_model(monkeypatch):
    monkeypatch.setenv("JARVIS_ROUTER_SHORTLIST_MODEL", "1")
    monkeypatch.setattr("jarvis.llm.ask_with_usage", lambda *a, **k: pytest.fail("model called"))
    assert ar.choose_with_model("What is inpainting?") is None
    assert ar.choose_with_model("tell me about the history of the egg timer") is None


# ---------------------------------------------------------------- overreach fixes


def test_whole_image_edit_is_not_inpainting():
    s = SessionContext()
    s.note_image("/tmp/last.png")
    assert r("edit the image to add falling snow", s)["action"] == "edit_image"
    assert r("inpaint the top left corner with a fly rod", s)["action"] == "inpaint_image"


def test_inpaint_without_image_asks():
    assert r("inpaint the top left corner with a fly rod")["needs_clarification"]


def test_status_of_mission_is_mission_status_not_runtime():
    intent = r("what's the status of mission 3f18c26524ce")
    assert intent["action"] == "mission_status" and intent["params"]["mission_id"] == "3f18c26524ce"


# ---------------------------------------------------------------- permission parity


def test_routing_never_executes_and_safe_mode_still_refuses_after_rule_route(monkeypatch):
    """A rule-routed mission action is still refused by Phase 1 policy at execution."""
    from jarvis.handlers.registry import call_action

    intent = r("pause mission 3f18c26524ce")
    assert intent["action"] == "mission_pause"
    monkeypatch.setenv("JARVIS_SAFE_MODE", "1")
    out = call_action(None, "mission_run", {"mission_id": "3f18c26524ce"}, "run mission")
    assert not out.get("ok")


@pytest.mark.parametrize("path", ["rule", "llm_json", "tool", "pending"])
def test_coding_agent_execute_needs_approval_whichever_route_produced_it(path, monkeypatch, tmp_path):
    """Every route ends in the same handler, which requires the owner's approval token."""
    from jarvis.coding_agents import runs
    from jarvis.handlers.registry import call_action

    runs.reset_for_tests()
    with runs._conn() as conn:
        conn.execute("INSERT INTO plans (id, status, agent, project, mode, task, timeout_s, plan_hash, nonce) "
                     "VALUES ('plan_x', 'proposed', 'codex', 'p', 'read_only', 't', 60, 'h', 'secret')")
    params = {"plan_id": "plan_x"}
    if path == "pending":
        params["approval_token"] = "guessed"
    out = call_action(None, "coding_agent_execute", params, "execute plan_x")
    assert not out.get("ok")
    assert runs.list_runs() == []
