#!/usr/bin/env python3
"""Run ARIA's router over the labelled corpus and score it.

Scores: correct action, correct arguments, false-positive side-effecting
actions (an action that changes something, chosen where it was not wanted),
clarification behaviour, latency, and model calls/tokens (from the inference
gateway's receipts). Uses whatever router code is importable, so the same
script measures the baseline and the improved router.

    JARVIS_DATA_DIR=<scratch> python scripts/routing_benchmark.py --out results.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))

logging.disable(logging.WARNING)

NON_EFFECT = {"chat", "greeting", "capabilities", "clarify", "nlu_clarify", "reflex_reply", "session_interrupt"}


def is_clarification(intent: dict) -> bool:
    return bool(intent.get("needs_clarification")) or intent.get("action") in ("clarify", "nlu_clarify")


def side_effecting(action: str) -> bool:
    from jarvis.handlers.registry import get_spec

    if action in NON_EFFECT:
        return False
    spec = get_spec(action)
    return not (spec and spec.info)


def args_ok(intent: dict, expected: dict | None) -> bool | None:
    if not expected:
        return None
    params = intent.get("params") or {}
    blob = json.dumps(params, default=str).lower()
    return all(str(v).lower() in blob for v in expected.values())


def note_turn(session, intent: dict) -> None:
    """What the assistant records after handling a turn, for follow-ups."""
    from jarvis.handlers.registry import get_spec

    action = intent.get("action") or "chat"
    spec = get_spec(action)
    if spec and spec.module:
        session.note_module(spec.module)
    if action in ("generate_image", "edit_image", "inpaint_image", "upscale_image"):
        session.note_image("/tmp/aria-bench/last.png")


def run(out: Path, corpus_name: str = "routing_corpus") -> dict:
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.inference import boundary
    from jarvis.router import route
    from jarvis.session import SessionContext

    import importlib

    corpus = importlib.import_module(corpus_name)

    ensure_handlers_loaded()
    rows = []
    for cid, category, text, acceptable, expected_args in corpus.CASES:
        session = SessionContext()
        turns = list(text) if isinstance(text, tuple) else [text]
        for earlier in turns[:-1]:
            note_turn(session, route(earlier, session))
        before = len(boundary.recent_receipts(50))
        t0 = time.perf_counter()
        error = ""
        try:
            intent = route(turns[-1], session)
        except Exception as exc:  # noqa: BLE001
            intent = {"action": "error"}
            error = f"{type(exc).__name__}: {exc}"
        ms = (time.perf_counter() - t0) * 1000
        receipts = boundary.recent_receipts(50)[before:] if before < 50 else []
        tokens = sum(
            (a.get("prompt_tokens") or 0) + (a.get("completion_tokens") or 0)
            for r in receipts for a in r.get("attempts") or []
        )
        action = str(intent.get("action") or "")
        clar = is_clarification(intent)
        correct = action in acceptable or ("clarify" in acceptable and clar)
        fp = (not correct) and side_effecting(action)
        rows.append({
            "id": cid, "category": category, "text": turns[-1], "expected": sorted(acceptable),
            "action": action, "clarification": clar, "correct": correct,
            "args_ok": args_ok(intent, expected_args), "false_positive_effect": fp,
            "stage": intent.get("router_stage") or intent.get("route_reason") or intent.get("thinking") or "",
            "ms": round(ms, 1), "model_calls": len(receipts), "tokens": tokens, "error": error,
            "params": intent.get("params") or {},
        })

    def pct(xs):
        return round(100 * sum(xs) / len(xs), 1) if xs else None

    summary = {
        "cases": len(rows),
        "correct": sum(r["correct"] for r in rows),
        "accuracy_pct": pct([r["correct"] for r in rows]),
        "args_checked": sum(r["args_ok"] is not None for r in rows),
        "args_correct": sum(bool(r["args_ok"]) for r in rows if r["args_ok"] is not None),
        "false_positive_effects": sum(r["false_positive_effect"] for r in rows),
        "clarifications": sum(r["clarification"] for r in rows),
        "by_category": {},
        "p50_ms": sorted(r["ms"] for r in rows)[len(rows) // 2],
        "max_ms": max(r["ms"] for r in rows),
        "model_calls": sum(r["model_calls"] for r in rows),
        "tokens": sum(r["tokens"] for r in rows),
        "errors": sum(bool(r["error"]) for r in rows),
    }
    for cat in sorted({r["category"] for r in rows}):
        sub = [r for r in rows if r["category"] == cat]
        summary["by_category"][cat] = f"{sum(r['correct'] for r in sub)}/{len(sub)}"
    result = {"summary": summary, "rows": rows}
    out.write_text(json.dumps(result, indent=1, default=str))
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--corpus", default="routing_corpus", help="routing_corpus or routing_corpus_heldout")
    args = ap.parse_args()
    res = run(Path(args.out), args.corpus)
    print(json.dumps(res["summary"], indent=1))
