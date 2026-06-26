"""Briefing news headlines."""

import re
from datetime import datetime, timezone

import pytest

from jarvis.briefing_news import (
    _build_primary_query,
    _filter_local_headlines,
    _filter_quality_headlines,
    _is_quality_headline,
    _is_relevant_local_headline,
    _merge_local_headlines,
    briefing_news_intent,
    match_headline,
    _parse_google_news_rss,
    _parse_rss_pub_date,
    fetch_briefing_news,
    format_news_markdown,
    load_recent_headlines,
    profile_location,
    resolve_local_news_scope,
    resolve_local_place,
)
from jarvis.session import SessionContext


@pytest.fixture
def journal(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_FILE", data_dir / "journal" / "bullet_journal.json")
    monkeypatch.setattr("jarvis.modules.journal.JOURNAL_DIR", data_dir / "journal")
    (data_dir / "journal").mkdir(parents=True, exist_ok=True)
    from jarvis.modules.journal import BulletJournal

    return BulletJournal(path=data_dir / "journal" / "bullet_journal.json")


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    from jarvis.modules.memory import MemoryStore

    return MemoryStore(path=data_dir / "memory.json")


SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Major policy shift announced - Reuters</title>
      <link>https://example.com/national</link>
      <source>Reuters</source>
      <pubDate>Mon, 08 Jun 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Bridge repair scheduled downtown - Valley News</title>
      <link>https://example.com/local</link>
      <source>Valley News</source>
      <pubDate>Mon, 08 Jun 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

STALE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Old town meeting recap - Valley News</title>
      <link>https://example.com/old</link>
      <source>Valley News</source>
      <pubDate>Mon, 01 May 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_parse_google_news_rss():
    hits = _parse_google_news_rss(SAMPLE_RSS, limit=5)
    assert len(hits) == 2
    assert hits[0]["title"] == "Major policy shift announced"
    assert hits[0]["source"] == "Reuters"
    assert hits[1]["url"] == "https://example.com/local"


def test_parse_google_news_rss_filters_by_age(monkeypatch):
    monkeypatch.setattr(
        "jarvis.briefing_news.datetime",
        type(
            "FrozenDateTime",
            (),
            {
                "now": staticmethod(
                    lambda tz=None: datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)
                ),
                "fromisoformat": datetime.fromisoformat,
            },
        ),
    )
    hits = _parse_google_news_rss(SAMPLE_RSS, limit=5, max_age_days=3)
    assert len(hits) == 2
    hits = _parse_google_news_rss(STALE_RSS, limit=5, max_age_days=3)
    assert hits == []


def test_parse_rss_pub_date():
    dt = _parse_rss_pub_date("Mon, 08 Jun 2026 10:00:00 GMT")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 6


def test_build_primary_query_avoids_bare_charlestown():
    q = _build_primary_query("Charlestown, NH", max_age_days=3)
    assert "Charlestown, NH" in q
    assert "Charlestown NH" in q
    assert "New Hampshire" in q
    assert "Sullivan County" in q
    assert re.search(r'OR\s+"Charlestown"\s', q) is None
    assert q.endswith("when:3d")


def test_filter_rejects_wrong_charlestown():
    scope = {"primary": "Charlestown, NH", "towns": [], "label": "test"}
    wrong = [
        {"title": "Charlestown MA town council vote", "url": "https://x.test", "source": "Boston Globe"},
        {"title": "Boston Charlestown development plan", "url": "https://y.test", "source": "WBUR"},
        {"title": "Rhode Island Charlestown beach access", "url": "https://z.test", "source": "Providence Journal"},
    ]
    kept = _filter_local_headlines(wrong, scope)
    assert kept == []


def test_filter_keeps_charlestown_nh():
    scope = {"primary": "Charlestown, NH", "towns": [], "label": "test"}
    good = [
        {"title": "Charlestown NH selectboard meeting", "url": "https://a.test", "source": "Eagle Times"},
        {"title": "Bridge work near Charlestown", "url": "https://b.test", "source": "Valley News"},
        {"title": "Upper Valley schools announce delay", "url": "https://c.test", "source": "Valley News"},
    ]
    assert _is_relevant_local_headline(good[0], scope)
    assert _is_relevant_local_headline(good[1], scope)
    assert _is_relevant_local_headline(good[2], scope)
    assert len(_filter_local_headlines(good, scope)) == 3


def test_filter_rejects_stale_and_junk_headlines():
    scope = {"primary": "Charlestown, NH", "towns": [], "label": "test"}
    junk = [
        {"title": "North Walpole, New Hampshire - Wikipedia", "url": "https://en.wikipedia.org/wiki/North_Walpole"},
        {"title": "Update: Drawdown Initiated – 8/1/23 - The Walpolean", "url": "https://x.test"},
        {"title": "NEWS - Walpole Outdoors", "url": "https://x.test"},
        {"title": "Connecticut River flooding - Facebook", "url": "https://facebook.com/x"},
    ]
    assert _filter_quality_headlines(junk, max_age_days=3) == []
    assert _is_quality_headline(junk[1], max_age_days=3) is False


def test_match_headline_ignores_stopwords():
    headlines = [
        {"title": "Under-16s to be banned from social media by next spring", "category": "national"},
        {"title": "Connecticut River drawdown | Local News", "category": "local"},
    ]
    assert match_headline("expand on that news from my briefing", headlines) is None
    assert match_headline("local headline 1", headlines)["category"] == "local"
    assert match_headline("tell me more about connecticut river drawdown", headlines) is not None


def test_load_recent_headlines_requires_today(monkeypatch):
    monkeypatch.setattr(
        "jarvis.config._load_chat_settings",
        lambda: {
            "morning_briefing": {
                "headlines_day": "2020-01-01",
                "headlines": [{"title": "Old story", "category": "local"}],
            }
        },
    )
    assert load_recent_headlines() == []


def test_merge_local_headlines_primary_first():
    primary = [
        {"title": "Charlestown fire department drill", "url": "https://a.test", "source": "Eagle"},
        {"title": "Shared headline", "url": "https://b.test", "source": "Eagle"},
    ]
    regional = [
        {"title": "Shared headline", "url": "https://b.test", "source": "Valley News"},
        {"title": "Lebanon hospital expansion", "url": "https://c.test", "source": "Valley News"},
    ]
    merged = _merge_local_headlines(primary, regional, limit=3)
    assert [item["title"] for item in merged] == [
        "Charlestown fire department drill",
        "Shared headline",
        "Lebanon hospital expansion",
    ]


def test_profile_location(store):
    store.add("fact", "User is based in Charlestown, NH.", namespace="profile")
    assert profile_location(store) == "Charlestown, NH"


def test_resolve_local_place_prefers_env(monkeypatch, store):
    monkeypatch.setenv("JARVIS_NEWS_LOCAL", "Lebanon, NH")
    assert resolve_local_place(memory_store=store) == "Lebanon, NH"


def test_resolve_local_news_scope_defaults(monkeypatch, store):
    monkeypatch.delenv("JARVIS_NEWS_LOCAL", raising=False)
    monkeypatch.delenv("JARVIS_NEWS_LOCAL_PRIMARY", raising=False)
    scope = resolve_local_news_scope(
        memory_store=store,
        weather={"location": "Charlestown, NH"},
    )
    assert scope["primary"] == "Charlestown, NH"
    assert "Walpole NH" in scope["towns"]
    assert "Bellows Falls VT" in scope["towns"]
    assert "Hartland VT" in scope["towns"]
    assert "Charlestown" not in " ".join(scope["towns"])
    assert "Connecticut River" in scope["label"]


def test_format_news_markdown():
    news = {
        "enabled": True,
        "national": [{"title": "Headline A", "url": "https://a.test", "source": "AP"}],
        "local": [{"title": "Town meeting", "url": "https://b.test", "source": "Local"}],
        "local_place": "Connecticut River Valley (Charlestown–Lebanon, NH & VT)",
        "local_primary": "Charlestown, NH",
    }
    lines = format_news_markdown(news)
    text = "\n".join(lines)
    assert "**National headlines**" in text
    assert "**Local headlines (Connecticut River Valley (Charlestown–Lebanon, NH & VT) · Charlestown, NH first)**" in text
    assert "1. [Headline A]" in text
    assert "Town meeting" in text
    assert "local headline 2" in text


def test_fetch_briefing_news_offline(monkeypatch, store):
    monkeypatch.setattr("jarvis.briefing_news.news_available", lambda: False)
    bundle = fetch_briefing_news(memory_store=store)
    assert bundle["enabled"] is False
    assert bundle["national"] == []


def test_fetch_briefing_news_uses_rss(monkeypatch, store):
    monkeypatch.setattr("jarvis.briefing_news.news_available", lambda: True)
    monkeypatch.setenv("JARVIS_NEWS_LOCAL", "Charlestown, NH")
    monkeypatch.setattr(
        "jarvis.briefing_news.datetime",
        type(
            "FrozenDateTime",
            (),
            {
                "now": staticmethod(
                    lambda tz=None: datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)
                ),
                "fromisoformat": datetime.fromisoformat,
            },
        ),
    )

    def fake_fetch(url, timeout=10):
        if "search" in url:
            return SAMPLE_RSS
        return SAMPLE_RSS

    monkeypatch.setattr("jarvis.briefing_news._fetch_bytes", fake_fetch)
    monkeypatch.setattr("jarvis.briefing_news._CACHE", {})

    bundle = fetch_briefing_news(memory_store=store, national_limit=2, local_limit=2)
    assert bundle["enabled"] is True
    assert len(bundle["national"]) >= 1
    assert bundle["local_primary"] == "Charlestown, NH"
    assert "Connecticut River" in bundle["local_place"]


def test_build_briefing_includes_news(journal, store, monkeypatch):
    monkeypatch.setattr("jarvis.modules.journal._today", lambda: "2026-06-08")
    monkeypatch.setattr("jarvis.morning_briefing.weather_for_day", lambda day: {
        "date": day,
        "condition": "Clear",
        "high": 72,
        "low": 58,
        "unit": "°F",
        "location": "Charlestown, NH",
        "icon": "☀️",
    })
    monkeypatch.setattr(
        "jarvis.briefing_news.fetch_briefing_news",
        lambda **kwargs: {
            "enabled": True,
            "national": [{"title": "Budget vote passes", "url": "https://n.test", "source": "AP"}],
            "local": [{"title": "School board meets", "url": "https://l.test", "source": "Valley News"}],
            "local_place": "Connecticut River Valley (Charlestown–Lebanon, NH & VT)",
            "local_primary": "Charlestown, NH",
            "skipped": None,
        },
    )
    from jarvis.morning_briefing import build_briefing

    briefing = build_briefing(
        journal=journal,
        memory_store=store,
        day="2026-06-08",
        reference=datetime(2026, 6, 8, 8, 30),
    )
    assert "National headlines" in briefing["markdown"]
    assert "Budget vote passes" in briefing["markdown"]
    assert "School board meets" in briefing["markdown"]


def test_match_headline_by_index():
    headlines = [
        {"title": "Bridge repair scheduled downtown", "url": "https://a.test", "category": "national"},
        {"title": "School board meets Tuesday", "url": "https://b.test", "category": "national"},
        {"title": "River drawdown planned", "url": "https://c.test", "category": "local"},
    ]
    hit = match_headline("tell me more about local headline 1", headlines)
    assert hit and hit["title"] == "River drawdown planned"
    hit = match_headline("tell me more about headline 2", headlines)
    assert hit and hit["title"] == "School board meets Tuesday"


def test_match_headline_by_words():
    headlines = [
        {"title": "Bridge repair scheduled downtown", "url": "https://a.test"},
        {"title": "School board meets Tuesday", "url": "https://b.test"},
    ]
    hit = match_headline("more about the bridge repair story", headlines)
    assert hit and "Bridge repair" in hit["title"]


def test_briefing_news_intent_routes_detail():
    session = SessionContext()
    session.note_briefing_headlines([
        {"title": "Bridge repair scheduled downtown", "url": "https://a.test", "source": "Valley News", "category": "local"},
    ])
    intent = briefing_news_intent("tell me more about the bridge repair", session)
    assert intent
    assert intent["action"] == "briefing_news_detail"
    assert intent["params"]["title"] == "Bridge repair scheduled downtown"


def test_briefing_news_intent_vague_still_routes():
    session = SessionContext()
    session.note_briefing_headlines([
        {"title": "Bridge repair scheduled downtown", "category": "local"},
    ])
    intent = briefing_news_intent("expand on that news from my briefing", session)
    assert intent
    assert intent["action"] == "briefing_news_detail"
    assert intent["params"]["title"] == ""
