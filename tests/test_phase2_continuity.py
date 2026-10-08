"""Phase 2 — persistent conversation continuity linked to ACM.

End to end: discuss an idea, decide, reject and correct, leave work open, let
the context window prune the start, restart ARIA, then ask naturally where we
left off. Plus the failure modes: missing records, unavailable retrieval,
duplicate ingestion, outbox recovery, deletion planning and history import.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from aria_core import acm_bridge, memory_manager
from jarvis import continuity
from jarvis.continuity import erase, history_import, ingest, store

CONVERSATION = [
    ("user", "I have an idea for a fishing application that logs catches by river."),
    ("assistant", "I suggest PostgreSQL for storage, or SQLite if it stays on one machine."),
    ("user", "Let's go with SQLite since it stays on my machine."),
    ("assistant", "One option is a web dashboard with maps of each catch."),
    ("user", "No, let's not build the web dashboard, keep it a desktop app."),
    ("user", "Actually, log catches by lake not by river."),
    ("user", "Next we need to design the catch entry form."),
]
PRIVATE = [
    ("user", "My blood pressure reading this morning was 150 over 95."),
    ("user", "The api_key=sk-test-abcdefghijklmnopqrstuvwx is for the weather service."),
]


@pytest.fixture
def acm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm.db"))
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    store.reset_for_tests()
    yield
    ingest.stop()
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


def _speak(conv, turns):
    for role, text in turns:
        (conv.add_user if role == "user" else conv.add_assistant)(text)


def _restart():
    """A new process: fresh engine on the same ACM file, fresh index handles."""
    acm_bridge.reset_for_tests()
    store.reset_for_tests()


def _fresh_assistant():
    from jarvis.assistant import JarvisAssistant

    return JarvisAssistant()


# ====================================================================== end to end


def test_where_we_left_off_survives_pruning_and_restart(acm, assistant):
    from jarvis.config import MAX_MESSAGES

    _speak(assistant.conversation, CONVERSATION)
    side = assistant.branches.get_conversation("health", "sys")
    _speak(side, PRIVATE)
    # Enough later chatter that the idea falls out of the model's context.
    for i in range(MAX_MESSAGES):
        assistant.conversation.add_user(f"unrelated small talk {i}")
        assistant.conversation.add_assistant(f"reply {i}")
    assert not any(
        "fishing application" in m["content"] for m in assistant.conversation.messages
    ), "test precondition: the idea must have been pruned from context"
    # Make the decision turns the most recent session again.
    _speak(assistant.conversation, CONVERSATION[2:])
    assistant.branches.persist(session=assistant.session)
    ingest.sync_all(missions=False)

    _restart()
    restarted = _fresh_assistant()
    out = restarted.process("Where did we leave off?")
    text = out.get("message") or out.get("answer") or ""

    assert out.get("action") in (None, "continuity_recall") or "continuity" in json.dumps(out)
    assert "Let's go with SQLite" in text
    assert "web dashboard" in text and "Rejected" in text
    assert "lake not by river" in text
    assert "catch entry form" in text and "Still open" in text
    assert "Sources:" in text
    assert "blood pressure" not in text and "sk-test" not in text


def test_natural_questions_retrieve_the_right_things(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    tomorrow = time.time() + 86400

    idea = continuity.retrieve("Remember that fishing application idea?")
    assert idea.status == continuity.HITS
    ideas = idea.sections["ideas"]
    assert "fishing application" in ideas[0].text
    assert "lake not by river" in ideas[0].note, "the correction must travel with the idea"

    yesterday = continuity.retrieve("What were we talking about yesterday?", now=tomorrow)
    assert yesterday.status == continuity.HITS
    assert any("SQLite" in i.text for i in yesterday.items)

    decided = continuity.retrieve("What did we decide about the storage, SQLite?")
    assert any("Let's go with SQLite" in i.text for i in decided.sections.get("decisions", []))

    # Every item cites a real archived turn.
    for item in idea.items + yesterday.items:
        for episode_id in item.episode_ids:
            episode = store.get_episode(episode_id)
            assert episode is not None and episode["content"]


def test_suggestions_decisions_and_corrections_keep_their_actors(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    records = {r["text"]: r for r in store.list_records(limit=50)}

    pg = records[CONVERSATION[1][1]]
    assert pg["actor"] == store.ASSISTANT and pg["kind"] == store.SUGGESTION
    assert pg["status"] == store.ACCEPTED  # settled by the user's decision, which is the record
    dashboard = records[CONVERSATION[3][1]]
    assert dashboard["status"] == store.REJECTED
    assert records[CONVERSATION[2][1]]["kind"] == store.DECISION
    assert records[CONVERSATION[2][1]]["actor"] == store.USER
    idea = records[CONVERSATION[0][1]]
    assert idea["status"] == store.SUPERSEDED
    assert store.get_record(idea["superseded_by"])["kind"] == store.CORRECTION

    answer = continuity.answer(continuity.retrieve("Where did we leave off?"))
    # ARIA's PostgreSQL suggestion must never be reported as the decision.
    decided = answer.split("**Decided**", 1)[1].split("**", 1)[0]
    assert "PostgreSQL" not in decided


def test_user_statements_reach_acm_with_provenance_and_survive_restart(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    decision = store.record_by_source(
        "episode:" + next(
            e["id"] for e in store.episodes_between(limit=50) if "Let's go with SQLite" in e["content"]
        )
    )
    assert decision["acm_ids"], "decision was not encoded into ACM"

    _restart()
    entry = acm_bridge.primary_get(decision["acm_ids"][0])
    assert entry is not None
    assert f"episode:{decision['episode_ids'][0]}" in entry["tags"]
    assert "continuity:decision" in entry["tags"]
    exp = acm_bridge.get_engine().store.experiences[decision["acm_ids"][0]]
    meta = exp.meta_dict()
    assert meta.get("source_actor") == "user"
    assert meta.get("source_message_role") == "user_statement"

    # Assistant suggestions never enter ACM.
    tagged = [
        e
        for e in acm_bridge.get_engine().store.experiences.values()
        if "continuity" in (e.context_tags or ())
    ]
    assert not any("I suggest PostgreSQL" in (e.summary or "") for e in tagged)


def test_context_bundle_is_backend_neutral_and_scoped(acm, assistant):
    from jarvis.behaviors.conversation import ConversationEngine

    _speak(assistant.conversation, CONVERSATION)
    _speak(assistant.branches.get_conversation("health", "sys"), PRIVATE)
    ingest.sync_all(missions=False)
    engine = ConversationEngine(assistant)
    question = "Continue the project we were discussing."
    prefix, _warnings, citations = engine.build_context_prefix(question)
    again, _w, _c = engine.build_context_prefix(question)
    assert prefix == again, "the same turn must yield the same context"
    assert "Let's go with SQLite" in prefix and citations

    received: dict[str, list[dict]] = {}
    messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": question}]
    for backend in ("local-ollama", "future-cloud"):
        received[backend] = engine.messages_for_llm(list(messages), prefix)
    assert received["local-ollama"] == received["future-cloud"]
    sent = json.dumps(received["future-cloud"])
    assert "blood pressure" not in sent, "unrelated private history leaked into context"
    assert "sk-test" not in sent
    assert len(prefix) < 6000


def test_secrets_are_redacted_even_when_relevant(acm, assistant):
    _speak(assistant.conversation, PRIVATE)
    ingest.sync_all(missions=False)
    result = continuity.retrieve("What did we decide about the weather service api key?")
    assert "sk-test" not in result.to_prompt()
    assert "sk-test" not in continuity.answer(result)


# ====================================================================== honesty


def test_missing_history_is_no_record_and_never_invented(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    result = continuity.retrieve("What did we decide about the boat trailer?")
    assert result.status == continuity.NO_RECORD
    assert "don't have any record" in continuity.answer(result)
    assert "NO_RECORD" in result.to_prompt()
    assert result.citations() == []


def test_unavailable_retrieval_is_not_reported_as_no_record(acm, assistant):
    with patch.object(store, "search_records", side_effect=RuntimeError("disk gone")):
        result = continuity.retrieve("What did we decide about ARIA?")
    assert result.status == continuity.UNAVAILABLE
    reply = continuity.answer(result)
    assert "couldn't search" in reply and "don't have any record" not in reply
    assert "UNAVAILABLE" in result.to_prompt()


def test_acm_prepare_context_cites_hits_and_reports_failures(acm, assistant):
    from jarvis.behaviors.memory.engine import MemoryEngine

    with patch.object(acm_bridge, "primary_context_fragments", return_value=["User likes trout."]):
        parts, cites = MemoryEngine.prepare_context(assistant, "what fish do I like")
    assert parts and cites, "ACM evidence returned without citations reads as no memory"
    with patch.object(acm_bridge, "primary_context_fragments", side_effect=RuntimeError("x")):
        parts, cites = MemoryEngine.prepare_context(assistant, "what fish do I like")
    assert any("UNAVAILABLE" in p for p in parts) and cites == []


# ====================================================================== routing


@pytest.mark.parametrize(
    "question",
    [
        "What were we talking about yesterday?",
        "Where did we leave off?",
        "Remember that fishing application idea?",
        "What did we decide about ARIA?",
        "Catch me up on the project",
    ],
)
def test_natural_questions_route_to_continuity(question):
    from jarvis.router import route
    from jarvis.session import SessionContext

    assert route(question, SessionContext())["action"] == "continuity_recall"


def test_store_commands_and_continuation_are_not_captured():
    from jarvis.context.policy import context_needs
    from jarvis.router import route
    from jarvis.session import SessionContext

    assert route("Remember that my car is red", SessionContext())["action"] == "remember"
    cont = "Continue the project we were discussing."
    assert route(cont, SessionContext())["action"] != "continuity_recall"
    needs = context_needs(cont)
    assert needs.continuity and needs.memory
    gate = context_needs("What did we decide about the ARIA project?")
    assert gate.memory and gate.continuity  # the assessment's lexical blind spot


# ====================================================================== durability


def test_ingestion_is_idempotent_across_restarts_and_resyncs(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    before = store.counts()
    # Simulate a crash that lost the sync offsets: everything is re-read.
    with store._conn() as conn:
        conn.execute("DELETE FROM sync_state")
    _restart()
    ingest.sync_all(missions=False)
    ingest.sync_all(missions=False)
    after = store.counts()
    assert after["episodes"] == before["episodes"]
    assert after["records"] == before["records"]
    assert after["outbox"] == before["outbox"]
    encoded = [
        e
        for e in acm_bridge.get_engine().store.experiences.values()
        if "continuity" in (e.context_tags or ())
    ]
    assert len(encoded) == len({t for e in encoded for t in e.context_tags if t.startswith("episode:")})


def test_crash_between_encode_and_ack_does_not_double_encode(acm, assistant):
    assistant.conversation.add_user("Let's go with SQLite since it stays on my machine.")
    ingest.sync_archives()
    [entry] = store.pending_outbox()
    episode = store.get_episode(entry["episode_id"])
    acm_bridge.encode_continuity_statement(
        episode["content"], kind="decision", episode_id=episode["id"]
    )  # encoded, but the process "died" before the outbox was marked
    ingest.drain_outbox()
    tag = f"episode:{episode['id']}"
    hits = [
        e for e in acm_bridge.get_engine().store.experiences.values() if tag in (e.context_tags or ())
    ]
    assert len(hits) == 1
    assert store.outbox_entry(episode["id"])["status"] == "done"


def test_acm_failures_stay_queued_visible_and_recover(acm, assistant):
    assistant.conversation.add_user("Let's go with SQLite since it stays on my machine.")
    ingest.sync_archives()
    with patch.object(acm_bridge, "encode_continuity_statement", side_effect=RuntimeError("acm down")):
        out = ingest.drain_outbox()
    assert out["failed"] == 1
    snap = continuity.status()
    assert snap["outbox"].get("failed") == 1 and "acm down" in snap["last_error"]
    _restart()
    assert ingest.drain_outbox()["encoded"] == 1
    assert continuity.status()["outbox"].get("done") == 1


def test_seeded_history_is_indexed_but_not_pushed_into_acm(acm, data_dir):
    from jarvis.branches import BRANCHES_FILE, BranchManager

    BRANCHES_FILE.write_text(
        json.dumps(
            {
                "active": "main",
                "branches": {
                    "main": {
                        "name": "Main",
                        "messages": [{"role": "user", "content": "Let's go with Rust for the CLI."}],
                    }
                },
            }
        )
    )
    BranchManager().get_conversation("main", "sys")
    ingest.sync_all(missions=False)
    assert store.list_records(kinds=[store.DECISION])
    assert store.pending_outbox() == [] and store.counts()["outbox"] == {}


def test_missions_and_tools_become_outcomes_not_acm_teaching(acm, data_dir):
    from jarvis import missions
    from jarvis.tools.memory_sink import record_tool_outcome

    done = missions.create_mission("Index the catch photos", steps=[{"name": "s", "action": "x"}])
    missions.run(done, lambda step, ctx: {"ok": True})
    missions.create_mission("Export the season report", steps=[{"name": "s", "action": "x"}])
    ingest.sync_missions()
    ingest.sync_missions()  # idempotent
    outcomes = store.list_records(kinds=[store.OUTCOME])
    assert [o["actor"] for o in outcomes] == [store.MISSION]
    assert "Index the catch photos" in outcomes[0]["text"] and outcomes[0]["status"] == store.DONE
    open_work = store.list_records(kinds=[store.TASK], statuses=[store.OPEN])
    assert any("Export the season report" in r["text"] for r in open_work)

    receipt = record_tool_outcome("claude_code", "refactor importer", ok=True, summary="done")
    assert receipt["recorded"] and receipt["store"] == "continuity"
    tool = store.get_record(receipt["record_id"])
    assert tool["actor"] == store.TOOL and not tool["verified"]
    assert not any(
        "refactor importer" in (e.summary or "")
        for e in acm_bridge.get_engine().store.experiences.values()
    ), "tool output must not enter ACM as user teaching"


# ====================================================================== deletion


def test_erasure_plan_is_read_only_and_apply_needs_the_token(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    archive = ingest.archive_root() / "main.jsonl"
    before = archive.read_bytes()
    plan = erase.plan_erasure(contains="web dashboard")
    assert archive.read_bytes() == before, "planning must not modify anything"
    assert len(plan["episodes"]) == 2 and plan["acm_experiences"]

    with pytest.raises(erase.ErasureError):
        erase.apply_erasure(plan, confirm="wrong")
    assert archive.read_bytes() == before

    result = erase.apply_erasure(plan, confirm=plan["token"])
    assert result["erased_episodes"] == 2
    assert "web dashboard" not in archive.read_text()
    assert continuity.retrieve("What did we decide about the web dashboard?").status == continuity.NO_RECORD
    # Unrelated history is intact and the index stays consistent after a resync.
    ingest.sync_all(missions=False)
    assert "Let's go with SQLite" in continuity.answer(continuity.retrieve("Where did we leave off?"))


def test_erasure_refuses_a_stale_plan(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    plan = erase.plan_erasure(contains="dashboard")
    assistant.conversation.add_user("Actually the dashboard is back on the table.")
    ingest.sync_all(missions=False)
    with pytest.raises(erase.ErasureError, match="changed"):
        erase.apply_erasure(plan, confirm=plan["token"])


# ====================================================================== history import


def _backup(tmp_path: Path) -> Path:
    backup = tmp_path / "aria-data-20260816T000000"
    backup.mkdir()
    (backup / "chat_branches.json").write_text(
        json.dumps(
            {
                "branches": {
                    "a1": {
                        "name": "New chat",
                        "created": "2026-08-09T10:00:00+00:00",
                        "messages": [
                            {"role": "system", "content": "sys"},
                            {"role": "user", "content": "Let's go with a canoe for the lake trip."},
                            {"role": "assistant", "content": "A canoe works."},
                        ],
                    },
                    "a2": {
                        "name": "fork",
                        "created": "2026-08-09T11:00:00+00:00",
                        "forked_from": "a1",
                        "messages": [
                            {"role": "user", "content": "Let's go with a canoe for the lake trip."},
                            {"role": "user", "content": "Already in live history."},
                        ],
                    },
                }
            }
        )
    )
    return backup


def test_history_dry_run_reads_only_and_classifies(acm, data_dir, tmp_path):
    from jarvis.branches import BRANCHES_FILE

    BRANCHES_FILE.write_text(
        json.dumps({"branches": {"main": {"messages": [{"role": "user", "content": "Already in live history."}]}}})
    )
    backup = _backup(tmp_path)
    snapshot = {p: p.read_bytes() for p in backup.iterdir()}
    manifest = history_import.dry_run(backup, manifest_path=tmp_path / "manifest.json")
    assert {p: p.read_bytes() for p in backup.iterdir()} == snapshot
    summary = manifest["summary"]
    assert summary["by_status"] == {
        "importable": 2,
        "duplicate_within_backup": 1,
        "present_in_live_store": 1,
    }
    assert summary["would_create_records"] == {"decision": 1}
    assert summary["per_message_timestamps"] is False
    assert all(e["provenance"].startswith("backup:") for e in manifest["entries"])
    assert not list(ingest.archive_root().glob("import-*")), "dry run wrote to the archive"


def test_history_import_requires_token_and_never_touches_acm(acm, data_dir, tmp_path):
    backup = _backup(tmp_path)
    manifest = history_import.dry_run(backup)
    with pytest.raises(ValueError):
        history_import.apply_import(manifest, confirm="nope", backup_dir=backup)
    out = history_import.apply_import(manifest, confirm=manifest["token"], backup_dir=backup)
    assert out["written"] == 3
    ingest.sync_all(missions=False)
    assert store.pending_outbox() == [], "imported history must not be auto-encoded into ACM"
    found = continuity.retrieve("Remember that canoe lake trip decision?")
    assert found.status == continuity.HITS
    assert "approximate" in continuity.answer(found)
    with pytest.raises(ValueError, match="already"):
        history_import.apply_import(
            history_import.dry_run(backup), confirm=history_import.dry_run(backup)["token"],
            backup_dir=backup,
        )


def test_status_action_reports_ingestion_health(acm, assistant):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    _speak(assistant.conversation, CONVERSATION)
    ingest.sync_all(missions=False)
    out = call_action(SimpleNamespace(), "continuity_status", {}, "continuity status")
    assert out["ok"] and "ACM ingestion" in out["message"]
    assert out["continuity"]["episodes"] == len(CONVERSATION)


# ====================================================================== privacy


def test_topicless_continuity_stays_in_the_active_branch(acm, assistant):
    _speak(assistant.conversation, CONVERSATION)
    work = assistant.branches.get_conversation("work", "sys")
    _speak(work, [("user", "Next we need to file the quarterly budget report.")])
    ingest.sync_all(missions=False)
    main = continuity.retrieve("Where did we leave off?", branch="main")
    assert "catch entry form" in main.to_prompt()
    assert "quarterly budget" not in main.to_prompt()
    other = continuity.retrieve("Where did we leave off?", branch="work")
    assert "quarterly budget" in other.to_prompt() and "SQLite" not in other.to_prompt()


def test_health_statements_are_withheld_unless_asked_and_never_sent_to_acm(acm, assistant):
    _speak(assistant.conversation, [
        ("user", "Next we need to refill my blood pressure medication."),
        ("user", "Next we need to design the catch entry form."),
    ])
    ingest.sync_all(missions=False)
    pending_or_done = [
        store.get_episode(e["episode_id"])["content"]
        for e in store.pending_outbox(limit=50)
    ] + [
        (acm_bridge.primary_get(i) or {}).get("content", "")
        for r in store.list_records(limit=50) for i in r["acm_ids"]
    ]
    assert not any("blood pressure" in c for c in pending_or_done)

    general = continuity.retrieve("Where did we leave off?", branch="main")
    assert "blood pressure" not in general.to_prompt() and general.withheld >= 1
    asked = continuity.retrieve("What did we decide about my blood pressure medication?")
    assert "blood pressure" in asked.to_prompt()
