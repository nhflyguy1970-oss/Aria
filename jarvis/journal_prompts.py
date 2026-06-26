"""Morning and evening journal prompts."""

from __future__ import annotations

from datetime import date

MORNING_PROMPTS = [
    "What would make today a good day?",
    "What is one thing you are grateful for right now?",
    "What is your top priority today?",
    "What energy do you want to bring into today?",
    "What might get in your way today — and how will you handle it?",
    "Who or what will you show up for today?",
    "What would your best self do first this morning?",
]

EVENING_PROMPTS = [
    "What went well today?",
    "What did you learn today?",
    "What would you do differently if you could replay today?",
    "What are you grateful for from today?",
    "What is still on your mind before sleep?",
    "Did you live according to your values today?",
    "What is one small win you can celebrate?",
]


def prompts_for_day(day: str | None = None) -> dict:
    d = date.fromisoformat(day) if day else date.today()
    n = d.toordinal()
    return {
        "morning_question": MORNING_PROMPTS[n % len(MORNING_PROMPTS)],
        "evening_question": EVENING_PROMPTS[n % len(EVENING_PROMPTS)],
    }
