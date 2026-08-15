"""Multi-step reasoning with planning, self-check, confidence, and traces."""

from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Any

log = logging.getLogger("jarvis.intelligence.reasoning")


def _split_steps(goal: str) -> list[str]:
    text = (goal or "").strip()
    if not text:
        return []
    # Prefer numbered lists
    numbered = re.findall(r"(?:^|\n)\s*\d+[.)]\s*(.+)", text)
    if len(numbered) >= 2:
        return [s.strip() for s in numbered if s.strip()][:8]
    # Sentence / semicolon split for planning
    parts = re.split(r"[;\n]+|(?<=[.!?])\s+(?=[A-Z])", text)
    parts = [p.strip(" -•\t") for p in parts if len(p.strip()) > 8]
    if len(parts) >= 2:
        return parts[:6]
    return [
        f"Clarify goal: {text[:160]}",
        "Gather relevant memory and documents",
        "Form a draft plan",
        "Self-check for gaps and risks",
        "Produce final answer with confidence",
    ]


def _heuristic_confidence(goal: str, steps: list[str], checks: list[dict[str, Any]]) -> float:
    score = 0.55
    if len(steps) >= 3:
        score += 0.1
    if any(c.get("ok") for c in checks):
        score += 0.15
    if re.search(r"\b(maybe|unsure|guess|unknown)\b", goal, re.I):
        score -= 0.2
    if re.search(r"\b(must|exactly|verify|prove)\b", goal, re.I):
        score -= 0.05  # stricter goals → slightly lower until verified
    failed = sum(1 for c in checks if c.get("ok") is False)
    score -= 0.12 * failed
    return max(0.05, min(0.98, score))


def _self_check(goal: str, plan: list[str], evidence: list[str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "name": "non_empty_plan",
            "ok": len(plan) >= 2,
            "detail": f"{len(plan)} steps",
        }
    )
    checks.append(
        {
            "name": "goal_covered",
            "ok": any(len(s) > 10 for s in plan),
            "detail": "plan has substantive steps",
        }
    )
    vague = sum(1 for s in plan if re.search(r"\b(somehow|etc|stuff|things)\b", s, re.I))
    checks.append(
        {
            "name": "specificity",
            "ok": vague == 0,
            "detail": f"vague_steps={vague}",
        }
    )
    checks.append(
        {
            "name": "evidence_present",
            "ok": bool(evidence),
            "detail": f"evidence_items={len(evidence)}",
        }
    )
    # Uncertainty detection
    uncertain = bool(re.search(r"\b(not sure|uncertain|might|possibly)\b", goal, re.I))
    checks.append(
        {
            "name": "uncertainty_flagged",
            "ok": True,
            "detail": "uncertain_goal" if uncertain else "confident_goal",
            "uncertain": uncertain,
        }
    )
    return checks


def reason(
    goal: str,
    *,
    assistant: Any | None = None,
    use_rag: bool = True,
    alternatives: int = 2,
) -> dict[str, Any]:
    """Run a multi-pass reasoning pipeline with a machine-readable trace."""
    started = time.time()
    trace_id = uuid.uuid4().hex[:12]
    goal = (goal or "").strip()
    if not goal:
        return {"ok": False, "error": "empty_goal", "trace_id": trace_id}

    evidence: list[str] = []
    citations: list[dict[str, Any]] = []
    if use_rag:
        try:
            from jarvis.intelligence.hybrid_rag import format_cited_context, hybrid_search

            rag = hybrid_search(goal, limit=4)
            citations = rag.get("citations") or []
            ctx = format_cited_context(rag)
            if ctx:
                evidence.append(ctx)
        except Exception as exc:
            log.warning("reasoning rag failed: %s", exc)
            evidence.append(f"(rag unavailable: {exc})")

    # Memory recall (best-effort)
    if assistant is not None:
        try:
            from jarvis.handlers.registry import call_action, has_action

            if has_action("memory_search"):
                mem = call_action(assistant, "memory_search", {"query": goal}, goal)
                msg = str(mem.get("message") or "")[:1200]
                if msg:
                    evidence.append(f"Memory:\n{msg}")
        except Exception as exc:
            log.debug("memory recall skipped: %s", exc)

    plan = _split_steps(goal)
    checks = _self_check(goal, plan, evidence)
    confidence = _heuristic_confidence(goal, plan, checks)

    alt_plans: list[list[str]] = []
    if alternatives > 0:
        alt_plans.append(
            [
                "Research-first approach",
                "Collect sources and citations",
                "Synthesize answer",
                "Verify claims against evidence",
            ]
        )
        if alternatives > 1:
            alt_plans.append(
                [
                    "Action-first approach",
                    "Propose concrete next actions",
                    "Execute safest step",
                    "Reflect and revise",
                ]
            )

    # Optional LLM pass for revision when available
    revision = None
    try:
        from jarvis import llm

        if llm.chat_available() if hasattr(llm, "chat_available") else False:
            pass
        # Keep offline-safe: only use generate if clearly available
        prompt = (
            "Revise this plan into 4 concise steps. Return steps only.\n"
            f"Goal: {goal}\nPlan: {plan}"
        )
        if hasattr(llm, "generate"):
            # Do not call network in default unit tests — gated by env
            import os

            if os.getenv("JARVIS_REASONING_LLM", "").strip() in ("1", "true", "yes"):
                revision = str(llm.generate(prompt) or "")[:2000]
    except Exception as exc:
        log.debug("llm revision skipped: %s", exc)

    if revision:
        revised = _split_steps(revision) or plan
        plan = revised
        checks = _self_check(goal, plan, evidence)
        confidence = _heuristic_confidence(goal, plan, checks)

    needs_revision = confidence < 0.45 or any(
        c.get("name") == "evidence_present" and not c.get("ok") for c in checks
    )
    if needs_revision and not evidence:
        plan = [
            "Identify missing information",
            "Search documents and memory",
            "Ask clarifying question if still blocked",
            "Answer with explicit uncertainty",
        ]
        checks = _self_check(goal, plan, evidence)
        confidence = _heuristic_confidence(goal, plan, checks)

    elapsed_ms = int((time.time() - started) * 1000)
    summary_lines = [f"{i}. {s}" for i, s in enumerate(plan, start=1)]
    return {
        "ok": True,
        "trace_id": trace_id,
        "goal": goal,
        "plan": plan,
        "alternative_plans": alt_plans[:alternatives],
        "checks": checks,
        "confidence": round(confidence, 3),
        "uncertain": any(c.get("uncertain") for c in checks),
        "citations": citations,
        "evidence_count": len(evidence),
        "elapsed_ms": elapsed_ms,
        "summary": "## Reasoning plan\n\n" + "\n".join(summary_lines),
        "trace": {
            "phases": ["retrieve", "plan", "self_check", "revise", "score"],
            "evidence_preview": [e[:240] for e in evidence[:3]],
        },
    }
