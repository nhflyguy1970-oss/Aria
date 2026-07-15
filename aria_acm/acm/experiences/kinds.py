"""Dual identity for Experiences — external source vs internal cognitive kind."""

from __future__ import annotations

import re
from enum import StrEnum


class ExternalKind(StrEnum):
    TEXT = "text"
    CONVERSATION = "conversation"
    VOICE = "voice"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    CODE = "code"
    TERMINAL = "terminal"
    PDF = "pdf"
    DOCUMENT = "document"
    SENSOR = "sensor"
    GPS = "gps"
    FILESYSTEM = "filesystem"
    OTHER = "other"


class CognitiveKind(StrEnum):
    OBSERVATION = "observation"
    CONVERSATION = "conversation"
    DISCOVERY = "discovery"
    FAILURE = "failure"
    SUCCESS = "success"
    DECISION = "decision"
    CORRECTION = "correction"
    LEARNING = "learning"
    GOAL_PROGRESS = "goal_progress"
    GOAL_COMPLETION = "goal_completion"
    UNEXPECTED = "unexpected"
    RELATIONSHIP = "relationship"
    CONFLICT = "conflict"
    QUESTION = "question"
    INSIGHT = "insight"
    IDENTITY_CHANGE = "identity_change"
    PREFERENCE = "preference"
    REFLECTION = "reflection"


_CORRECTION = re.compile(r"\b(actually|instead|correct(?:ion)?|update|change that)\b", re.I)
_FAILURE = re.compile(r"\b(failed|failure|error|broke|bug|mistak(?:e|en))\b", re.I)
_SUCCESS = re.compile(r"\b(succeed(?:ed)?|success|fixed|resolved|completed)\b", re.I)
_DECISION = re.compile(r"\b(decid(?:e|ed)|chose|choice|will\s+go\s+with)\b", re.I)
_QUESTION = re.compile(r"\?$|^\s*(what|why|how|when|where|who)\b", re.I)
_INSIGHT = re.compile(r"\b(realized|insight|aha|epiphany|learned that)\b", re.I)
_DISCOVERY = re.compile(r"\b(discover(?:ed|y)|found\s+that|noticed)\b", re.I)
_LEARNING = re.compile(r"\b(learn(?:ed|ing)|practice|studied)\b", re.I)
_CONFLICT = re.compile(r"\b(conflict|disagree|contradict)\b", re.I)
_RELATION = re.compile(r"\b(friend|partner|colleague|relationship|met)\b", re.I)
_UNEXPECTED = re.compile(r"\b(unexpected|surpris(?:e|ing)|didn'?t\s+expect)\b", re.I)
_GOAL_PROG = re.compile(r"\b(progress|working\s+on|almost\s+done)\b", re.I)


def classify_cognitive_kind(
    text: str,
    *,
    encode_kind: str = "experience",
    revises_id: str | None = None,
    reflects_on_id: str | None = None,
    goal_completed: bool = False,
) -> CognitiveKind:
    if reflects_on_id:
        return CognitiveKind.REFLECTION
    if revises_id or _CORRECTION.search(text or ""):
        return CognitiveKind.CORRECTION
    if goal_completed:
        return CognitiveKind.GOAL_COMPLETION
    if encode_kind == "identity":
        return CognitiveKind.IDENTITY_CHANGE
    if encode_kind == "preference":
        return CognitiveKind.PREFERENCE
    if _QUESTION.search(text or ""):
        return CognitiveKind.QUESTION
    if _INSIGHT.search(text or ""):
        return CognitiveKind.INSIGHT
    if _DISCOVERY.search(text or ""):
        return CognitiveKind.DISCOVERY
    if _FAILURE.search(text or ""):
        return CognitiveKind.FAILURE
    if _SUCCESS.search(text or ""):
        return CognitiveKind.SUCCESS
    if _DECISION.search(text or ""):
        return CognitiveKind.DECISION
    if _LEARNING.search(text or ""):
        return CognitiveKind.LEARNING
    if _CONFLICT.search(text or ""):
        return CognitiveKind.CONFLICT
    if _RELATION.search(text or ""):
        return CognitiveKind.RELATIONSHIP
    if _UNEXPECTED.search(text or ""):
        return CognitiveKind.UNEXPECTED
    if _GOAL_PROG.search(text or ""):
        return CognitiveKind.GOAL_PROGRESS
    if encode_kind == "conversation":
        return CognitiveKind.CONVERSATION
    return CognitiveKind.OBSERVATION


def normalize_external_kind(kind: str | ExternalKind | None) -> ExternalKind:
    if kind is None:
        return ExternalKind.TEXT
    if isinstance(kind, ExternalKind):
        return kind
    key = str(kind).strip().lower()
    for candidate in ExternalKind:
        if candidate.value == key:
            return candidate
    return ExternalKind.OTHER
