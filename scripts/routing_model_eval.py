#!/usr/bin/env python3
"""Measure installed local models on ARIA's shortlisted routing task.

For every case in the routing corpora, build the same candidate shortlist the
router builds and ask each model to pick (the router's own prompt). Gold:

* an acceptable action is in the shortlist → that action
* otherwise → "chat" (or "clarify" where the corpus accepts a clarification):
  with no right action on offer, picking one is a wrong action

Scored: accuracy, wrong-action rate (chose an action that is not acceptable —
the costly error), side-effecting wrong actions, p50 latency, tokens.

    JARVIS_DATA_DIR=<scratch> JARVIS_EXECUTION_MODEL=<model> \
        python scripts/routing_model_eval.py --models <model> --out eval.json

Pin the model with JARVIS_EXECUTION_MODEL: otherwise ARIA's execution policy
answers every "router" call with the configured router model, whatever was
requested. Each row records the model that actually served it.
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "fixtures"))
logging.disable(logging.WARNING)


def cases() -> list[tuple[str, str, set[str]]]:
    import routing_corpus
    import routing_corpus_heldout

    out = []
    for mod in (routing_corpus, routing_corpus_heldout):
        for cid, _cat, text, acceptable, _args in mod.CASES:
            if isinstance(text, tuple):
                continue  # follow-ups depend on session state, not on the chooser
            out.append((cid, text, set(acceptable)))
    return out


def _served_model() -> str:
    """The model that actually answered (execution policy may substitute one)."""
    from jarvis.inference import boundary

    recent = boundary.recent_receipts(1)
    attempts = (recent[-1].get("attempts") or []) if recent else []
    return str(attempts[-1].get("model") or "") if attempts else ""


def run(models: list[str], out: Path) -> dict:
    from jarvis import llm
    from jarvis.action_routing import _CHOOSER_PROMPT, _parse_choice, action_meta, clean, shortlist
    from jarvis.handlers.registry import is_info_action

    rows = []
    prepared = []
    for cid, text, acceptable in cases():
        cands = [a for a, _ in shortlist(text)]
        on_offer = acceptable & set(cands)
        gold = on_offer or ({"chat"} | ({"clarify"} & acceptable))
        options = "\n".join(f"- {a}: {action_meta(a)['description']}" for a in cands)
        prompt = _CHOOSER_PROMPT.format(options=options, message=clean(text).replace('"', "'"))
        prepared.append((cid, text, acceptable, cands, gold, prompt))

    summary = {}
    for model in models:
        # Warm the model so a cold load is not charged to the first case.
        try:
            llm.ask_with_usage(model, [{"role": "user", "content": "Reply with: ok"}], role="router",
                               options={"num_predict": 4})
        except Exception as exc:  # noqa: BLE001
            summary[model] = {"error": f"{type(exc).__name__}: {exc}"}
            continue
        correct = wrong_action = wrong_effect = 0
        lat, toks = [], []
        for cid, text, acceptable, cands, gold, prompt in prepared:
            t0 = time.perf_counter()
            try:
                raw, usage = llm.ask_with_usage(
                    model, [{"role": "user", "content": prompt}], role="router", options={"num_predict": 24}
                )
            except Exception as exc:  # noqa: BLE001
                raw, usage = f"ERROR {type(exc).__name__}", {}
            ms = (time.perf_counter() - t0) * 1000
            served = _served_model()
            answer = _parse_choice(raw, cands) or "unparsed"
            ok = answer in gold
            is_wrong_action = answer not in ("chat", "clarify", "unparsed") and answer not in acceptable
            correct += ok
            wrong_action += is_wrong_action
            wrong_effect += is_wrong_action and not is_info_action(answer)
            lat.append(ms)
            toks.append((usage or {}).get("prompt_tokens", 0) + (usage or {}).get("completion_tokens", 0))
            rows.append({"model": model, "id": cid, "text": text, "candidates": cands, "gold": sorted(gold),
                         "answer": answer, "served_by": served, "raw": (raw or "")[:60], "ok": ok, "wrong_action": is_wrong_action,
                         "ms": round(ms, 1)})
        n = len(prepared)
        served_set = sorted({r["served_by"] for r in rows if r["model"] == model})
        summary[model] = {
            "served_by": served_set,
            "cases": n,
            "accuracy_pct": round(100 * correct / n, 1),
            "wrong_action_pct": round(100 * wrong_action / n, 1),
            "wrong_side_effect": wrong_effect,
            "p50_ms": round(statistics.median(lat), 1),
            "p95_ms": round(sorted(lat)[int(0.95 * (n - 1))], 1),
            "mean_tokens": round(statistics.mean(toks), 1) if toks else 0,
        }
        print(model, json.dumps(summary[model]), flush=True)
    gold_on_offer = sum(1 for p in prepared if p[2] & set(p[3]))
    result = {"summary": summary, "shortlist_recall": f"{gold_on_offer}/{len(prepared)}", "rows": rows}
    out.write_text(json.dumps(result, indent=1))
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = run([m.strip() for m in args.models.split(",") if m.strip()], Path(args.out))
    print("shortlist recall (an acceptable action in the top-K):", res["shortlist_recall"])
