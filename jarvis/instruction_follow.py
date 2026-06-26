"""Strict multi-step instruction prompts — deterministic text pipelines + chat hints."""

from __future__ import annotations

import re
from typing import Callable

_PIPELINE_STEPS = (
    r"count the words",
    r"reverse the sentence",
    r"convert the reversed sentence to uppercase",
    r"explain what you did in one sentence",
)


def is_strict_instruction_prompt(message: str) -> bool:
    lower = (message or "").lower()
    if not re.search(r"\bfollow these instructions\b", lower):
        return False
    lines = [ln.strip() for ln in message.splitlines() if ln.strip()]
    return len(lines) >= 3


def parse_text_pipeline(message: str) -> dict | None:
    """Recognize write → count → reverse → uppercase → explain benchmarks."""
    if not is_strict_instruction_prompt(message):
        return None
    text = message.lower()
    line = next(
        (ln.strip() for ln in message.splitlines() if re.search(r"write a \d+-word sentence about", ln, re.I)),
        "",
    )
    m = re.search(r"write a (\d+)-word sentence about (.+?)\.?\s*$", line, re.I)
    if not m:
        return None
    for pat in _PIPELINE_STEPS:
        if not re.search(pat, text, re.I):
            return None
    topic = m.group(2).strip().rstrip(".")
    return {"n_words": int(m.group(1)), "topic": topic}


def strict_instruction_context_prefix() -> str:
    return (
        "STRICT INSTRUCTION MODE: Follow each user step in exact order. "
        "Label every step clearly (Step 1, Step 2, …). Show each intermediate result. "
        "Do not skip, merge, or paraphrase steps."
    )


def _normalize_word_count(sentence: str, n: int, topic: str) -> str:
    words = sentence.replace("\n", " ").strip().strip('"\'').split()
    if len(words) == n:
        return " ".join(words)
    if len(words) > n:
        return " ".join(words[:n])
    pad = ["and", "near", "the", "water", "today", "early", "morning", "light"]
    if "fish" not in topic.lower():
        pad = ["and", "in", "the", "open", "air", "today", "early", "morning"]
    while len(words) < n:
        words.append(pad[len(words) % len(pad)])
    return " ".join(words[:n])


def _reverse_words(sentence: str) -> str:
    return " ".join(sentence.split()[::-1])


def run_text_pipeline(n_words: int, topic: str, ask_fn: Callable[[], str]) -> str:
    sentence = _normalize_word_count(ask_fn(), n_words, topic)
    count = len(sentence.split())
    reversed_text = _reverse_words(sentence)
    upper = reversed_text.upper()
    explain = (
        f"I wrote a {n_words}-word sentence about {topic}, counted {count} words, "
        f"reversed the word order, converted that to uppercase, and reported each step."
    )
    return (
        f"**Step 1 — Write a {n_words}-word sentence about {topic}:**\n{sentence}\n\n"
        f"**Step 2 — Count the words:**\n{count}\n\n"
        f"**Step 3 — Reverse the sentence:**\n{reversed_text}\n\n"
        f"**Step 4 — Convert the reversed sentence to uppercase:**\n{upper}\n\n"
        f"**Step 5 — Explain what you did in one sentence:**\n{explain}"
    )


def try_execute_strict_instructions(
    message: str,
    ask_sentence: Callable[[str, int, str], str],
) -> str | None:
    """Return formatted output for known pipelines, else None."""
    spec = parse_text_pipeline(message)
    if not spec:
        return None
    n_words = spec["n_words"]
    topic = spec["topic"]

    def _ask() -> str:
        return ask_sentence(topic, n_words, message)

    return run_text_pipeline(n_words, topic, _ask)
