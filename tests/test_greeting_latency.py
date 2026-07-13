"""Regression: trivial greetings must stay on the instant path."""

from __future__ import annotations

import time

import pytest

from jarvis.request_timing import time_greeting_route
from jarvis.router import is_trivial_social_prompt, route
from jarvis.session import SessionContext

GREETINGS = (
    "Hello Aria",
    "Hello",
    "Hi",
    "Good morning",
    "How are you?",
    "Hey Jarvis",
    "What's up",
)


@pytest.mark.parametrize("message", GREETINGS)
def test_trivial_social_detected(message: str):
    assert is_trivial_social_prompt(message)


@pytest.mark.parametrize("message", GREETINGS)
def test_greetings_route_to_greeting_without_nlu(message: str, monkeypatch):
    calls = {"nlu": 0}

    def _boom(*_a, **_k):
        calls["nlu"] += 1
        raise AssertionError("NLU must not run for trivial greetings")

    monkeypatch.setattr("jarvis.nlu.pipeline.route_via_nlu", _boom)
    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)

    intent = route(message, SessionContext())
    assert intent["action"] == "greeting"
    assert calls["nlu"] == 0
    assert intent.get("router_stage") == "pre_nlu_reflex"


@pytest.mark.parametrize("message", GREETINGS)
def test_greeting_route_under_100ms(message: str, monkeypatch):
    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)

    def _fail(*_a, **_k):
        raise AssertionError("NLU invoked")

    monkeypatch.setattr("jarvis.nlu.pipeline.route_via_nlu", _fail)
    t0 = time.perf_counter()
    intent = route(message, SessionContext())
    ms = (time.perf_counter() - t0) * 1000
    assert intent["action"] == "greeting"
    assert ms < 100, f"{message!r} took {ms:.1f}ms"


def test_hello_aria_timing_table_skips_heavy_subsystems(monkeypatch):
    monkeypatch.setattr("jarvis.nlu.pipeline.nlu_enabled", lambda: True)
    monkeypatch.setattr(
        "jarvis.nlu.pipeline.route_via_nlu",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("nlu")),
    )
    report = time_greeting_route("Hello Aria")
    assert report["intent"]["action"] == "greeting"
    assert report["total_ms"] < 100
    assert report["invoked"]["classifier_nlu"] is False
    assert report["invoked"]["memory_lookup"] is False
    assert report["invoked"]["knowledge_lookup"] is False
    assert report["invoked"]["learning_manager"] is False
    assert report["invoked"]["model_request"] is False
    assert not report["over_budget"]


def test_good_morning_briefing_still_available():
    intent = route("good morning briefing", SessionContext())
    assert intent["action"] == "morning_briefing"


def test_greeting_handler_does_not_force_briefing_for_bare_good_morning(monkeypatch):
    from jarvis.handlers.meta import greeting

    class _A:
        pass

    out = greeting(_A(), {}, "Good morning")
    assert out.get("ok") is True
    assert "briefing" not in (out.get("type") or "")


def test_embed_available_is_cached(monkeypatch):
    import jarvis.llm as llm

    calls = {"n": 0}

    def _embed(_text):
        calls["n"] += 1
        return [0.1, 0.2]

    monkeypatch.setattr(llm, "embed_text", _embed)
    llm._EMBED_AVAIL_CACHE.clear()
    assert llm.embed_available() is True
    assert llm.embed_available() is True
    assert calls["n"] == 1


def test_placement_config_does_not_block_on_benchmark(monkeypatch, tmp_path):
    import jarvis.nlu.placement as placement

    monkeypatch.setattr(placement, "_PLACEMENT_FILE", tmp_path / "missing.json")
    monkeypatch.delenv("JARVIS_NLU_MODEL", raising=False)
    monkeypatch.setenv("JARVIS_NLU_SKIP_BENCHMARK", "1")
    placement._BENCHMARK_SCHEDULED = False

    def _never():
        raise AssertionError("benchmark must not run synchronously")

    monkeypatch.setattr("jarvis.nlu.benchmark.ensure_benchmark", _never)
    t0 = time.perf_counter()
    cfg = placement.placement_config()
    ms = (time.perf_counter() - t0) * 1000
    assert cfg["model"] == "structure"
    assert ms < 100
