"""Deep Research Engine — evidence, citations, contradictions, persistence, recovery."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from jarvis import missions
from jarvis.missions import store as mstore
from jarvis.missions import worker
from jarvis.research import engine, store

REPO_ROOT = Path(__file__).resolve().parents[1]


# ----------------------------------------------------------------- fakes
# Deterministic: the suite must never depend on the live internet.


def fake_search(
    hits_by_query: dict[str, list[dict]] | None = None, default: list[dict] | None = None
):
    def _search(query: str, limit: int) -> list[dict]:
        if hits_by_query and query in hits_by_query:
            return hits_by_query[query][:limit]
        return (default or [])[:limit]

    return _search


def fake_fetch(pages: dict[str, str], fail: set[str] | None = None):
    def _fetch(url: str) -> str:
        if fail and url in fail:
            raise RuntimeError("fetch blocked")
        if url not in pages:
            raise RuntimeError("not retrievable")
        return pages[url]

    return _fetch


SUPPORTING = [
    {"url": "https://nasa.gov/a", "title": "NASA A", "snippet": "The sky appears blue."},
    {"url": "https://nih.gov/b", "title": "NIH B", "snippet": "Observations confirm blue sky."},
]
CONTRADICTING = [
    {"url": "https://blog.example.com/c", "title": "Blog C", "snippet": "This is false, a myth."},
]


@pytest.fixture(autouse=True)
def _stop_worker():
    yield
    worker.stop(timeout=5)


def _run_all(rid: str, search_fn=None, fetch_fn=None):
    for phase in engine.PHASES:
        engine.run_phase(rid, phase, search_fn=search_fn, fetch_fn=fetch_fn)


# ----------------------------------------------------------------- creation & storage


def test_research_creation_persists(data_dir: Path):
    created = engine.create_research("is the sky blue")
    rid = created["research_id"]
    job = store.get_job(rid)
    assert job["objective"] == "is the sky blue"
    assert job["status"] == store.PENDING
    assert job["mission_id"] == created["mission_id"]
    assert store.DB_PATH.is_file()


def test_research_store_is_inside_isolated_root(data_dir: Path):
    assert data_dir in store.DB_PATH.resolve().parents


def test_research_creates_a_mission_with_all_phases(data_dir: Path):
    created = engine.create_research("topic")
    mission = missions.get(created["mission_id"])
    assert mission["kind"] == "research"
    assert [s["params"]["phase"] for s in mission["steps"]] == list(engine.PHASES)


# ----------------------------------------------------------------- plan / questions


def test_plan_creates_questions_and_plan(data_dir: Path):
    rid = engine.create_research("caffeine and sleep")["research_id"]
    out = engine.phase_plan(rid)
    assert out["questions"] >= 2
    qs = store.questions(rid)
    assert len(qs) == out["questions"]
    assert store.get_job(rid)["plan"]


def test_plan_is_idempotent(data_dir: Path):
    rid = engine.create_research("x")["research_id"]
    engine.phase_plan(rid)
    first = len(store.questions(rid))
    engine.phase_plan(rid)
    assert len(store.questions(rid)) == first, "re-planning duplicated questions"


def test_decompose_handles_empty_objective(data_dir: Path):
    assert engine.decompose("") == []


# ----------------------------------------------------------------- search & sources


def test_search_records_sources_and_searches(data_dir: Path):
    rid = engine.create_research("sky")["research_id"]
    engine.phase_plan(rid)
    out = engine.phase_search(rid, fake_search(default=SUPPORTING))
    assert out["unique_sources"] == 2
    assert len(store.searches(rid)) == len(store.questions(rid))
    assert {s["url"] for s in store.sources(rid)} == {h["url"] for h in SUPPORTING}


def test_sources_are_deduplicated_across_queries(data_dir: Path):
    """The same source found by every question must be stored once."""
    rid = engine.create_research("dedupe")["research_id"]
    engine.phase_plan(rid)
    dupes = [
        {"url": "https://nasa.gov/a", "title": "A", "snippet": "one"},
        {"url": "https://www.nasa.gov/a/", "title": "A dup", "snippet": "two"},
        {"url": "http://NASA.gov/a#frag", "title": "A dup2", "snippet": "three"},
    ]
    engine.phase_search(rid, fake_search(default=dupes))
    assert len(store.sources(rid)) == 1, store.sources(rid)


def test_canonical_url_normalisation(data_dir: Path):
    c = store.canonical_url
    assert c("https://www.Example.com/path/") == c("http://example.com/path#x")
    assert c("") == ""


def test_search_failure_is_recorded_not_raised(data_dir: Path):
    rid = engine.create_research("boom")["research_id"]
    engine.phase_plan(rid)

    def exploding(query: str, limit: int):
        raise RuntimeError("search down")

    out = engine.phase_search(rid, exploding)
    assert out["unique_sources"] == 0
    assert all(s["error"] for s in store.searches(rid))


def test_source_quality_tier_recorded(data_dir: Path):
    rid = engine.create_research("tiers")["research_id"]
    engine.phase_plan(rid)
    engine.phase_search(rid, fake_search(default=SUPPORTING + CONTRADICTING))
    tiers = {s["url"]: s["tier"] for s in store.sources(rid)}
    assert all(isinstance(t, int) for t in tiers.values())


# ----------------------------------------------------------------- collection & evidence


def test_collect_marks_inspected_and_creates_evidence(data_dir: Path):
    rid = engine.create_research("collect")["research_id"]
    engine.phase_plan(rid)
    engine.phase_search(rid, fake_search(default=SUPPORTING))
    pages = {h["url"]: f"full text of {h['title']}" for h in SUPPORTING}
    out = engine.phase_collect(rid, fake_fetch(pages))

    assert out["inspected"] == 2
    assert out["evidence"] == 2
    assert all(s["inspected"] for s in store.sources(rid))
    assert all("full text" in e["excerpt"] for e in store.evidence(rid))


def test_unretrievable_source_is_not_claimed_as_inspected(data_dir: Path):
    """The engine must never claim it read something it could not fetch."""
    rid = engine.create_research("blocked")["research_id"]
    engine.phase_plan(rid)
    engine.phase_search(rid, fake_search(default=SUPPORTING))
    out = engine.phase_collect(rid, fake_fetch({}, fail={h["url"] for h in SUPPORTING}))

    assert out["inspected"] == 0
    assert out["retrieval_failed"] == 2
    for s in store.sources(rid):
        assert s["inspected"] == 0
        assert s["retrieval_error"]
    # Snippets still become evidence, attributed to the un-inspected source.
    assert len(store.evidence(rid)) == 2


def test_collect_is_idempotent(data_dir: Path):
    rid = engine.create_research("idem")["research_id"]
    engine.phase_plan(rid)
    engine.phase_search(rid, fake_search(default=SUPPORTING))
    pages = {h["url"]: "text" for h in SUPPORTING}
    engine.phase_collect(rid, fake_fetch(pages))
    before = len(store.evidence(rid))
    engine.phase_collect(rid, fake_fetch(pages))
    assert len(store.evidence(rid)) == before, "re-collection duplicated evidence"


# ----------------------------------------------------------------- claims & contradictions


def test_supporting_evidence_yields_verified_high_confidence(data_dir: Path):
    rid = engine.create_research("the sky is blue")["research_id"]
    _run_all(
        rid,
        fake_search(default=SUPPORTING),
        fake_fetch({h["url"]: "clear agreement" for h in SUPPORTING}),
    )
    claim = store.claims(rid)[0]
    assert claim["verified"] == 1
    assert claim["confidence"] == "high"


def test_contradiction_is_detected_and_preserved(data_dir: Path):
    rid = engine.create_research("the earth is flat")["research_id"]
    pages = {h["url"]: "supporting text" for h in SUPPORTING}
    pages[CONTRADICTING[0]["url"]] = "This is false and a myth, refuted by data."
    _run_all(rid, fake_search(default=SUPPORTING + CONTRADICTING), fake_fetch(pages))

    claim = store.claims(rid)[0]
    linked = store.claim_evidence(claim["id"])
    stances = {r["stance"] for r in linked}
    assert store.CONTRADICTS in stances, "contradiction was not recorded"
    assert store.SUPPORTS in stances, "disagreement collapsed to one side"
    assert claim["confidence"] == "contested"
    assert claim["verified"] == 0
    assert any("disagree" in u["text"] for u in store.unresolved(rid))


def test_single_source_support_is_low_confidence_and_flagged(data_dir: Path):
    rid = engine.create_research("solo claim")["research_id"]
    one = [SUPPORTING[0]]
    _run_all(rid, fake_search(default=one), fake_fetch({one[0]["url"]: "agreement"}))
    claim = store.claims(rid)[0]
    assert claim["confidence"] == "low"
    assert claim["verified"] == 0
    assert any("one independent source" in u["text"] for u in store.unresolved(rid))


def test_no_evidence_is_reported_as_uncertainty(data_dir: Path):
    rid = engine.create_research("nothing findable")["research_id"]
    _run_all(rid, fake_search(default=[]), fake_fetch({}))
    assert store.claims(rid)[0]["confidence"] == "none"
    assert any("No evidence" in u["text"] for u in store.unresolved(rid))


def test_independent_verification_recorded(data_dir: Path):
    rid = engine.create_research("verified thing")["research_id"]
    _run_all(
        rid, fake_search(default=SUPPORTING), fake_fetch({h["url"]: "agree" for h in SUPPORTING})
    )
    linked = store.claim_evidence(store.claims(rid)[0]["id"])
    assert any(r["stance"] == store.VERIFIES for r in linked)


# ----------------------------------------------------------------- citations & traceability


def test_citations_trace_source_to_evidence_to_claim(data_dir: Path):
    rid = engine.create_research("traceable")["research_id"]
    pages = {h["url"]: f"body of {h['title']}" for h in SUPPORTING}
    _run_all(rid, fake_search(default=SUPPORTING), fake_fetch(pages))

    rep = engine.report(rid)
    claim = rep["claims"][0]
    assert claim["evidence"], "claim has no evidence"
    for row in claim["evidence"]:
        # Every citation points at a source that really exists in this job.
        assert row["url"] in {s["url"] for s in rep["sources"]}
        assert row["evidence_id"] in {e["id"] for e in rep["evidence"]}
        assert row["excerpt"]


def test_synthesis_cites_only_recorded_sources(data_dir: Path):
    rid = engine.create_research("cite check")["research_id"]
    _run_all(rid, fake_search(default=SUPPORTING), fake_fetch({h["url"]: "t" for h in SUPPORTING}))
    synthesis = store.get_job(rid)["synthesis"]
    import re

    cited = set(re.findall(r"\((https?://[^)]+)\)", synthesis))
    known = {s["url"] for s in store.sources(rid)}
    assert cited, "synthesis produced no citations"
    assert cited <= known, f"fabricated citation: {cited - known}"


def test_synthesis_marks_uninspected_sources(data_dir: Path):
    rid = engine.create_research("honest citations")["research_id"]
    _run_all(
        rid, fake_search(default=SUPPORTING), fake_fetch({}, fail={h["url"] for h in SUPPORTING})
    )
    synthesis = store.get_job(rid)["synthesis"]
    assert "not inspected" in synthesis


def test_final_result_persists_and_completes(data_dir: Path):
    rid = engine.create_research("final")["research_id"]
    _run_all(rid, fake_search(default=SUPPORTING), fake_fetch({h["url"]: "t" for h in SUPPORTING}))
    job = store.get_job(rid)
    assert job["status"] == store.COMPLETED
    assert job["synthesis"].startswith("# Research:")
    assert job["confidence"] == "high"


# ----------------------------------------------------------------- mission integration


def test_research_runs_end_to_end_through_the_mission_engine(data_dir: Path, monkeypatch):
    monkeypatch.setattr(engine, "_default_search", fake_search(default=SUPPORTING))
    monkeypatch.setattr(engine, "_default_fetch", lambda url: "agreeing body text")

    created = engine.create_research("mission integration")
    rid, mid = created["research_id"], created["mission_id"]

    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    missions.run(mid, lambda step, ctx: call_action(None, step["action"], step["params"], ""))

    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert store.get_job(rid)["status"] == store.COMPLETED
    assert len(mstore.checkpoints(mid)) == len(engine.PHASES)


def test_background_worker_executes_research(data_dir: Path, monkeypatch):
    monkeypatch.setenv("JARVIS_MISSION_WORKER", "1")
    monkeypatch.setattr(engine, "_default_search", fake_search(default=SUPPORTING))
    monkeypatch.setattr(engine, "_default_fetch", lambda url: "agreeing body")

    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    created = engine.create_research("worker research")
    worker.start(
        lambda step, ctx: call_action(None, step["action"], step["params"], ""), poll_s=0.05
    )

    deadline = time.time() + 20
    while time.time() < deadline:
        if store.get_job(created["research_id"])["status"] == store.COMPLETED:
            break
        time.sleep(0.05)
    assert store.get_job(created["research_id"])["status"] == store.COMPLETED


def test_pause_resume_and_cancel_via_mission(data_dir: Path, monkeypatch):
    monkeypatch.setattr(engine, "_default_search", fake_search(default=SUPPORTING))
    monkeypatch.setattr(engine, "_default_fetch", lambda url: "body")
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    runner = lambda step, ctx: call_action(None, step["action"], step["params"], "")  # noqa: E731

    created = engine.create_research("pause me")
    mid = created["mission_id"]
    missions.run(mid, runner, max_steps=2)
    assert missions.get(mid)["state"] == mstore.PAUSED
    done_before = missions.get(mid)["completed_steps"]

    mstore.make_runnable(mid)
    missions.run(mid, runner)
    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert missions.get(mid)["completed_steps"] > done_before

    other = engine.create_research("cancel me")
    assert missions.cancel(other["mission_id"]) is True
    assert missions.get(other["mission_id"])["state"] == mstore.CANCELLED


def test_bounded_execution_does_not_loop(data_dir: Path, monkeypatch):
    monkeypatch.setattr(engine, "_default_search", fake_search(default=SUPPORTING))
    monkeypatch.setattr(engine, "_default_fetch", lambda url: "body")
    rid = engine.create_research("bounded")["research_id"]
    calls = {"n": 0}
    orig = engine.run_phase

    def counting(research_id, phase, **kw):
        calls["n"] += 1
        return orig(research_id, phase, **kw)

    monkeypatch.setattr(engine, "run_phase", counting)
    for phase in engine.PHASES:
        engine.run_phase(rid, phase)
    assert calls["n"] == len(engine.PHASES)


def test_terminal_failure_is_persisted(data_dir: Path):
    with pytest.raises(ValueError):
        engine.run_phase("does-not-exist", "plan")


def test_unknown_phase_rejected(data_dir: Path):
    rid = engine.create_research("bad phase")["research_id"]
    with pytest.raises(ValueError):
        engine.run_phase(rid, "not_a_phase")


# ----------------------------------------------------------------- isolation between jobs


def test_multiple_research_jobs_do_not_interfere(data_dir: Path):
    a = engine.create_research("job A")["research_id"]
    b = engine.create_research("job B")["research_id"]
    _run_all(
        a, fake_search(default=SUPPORTING), fake_fetch({h["url"]: "a body" for h in SUPPORTING})
    )
    _run_all(
        b, fake_search(default=CONTRADICTING), fake_fetch({CONTRADICTING[0]["url"]: "false myth"})
    )

    assert {s["research_id"] for s in store.sources(a)} == {a}
    assert {s["research_id"] for s in store.sources(b)} == {b}
    assert store.claims(a)[0]["confidence"] == "high"
    assert store.claims(b)[0]["confidence"] == "contradicted"
    assert store.get_job(a)["synthesis"] != store.get_job(b)["synthesis"]


def test_module_reload_durability(data_dir: Path):
    import importlib

    rid = engine.create_research("reload")["research_id"]
    engine.phase_plan(rid)
    importlib.reload(store)
    assert store.get_job(rid)["objective"] == "reload"
    assert len(store.questions(rid)) >= 2


# ----------------------------------------------------------------- handlers


def test_research_actions_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {s["action"] for s in all_actions()}
    for action in (
        "research_create",
        "research_status",
        "research_list",
        "research_report",
        "research_run",
        "research_pause",
        "research_cancel",
        "research_recover",
        "research_step",
    ):
        assert action in names, f"{action} not registered"


def test_handler_round_trip(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    created = call_action(None, "research_create", {"objective": "handler rt"}, "")
    assert created["ok"] is True
    rid = created["research_id"]

    status = call_action(None, "research_status", {"research_id": rid}, "")
    assert status["ok"] is True
    assert status["research"]["objective"] == "handler rt"

    listed = call_action(None, "research_list", {}, "")
    assert any(j["id"] == rid for j in listed["research"])

    cancelled = call_action(None, "research_cancel", {"research_id": rid}, "")
    assert cancelled["ok"] is True
    assert store.get_job(rid)["status"] == store.CANCELLED


def test_report_handler_returns_traceable_structure(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    rid = engine.create_research("report handler")["research_id"]
    _run_all(rid, fake_search(default=SUPPORTING), fake_fetch({h["url"]: "b" for h in SUPPORTING}))
    out = call_action(None, "research_report", {"research_id": rid}, "")
    assert out["ok"] is True
    assert out["report"]["claims"][0]["evidence"]


# ----------------------------------------------------------------- crash recovery

_CRASH = """
import os, sys
sys.path.insert(0, {repo!r})
os.environ["JARVIS_DATA_DIR"] = {data_dir!r}
from unittest.mock import MagicMock
sys.modules.setdefault("ollama", MagicMock())

from jarvis.research import engine, store

rid = {rid!r}
SUP = {sup!r}

engine.phase_plan(rid)
engine.phase_search(rid, lambda q, n: SUP[:n])
engine.phase_collect(rid, lambda url: "collected body text")
# Evidence is now durable. Die before analysis/synthesis.
os._exit(9)
"""


def test_evidence_survives_real_process_crash(data_dir: Path, tmp_path: Path):
    rid = engine.create_research("crash research")["research_id"]

    script = tmp_path / "crash_research.py"
    script.write_text(
        textwrap.dedent(_CRASH).format(
            repo=str(REPO_ROOT), data_dir=str(data_dir), rid=rid, sup=SUPPORTING
        ),
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["JARVIS_DATA_DIR"] = str(data_dir)
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120, env=env
    )
    assert proc.returncode == 9, f"child did not crash: {proc.stderr[-1500:]}"

    # Everything collected before the crash is still on disk.
    assert len(store.questions(rid)) >= 2
    assert len(store.sources(rid)) == 2
    assert len(store.evidence(rid)) == 2
    assert all(s["inspected"] for s in store.sources(rid))
    assert store.get_job(rid)["synthesis"] is None

    # Resuming does not re-fetch what was already collected.
    fetches: list[str] = []

    def counting_fetch(url: str) -> str:
        fetches.append(url)
        return "refetched"

    engine.phase_collect(rid, counting_fetch)
    assert fetches == [], "resumed research re-fetched already-inspected sources"

    engine.phase_analyze(rid)
    engine.phase_synthesize(rid)
    assert store.get_job(rid)["status"] == store.COMPLETED
    assert len(store.evidence(rid)) == 2, "recovery duplicated evidence"
