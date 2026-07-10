#!/usr/bin/env python3
"""Benchmark NLU classifier models and hardware placement."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = [
    "What GPU am I using?",
    "What is a GPU?",
    "Show Docker Compose documentation.",
    "How do I configure Docker Compose?",
    "Search my memory for vacation plans.",
]

CANDIDATES = (
    "qwen2.5:0.5b",
    "qwen2.5:1.5b",
    "qwen3:1.7b",
    "smollm:360m",
    "gemma2:2b",
)
DEVICES = ("cpu", "nvidia", "amd")


def _ollama_models() -> set[str]:
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, timeout=10)
    except Exception:
        return set()
    names: set[str] = set()
    for line in out.splitlines()[1:]:
        parts = line.split()
        if parts:
            names.add(parts[0])
    return names


def _bench_once(model: str, device: str, prompt: str) -> dict:
    from jarvis.nlu.placement import ollama_options_for_device

    sys.path.insert(0, str(ROOT))
    from jarvis import llm

    opts = ollama_options_for_device(device)
    t0 = time.perf_counter()
    try:
        raw = llm.ask_with_system(
            model,
            'Reply JSON only: {"intent":"runtime","action":"status","subject":"gpu","confidence":0.9}',
            prompt,
            options=opts,
        )
        ok = "{" in raw
    except Exception as exc:
        raw = str(exc)
        ok = False
    ms = (time.perf_counter() - t0) * 1000.0
    return {"ok": ok, "latency_ms": round(ms, 1), "raw_len": len(raw)}


def main() -> int:
    sys.path.insert(0, str(ROOT))
    available = _ollama_models()
    models = [m for m in CANDIDATES if m in available] or list(CANDIDATES[:2])
    results: list[dict] = []
    for model in models:
        for device in DEVICES:
            latencies: list[float] = []
            successes = 0
            for prompt in PROMPTS:
                row = _bench_once(model, device, prompt)
                latencies.append(row["latency_ms"])
                successes += int(row["ok"])
            if not latencies:
                continue
            avg = sum(latencies) / len(latencies)
            results.append(
                {
                    "model": model,
                    "device": device,
                    "avg_latency_ms": round(avg, 1),
                    "success_rate": round(100.0 * successes / len(PROMPTS), 1),
                }
            )
    results.sort(key=lambda r: (r["avg_latency_ms"], -r["success_rate"]))
    winner = results[0] if results else {"model": "qwen2.5:1.5b", "device": "cpu"}
    placement = {
        "model": winner["model"],
        "device": winner["device"],
        "source": "benchmark",
        "benchmark_at": time.time(),
        "results": results,
    }
    from jarvis.config import DATA_DIR
    from jarvis.nlu.placement import save_placement

    save_placement(placement)
    report_path = ROOT / "docs" / "NLU_CLASSIFIER_BENCHMARK.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# NLU Classifier Benchmark",
        "",
        f"**Selected model:** `{winner['model']}`",
        f"**Selected device:** `{winner['device']}`",
        "",
        "Selection criteria: lowest average latency with successful JSON classification.",
        "",
        "| Model | Device | Avg latency (ms) | Success % |",
        "|-------|--------|------------------|-----------|",
    ]
    for row in results:
        lines.append(
            f"| {row['model']} | {row['device']} | {row['avg_latency_ms']} | {row['success_rate']} |"
        )
    lines.extend(
        [
            "",
            "Placement saved to `jarvis/data/nlu_placement.json`.",
            "Override with `JARVIS_NLU_MODEL` and `JARVIS_NLU_DEVICE`.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(placement, indent=2))
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
