#!/usr/bin/env python3
"""Operator CLI: harvest legacy MemoryStore INTO Aria ACM (M2).

Never runs automatically. Legacy remains authoritative until M3.

Usage:
  python scripts/acm_harvest.py [--dry-run] [--report PATH] [--persist-path PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="M2 harvest MemoryStore → ACM (operator only)")
    parser.add_argument("--dry-run", action="store_true", help="Count/select only; no encode")
    parser.add_argument(
        "--report",
        default="",
        help="Write JSON migration report to this path",
    )
    parser.add_argument(
        "--persist-path",
        default="",
        help="ACM durable path (sets ARIA_ACM_PERSIST_PATH for this process)",
    )
    parser.add_argument(
        "--no-assent-identity",
        action="store_true",
        help="Do not assent high-impact identity proposals during harvest",
    )
    parser.add_argument(
        "--priorities",
        default="P0,P1",
        help="Comma list of priorities to harvest (default P0,P1)",
    )
    args = parser.parse_args()

    if args.persist_path:
        os.environ["ARIA_ACM_PERSIST_PATH"] = args.persist_path

    # Harvest must not enable PRIMARY
    os.environ.setdefault("ARIA_ACM_PRIMARY", "0")

    from aria_core.acm_harvest import harvest_into_acm

    prios = frozenset(p.strip() for p in args.priorities.split(",") if p.strip())
    report = harvest_into_acm(
        dry_run=bool(args.dry_run),
        assent_identity=not args.no_assent_identity,
        priorities=prios,
        report_path=args.report or None,
    )
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
