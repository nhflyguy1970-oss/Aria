"""Chat-related router fast-path tests (no LLM)."""

import pytest
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture
def session():
    return SessionContext()


def test_plain_chat_fallback(session, monkeypatch):
    monkeypatch.setattr("jarvis.llm.route_with_tools", lambda *a, **k: None)
    monkeypatch.setattr("jarvis.llm.ask", lambda *a, **k: "not json")
    intent = route("Tell me a joke about Python", session)
    assert intent["action"] == "chat"


def test_remember(session):
    intent = route("Remember that I like dark mode", session)
    assert intent["action"] == "remember"
    assert "dark mode" in intent["params"]["text"].lower()


def test_recall(session):
    intent = route("recall", session)
    assert intent["action"] == "recall"


def test_web_search(session):
    intent = route("Search the web for local LLM benchmarks", session)
    assert intent["action"] == "web_search"
    assert "benchmark" in intent["params"]["query"].lower()


def test_greeting(session):
    intent = route("hello", session)
    assert intent["action"] == "greeting"


def test_capabilities(session):
    intent = route("what can you do?", session)
    assert intent["action"] == "capabilities"


def test_file_attachment_routes_to_chat(session):
    attachment = {"path": "/tmp/notes.txt", "kind": "file", "name": "notes.txt"}
    intent = route("Summarize this", session, attachment)
    assert intent["action"] == "chat"
    assert intent["params"]["file_path"] == "/tmp/notes.txt"


def test_clarification_resolution(session):
    session.pending_clarification = {
        "action": "coding_fix",
        "choices": ["data/scripts/a.py", "data/scripts/b.py"],
    }
    intent = route("2", session)
    assert intent["action"] == "coding_fix"
    assert intent["params"]["path"] == "data/scripts/b.py"
    assert session.pending_clarification is None


def test_branch_list(session):
    intent = route("list branches", session)
    assert intent["action"] == "branch_list"


def test_clear(session):
    intent = route("clear", session)
    assert intent["action"] == "clear"


def test_weather_forecast_route(session):
    intent = route("tell me what tomorrow's weather will be", session)
    assert intent["action"] == "weather_forecast"


def test_inpaint_not_triggered_for_coding_fix(session):
    intent = route("fix the bug in jarvis/router.py", session)
    assert intent["action"] != "inpaint_image"


def test_inpaint_not_triggered_for_change_settings(session):
    intent = route("change the settings for whisper", session)
    assert intent["action"] != "inpaint_image"


def test_inpaint_not_triggered_for_remove_memory(session):
    intent = route("remove the old memory about vim", session)
    assert intent["action"] != "inpaint_image"


def test_inpaint_with_explicit_image_noun(session):
    session.note_image("/tmp/test.png")
    intent = route("change the background to a sunset sky", session)
    assert intent["action"] == "edit_image"
    assert "sunset" in intent["params"]["prompt"].lower()


def test_inpaint_with_last_image_and_region(session):
    session.note_image("/tmp/test.png")
    intent = route("remove the person in the top-left region", session)
    assert intent["action"] == "inpaint_image"


def test_inpaint_explicit_keyword(session):
    session.note_image("/tmp/test.png")
    intent = route("inpaint: add fluffy clouds", session)
    assert intent["action"] == "inpaint_image"
    assert "cloud" in intent["params"]["prompt"].lower()


def test_meta_self_question_routes_to_chat(session):
    msg = "how hard would it be for you to fix or upgrade yourself"
    intent = route(msg, session)
    assert intent["action"] == "chat"
    assert intent["action"] != "inpaint_image"


def test_meta_self_question_blocked_by_finalize(session, monkeypatch):
    """Even if LLM returns inpaint, finalize guard forces chat."""
    monkeypatch.setattr(
        "jarvis.llm.route_with_tools",
        lambda *a, **k: {"action": "inpaint_image", "params": {"prompt": "upgrade"}},
    )
    intent = route("how hard would it be for you to fix or upgrade yourself", session)
    assert intent["action"] == "chat"

    session.note_image("/tmp/test.png")
    intent = route("how hard would it be for you to fix or upgrade yourself", session)
    assert intent["action"] == "chat"


def test_generate_image_not_inpaint(session):
    intent = route("generate an image of a mountain lake", session)
    assert intent["action"] == "generate_image"


def test_create_image_not_misrouted(session):
    for msg in (
        "create an image of a sunset",
        "create a image of a cat",
        "make a picture of mountains",
        "create an ai-generated image of a robot",
    ):
        intent = route(msg, session)
        assert intent["action"] == "generate_image", msg


def test_development_roadmap_not_coding_agent(session):
    msg = (
        "I want to build a local AI fly-tying assistant using scraped fly patterns, videos, "
        "and forum posts. Create a complete step-by-step development roadmap from data collection "
        "through model deployment."
    )
    intent = route(msg, session)
    assert intent["action"] != "engineering_design"
    assert not intent["action"].startswith("engineering_")


def test_make_picture_not_edit_when_last_image(session):
    session.note_image("/tmp/test.png")
    intent = route("make a picture of a dog in space", session)
    assert intent["action"] == "generate_image"


def test_edit_image_with_last_image(session):
    session.note_image("/tmp/test.png")
    intent = route("edit the image: make the sky a dramatic sunset", session)
    assert intent["action"] == "edit_image"
    assert intent["params"]["path"] == "/tmp/test.png"
    assert "sunset" in intent["params"]["prompt"].lower()


def test_edit_image_change_background(session):
    session.note_image("/tmp/test.png")
    intent = route("change the background to a snowy winter scene", session)
    assert intent["action"] == "edit_image"
    assert "snow" in intent["params"]["prompt"].lower()


def test_inpaint_region_not_edit_image(session):
    session.note_image("/tmp/test.png")
    intent = route("remove the person in the top-left region", session)
    assert intent["action"] == "inpaint_image"


def test_inpaint_keyword_not_edit_image(session):
    session.note_image("/tmp/test.png")
    intent = route("inpaint: add fluffy clouds", session)
    assert intent["action"] == "inpaint_image"


def test_parse_weather_day():
    from datetime import date
    from jarvis.journal_weather import parse_weather_day

    ref = date(2026, 6, 10)
    assert parse_weather_day("what about tomorrow?", reference=ref) == "2026-06-11"
    assert parse_weather_day("weather today", reference=ref) == "2026-06-10"


def test_weather_forecast_handler(assistant, monkeypatch):
    from jarvis import journal_weather

    monkeypatch.setattr("jarvis.llm.route_with_tools", lambda *a, **k: None)
    fake = {
        "date": "2026-06-11",
        "location": "Charlestown, NH",
        "high": 74.0,
        "low": 52.0,
        "unit": "°F",
        "code": 2,
        "icon": "⛅",
        "condition": "Partly cloudy",
        "summary": "Partly cloudy · H 74°F / L 52°F",
        "source": "open-meteo",
    }
    def fake_weather(day=None):
        target = day or fake["date"]
        return {**fake, "date": target}

    monkeypatch.setattr(journal_weather, "weather_for_day", fake_weather)
    monkeypatch.setattr(
        journal_weather,
        "parse_weather_day",
        lambda message, reference=None: "2026-06-12",
    )
    monkeypatch.setattr(journal_weather, "weather_day_label", lambda day, reference=None: "Tomorrow")
    result = assistant.process("tell me what tomorrow's weather will be")
    assert result["ok"] is True
    assert result["action"] == "weather_forecast"
    assert "Tomorrow" in result["message"]
    assert "Partly cloudy" in result["message"]
    assert "Charlestown" in result["message"]


def test_normalize_route_intent_dict_action():
    from jarvis.router import normalize_route_intent

    out = normalize_route_intent({"action": {"name": "weather_forecast"}, "params": {}})
    assert out["action"] == "weather_forecast"


def test_movidius_routes_to_web_search(session, monkeypatch):
    monkeypatch.setattr("jarvis.llm.route_with_tools", lambda *a, **k: None)
    monkeypatch.setattr("jarvis.llm.ask", lambda *a, **k: "not json")
    msg = "would a Intel Movidius VPU work for ai"
    intent = route(msg, session)
    assert intent["action"] == "web_search"
    assert "movidius" in intent["params"]["query"].lower()


def test_how_does_jarvis_router_stays_coding_chat(session):
    intent = route("how does the router work in jarvis", session)
    assert intent["action"] == "coding_chat"


def test_is_codebase_question_general_tech():
    from jarvis.router import is_codebase_question, is_general_knowledge_question

    assert not is_codebase_question("how does Intel Movidius VPU work for ai")
    assert is_codebase_question("how does branch delete work in jarvis")
    assert is_general_knowledge_question("would a Intel Movidius VPU work for ai")
    assert not is_general_knowledge_question("how does branch delete work in jarvis")


FISHING_INSTRUCTION_PROMPT = """Follow these instructions exactly:
Write a 10-word sentence about fishing.
Count the words.
Reverse the sentence.
Convert the reversed sentence to uppercase.
Explain what you did in one sentence."""


def test_fishing_instruction_prompt_not_audio(session):
    intent = route(FISHING_INSTRUCTION_PROMPT, session)
    assert intent["action"] not in ("transform_genre", "generate_song", "generate_music", "voice_to_song")


def test_convert_to_jazz_still_transform_genre(session):
    intent = route("convert this track to jazz", session)
    assert intent["action"] == "transform_genre"


def test_convert_to_uppercase_not_transform_genre(session):
    from jarvis.router import _quick_route

    msg = "Convert the reversed sentence to uppercase."
    assert _quick_route(msg, None, session) is None or _quick_route(msg, None, session).get("action") != "transform_genre"
