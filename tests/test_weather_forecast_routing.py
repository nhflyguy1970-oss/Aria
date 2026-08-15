"""Weather forecast routing — must not fall through to chat/Ollama."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.parametrize(
    "message",
    [
        "What is the weather today?",
        "What's the weather today?",
        "How's the weather?",
        "Will it rain tomorrow?",
        "What's the forecast for tonight?",
    ],
)
def test_is_weather_forecast_question(message: str) -> None:
    from jarvis.nlu.mapping import is_calendar_fact_question, is_weather_forecast_question

    assert is_weather_forecast_question(message)
    assert not is_calendar_fact_question(message)


@pytest.mark.parametrize(
    "message",
    [
        "What day is today?",
        "What time is it?",
        "Hello",
        "Explain recursion.",
    ],
)
def test_non_weather_not_matched(message: str) -> None:
    from jarvis.nlu.mapping import is_weather_forecast_question

    assert not is_weather_forecast_question(message)


def test_route_via_nlu_weather_short_circuit() -> None:
    from jarvis.nlu.pipeline import route_via_nlu

    intent = route_via_nlu("What is the weather today?", SimpleNamespace())
    assert intent is not None
    assert intent["action"] == "weather_forecast"
    assert intent.get("rule_matched") == "weather_forecast"
    assert intent.get("route_reason") == "weather_forecast"


def test_router_weather_not_chat(monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis import router
    from jarvis.session import SessionContext

    # Ensure NLU path is active (default) and still lands on weather_forecast.
    session = SessionContext()
    intent = router.route("What is the weather today?", session)
    assert intent["action"] == "weather_forecast"
    assert intent.get("action") != "chat"


def test_weather_forecast_text_is_compact() -> None:
    from jarvis.journal_weather import weather_forecast_text

    text = weather_forecast_text(message="What is the weather today?")
    assert text
    assert len(text) < 400
    assert "hourly" not in text.lower()
