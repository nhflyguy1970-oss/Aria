"""Aggregate latency metrics for Mission Control / Provider Health panels."""

from __future__ import annotations

from typing import Any

from jarvis.latency_observability.store import load_traces
from jarvis.latency_observability.trace import live_traces


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    idx = int(round((p / 100.0) * (len(xs) - 1)))
    idx = max(0, min(len(xs) - 1, idx))
    return round(xs[idx], 2)


def stats_payload(*, limit: int = 200) -> dict[str, Any]:
    rows = load_traces(limit=limit)
    first_tokens = [float(r["stream"]["first_token_ms"]) for r in rows if (r.get("stream") or {}).get("first_token_ms") is not None]
    elapsed = [float(r["elapsed_ms"]) for r in rows if r.get("elapsed_ms") is not None]
    cancels = sum(1 for r in rows if any("cancel" in str(e).lower() for e in (r.get("errors") or [])))
    timeouts = sum(
        1
        for r in rows
        if any("timeout" in str(e).lower() for e in (r.get("errors") or []))
        or str((r.get("stream") or {}).get("reason") or "").endswith("timeout")
    )
    cold = sum(1 for r in rows if (r.get("model") or {}).get("load") == "cold")
    warm = sum(1 for r in rows if (r.get("model") or {}).get("load") == "warm")
    ok_n = sum(1 for r in rows if r.get("ok") is True)
    fail_n = sum(1 for r in rows if r.get("ok") is False)
    return {
        "ok": True,
        "product": "Latency Observability",
        "sample_size": len(rows),
        "live_count": len(live_traces()),
        "first_token": {
            "avg_ms": round(sum(first_tokens) / len(first_tokens), 2) if first_tokens else None,
            "p50_ms": _percentile(first_tokens, 50),
            "p95_ms": _percentile(first_tokens, 95),
            "p99_ms": _percentile(first_tokens, 99),
            "count": len(first_tokens),
        },
        "completion": {
            "avg_ms": round(sum(elapsed) / len(elapsed), 2) if elapsed else None,
            "p95_ms": _percentile(elapsed, 95),
            "count": len(elapsed),
        },
        "cancellation_rate": round(cancels / len(rows), 4) if rows else 0.0,
        "timeout_rate": round(timeouts / len(rows), 4) if rows else 0.0,
        "ok_rate": round(ok_n / len(rows), 4) if rows else None,
        "fail_count": fail_n,
        "model_load": {"cold": cold, "warm": warm},
        "live": live_traces()[:12],
        "recent": rows[:12],
    }


def diagnostics() -> dict[str, Any]:
    stats = stats_payload()
    return {
        "ok": True,
        "product": "Latency Observability",
        "stats": stats,
        "budgets": {
            "routing_ms": 20,
            "context_ms": 50,
            "prompt_build_ms": 20,
            "provider_queue_ms": 250,
            "first_token_ms": 2000,
        },
        "exports": [
            "/api/latency/export?trace_id=…&format=json",
            "/api/latency/export?trace_id=…&format=csv",
            "/api/latency/export?trace_id=…&format=waterfall",
        ],
    }
