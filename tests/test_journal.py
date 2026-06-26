"""Bullet journal store, routing, and handlers."""

import pytest
from jarvis.modules.journal import BulletJournal, _format_bullet, _month_key, _today
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture
def journal(data_dir):
    return BulletJournal(path=data_dir / "journal" / "bullet_journal.json")


@pytest.fixture
def session():
    return SessionContext()


def test_daily_add_and_complete(journal):
    b = journal.daily_add("Write tests", "task")
    assert b["type"] == "task"
    page = journal.daily_get()
    assert len(page["bullets"]) == 1
    done = journal.bullet_complete(b["id"])
    assert done and done["status"] == "done"


def test_parse_rapid_log(journal):
    text = "• task one\n○ meeting\n— note line"
    created = journal.parse_rapid_log(text)
    assert len(created) == 3
    types = {c["type"] for c in created}
    assert types == {"task", "event", "note"}


def test_parse_rapid_log_default_type(journal):
    created = journal.parse_rapid_log("Dentist at 3pm", default_type="event")
    assert len(created) == 1
    assert created[0]["type"] == "event"


def test_parse_rapid_log_text_prefixes(journal):
    created = journal.parse_rapid_log("e: team standup\nt: pytest journal scratch\nn: idea")
    assert [c["type"] for c in created] == ["event", "task", "note"]


def test_monthly_calendar(journal):
    journal.daily_add("Day entry", "task", day="2026-06-08")
    journal.monthly_calendar_note(8, "Fly fishing")
    cal = journal.monthly_calendar("2026-06")
    assert len(cal["weeks"]) >= 4
    assert cal["days"]["8"]["count"] == 1
    assert cal["calendar_notes"]["8"] == "Fly fishing"
    assert "2026-06-19" in cal["holidays"]
    assert cal["holidays"]["2026-06-19"][0]["name"] == "Juneteenth"


def test_journal_holidays_observed_weekend(monkeypatch):
    from jarvis.journal_holidays import holidays_for_month

    monkeypatch.delenv("JARVIS_HOLIDAY_STATE", raising=False)
    monkeypatch.delenv("JARVIS_WEATHER_LOCATION", raising=False)
    july = holidays_for_month("2026-07", state=None)
    assert "2026-07-03" in july
    assert july["2026-07-03"][0]["name"] == "Independence Day"


def test_journal_holidays_observances(monkeypatch):
    from jarvis.journal_holidays import holidays_for_month

    monkeypatch.setenv("JARVIS_HOLIDAY_OBSERVANCES", "1")
    may = holidays_for_month("2026-05", state=None)
    assert "2026-05-10" in may
    assert any(h["name"] == "Mother's Day" for h in may["2026-05-10"])
    june = holidays_for_month("2026-06", state=None)
    assert "2026-06-21" in june
    assert any(h["name"] == "Father's Day" for h in june["2026-06-21"])


def test_open_tasks(journal):
    journal.daily_add("Open task", "task")
    journal.daily_add("Done task", "task")
    journal.bullet_complete(journal.daily_get()["bullets"][1]["id"])
    journal.monthly_add("Monthly task", "task")
    open_tasks = journal.open_tasks()
    assert len(open_tasks) == 2


def test_migrate_month(journal):
    mk = _month_key()
    journal.monthly_add("Carry forward", "task", month=mk)
    y, m = map(int, mk.split("-"))
    nm = f"{y:04d}-{m+1:02d}" if m < 12 else f"{y+1:04d}-01"
    r = journal.migrate_month(mk, nm, dest="monthly")
    assert r["migrated"] == 1
    src = journal.monthly_get(mk)["bullets"]
    assert len(src) == 1 and src[0]["status"] == "migrated"
    assert len(journal.monthly_get(nm)["bullets"]) == 1


def test_migrate_month_to_future(journal):
    mk = _month_key()
    journal.monthly_add("Future bound", "task", month=mk)
    y, m = map(int, mk.split("-"))
    nm = f"{y:04d}-{m+1:02d}" if m < 12 else f"{y+1:04d}-01"
    r = journal.migrate_month(mk, nm, dest="future")
    assert r["migrated"] == 1
    assert len(journal.future_list(nm)) == 1


def test_search(journal):
    journal.daily_add("Unique zebra keyword", "note")
    hits = journal.search("zebra")
    assert hits and "zebra" in hits[0]["content"].lower()


def test_stats(journal):
    journal.daily_add("One", "task")
    s = journal.stats()
    assert s["open_tasks"] >= 1
    assert s["today"] == _today()


def test_journal_today_route(session):
    assert route("journal today", session)["action"] == "journal_today"


def test_journal_open_tasks_route(session):
    assert route("what are my open tasks", session)["action"] == "journal_open_tasks"


def test_journal_log_handler(assistant, data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    assert assistant.journal.path == data_dir / "journal" / "bullet_journal.json"
    result = assistant.process("Log: • pytest journal scratch")
    assert result["ok"] is True
    assert result["module"] == "journal"
    assert assistant.journal.daily_get()["bullets"]


def test_format_bullet():
    b = {"type": "task", "status": "open", "content": "hello", "signifiers": ["important"]}
    assert "hello" in _format_bullet(b)


def test_collection_presets(journal):
    from jarvis.journal_presets import list_presets, preset_by_id

    presets = list_presets([])
    assert len(presets) >= 8
    assert not presets[0]["active"]
    p = preset_by_id("books")
    assert p and p["name"] == "Books to Read"
    journal.collection_create(p["name"], p["description"])
    active = list_presets(journal.collection_list())
    books = next(x for x in active if x["id"] == "books")
    assert books["active"] is True


def test_daily_quote(journal):
    page = journal.daily_get("2026-06-08")
    q = page.get("quote") or {}
    assert q.get("text")
    assert q.get("tradition") in ("stoic", "native_american", "tai_chi")


def test_daily_weather(journal, monkeypatch):
    from jarvis import journal_weather

    fake = {
        "date": "2026-06-08",
        "location": "Testville",
        "high": 72.0,
        "low": 55.0,
        "unit": "°F",
        "code": 2,
        "icon": "⛅",
        "condition": "Partly cloudy",
        "summary": "Partly cloudy · H 72°F / L 55°F",
        "source": "open-meteo",
    }
    monkeypatch.setattr(journal_weather, "weather_for_day", lambda day=None: fake)
    page = journal.daily_get("2026-06-08")
    assert page.get("weather", {}).get("high") == 72.0
    assert "Partly cloudy" in page["weather"]["summary"]


def test_weather_module(monkeypatch):
    from jarvis.journal_weather import format_weather_line, weather_for_day

    def fake_json(url, timeout=12.0):
        if "ip-api.com" in url:
            return {"status": "success", "lat": 43.0, "lon": -77.0, "city": "Rochester", "regionName": "NY", "countryCode": "US"}
        if "open-meteo.com/v1/forecast" in url:
            return {
                "daily": {
                    "time": ["2026-06-10"],
                    "temperature_2m_max": [75.2],
                    "temperature_2m_min": [58.1],
                    "weathercode": [2],
                }
            }
        return None

    monkeypatch.setattr("jarvis.journal_weather._http_json", fake_json)
    monkeypatch.setenv("JARVIS_WEATHER_IP_LOOKUP", "1")
    monkeypatch.delenv("JARVIS_WEATHER_CITY", raising=False)
    monkeypatch.delenv("JARVIS_WEATHER_LAT", raising=False)
    w = weather_for_day("2026-06-10")
    assert w and w["high"] == 75.2
    assert "Partly cloudy" in w["condition"]
    assert w.get("icon") == "⛅"
    assert format_weather_line(w).startswith("⛅ Rochester")


def test_daily_prompts(journal):
    page = journal.daily_get("2026-06-08")
    prompts = page.get("prompts") or {}
    assert prompts.get("morning_question")
    assert prompts.get("evening_question")
    journal.daily_set_prompts("2026-06-08", morning="Ready", evening="Tired")
    updated = journal.daily_get("2026-06-08")
    assert updated["prompts"]["morning"] == "Ready"


def test_weekly_log(journal):
    from jarvis.modules.journal import _week_key

    b = journal.weekly_add("Weekly task", "task")
    assert b["location"].startswith("weekly:")
    page = journal.weekly_get(_week_key())
    assert any(x["content"] == "Weekly task" for x in page["bullets"])


def test_habit_tracker(journal):
    journal.habit_toggle("meditation", "2026-06-08")
    tracker = journal.habit_tracker("2026-06")
    med = next(h for h in tracker["habits"] if h["id"] == "meditation")
    assert med["days"]["2026-06-08"] is True


def test_daily_photo(journal, tmp_path, monkeypatch):
    from jarvis.modules import journal as journal_mod

    monkeypatch.setattr(journal_mod, "JOURNAL_PHOTOS_DIR", tmp_path / "photos")
    entry = journal.daily_add_photo("2026-06-08", "test.png", b"\x89PNG\r\n", "Sunset")
    assert entry["caption"] == "Sunset"
    page = journal.daily_get("2026-06-08")
    assert len(page["photos"]) == 1
    assert journal.daily_delete_photo("2026-06-08", entry["id"])


def test_bullet_remember_text(journal):
    b = journal.daily_add("Remember me", "note")
    text = journal.bullet_remember_text(b["id"])
    assert text and "Remember me" in text


def test_journal_remember_route(session):
    assert route("remember journal entry", session)["action"] == "journal_remember"


def test_auto_index_daily(journal):
    journal.daily_add("Indexed day", "task", day="2026-06-08")
    entries = journal.index_list()
    assert any(e.get("auto_source") == "daily:2026-06-08" for e in entries)


def test_auto_index_important_bullet(journal):
    b = journal.daily_add("* Big idea", "note")
    journal.bullet_toggle_signifier(b["id"], "important")
    entries = journal.index_list()
    assert any(e.get("auto_source") == f"bullet:{b['id']}" for e in entries)


def test_rebuild_auto_index(journal):
    journal.daily_add("One", "task", day="2026-06-01")
    journal.weekly_add("Week task", "task")
    journal.collection_create("Test Col", "desc")
    r = journal.rebuild_auto_index()
    assert r["total"] >= 3
    assert r["auto"] >= 3


def test_bullet_add_child(journal):
    parent = journal.daily_add("Parent task", "task")
    child = journal.bullet_add_child(parent["id"], "Sub step", "task")
    assert child and child["content"] == "Sub step"
    page = journal.daily_get()
    assert page["bullets"][0].get("children")


def test_bullet_schedule(journal):
    b = journal.monthly_add("Schedule me", "task")
    scheduled = journal.bullet_schedule(b["id"], "2026-12")
    assert scheduled
    found = journal._find_bullet(b["id"])
    assert found and found[0]["status"] == "scheduled"


def test_thread_to_daily(journal):
    b = journal.monthly_add("Thread me", "task")
    threaded = journal.bullet_thread_to_daily(b["id"], "2026-06-10")
    assert threaded
    src = journal._find_bullet(b["id"])
    assert src and src[0]["status"] == "migrated"
    day = journal.daily_get("2026-06-10", enrich=False)
    assert any(x["content"] == "Thread me" for x in day["bullets"])


def test_transfer_future_to_month(journal):
    journal.future_add("2026-12", "Future task", "task")
    r = journal.transfer_future_to_month("2026-12", "2026-06")
    assert r["migrated"] == 1
    assert journal.monthly_get("2026-06")["bullets"]


def test_page_numbers(journal):
    page = journal.daily_get("2026-06-08", enrich=False)
    assert page.get("page_number")


def test_wellness(journal):
    journal.daily_set_wellness("2026-06-08", mood=4, gratitude=["Sun", "Coffee"])
    overview = journal.wellness_overview("2026-06")
    assert overview["mood_average"] == 4.0
    assert len(overview["gratitude_stream"]) == 2


def test_monthly_review(journal):
    r = journal.monthly_review_toggle("scan_monthly", "2026-06")
    assert r["review"]["scan_monthly"] is True


def test_undo(journal):
    journal.daily_add("Before undo", "note")
    journal.daily_add("After undo", "note")
    result = journal.undo()
    assert result.get("ok")
    page = journal.daily_get(enrich=False)
    assert len(page["bullets"]) == 1
    assert page["bullets"][0]["content"] == "Before undo"


def test_event_time_parse(journal):
    b = journal.daily_add("14:30 Team standup", "event", day="2026-06-08")
    assert b.get("time") == "14:30"
    assert "standup" in b.get("content", "").lower()


def test_search_nested(journal):
    parent = journal.daily_add("Parent", "task", day="2026-06-08")
    journal.bullet_add_child(parent["id"], "Nested zebra", "note")
    hits = journal.search("zebra")
    assert any("zebra" in h.get("content", "").lower() for h in hits)


def test_rapid_log_indent(journal):
    created = journal.parse_rapid_log("Main task\n  sub note", day="2026-06-08")
    assert len(created) == 2
    page = journal.daily_get("2026-06-08", enrich=False)
    assert page["bullets"][0].get("children")


def test_redo(journal):
    journal.daily_add("One", "note")
    journal.daily_add("Two", "note")
    journal.undo()
    assert len(journal.daily_get(enrich=False)["bullets"]) == 1
    journal.redo()
    assert len(journal.daily_get(enrich=False)["bullets"]) == 2


def test_migrate_daily_open(journal):
    journal.daily_add("Carry", "task", day="2026-06-08")
    r = journal.migrate_daily_open("2026-06-08", "2026-06-09")
    assert r["migrated"] == 1
    src = journal.daily_get("2026-06-08", enrich=False)["bullets"]
    assert len(src) == 1 and src[0]["status"] == "migrated"
    assert journal.daily_get("2026-06-09", enrich=False)["bullets"]


def test_weekly_review(journal):
    wk = "2026-W23"
    journal.weekly_review_toggle("scan_weekly", wk)
    r = journal.weekly_review_get(wk)
    assert r["review"]["scan_weekly"] is True
    journal.weekly_review_set_notes("Good week", wk)
    assert journal.weekly_review_get(wk)["review_notes"] == "Good week"


def test_daily_timeline(journal):
    journal.daily_add("Team standup", "event", day="2026-06-08", time="09:30")
    t = journal.daily_timeline("2026-06-08")
    assert len(t["events"]) == 1
    assert t["events"][0]["time"] == "09:30"


def test_gratitude_prefix(journal):
    page = journal.daily_add_gratitude("2026-06-08", "my health")
    assert page["gratitude"][-1] == "I am grateful for my health"
    page = journal.daily_add_gratitude("2026-06-08", "I am grateful for coffee")
    assert page["gratitude"][-1] == "I am grateful for coffee"


def test_match_open_task(journal):
    journal.monthly_add("Finish taxes", "task")
    journal.monthly_add("Buy groceries", "task")
    task, candidates, hint = journal.match_open_task("schedule finish taxes to 2026-08")
    assert task and "taxes" in task["content"].lower()
    assert not candidates
    task2, candidates2, _ = journal.match_open_task("schedule task to 2026-08")
    assert task2 is None
    assert len(candidates2) >= 2


def test_month_print_html_sections(journal):
    from jarvis.journal_export import month_print_html

    journal.monthly_add("Monthly item", "task")
    journal.daily_add("Daily item", "note", day="2026-06-08")
    html = month_print_html(journal, "2026-06")
    assert "Calendar" in html
    assert "Future log" in html
    assert "Habit tracker" in html
    assert "Weekly ·" in html
    assert "status-" in html or "Daily item" in html
