#!/usr/bin/env python3
"""Render coding-agent benchmark JSON (scripts/coding_agent_benchmark.py) as
Markdown tables, and optionally write the selection file ARIA reads.

    python scripts/render_agent_benchmark.py standard.json hard.json [--rerun rerun.json] \
        [--exclude run-id ...] [--selection data/coding_agent_benchmark.json]

``--rerun`` rows replace rows of the same (agent, kind, rep) — used when a run
was invalidated by the harness, never to drop an agent's genuine failure.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coding_agent_benchmark import qualifies

BASE_KIND = {"hard_diagnosis": "bug_diagnosis", "hard_repair": "small_repair"}


def base_kind(kind: str) -> str:
    return BASE_KIND.get(kind, kind.removeprefix("hard_"))

AGENTS = ["codex", "claude_code", "antigravity"]
LABEL = {"codex": "Codex", "claude_code": "Claude Code", "antigravity": "Antigravity"}


def load(paths: list[str], reruns: list[str], invalid: set[tuple]) -> tuple[list[dict], list[dict]]:
    rows, meta = [], []
    for p in paths:
        d = json.loads(Path(p).read_text())
        meta.append({k: d.get(k) for k in ("suite", "versions", "fixture_sha256", "repeat", "finished_at", "mode")})
        rows += [dict(r, suite=d.get("suite", "standard")) for r in d["rows"] if "kind" in r]
    replaced = []
    for p in reruns:
        d = json.loads(Path(p).read_text())
        for r in d["rows"]:
            if "kind" not in r:
                continue
            key = (r["agent"], r["kind"], r.get("rep", 0))
            for i, old in enumerate(rows):
                if (old["agent"], old["kind"], old.get("rep", 0)) == key and key in invalid:
                    replaced.append({"replaced": {k: old.get(k) for k in ("agent", "kind", "rep", "status")},
                                     "by": {k: r.get(k) for k in ("status", "check_ok")}})
                    rows[i] = dict(r, suite=d.get("suite", "standard"), rerun=True)
                    break
    return rows, meta + [{"reruns": replaced}]


def by_kind(rows: list[dict]) -> dict:
    out: dict = {}
    for r in rows:
        if r.get("status") == "skipped":
            continue
        c = out.setdefault(r["kind"], {}).setdefault(r["agent"], {"n": 0, "ok": 0, "secs": []})
        c["n"] += 1
        c["ok"] += qualifies(r)
        c["secs"].append(r["seconds"])
    for kind in out.values():
        for agent, c in kind.items():
            kind[agent] = {"n": c["n"], "verified_pct": round(100 * c["ok"] / c["n"]),
                           "p50_s": round(statistics.median(c["secs"]), 1)}
    return out


def per_agent(rows: list[dict]) -> dict:
    out = {}
    for a in AGENTS:
        rs = [r for r in rows if r["agent"] == a and r.get("status") != "skipped"]
        if not rs:
            continue
        out[a] = {
            "runs": len(rs), "passed": sum(qualifies(r) for r in rs),
            "timeouts": sum(bool(r.get("timed_out")) for r in rs),
            "violations": sum(r.get("status") == "boundary_violation" for r in rs),
            "outside_attempts": sum(bool(r.get("outside_attempts")) or not r.get("canary_intact", True) for r in rs),
            "noncompliant": sum(not r.get("instruction_compliant", True) for r in rs),
            "structured_ok": sum(bool(r.get("structured_ok")) for r in rs),
            "execution_ok": sum(r.get("status") in ("completed", "verified", "changes_unverified", "no_changes") for r in rs),
            "capacity_failures": sum(bool(r.get("quota_exhausted")) for r in rs),
            "contradicted_claims": sum(len(r.get("contradicted_claims") or []) for r in rs),
            "p50_s": round(statistics.median(r["seconds"] for r in rs), 1),
            "total_s": round(sum(r["seconds"] for r in rs), 1),
            "cpu_s_total": round(sum((r.get("resources") or {}).get("cpu_seconds") or 0 for r in rs), 1),
            "peak_rss_mb_max": max(((r.get("resources") or {}).get("peak_rss_mb") or 0) for r in rs),
            "diff_lines_total": sum(r.get("diff_lines") or 0 for r in rs),
        }
    return out


def selection(rows: list[dict], meta: list[dict], source: list[str], previous: dict | None = None) -> dict:
    """Refresh scores without silently clearing previously recorded boundaries."""
    previous = previous or {}
    summaries = per_agent(rows)
    history = list(previous.get("associated_boundary_history") or [])
    # Count distinct receipts, so refreshing the same evidence never inflates it.
    for agent in set(summaries) | set(previous.get("summary") or {}):
        summary = summaries.setdefault(agent, {"runs": 0, "passed": 0})
        scored = int(summary.get("violations") or 0)
        receipts = {r["run_id"] for r in history if r.get("agent") == agent and r.get("run_id")}
        old = ((previous.get("summary") or {}).get(agent) or {})
        summary["scored_violations"] = scored
        summary["historical_violations"] = len(receipts)
        summary["violations"] = max(scored + len(receipts), int(old.get("violations") or 0))
        summary["retained_summary_violations"] = summary["violations"] - scored - len(receipts)
        summary["outside_attempts"] = max(int(summary.get("outside_attempts") or 0),
                                          int(old.get("outside_attempts") or 0))
    return {"source": source, "meta": meta, "associated_boundary_history": history,
            "by_category": by_kind([dict(r, kind=base_kind(r["kind"])) for r in rows]),
            "by_task": by_kind(rows), "summary": summaries}


def markdown(rows: list[dict]) -> str:
    kinds = []
    for r in rows:
        if r["kind"] not in kinds:
            kinds.append(r["kind"])
    bk = by_kind(rows)
    lines = ["| Task | " + " | ".join(LABEL[a] for a in AGENTS) + " |", "|---|" + "---|" * len(AGENTS)]
    for k in kinds:
        cells = []
        for a in AGENTS:
            c = bk.get(k, {}).get(a)
            cells.append(f"{c['verified_pct']}% (n={c['n']}, p50 {c['p50_s']:.0f}s)" if c else "–")
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    pa = per_agent(rows)
    lines += ["", "| Agent | Passed | Timeouts | Violations | Outside attempts | Off-scope edits | Structured output | "
                  "Contradicted claims | p50 s | Total s | CPU s | Peak RSS MB | Diff lines |",
              "|---|" + "---|" * 12]
    for a, s in pa.items():
        lines.append(f"| {LABEL[a]} | {s['passed']}/{s['runs']} | {s['timeouts']} | {s['violations']} | "
                     f"{s['outside_attempts']} | {s['noncompliant']} | {s['structured_ok']}/{s['runs']} | "
                     f"{s['contradicted_claims']} | {s['p50_s']} | {s['total_s']} | {s['cpu_s_total']} | "
                     f"{s['peak_rss_mb_max']} | {s['diff_lines_total']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--rerun", action="append", default=[])
    ap.add_argument("--invalid", action="append", default=[], help="agent:kind:rep invalidated by the harness")
    ap.add_argument("--selection", default="")
    ap.add_argument("--md", default="")
    args = ap.parse_args()
    invalid = {(x.split(":")[0], x.split(":")[1], int(x.split(":")[2])) for x in args.invalid}
    rows, meta = load(args.results, args.rerun, invalid)
    md = markdown(rows)
    print(md)
    if args.md:
        Path(args.md).write_text(md + "\n")
    if args.selection:
        destination = Path(args.selection)
        # Invalid existing safety data must raise, not be replaced with a clean record.
        previous = json.loads(destination.read_text()) if destination.exists() else {}
        destination.write_text(json.dumps(selection(rows, meta,
            [str(Path(p).name) for p in args.results + args.rerun], previous), indent=1))
