"""Semantic intent classifier — small local model, classification only."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from jarvis.nlu.placement import ollama_options_for_device, placement_config
from jarvis.nlu.types import (
    GrammarAnalysis,
    MorphologyAnalysis,
    SemanticClassification,
    SyntaxAnalysis,
)

log = logging.getLogger("jarvis.nlu")

_VALID_INTENTS = frozenset(
    {
        "runtime",
        "knowledge",
        "reference",
        "memory",
        "web_search",
        "coding",
        "chat",
        "automation",
        "vision",
        "voice",
        "planning",
        "tools",
    }
)

_JSON_RE = re.compile(r"\{[^{}]*\}", re.S)


def _system_prompt() -> str:
    return (
        "You are an intent classifier. Reply with ONLY one JSON object.\n"
        'Keys: "intent", "action", "subject", "confidence" (0.0-1.0).\n'
        "Intents:\n"
        "- runtime: LIVE workstation state only (my GPU, services running, status, health, models loaded)\n"
        "- knowledge: explain concepts, teach, compare, history, what is X (encyclopedic)\n"
        "- reference: how to configure/setup, show docs/manuals/README/project reference\n"
        "- memory: search my memory, recall, remember facts about Jeff\n"
        "- web_search: explicit search the web / look up online\n"
        "- coding: fix/implement/refactor code files\n"
        "- chat: general conversation\n"
        "Never answer the user. Never include reasoning. JSON only."
    )


def _build_user_prompt(
    message: str,
    *,
    grammar: GrammarAnalysis,
    morphology: MorphologyAnalysis,
    syntax: SyntaxAnalysis,
    context: str,
    keyword_hint: str,
) -> str:
    lines = [
        f"Prompt: {message}",
        f"Grammar: {grammar.sentence_type} mood={grammar.mood} question={grammar.question_type or '-'}",
        f"Stems: {', '.join(morphology.stems[:16]) or '-'}",
        (
            f"Syntax: subject={syntax.subject or '-'} verb={syntax.verb or '-'} "
            f"object={syntax.object or '-'}"
        ),
    ]
    if context:
        lines.append(f"Context: {context[:400]}")
    if keyword_hint:
        lines.append(f"Keyword hint (weak): {keyword_hint}")
    return "\n".join(lines)


def _parse_json(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    m = _JSON_RE.search(text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def classify_semantic(
    message: str,
    *,
    grammar: GrammarAnalysis,
    morphology: MorphologyAnalysis,
    syntax: SyntaxAnalysis,
    context: str = "",
    keyword_hint: str = "",
) -> SemanticClassification | None:
    text = (message or "").strip()
    if not text or len(text) > 600:
        return None

    cfg = placement_config()
    model = str(cfg.get("model") or "structure")
    device = str(cfg.get("device") or "cpu")
    if model == "structure":
        return None

    try:
        from jarvis.nlu.health import (
            record_classify_failure,
            record_classify_success,
            record_queue_enqueue,
        )

        record_queue_enqueue()
    except Exception:
        pass

    try:
        from jarvis import llm

        t0 = time.perf_counter()
        raw = llm.ask_with_system(
            model,
            _system_prompt(),
            _build_user_prompt(
                text,
                grammar=grammar,
                morphology=morphology,
                syntax=syntax,
                context=context,
                keyword_hint=keyword_hint,
            ),
            options=ollama_options_for_device(device),
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0
        parsed = _parse_json(raw)
        if not parsed:
            try:
                record_classify_failure("invalid_json")
            except Exception:
                pass
            return None
        intent = str(parsed.get("intent") or "chat").strip().lower()
        if intent == "documentation":
            intent = "reference"
        if intent not in _VALID_INTENTS:
            intent = "chat"
        confidence = float(parsed.get("confidence") or 0.5)
        try:
            record_classify_success(latency_ms=latency_ms, model=model, device=device)
        except Exception:
            pass
        return SemanticClassification(
            intent=intent,
            action=str(parsed.get("action") or "").strip().lower(),
            subject=str(parsed.get("subject") or syntax.object or "").strip().lower(),
            confidence=confidence,
            model=model,
            device=device,
            latency_ms=round(latency_ms, 1),
        )
    except Exception as exc:
        log.debug("semantic classifier skipped: %s", exc)
        try:
            from jarvis.nlu.health import record_classify_failure

            record_classify_failure(str(exc))
        except Exception:
            pass
        return None
