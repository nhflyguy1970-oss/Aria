"""Nightly knowledge research tests."""

import pytest

from jarvis.knowledge_research_daily import (
    RESEARCH_DIR,
    STATE_FILE,
    append_research_digest,
    build_daily_digest,
    get_category,
    research_category,
    run_nightly_research,
    _profile_research_categories,
    _profile_topic_phrases,
)


@pytest.fixture
def research_env(data_dir, monkeypatch):
    knowledge = data_dir / "knowledge"
    research = knowledge / "research"
    research.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("jarvis.knowledge.KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr("jarvis.knowledge_research_daily.KNOWLEDGE_DIR", knowledge)
    monkeypatch.setattr("jarvis.knowledge_research_daily.RESEARCH_DIR", research)
    monkeypatch.setattr("jarvis.knowledge_research_daily.STATE_FILE", research / "_state.json")
    monkeypatch.setenv("JARVIS_KNOWLEDGE_RESEARCH_DAILY", "1")
    monkeypatch.setenv("JARVIS_KNOWLEDGE_RESEARCH_REMEMBER", "0")
    return research


def test_get_category():
    cat = get_category("ai_news")
    assert cat is not None
    assert cat["slug"] == "ai-news"


def test_append_research_digest(research_env):
    saved = append_research_digest(
        "ai-news",
        "AI news",
        "2026-06-17",
        "## 2026-06-17\n\n### Summary\n\nTest digest.\n",
        [{"title": "T", "url": "http://x"}],
    )
    path = research_env / "ai-news.md"
    assert path.is_file()
    assert "Test digest" in path.read_text(encoding="utf-8")
    assert saved["slug"] == "ai-news"


def test_build_daily_digest_mocked(monkeypatch):
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: "### Summary\n\nOllama 0.6 released.\n\n### Key updates\n- New models\n",
    )
    body = build_daily_digest(
        "Ollama updates",
        [{"title": "Release", "url": "http://x", "snippet": "Ollama 0.6"}],
        day="2026-06-17",
        local_context="Installed Ollama: 0.5.0",
    )
    assert "2026-06-17" in body
    assert "Ollama" in body


def test_research_category_mocked(research_env, monkeypatch):
    monkeypatch.setattr(
        "jarvis.knowledge_research_daily._collect_results",
        lambda queries: [{"title": "AI", "url": "http://a", "snippet": "news"}],
    )
    monkeypatch.setattr(
        "jarvis.knowledge_research_daily.build_daily_digest",
        lambda *a, **k: "## 2026-06-17\n\n### Summary\n\nAI news today.\n",
    )
    result = research_category("ai_news", day="2026-06-17", force=True)
    assert result["ok"]
    assert (research_env / "ai-news.md").is_file()


def test_run_nightly_research_all_categories(research_env, monkeypatch):
    monkeypatch.setattr(
        "jarvis.knowledge_research_daily._collect_results",
        lambda queries: [{"title": "X", "url": "http://x", "snippet": "fact"}],
    )
    monkeypatch.setattr(
        "jarvis.knowledge_research_daily.build_daily_digest",
        lambda *a, **k: "## 2026-06-17\n\n### Summary\n\nUpdate.\n",
    )
    results = run_nightly_research(day="2026-06-17", force=True)
    assert len(results) >= 14
    assert all(r.get("ok") for r in results)
    assert STATE_FILE.is_file()


def test_profile_research_categories_from_memory():
    class FakeMemory:
        def list_entries(self, namespace=None, **kwargs):
            if namespace != "profile":
                return []
            return [
                {
                    "content": "User often works on: fly tying, home automation, and local LLMs.",
                    "tags": ["profile", "interests"],
                },
                {
                    "content": "User's tech stack and tools: Python, Ollama, Cursor.",
                    "tags": ["profile", "tech_stack"],
                },
            ]

    mem = FakeMemory()
    phrases = _profile_topic_phrases(mem)
    assert "fly tying" in phrases
    assert "home automation" in phrases
    cats = _profile_research_categories(mem)
    assert any(c["kind"] == "profile" for c in cats)
    assert any("fly tying" in c["title"].lower() for c in cats)


def test_router_knowledge_research():
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("run nightly knowledge research", SessionContext())
    assert intent["action"] == "knowledge_research_run"
