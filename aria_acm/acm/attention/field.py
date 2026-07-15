"""Attention field — gates encoding strength (M0-minimal)."""

from __future__ import annotations

import re

from acm.types import AttentionClass

_PIN = re.compile(r"\b(remember|don'?t forget|pin this)\b", re.I)
_PREFERENCE = re.compile(r"\b(prefer|favorite|favourite)\b", re.I)
_CORRECT = re.compile(r"\b(actually|instead|correct|update|change)\b", re.I)
_STAKES = re.compile(r"\b(health|safety|password|secret|emergency|vet)\b", re.I)


def classify_attention(text: str, *, has_open_goal: bool = False) -> AttentionClass:
    if _PIN.search(text or ""):
        return AttentionClass.USER_PIN
    if _CORRECT.search(text or ""):
        return AttentionClass.PREDICTION_ERROR
    if _STAKES.search(text or ""):
        return AttentionClass.STAKES
    if has_open_goal and len((text or "").split()) >= 4:
        return AttentionClass.GOAL
    if _PREFERENCE.search(text or ""):
        return AttentionClass.NOVELTY
    return AttentionClass.DEFAULT


def encode_weight(attention: AttentionClass) -> float:
    return {
        AttentionClass.USER_PIN: 1.0,
        AttentionClass.PREDICTION_ERROR: 0.95,
        AttentionClass.STAKES: 0.9,
        AttentionClass.GOAL: 0.8,
        AttentionClass.NOVELTY: 0.75,
        AttentionClass.FREQUENCY: 0.7,
        AttentionClass.SENSORY: 0.7,
        AttentionClass.DEFAULT: 0.35,
    }[attention]
