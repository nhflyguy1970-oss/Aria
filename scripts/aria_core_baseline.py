#!/usr/bin/env python3
"""Capture Aria Core measurable baselines (Phase 1).

Writes JSONL under {AI_ROOT}/Data/automation/aria_core_baselines.jsonl
(or JARVIS data automation fallback). Never changes product behavior.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ai_root() -> Path:
    return Path(os.getenv("AI_ROOT") or "/media/jeff/AI")


def _out_path() -> Path:
    root = _ai_root() / "Data" / "automation"
    root.mkdir(parents=True, exist_ok=True)
    return root / "aria_core_baselines.jsonl"


def _http_ms(url: str, timeout: float = 5.0) -> tuple[float, str]:
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            resp.read(512)
        return round((time.perf_counter() - t0) * 1000, 2), "ok"
    except Exception as exc:
        return round((time.perf_counter() - t0) * 1000, 2), f"err:{type(exc).__name__}"


def _bench(fn, *, iterations: int = 5) -> dict:
    samples: list[float] = []
    err = None
    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            fn()
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            break
        samples.append((time.perf_counter() - t0) * 1000)
    if not samples:
        return {"ok": False, "error": err or "no samples"}
    samples.sort()
    return {
        "ok": True,
        "p50_ms": round(samples[len(samples) // 2], 2),
        "min_ms": round(samples[0], 2),
        "max_ms": round(samples[-1], 2),
        "n": len(samples),
        "error": err,
    }


def main() -> int:
    # Ensure repo root is importable when run as a script.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    rows: list[dict] = [{"event": "baseline_capture", "ts": ts, "phase": "1"}]

    for name, url in (
        ("mc_health_ms", "http://127.0.0.1:8780/api/health"),
        ("mc_overview_ms", "http://127.0.0.1:8780/api/mission-control"),
        ("aria_live_ms", "http://127.0.0.1:8765/api/live"),
    ):
        ms, status = _http_ms(url)
        rows.append({"metric": name, "ms": ms, "status": status, "ts": ts})

    # In-process microbenchmarks (work even when servers are down)
    try:
        from jarvis.learning_governor import clear_audit, commit, propose

        clear_audit()

        def _noop_write():
            return {"ok": True}

        rows.append(
            {
                "metric": "learning_governor_passthrough_ms",
                "ts": ts,
                **_bench(
                    lambda: commit(propose(kind="baseline", payload={}), _noop_write),
                    iterations=20,
                ),
            }
        )
    except Exception as exc:
        rows.append(
            {"metric": "learning_governor_passthrough_ms", "ok": False, "error": str(exc), "ts": ts}
        )

    try:
        import tempfile
        from pathlib import Path as P

        import jarvis.nlu.learning as learning_mod
        from jarvis.nlu.learning import record_correction

        # Use temp corrections file for baseline write timing
        fd, tmp = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        prev = learning_mod._CORRECTIONS
        learning_mod._CORRECTIONS = P(tmp)
        try:
            rows.append(
                {
                    "metric": "learning_write_ms",
                    "ts": ts,
                    **_bench(
                        lambda: record_correction(
                            prompt="baseline probe",
                            original_intent="a",
                            corrected_intent="b",
                        ),
                        iterations=10,
                    ),
                }
            )
        finally:
            learning_mod._CORRECTIONS = prev
            P(tmp).unlink(missing_ok=True)
    except Exception as exc:
        rows.append({"metric": "learning_write_ms", "ok": False, "error": str(exc), "ts": ts})

    try:
        from aiplatform.mission_control.production_smoke import smoke_summary

        last = smoke_summary().get("last_smoke") or {}
        rows.append(
            {
                "metric": "last_smoke",
                "duration_seconds": last.get("duration_seconds"),
                "result": last.get("result"),
                "ts": ts,
            }
        )
    except Exception as exc:
        rows.append({"metric": "last_smoke", "error": str(exc), "ts": ts})

    try:
        from aiplatform.workstation.acceptance import last_acceptance

        acc = last_acceptance() or {}
        scores = acc.get("score") or {}
        rows.append(
            {
                "metric": "last_acceptance",
                "overall": scores.get("overall"),
                "production_readiness": scores.get("production_readiness"),
                "ts": ts,
            }
        )
    except Exception as exc:
        rows.append({"metric": "last_acceptance", "error": str(exc), "ts": ts})

    out = _out_path()
    with out.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"wrote": str(out), "rows": len(rows), "sample": rows[:5]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
