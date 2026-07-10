"""NLU structured types — execution metadata only, never chain-of-thought."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GrammarAnalysis:
    sentence_type: str = "declarative"
    question_type: str = ""
    mood: str = "neutral"


@dataclass
class MorphologyAnalysis:
    tokens: list[str] = field(default_factory=list)
    stems: list[str] = field(default_factory=list)


@dataclass
class SyntaxAnalysis:
    subject: str = ""
    verb: str = ""
    object: str = ""
    modifiers: list[str] = field(default_factory=list)


@dataclass
class SemanticClassification:
    intent: str = "chat"
    action: str = ""
    subject: str = ""
    confidence: float = 0.0
    model: str = ""
    device: str = ""
    latency_ms: float = 0.0


@dataclass
class NLUResult:
    prompt: str
    grammar: GrammarAnalysis
    morphology: MorphologyAnalysis
    syntax: SyntaxAnalysis
    semantic: SemanticClassification
    conversation_context: str = ""
    learned_match: bool = False
    keyword_hint: str = ""

    def to_debug(self) -> dict[str, Any]:
        return {
            "grammar": {
                "sentence_type": self.grammar.sentence_type,
                "question_type": self.grammar.question_type,
                "mood": self.grammar.mood,
            },
            "morphology": {"stems": self.morphology.stems[:12]},
            "syntax": {
                "subject": self.syntax.subject,
                "verb": self.syntax.verb,
                "object": self.syntax.object,
                "modifiers": self.syntax.modifiers[:8],
            },
            "semantic": {
                "intent": self.semantic.intent,
                "action": self.semantic.action,
                "subject": self.semantic.subject,
                "confidence": self.semantic.confidence,
                "model": self.semantic.model,
                "device": self.semantic.device,
                "latency_ms": self.semantic.latency_ms,
            },
            "learned_match": self.learned_match,
            "keyword_hint": self.keyword_hint,
        }
