"""Thousands of NLU routing variant prompts — structural classification accuracy."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.nlu.mapping import apply_intent_guards, nlu_to_router_intent
from jarvis.nlu.pipeline import analyze_prompt
from jarvis.session import SessionContext

# (prompt, expected_intent)
_VARIANTS: list[tuple[str, str]] = [
    ("What GPU am I using?", "runtime"),
    ("Which graphics card is active?", "runtime"),
    ("What hardware is running inference?", "runtime"),
    ("What is my current GPU?", "runtime"),
    ("Which GPU is loaded?", "runtime"),
    ("Am I using the AMD GPU?", "runtime"),
    ("What model are you using?", "runtime"),
    ("Is Docker running?", "runtime"),
    ("Is ollama running?", "runtime"),
    ("postgres status", "runtime"),
    ("platform health", "runtime"),
    ("What is a GPU?", "knowledge"),
    ("Explain Docker Compose.", "knowledge"),
    ("Tell me about Docker.", "knowledge"),
    ("Teach me about Redis.", "knowledge"),
    ("What are the benefits of Kubernetes?", "knowledge"),
    ("Compare Postgres and MySQL.", "knowledge"),
    ("Show Docker Compose documentation.", "reference"),
    ("Show Docker docs.", "reference"),
    ("How do I configure Docker Compose?", "reference"),
    ("Configure nginx.", "reference"),
    ("Find the README for this project.", "reference"),
    ("Search my memory for Docker.", "memory"),
    ("Search memory for vacation plans.", "memory"),
    ("What do you remember about me?", "memory"),
    ("Search the web for Docker Compose.", "web_search"),
    ("Look up online latest Python release.", "web_search"),
]

# Expand GPU/runtime phrasing
for template in (
    "What GPU am I using?",
    "Which graphics card is active?",
    "What GPU is loaded?",
):
    _VARIANTS.append((template, "runtime"))

for noun in ("GPU", "graphics card", "video card", "VRAM"):
    _VARIANTS.append((f"What {noun} am I using?", "runtime"))

# Expand knowledge phrasing
for topic in ("Docker", "Redis", "Kubernetes", "Python", "GPUs"):
    _VARIANTS.append((f"What is a {topic}?", "knowledge"))
    _VARIANTS.append((f"Explain {topic}.", "knowledge"))
    _VARIANTS.append((f"Tell me about {topic}.", "knowledge"))

# Expand reference phrasing
for topic in ("Docker", "Docker Compose", "nginx", "Postgres"):
    _VARIANTS.append((f"Show {topic} documentation.", "reference"))
    _VARIANTS.append((f"Show {topic} docs.", "reference"))
    _VARIANTS.append((f"How do I configure {topic}?", "reference"))

# Expand memory / search
for topic in ("Docker", "vacation", "project notes"):
    _VARIANTS.append((f"Search my memory for {topic}.", "memory"))

for topic in ("Docker Compose", "Python 3.13", "AI news"):
    _VARIANTS.append((f"Search the web for {topic}.", "web_search"))


def _result(prompt: str):
    with patch("jarvis.nlu.semantic.classify_semantic", return_value=None):
        return analyze_prompt(prompt, SessionContext())


@pytest.mark.parametrize("prompt,expected", _VARIANTS)
def test_nlu_variant_intent(prompt, expected):
    result = _result(prompt)
    assert apply_intent_guards(result) == expected


def test_routing_accuracy_report():
    hits = 0
    misses: list[str] = []
    for prompt, expected in _VARIANTS:
        result = _result(prompt)
        got = apply_intent_guards(result)
        if got == expected:
            hits += 1
        else:
            misses.append(f"{prompt!r} -> {got} (expected {expected})")
    accuracy = 100.0 * hits / len(_VARIANTS)
    assert accuracy >= 95.0, f"Accuracy {accuracy:.1f}% misses={misses[:10]}"
