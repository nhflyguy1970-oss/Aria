"""Morphology — stems and normalized word forms (not routing)."""

from __future__ import annotations

import re

from jarvis.nlu.types import MorphologyAnalysis

_TOKEN = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.I)

_SUFFIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"ies$"), "y"),
    (re.compile(r"ations$"), "ate"),
    (re.compile(r"ation$"), "ate"),
    (re.compile(r"ments$"), "ment"),
    (re.compile(r"ing$"), ""),
    (re.compile(r"edly$"), "ed"),
    (re.compile(r"edly$"), ""),
    (re.compile(r"ed$"), ""),
    (re.compile(r"es$"), ""),
    (re.compile(r"s$"), ""),
)


def stem_word(word: str) -> str:
    w = (word or "").lower().strip()
    if len(w) < 4:
        return w
    for pattern, repl in _SUFFIXES:
        if pattern.search(w):
            candidate = pattern.sub(repl, w)
            if len(candidate) >= 3:
                return candidate
    return w


def analyze_morphology(text: str) -> MorphologyAnalysis:
    tokens = _TOKEN.findall(text or "")
    stems = [stem_word(t) for t in tokens]
    return MorphologyAnalysis(tokens=tokens, stems=stems)
