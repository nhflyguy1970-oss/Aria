#!/usr/bin/env python3
"""Run automatic execution-path benchmark and refresh routing policy/docs.

Examples:
  cd /path/to/jarvis && ./venv/bin/python scripts/run_execution_benchmark.py --quick
  ./venv/bin/python scripts/run_execution_benchmark.py --full
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark Aria execution routing")
    parser.add_argument("--quick", action="store_true", help="Fewer models/runs (default)")
    parser.add_argument("--full", action="store_true", help="More models and warm runs")
    parser.add_argument(
        "--workloads",
        default="lightweight,coding,reasoning,vision,voice",
        help="Comma-separated workloads",
    )
    args = parser.parse_args(argv)
    quick = not args.full
    if args.quick:
        quick = True

    from jarvis.inference.execution_benchmark import run_execution_benchmark

    workloads = [w.strip() for w in args.workloads.split(",") if w.strip()]
    print(f"Running execution benchmark quick={quick} workloads={workloads}", flush=True)
    policy = run_execution_benchmark(workloads=workloads, quick=quick)
    print(
        json.dumps(
            {
                "benchmark_date": policy.get("benchmark_date"),
                "devices": policy.get("devices_tested"),
            },
            indent=2,
        )
    )
    for wl, block in (policy.get("workloads") or {}).items():
        print(
            f"  {wl}: model={block.get('model')} hw={block.get('hardware')} "
            f"warm_ms={block.get('warm_latency_ms')} tps={block.get('tokens_per_sec')}",
            flush=True,
        )
    print(
        "Wrote execution_routing_policy.json + docs/ROUTING_MATRIX.md + "
        "docs/EXECUTION_BENCHMARK_REPORT.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
