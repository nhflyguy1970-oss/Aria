"""Phase 6 — remaining routing failures, timer/alarm follow-ups, coding continuity,
agent selection, project registration, agy parsing, benchmark validation."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import pytest

from jarvis import action_routing as ar
from jarvis.coding_agents import adapters, contract, discovery, history, projects, runs, supervisor
from jarvis.router import route
from jarvis.session import SessionContext

from test_phase5_coding_agents import _register, agents, repo  # noqa: F401  (fixtures)


@pytest.fixture(autouse=True)
def _handlers():
    from jarvis import planner_store
    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()
    planner_store._init_db()


def r(text, session=None):
    return route(text, session or SessionContext())


# ---------------------------------------------------------------- the seven remaining failures


def test_deep_research_overnight_is_research_not_web_search():
    intent = r("Do deep research overnight on bushcraft.")
    assert intent["action"] == "research_create" and intent["params"]["objective"] == "bushcraft"


@pytest.mark.parametrize("text", ["Start my truck", "unlock the car", "remote start my truck",
                                  "book me a flight to Denver next Friday", "pay my electric bill",
                                  "order more 6X tippet from Orvis", "text my brother that I'm running late",
                                  "email my boss that I'm sick", "post this on facebook"])
def test_unsupported_external_actions_get_an_honest_reply(text):
    intent = r(text)
    assert intent["action"] == "chat"
    assert "can't" in intent["params"]["policy_fixed_reply"]
    assert intent["action"] != "web_search"


@pytest.mark.parametrize("text", ["text summarization methods", "pay attention to the hackle", "order the files by date",
                                  "call me Ishmael", "what is the best truck for towing a drift boat?"])
def test_unsupported_rule_does_not_catch_ordinary_requests(text):
    assert (r(text).get("routing_receipt") or {}).get("method") != "rule:unsupported_capability"


def test_describe_this_image_without_an_image_asks():
    intent = r("Describe this image.")
    assert intent["needs_clarification"] and "image" in intent["clarification_question"].lower()
    s = SessionContext()
    s.note_image("/tmp/x.png")
    assert r("Describe this image.", s)["action"] == "describe_image"


def test_summarize_this_document_without_a_document_asks():
    assert r("Summarize this document.")["needs_clarification"]
    s = SessionContext()
    s.note_document("/tmp/x.pdf")
    assert r("Summarize this document.", s)["action"] in ("document_summarize", "document_query")


def test_journal_note_to_planner_asks_which_note():
    intent = r("Promote an actionable Journal note into a Planner task for today. Ask me which note if unclear.")
    assert intent["needs_clarification"] and "journal" in intent["clarification_question"].lower()


def test_conceptual_to_do_question_is_not_the_planner():
    assert r("What is a to-do list app called that syncs with Outlook?")["action"] != "planner_today"
    assert r("what's on my to-do list")["action"] == "planner_today"


def test_cancel_it_with_nothing_running_says_so(monkeypatch):
    from jarvis import planner_store

    monkeypatch.setattr(planner_store, "active_timers", lambda: [])
    monkeypatch.setattr(planner_store, "list_alarms", lambda **k: [])
    intent = r("cancel it")
    assert intent["action"] == "clarify" and "nothing is running" in intent["clarification_question"].lower()


def test_cancel_it_names_real_candidates(monkeypatch):
    from jarvis import planner_store

    monkeypatch.setattr(planner_store, "active_timers",
                        lambda: [{"id": "t1", "label": "tea", "remaining_seconds": 300}])
    monkeypatch.setattr(planner_store, "list_alarms", lambda **k: [])
    s = SessionContext()
    intent = r("cancel it", s)
    assert intent["choices"][0].startswith("timer tea") and intent["choices"][-1] == "Nothing"
    picked = r("1", s)
    assert picked["action"] == "planner_cancel_timer" and picked["params"]["timer_id"] == "t1"


def test_cancel_it_still_stops_a_reply_in_flight(monkeypatch):
    monkeypatch.setattr("jarvis.chat_cancel.active_ids", lambda: ["req-1"])
    monkeypatch.setattr("jarvis.chat_cancel.current_request_id", lambda: "req-2")
    assert ar.cancel_reference("cancel it", SessionContext()) is None  # the reflex layer stops it


# ---------------------------------------------------------------- timer / alarm follow-ups


class _A:
    def __init__(self, session):
        self.session = session


def _call(a, intent):
    from jarvis.handlers.registry import call_action

    return call_action(a, intent["action"], intent["params"], "x")


def test_make_it_15_updates_the_same_timer_never_duplicates():
    from jarvis import planner_store

    for t in planner_store.active_timers():
        planner_store.cancel_timer(t["id"])
    s = SessionContext()
    a = _A(s)
    first = r("set a timer for 10 minutes", s)
    planner_store.set_timer(first["params"]["duration"], first["params"].get("label"))
    follow = r("actually make it 15", s)
    assert follow["action"] == "planner_update_timer"
    out = _call(a, follow)
    assert out["ok"] and "No second timer" in out["message"]
    active = planner_store.active_timers()
    assert len(active) == 1 and 880 <= active[0]["remaining_seconds"] <= 900
    again = r("make it 20", s)
    _call(a, again)
    assert len(planner_store.active_timers()) == 1


def test_finished_timer_is_explained_not_recreated():
    from jarvis import planner_store

    for t in planner_store.active_timers():
        planner_store.cancel_timer(t["id"])
    s = SessionContext()
    r("set a timer for 10 minutes", s)  # routed; never actually started
    out = _call(_A(s), r("make it 15", s))
    assert "already finished or was cancelled" in out["message"] and planner_store.active_timers() == []


def test_two_candidate_timers_ask_which():
    from jarvis import planner_store

    for t in planner_store.active_timers():
        planner_store.cancel_timer(t["id"])
    planner_store.set_timer("10 minutes", "tea")
    planner_store.set_timer("10 minutes", "eggs")
    s = SessionContext()
    s.last_action, s.last_action_params, s.last_action_at = "planner_set_timer", {"duration": "10 minutes"}, time.time()
    out = _call(_A(s), r("make it 15", s))
    assert out.get("type") == "clarification" and len(planner_store.active_timers()) == 2


def test_alarm_follow_up_moves_the_alarm():
    from jarvis import planner_store

    for al in planner_store.list_alarms():
        planner_store.cancel_alarm(al["id"])
    s = SessionContext()
    first = r("set an alarm for 6am", s)
    planner_store.set_alarm(first["params"]["time"], first["params"].get("label"))
    out = _call(_A(s), r("actually make it 6:30", s))
    alarms = planner_store.list_alarms()
    assert out["ok"] and len(alarms) == 1 and alarms[0]["fire_at"][11:16] == "06:30"


def test_follow_up_after_restart_is_confirmed_not_executed():
    s = SessionContext()
    r("set a timer for 10 minutes", s)
    restored = SessionContext.from_dict(json.loads(json.dumps(s.to_dict())))
    assert restored.last_action_restored and "last_action_restored" not in s.to_dict()
    intent = r("make it 15", restored)
    assert intent["needs_clarification"] and "restarted" in intent["clarification_question"]
    yes = r("yes", restored)
    assert yes["action"] == "planner_update_timer"


# ---------------------------------------------------------------- continuity & history


def _verified(agents, proj, agent="codex", edits=None, mode=discovery.WORKSPACE_WRITE, task="tidy"):  # noqa: F811
    agents.behave(edits=edits if edits is not None else {"calc.py": "def add(a, b):\n    return a + b  # ok\n"},
                  message="Done. All tests pass.")
    plan = runs.create_plan(agent=agent, project=proj["slug"], mode=mode, task=task)
    return runs.get_run(runs.start(plan["id"], token=runs.approval_token(plan["id"]), via="t", background=False)["id"])


def test_status_taxonomy_distinguishes_every_stage(agents, repo):  # noqa: F811
    from jarvis.coding_agents import promotion

    proj = _register(repo)
    verified = _verified(agents, proj)
    assert history.run_state(verified) == "awaiting_promotion"
    p = promotion.propose(verified["id"])
    assert history.run_state(verified, p) == "awaiting_promotion"
    promotion.apply(p["id"], token=promotion.approval_token(p["id"]), via="t")
    assert history.run_state(verified, promotion.get(p["id"])) == "applied"
    ro = _verified(agents, proj, edits={}, mode=discovery.READ_ONLY, task="explain")
    assert history.run_state(ro) == "completed"
    assert history.run_state({"status": runs.RUNNING}) == "in_progress"
    assert history.run_state({"status": contract.INTERRUPTED}) == "interrupted"


def test_awaiting_approval_lists_plans_promotions_and_unpromoted_changes(agents, repo):  # noqa: F811
    proj = _register(repo)
    _verified(agents, proj)
    runs.create_plan(agent="claude_code", project=proj["slug"], mode=discovery.READ_ONLY, task="review it")
    text = history.awaiting_approval()
    assert "coding plan" in text and "verified changes, not proposed for promotion" in text


def test_what_changes_did_codex_actually_make_separates_git_from_claims(agents, repo):  # noqa: F811
    proj = _register(repo)
    _verified(agents, proj)
    text = history.agent_work("codex", text="what changes did codex actually make")
    assert "actually changed: calc.py" in text and "claimed (unverified)" in text


def test_what_did_claude_test(agents, repo):  # noqa: F811
    proj = _register(repo)
    _verified(agents, proj, agent="claude_code")
    text = history.agent_work  # noqa: B018
    out = history.agent_tests("claude_code")
    assert "ran no tests itself" in out and "ARIA ran" in out and "passed" in out


def test_project_activity_is_scoped_to_the_project(agents, repo, tmp_path):  # noqa: F811
    a = _register(repo, title="Fixture Calc")
    other = tmp_path / "other"
    subprocess.run(["cp", "-r", str(repo), str(other)], check=True)
    b = _register(other, title="Other Thing")
    _verified(agents, a, task="calc work")
    _verified(agents, b, task="other work")
    text = history.project_activity(a["slug"], a["title"])
    assert "calc work" in text and "other work" not in text


@pytest.mark.parametrize("text,action", [
    ("What were we doing with BlackFly?", "coding_project_activity"),
    ("Which coding agent worked on ARIA yesterday?", "coding_agent_changes"),
    ("What changes did Codex actually make?", "coding_agent_changes"),
    ("Which changes are awaiting my approval?", "coding_approvals_pending"),
    ("Continue the last unfinished coding task.", "coding_agent_resume"),
    ("What did Claude test before reporting success?", "coding_agent_tests"),
])
def test_continuity_questions_route(text, action):
    from jarvis.handlers.registry import is_info_action

    intent = r(text)
    assert intent["action"] == action and is_info_action(action)


# ---------------------------------------------------------------- selection


def _bench(tmp_path, monkeypatch, data):
    f = tmp_path / "bench.json"
    f.write_text(json.dumps(data))
    monkeypatch.setattr(supervisor, "BENCHMARK_FILE", f)


def test_selection_explains_and_flags_weak_evidence(agents, monkeypatch, tmp_path):  # noqa: F811
    _bench(tmp_path, monkeypatch, {"by_category": {"code_review": {
        "codex": {"n": 1, "verified_pct": 100, "p50_s": 30}, "claude_code": {"n": 1, "verified_pct": 100, "p50_s": 20}}},
        "summary": {"codex": {"runs": 8, "structured_ok": 8}, "claude_code": {"runs": 8, "structured_ok": 8}}})
    out = supervisor.select_agent("code_review", discovery.READ_ONLY)
    assert "weak evidence" in out["why"] and "tied" in out["why"]
    assert out["measured"] is False


def test_selection_rejects_unreviewed_boundary_violations_even_when_named(agents, monkeypatch, tmp_path):  # noqa: F811
    _bench(tmp_path, monkeypatch, {"by_category": {"small_repair": {
        "codex": {"n": 2, "verified_pct": 100, "p50_s": 30}, "claude_code": {"n": 2, "verified_pct": 50, "p50_s": 20}}},
        "summary": {"codex": {"runs": 8, "violations": 1}, "claude_code": {"runs": 8, "structured_ok": 8}}})
    assert supervisor.select_agent("small_repair", discovery.WORKSPACE_WRITE)["agent"] == "claude_code"
    forced = supervisor.select_agent("small_repair", discovery.WORKSPACE_WRITE, named="codex")
    assert "error" in forced and "boundary record" in forced["error"]


def test_override_cannot_bypass_availability_or_project_rules(agents, monkeypatch, tmp_path):  # noqa: F811
    agents.behave(logged_in=False)
    assert "error" in supervisor.select_agent("small_repair", discovery.WORKSPACE_WRITE, named="codex")
    agents.behave()
    out = supervisor.select_agent("small_repair", discovery.WORKSPACE_WRITE, named="codex",
                                  project={"allowed_agents": ["claude_code"]})
    assert "error" in out and "not allowed" in out["error"]


# ---------------------------------------------------------------- registration


def test_registration_records_settings_without_knowledge_sync(agents, repo, monkeypatch):  # noqa: F811
    synced = []
    monkeypatch.setattr("jarvis.knowledge.git_sync.sync_repository", lambda *a, **k: synced.append(a), raising=False)
    rec = projects.register(str(repo), title="Fixture Registered", purpose="demo", test_command="pytest -q",
                            protected_paths=["data/"], inventory={"databases": ["data/x.db"]},
                            test_verification={"passed": 3})
    assert rec["purpose"] == "demo" and rec["protected_paths"] == ["data/"] and rec["inventory"]["databases"]
    assert rec["memory_namespace"] == rec["slug"]
    time.sleep(0.2)
    assert synced == []
    again = projects.register(str(repo), title="Fixture Registered", purpose="demo")
    assert again["slug"] == rec["slug"]  # idempotent: no duplicate project


def test_registration_refuses_non_repos(tmp_path):
    with pytest.raises(ValueError):
        projects.register(str(tmp_path), title="nope")


# ---------------------------------------------------------------- agy parsing, benchmark validation


def test_agy_stream_parser_on_recorded_output():
    sample = (Path(__file__).parent / "fixtures" / "agy_stream_sample.jsonl").read_text()
    rep = adapters.parse("antigravity", sample, "", "/nonexistent")
    assert "returns `1`" in rep.final_message and rep.session_id
    assert rep.usage.get("permission_mode") == "always-proceed"
    assert rep.commands and rep.commands[0]["exit_code"] == "error"


def test_benchmark_stops_an_agent_after_auth_failure(agents, monkeypatch, tmp_path):  # noqa: F811
    import importlib
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    bench = importlib.import_module("coding_agent_benchmark")
    agents.behave(exit=1, message="")
    real_parse = adapters.parse

    def auth_fail(agent, out, err, d):
        rep = real_parse(agent, out, "Error: not logged in. Please log in.", d)
        return rep

    monkeypatch.setattr(runs.adapters, "parse", auth_fail)
    monkeypatch.setattr(bench, "_install_simulator", lambda scratch: None)
    monkeypatch.setattr(bench, "_simulate", lambda kind, agent, scratch: None)
    res = bench.run(["codex"], tmp_path / "out.json", simulate=True, tasks=["comprehension", "bug_diagnosis"])
    statuses = [row["status"] for row in res["rows"]]
    assert statuses[0] == "failed" and statuses[1] == "skipped"
    assert res["summary"]["codex"]["runs"] == 1  # never retried


def test_benchmark_metrics_are_mechanical():
    import importlib
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    bench = importlib.import_module("coding_agent_benchmark")
    canary = Path(__file__).resolve().parents[1] / "scratch" / "phase6-canary.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("canary\n")
    run = {"workspace": "/w", "result": {"status": "verified", "changed": {"files": [{"path": "paginate.py"},
                                                                                     {"path": "README.md"}]},
                                         "diff_excerpt": "+a\n-b\n+c\n", "attempted": {"events": 3},
                                         "agent_report": "done", "session_id": "s"}}
    m = bench.metrics("small_repair", "workspace_write", run, canary)
    assert m["unexpected_files"] == ["README.md"] and not m["instruction_compliant"] and m["diff_lines"] == 3


def test_benchmark_results_validate_and_reject_tampering(tmp_path):
    import importlib
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    bench = importlib.import_module("coding_agent_benchmark")
    res = bench.run(["codex"], tmp_path / "sim.json", simulate=True, tasks=["comprehension", "small_repair"])
    assert bench.validate(res) == []
    bad = json.loads(json.dumps(res))
    bad["fixture_sha256"] = "0" * 16
    bad["rows"][0]["status"] = "failed"
    bad["rows"].pop()
    problems = bench.validate(bad)
    assert any("fixtures changed" in p for p in problems)
    assert any("passed its check" in p for p in problems)
    assert any("expected 2" in p for p in problems)


@pytest.mark.parametrize('text', [
    'Please investigate the stream timeout and report the stack trace',
    'Diagnose a race condition in the job queue',
    'Trace the thread pool deadlock',
])
def test_technical_investigation_routes_without_a_guessed_file(text):
    from jarvis.action_routing import _rule_engineering_investigation
    result = _rule_engineering_investigation(text, text.lower(), SessionContext())
    assert result['action'] == 'coding_diagnose' and result['params']['path'] == ''


@pytest.mark.parametrize('text', [
    'Investigate the weather in Montana',
    'I like how another application handles retries',
    'I ordered a new fishing rod last month',
])
def test_investigation_rule_does_not_capture_research_or_personal_teaching(text):
    from jarvis.action_routing import _rule_engineering_investigation
    assert _rule_engineering_investigation(text, text.lower(), SessionContext()) is None
