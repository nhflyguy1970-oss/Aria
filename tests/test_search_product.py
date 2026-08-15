"""Search product — one engine, federation, ranking, history, Mission Control."""

from __future__ import annotations

import pytest


@pytest.fixture()
def search_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.search_product.history as history
    import jarvis.search_product.sessions as sessions
    import jarvis.search_product.settings as settings

    (tmp_path / "search_product").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "search_product" / "history.json")
    monkeypatch.setattr(history, "SAVED_FILE", tmp_path / "search_product" / "saved.json")
    monkeypatch.setattr(sessions, "SESSIONS_FILE", tmp_path / "search_product" / "sessions.json")
    monkeypatch.setattr(settings, "SETTINGS_FILE", tmp_path / "search_product" / "settings.json")
    return tmp_path


def test_terminology_boundaries():
    from jarvis.search_product.terminology import BOUNDARIES, FACETS, MENTAL_MODEL, TERMINOLOGY

    assert TERMINOLOGY["product"] == "Search"
    assert TERMINOLOGY["pipeline"] == "shared_search_pipeline"
    assert "search_result_contract" in BOUNDARIES["owns"]
    assert "documents_corpus" in BOUNDARIES["does_not_own"]
    assert "second_search_engine" in BOUNDARIES["does_not_own"]
    assert "everything" in FACETS
    assert "web" in FACETS
    assert MENTAL_MODEL["sidebar"].startswith("Filter")


def test_search_result_contract():
    from jarvis.search_product.contract import make_result, to_legacy_hit, validate_result

    r = make_result(
        source="documents",
        source_label="Documents",
        title="Warranty",
        summary="oven warranty",
        preview="oven warranty pdf",
        location="/docs/warranty.pdf",
        score=0.9,
        open_action={"view": "documents", "query": "warranty"},
    )
    assert validate_result(r)
    assert r["confidence"] > 0
    legacy = to_legacy_hit(r)
    assert legacy["source_type"] == "documents"
    assert "excerpt" in legacy


def test_intent_classification():
    from jarvis.search_product.intent import classify_intent, select_corpora
    from jarvis.search_product.terminology import FACETS

    code = classify_intent("find the python function import")
    assert code["primary"] == "code"
    web = classify_intent("latest news today online")
    assert "web" in web["intents"]
    enabled = {f for f in FACETS if f != "everything"}
    picked = select_corpora(code, facets=None, enabled=enabled)
    assert "code" in picked
    assert "memory" in picked
    everything = select_corpora(classify_intent("alpha beta"), facets=None, enabled=enabled)
    from jarvis.search_product.intent import _FAST_EVERYTHING

    assert everything == [f for f in _FAST_EVERYTHING if f in enabled]
    assert "web" not in everything
    assert "code" not in everything
    # Explicit everything facet still fans out.
    full = select_corpora(classify_intent("alpha beta"), facets=["everything"], enabled=enabled)
    assert full == [f for f in FACETS if f != "everything"]


def test_ranking_and_dedupe():
    from jarvis.search_product.ranking import dedupe_results, rank_results

    results = [
        {"id": "1", "source": "documents", "title": "Docker Compose", "summary": "compose file", "preview": "docker compose", "score": 0.5, "strategy": "keyword", "metadata": {}, "open": {}},
        {"id": "2", "source": "code", "title": "other", "summary": "unrelated", "preview": "zzz", "score": 0.9, "strategy": "semantic", "metadata": {}, "open": {}},
        {"id": "3", "source": "documents", "title": "Docker Compose", "summary": "compose file", "preview": "docker compose", "score": 0.4, "strategy": "keyword", "metadata": {}, "open": {}},
    ]
    ranked = rank_results(results, query="docker compose", intent={"primary": "documents"})
    assert ranked[0]["source"] == "documents"
    deduped = dedupe_results(ranked)
    assert len(deduped) == 2


def test_pipeline_mocked_retrievers(search_data, monkeypatch):
    from jarvis.search_product import pipeline as pipe
    from jarvis.search_product.contract import make_result

    def fake_docs(q, limit):
        return [
            make_result(
                source="documents",
                source_label="Documents",
                title="Hit",
                summary=q,
                preview=q,
                score=0.8,
                open_action={"view": "documents", "query": q},
            )
        ]

    monkeypatch.setitem(pipe.RETRIEVERS if hasattr(pipe, "RETRIEVERS") else {}, "documents", fake_docs)
    # Patch module-level RETRIEVERS used inside run_search
    import jarvis.search_product.retrievers as ret

    monkeypatch.setitem(ret.RETRIEVERS, "documents", fake_docs)
    for k in list(ret.RETRIEVERS):
        if k != "documents":
            monkeypatch.setitem(ret.RETRIEVERS, k, lambda q, limit, **kw: [])

    # Restrict enabled corpora
    import jarvis.search_product.settings as settings

    monkeypatch.setattr(
        settings,
        "load_settings",
        lambda: {
            **settings.DEFAULTS,
            "enabled_corpora": ["documents"],
            "opt_in_corpora": {},
            "parallel_retrieval": False,
            "record_history": True,
        },
    )
    monkeypatch.setattr(settings, "enabled_corpora_set", lambda _s=None: {"documents"})

    from jarvis.search_product.pipeline import run_search

    out = run_search("warranty", facets=["documents"], limit=5, parallel=False)
    assert out["ok"] is True
    assert out["hit_count"] >= 1
    assert out["results"][0]["source"] == "documents"
    assert out["pipeline"] == "shared_search_pipeline"
    assert out["latency_ms"] >= 0


def test_history_and_saved(search_data):
    from jarvis.search_product.history import clear_history, list_history, list_saved, record_query, save_search, delete_saved

    record_query("alpha", facets=["documents"], hit_count=2, latency_ms=12)
    record_query("beta", facets=["memory"], hit_count=1, latency_ms=8)
    hist = list_history()
    assert hist[0]["query"] == "beta"
    saved = save_search("alpha", name="Alpha docs", facets=["documents"])
    assert saved["ok"] is True
    assert list_saved()[0]["query"] == "alpha"
    delete_saved(saved["saved"]["id"])
    assert list_saved() == []
    clear_history()
    assert list_history() == []


def test_settings_opt_in(search_data):
    from jarvis.search_product.terminology import FACETS
    from jarvis.search_product.settings import enabled_corpora_set, load_settings, save_settings

    s = save_settings({"opt_in_corpora": {"gallery": True, "home_assistant": False}})
    enabled = enabled_corpora_set(s)
    assert enabled == {f for f in FACETS if f != "everything"}
    assert "gallery" in enabled
    assert "home_assistant" in enabled
    assert "documents" in enabled
    assert load_settings()["opt_in_corpora"]["gallery"] is True


def test_pipeline_reports_partial_and_all_failures(search_data, monkeypatch):
    from jarvis.search_product import pipeline as pipe
    from jarvis.search_product.contract import make_result

    def ok_docs(q, limit):
        return [
            make_result(
                source="documents",
                source_label="Documents",
                title="Hit",
                summary=q,
                preview=q,
                score=0.8,
                open_action={"view": "documents", "query": q},
            )
        ]

    def broken(q, limit):
        raise RuntimeError("corpus exploded")

    monkeypatch.setattr(
        "jarvis.search_product.settings.load_settings",
        lambda: {
            "enabled_corpora": ["documents", "memory"],
            "opt_in_corpora": {},
            "parallel_retrieval": False,
            "record_history": False,
            "max_results": 10,
            "default_mode": "browse",
            "code_mode": "auto",
        },
    )
    monkeypatch.setattr(
        "jarvis.search_product.settings.enabled_corpora_set",
        lambda _s=None: {"documents", "memory"},
    )
    monkeypatch.setattr(pipe, "load_settings", lambda: {
        "enabled_corpora": ["documents", "memory"],
        "opt_in_corpora": {},
        "parallel_retrieval": False,
        "record_history": False,
        "max_results": 10,
        "default_mode": "browse",
        "code_mode": "auto",
    })
    monkeypatch.setattr(pipe, "enabled_corpora_set", lambda _s=None: {"documents", "memory"})
    monkeypatch.setitem(pipe.RETRIEVERS, "documents", ok_docs)
    monkeypatch.setitem(pipe.RETRIEVERS, "memory", broken)

    partial = pipe.run_search("warranty", facets=["documents", "memory"], parallel=False)
    assert partial["ok"] is True
    assert partial["degraded"] is True
    assert partial["failures"][0]["corpus"] == "memory"
    assert set(partial["searched"]) == {"documents", "memory"}

    monkeypatch.setitem(pipe.RETRIEVERS, "documents", broken)
    all_failed = pipe.run_search("warranty", facets=["documents", "memory"], parallel=False)
    assert all_failed["ok"] is False
    assert all_failed["degraded"] is True
    assert {f["corpus"] for f in all_failed["failures"]} == {"documents", "memory"}


def test_unified_search_delegates(search_data, monkeypatch):
    from jarvis.search_product.contract import make_result

    import jarvis.search_product.retrievers as ret

    monkeypatch.setitem(
        ret.RETRIEVERS,
        "memory",
        lambda q, limit, **kw: [
            make_result(
                source="memory",
                source_label="Memory",
                title="mem",
                summary=f"about {q}",
                preview=f"about {q}",
                score=0.7,
                open_action={"view": "memory", "query": q},
            )
        ],
    )
    for k in list(ret.RETRIEVERS):
        if k != "memory":
            monkeypatch.setitem(ret.RETRIEVERS, k, lambda q, limit, **kw: [])

    import jarvis.search_product.settings as settings

    monkeypatch.setattr(settings, "enabled_corpora_set", lambda _s=None: {"memory"})
    monkeypatch.setattr(
        settings,
        "load_settings",
        lambda: {**settings.DEFAULTS, "enabled_corpora": ["memory"], "opt_in_corpora": {}, "parallel_retrieval": False},
    )

    from jarvis.knowledge.search import format_unified_results, unified_search

    result = unified_search("jeff", limit=5)
    assert result["ok"] is True
    assert result["pipeline"] == "shared_search_pipeline"
    assert result["hits"]
    assert result["results"]
    msg = format_unified_results(result)
    assert "jeff" in msg.lower() or "Search" in msg


def test_product_status_and_home(search_data, monkeypatch):
    from jarvis.search_product.engine import home_payload, product_status

    monkeypatch.setattr(
        "jarvis.search_product.pipeline.run_search",
        lambda *a, **k: {"ok": True, "results": [], "searched": [], "latency_ms": 1},
    )
    st = product_status()
    assert st["product"] == "Search"
    assert st["ok"] is True
    home = home_payload(q="")
    assert home["home"] == "Search Home"
    assert "mental_model" in home
    assert "history" in home


def test_mission_panel(search_data):
    from jarvis.search_product.mission_bridge import search_mission_panel

    panel = search_mission_panel()
    assert panel["product"] == "Search"
    assert "deep_links" in panel
    assert panel["deep_links"]["home"] == "#search"


def test_diagnostics_and_recovery(search_data):
    from jarvis.search_product.diagnostics import diagnostics, recovery_status

    d = diagnostics()
    assert d["ok"] is True
    assert d["pipeline"] == "shared_search_pipeline"
    assert isinstance(d["corpora"], list)
    r = recovery_status()
    assert "steps" in r


def test_experimental_answer_browse(search_data, monkeypatch):
    from jarvis.search_product.experimental import answer_vs_browse, experimental_status

    monkeypatch.setattr(
        "jarvis.search_product.experimental.run_search",
        lambda q, mode="browse", limit=8: {"ok": True, "mode": mode, "results": [], "query": q},
    )
    st = experimental_status()
    assert st["features"]
    out = answer_vs_browse("what is docker?")
    assert out["recommended_mode"] in ("answer", "browse")


def test_planner_calendar_retrievers(search_data, monkeypatch):
    from jarvis.search_product.retrievers import retrieve_calendar, retrieve_planner

    monkeypatch.setattr(
        "jarvis.planner_store.list_tasks",
        lambda include_completed=True: [{"id": "t1", "text": "Buy milk", "notes": "", "project": "", "completed": 0, "priority": 1}],
    )
    hits = retrieve_planner("milk", 5)
    assert hits and hits[0]["source"] == "planner"

    monkeypatch.setattr(
        "jarvis.calendar_store.load_work_schedule",
        lambda: {"enabled": True, "days": {"mon": [{"start": "09:00", "end": "17:00", "label": "Deep work"}], "tue": [], "wed": [], "thu": [], "fri": [], "sat": [], "sun": []}},
    )
    cal = retrieve_calendar("deep", 5)
    assert cal and cal[0]["source"] == "calendar"


def test_code_facet_modes(search_data, monkeypatch):
    from jarvis.search_product.contract import make_result
    from jarvis.search_product.retrievers import retrieve_code

    monkeypatch.setattr(
        "jarvis.code_index.search",
        lambda q, limit=8, root=None: [{"source": "a.py", "text": "def foo", "score": 0.9}],
    )
    monkeypatch.setattr("jarvis.knowledge.git_sync.list_repo_states", lambda: [])

    calls = {"grep": 0}

    def fake_grep(text, root):
        calls["grep"] += 1
        return [("a.py", 1, "def foo")]

    monkeypatch.setattr("jarvis.fs.search_files", fake_grep)
    sem = retrieve_code("foo", 5, mode="semantic")
    assert sem
    assert all(h["metadata"].get("code_mode") == "semantic" for h in sem)
    grep_hits = retrieve_code("foo", 5, mode="grep")
    assert grep_hits
    assert calls["grep"] >= 1


def test_api_routes_registered(chat_app):
    res = chat_app.get("/api/search/product")
    assert res.status_code == 200
    body = res.json()
    assert body.get("product") == "Search"
    home = chat_app.get("/api/search/product/home")
    assert home.status_code == 200
    assert home.json().get("home") == "Search Home"
    mission = chat_app.get("/api/search/product/mission")
    assert mission.status_code == 200
    assert mission.json().get("product") == "Search"
    q = chat_app.post("/api/search/product/query", json={"query": "test", "facets": ["planner"], "limit": 5})
    assert q.status_code == 200
    assert "results" in q.json()


def test_search_product_ui_wired():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    home_js = Path("jarvis/gui/static/search_home.js").read_text(encoding="utf-8")
    router = Path("jarvis/gui/static/view_router.js").read_text(encoding="utf-8")
    palette = Path("jarvis/gui/static/command_palette.js").read_text(encoding="utf-8")
    mc = Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    sidebar = Path("jarvis/gui/static/sidebar_search.js").read_text(encoding="utf-8")
    assert 'data-view="search"' in html
    assert 'id="searchView"' in html
    assert "search_home.js" in html
    assert "initSearchHome" in home_js
    assert "searchView" in router
    assert "/api/search/product/query" in palette
    assert "Search Home" in mc
    assert "Open Search Home" in sidebar or "Filter navigation" in sidebar
