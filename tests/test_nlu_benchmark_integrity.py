"""The NLU benchmark must measure classification, not prompt echoing.

The audit proved the reported 17% was an instrumentation defect: the benchmark
system prompt was a bare literal example — {"intent":"runtime",...} — with no
task statement and no intent vocabulary. Models echoed it or invented labels, so
every candidate scored 0.0 or exactly 1/6 = 16.7%, the accuracy gate could never
be met, and placement was pinned to the structural fallback forever.
"""

from __future__ import annotations

from collections import Counter

import pytest

from jarvis.nlu.benchmark import (
    _BENCHMARK_PROMPTS,
    _bench_model_device,
    _classifier_system_prompt,
    _score_json,
)
from jarvis.nlu.semantic import _VALID_INTENTS

# --- the prompt must actually describe the task ---------------------------


def test_benchmark_prompt_states_the_task() -> None:
    p = _classifier_system_prompt().lower()
    assert "intent classifier" in p, "benchmark prompt must state the task"
    assert "json" in p


def test_benchmark_prompt_lists_the_intent_vocabulary() -> None:
    """Models cannot hit ARIA's labels unless the labels are given."""
    p = _classifier_system_prompt().lower()
    for intent in {e for _, e in _BENCHMARK_PROMPTS}:
        assert intent in p, f"benchmark prompt never mentions intent '{intent}'"


def test_benchmark_prompt_specifies_schema_and_confidence() -> None:
    p = _classifier_system_prompt()
    for key in ("intent", "action", "subject", "confidence"):
        assert f'"{key}"' in p, f"schema key {key} missing from benchmark prompt"
    assert "0.0-1.0" in p or "0.0" in p, "confidence range must be specified"


def test_benchmark_prompt_is_the_production_prompt() -> None:
    """Benchmarking a different prompt measures nothing about production."""
    from jarvis.nlu.semantic import _system_prompt

    assert _classifier_system_prompt() == _system_prompt()


def test_benchmark_prompt_is_not_a_bare_example() -> None:
    """Regression: the old prompt was one literal answer, which models copied."""
    p = _classifier_system_prompt()
    assert not p.strip().startswith("Reply JSON only: {")


def test_expected_intents_are_all_valid() -> None:
    for _, expected in _BENCHMARK_PROMPTS:
        assert expected in _VALID_INTENTS or expected == "reference", expected


# --- a constant answer must not pass the gate -----------------------------


def test_constant_answer_cannot_meet_the_accuracy_gate() -> None:
    """A model replying the same intent every time must score below the gate.

    Under the old prompt an always-"runtime" reply scored 1/6 = 16.7%, which is
    exactly what the broken benchmark reported as its best result.
    """
    counts = Counter(expected for _, expected in _BENCHMARK_PROMPTS)
    total = len(_BENCHMARK_PROMPTS)
    best_constant = max(counts.values()) / total
    assert best_constant < 0.5, (
        f"a constant answer scores {best_constant:.0%} — the 0.5 gate would admit it"
    )


def test_always_runtime_scores_exactly_the_old_reported_number() -> None:
    """Pins the audit's arithmetic proof that 16.7% == 'always answered runtime'."""
    counts = Counter(expected for _, expected in _BENCHMARK_PROMPTS)
    assert counts["runtime"] / len(_BENCHMARK_PROMPTS) == pytest.approx(0.1667, abs=0.001)


def test_benchmark_prompts_cover_several_intents() -> None:
    """A single-intent suite could be passed by a constant answer."""
    distinct = {expected for _, expected in _BENCHMARK_PROMPTS}
    assert len(distinct) >= 4, distinct


# --- scoring measures the intended vocabulary -----------------------------


def test_scoring_accepts_the_expected_label() -> None:
    ok, intent = _score_json('{"intent":"memory","action":"search","confidence":0.8}')
    assert ok is True
    assert intent == "memory"


def test_scoring_rejects_an_invented_label() -> None:
    """Live probes returned 'definition'/'informational' — not ARIA's vocabulary."""
    ok, intent = _score_json('{"intent":"informational","action":"x","confidence":0.8}')
    assert ok is True
    assert intent not in _VALID_INTENTS


def test_scoring_reports_missing_json() -> None:
    ok, intent = _score_json("I think this is a runtime question.")
    assert ok is False
    assert intent is None


def test_bench_uses_the_shared_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    """_bench_model_device must send the vocabulary-bearing prompt."""
    seen: dict[str, str] = {}

    def fake_ask_with_system(model, system, prompt, **kw):
        seen["system"] = system
        return '{"intent":"chat","action":"reply","subject":"","confidence":0.9}'

    monkeypatch.setattr("jarvis.llm.ask_with_system", fake_ask_with_system)
    monkeypatch.setattr(
        "jarvis.nlu.placement.ollama_options_for_device", lambda d: {}, raising=False
    )
    row = _bench_model_device("fake-model", "cpu")

    assert "intent classifier" in seen["system"].lower()
    assert "web_search" in seen["system"]
    # Constant "chat" answers score below the gate.
    assert row["intent_accuracy"] < 0.5


def test_bench_reports_accuracy_for_a_perfect_classifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model that answers correctly must measure ~1.0, proving the metric works."""
    answers = {prompt: expected for prompt, expected in _BENCHMARK_PROMPTS}

    def perfect(model, system, prompt, **kw):
        return f'{{"intent":"{answers[prompt]}","action":"x","subject":"y","confidence":0.9}}'

    monkeypatch.setattr("jarvis.llm.ask_with_system", perfect)
    monkeypatch.setattr(
        "jarvis.nlu.placement.ollama_options_for_device", lambda d: {}, raising=False
    )
    row = _bench_model_device("perfect-model", "cpu")

    assert row["intent_accuracy"] == pytest.approx(1.0)
    assert row["json_correct_rate"] == pytest.approx(1.0)
