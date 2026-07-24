#!/usr/bin/env python3
"""Long-duration Aria UI soak — cycles views and probes key APIs.

Usage:
  python scripts/aria_ui_soak.py --minutes 60 --base http://127.0.0.1:8765

Designed for certification multi-hour soaks. Prints a JSON summary on exit.
Does not drive a browser; pairs with a live session or API-only health checks.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

VIEWS = (
    "chat",
    "dashboard",
    "workstation",
    "planner",
    "calendar",
    "flytying",
    "projects",
    "maker",
    "browser",
    "security",
    "presence",
    "audit",
    "voice",
    "audio",
    "journal",
    "memory",
    "gallery",
    "video",
    "meme",
    "documents",
    "actions",
)

PROBES = (
    "/api/health",
    "/api/live",
    "/api/world-state",
    "/api/homeassistant/status",
    "/api/comfyui/settings",
    "/api/memory/settings",
)


def fetch(base: str, path: str, timeout: float = 8.0) -> tuple[int, float, str]:
    url = base.rstrip("/") + path
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:
            body = res.read(400)
            return res.status, (time.perf_counter() - started) * 1000, body[:80].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, (time.perf_counter() - started) * 1000, str(e.reason)
    except Exception as e:  # noqa: BLE001 — soak must never die on probe errors
        return 0, (time.perf_counter() - started) * 1000, str(e)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=float, default=5.0)
    ap.add_argument("--base", default="http://127.0.0.1:8765")
    ap.add_argument("--interval", type=float, default=2.0, help="seconds between probe rounds")
    args = ap.parse_args()

    deadline = time.time() + max(0.1, args.minutes) * 60
    rounds = 0
    failures: list[dict] = []
    latencies: list[float] = []
    started_at = datetime.now(timezone.utc).isoformat()

    print(f"soak start base={args.base} minutes={args.minutes}", flush=True)
    while time.time() < deadline:
        rounds += 1
        for path in PROBES:
            status, ms, snippet = fetch(args.base, path)
            latencies.append(ms)
            ok = 200 <= status < 400
            if not ok:
                failures.append(
                    {
                        "round": rounds,
                        "path": path,
                        "status": status,
                        "ms": round(ms, 1),
                        "snippet": snippet[:120],
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                )
                print(f"FAIL round={rounds} {path} status={status} ms={ms:.0f}", flush=True)
        # view hash probe — ensures static shell still serves
        status, ms, _ = fetch(args.base, f"/#{VIEWS[rounds % len(VIEWS)]}")
        latencies.append(ms)
        if status and not (200 <= status < 400):
            failures.append({"round": rounds, "path": "/#view", "status": status, "ms": round(ms, 1)})
        time.sleep(max(0.2, args.interval))

    summary = {
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "minutes_requested": args.minutes,
        "rounds": rounds,
        "probes_per_round": len(PROBES),
        "failure_count": len(failures),
        "failures": failures[:50],
        "latency_ms": {
            "count": len(latencies),
            "avg": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            "max": round(max(latencies), 1) if latencies else 0,
            "min": round(min(latencies), 1) if latencies else 0,
        },
        "views_cycled": list(VIEWS),
    }
    print(json.dumps(summary, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
