"""Strict instruction prompt handling."""

from jarvis.instruction_follow import (
    parse_text_pipeline,
    run_text_pipeline,
    try_execute_strict_instructions,
)


FISHING_PROMPT = """Follow these instructions exactly:
Write a 10-word sentence about fishing.
Count the words.
Reverse the sentence.
Convert the reversed sentence to uppercase.
Explain what you did in one sentence."""


def test_parse_text_pipeline():
    spec = parse_text_pipeline(FISHING_PROMPT)
    assert spec is not None
    assert spec["n_words"] == 10
    assert "fishing" in spec["topic"]


def test_run_text_pipeline_deterministic():
    out = run_text_pipeline(10, "fishing", lambda: "Anglers cast lines on the quiet river at dawn today")
    assert "**Step 1" in out
    assert "**Step 2" in out
    assert "**Step 5" in out
    assert "10" in out
    assert out.split("**Step 4")[1].isupper() or "DAWN" in out.upper()


def test_try_execute_with_mock():
    result = try_execute_strict_instructions(
        FISHING_PROMPT,
        lambda topic, n, _orig: " ".join(["fishing"] * n),
    )
    assert result is not None
    assert "Step 3" in result
    assert "GNihsif" not in result
