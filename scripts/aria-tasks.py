#!/usr/bin/env python3
"""ARIA task CLI. Uses the same owner-gated API as the desktop Mission room."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def request(path: str, body: dict | None = None) -> dict:
    base = os.environ.get("ARIA_TASKS_URL", "http://127.0.0.1:8765").rstrip("/")
    url = base + path
    payload = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"} if payload else {},
                                 method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            error = json.load(exc).get("error") or exc.reason
        except ValueError:
            error = exc.reason
        raise RuntimeError(f"ARIA refused ({exc.code}): {error}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect and control ARIA autonomous tasks")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="list recent tasks")
    listing.add_argument("--project", default="")
    listing.add_argument("--query", default="")
    show = sub.add_parser("show", help="show state, plan and events")
    show.add_argument("task_id")
    create = sub.add_parser("new", help="propose a goal; execution needs owner approval")
    create.add_argument("goal")
    create.add_argument("--project", default="general")
    create.add_argument("--steps-file", help="optional reviewed JSON step list")
    create.add_argument("--at", help="ISO-8601 time with timezone, such as 2026-10-13T09:00:00-04:00")
    for name in ("approve", "deny", "pause", "resume", "cancel"):
        sub.add_parser(name).add_argument("task_id")
    redirect = sub.add_parser("redirect", help="change a paused goal; requires new approval")
    redirect.add_argument("task_id")
    redirect.add_argument("goal")
    redirect.add_argument("--steps-file", help="replacement JSON step list; default preserves plan")
    reconcile = sub.add_parser("reconcile", help="record externally verified operation outcome")
    reconcile.add_argument("task_id")
    reconcile.add_argument("step_index", type=int)
    reconcile.add_argument("outcome", choices=("completed", "not_executed"))
    reconcile.add_argument("evidence")
    reconcile.add_argument("--result-file", help="observed result JSON for completed outcome")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            result = request("/api/agent-tasks?" + urllib.parse.urlencode(
                {"project": args.project, "query": args.query}))
        elif args.command == "show":
            result = request("/api/agent-tasks/" + urllib.parse.quote(args.task_id))
        elif args.command == "new":
            body = {"objective": args.goal, "project": args.project}
            if args.at:
                when = datetime.datetime.fromisoformat(args.at)
                if when.tzinfo is None:
                    raise ValueError("--at needs an explicit timezone")
                body["scheduled_at"] = when.timestamp()
            if args.steps_file:
                with open(args.steps_file, encoding="utf-8") as source:
                    body["steps"] = json.load(source)
            result = request("/api/agent-tasks", body)
        elif args.command == "redirect":
            if args.steps_file:
                with open(args.steps_file, encoding="utf-8") as source:
                    steps = json.load(source)
            else:
                steps = request("/api/agent-tasks/" + urllib.parse.quote(args.task_id))["task"]["steps"]
            result = request(f"/api/agent-tasks/{urllib.parse.quote(args.task_id)}/redirect",
                             {"objective": args.goal, "steps": steps})
        elif args.command == "reconcile":
            observed = None
            if args.result_file:
                with open(args.result_file, encoding="utf-8") as source:
                    observed = json.load(source)
            result = request(f"/api/agent-tasks/{urllib.parse.quote(args.task_id)}/reconcile",
                             {"step_index": args.step_index, "outcome": args.outcome,
                              "evidence": args.evidence, "result": observed})
        else:
            result = request(f"/api/agent-tasks/{urllib.parse.quote(args.task_id)}/{args.command}", {})
        print(json.dumps(result, indent=2))
        return 0
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
