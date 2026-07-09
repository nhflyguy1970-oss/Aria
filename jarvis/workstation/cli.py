"""CLI entry point for workstation lifecycle."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aria workstation control plane",
        prog="workstation",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="Fresh-machine install (venv, deps, platform init)")
    sub.add_parser("configure", help="Create jarvis.env and initialize platform paths")
    sub.add_parser("start", help="Start Aria desktop (tray + server + window)")
    sub.add_parser("stop", help="Stop tray and server")
    sub.add_parser("update", help="git pull + pip sync + restart if running")
    sub.add_parser("backup", help="Backup jarvis data and platform state")
    restore_p = sub.add_parser("restore", help="Restore from backup-workstation archive")
    restore_p.add_argument("archive", help="Path to workstation_*.tar.gz")
    sub.add_parser("verify", help="Hardware-agnostic install verification")
    sub.add_parser("hardware", help="Detect hardware and print workload recommendations")
    sub.add_parser("doctor", help="Diagnose workstation + AI-Platform")

    sub.add_parser("status", help="Show workstation status (JSON)")

    up_p = sub.add_parser("up", help="Start workstation services or a component")
    up_p.add_argument("target", nargs="?", help="Component id (default: bootstrap all autostart)")
    up_p.add_argument("--profile", help="Start AI Platform docker profile (data, inference)")

    down_p = sub.add_parser("down", help="Stop optional managed components")
    down_p.add_argument("target", nargs="?", help="Component id")
    down_p.add_argument("--profile", help="Stop AI Platform docker profile")

    restart_p = sub.add_parser("restart", help="Restart a managed component")
    restart_p.add_argument("target", help="Component id")

    sub.add_parser("diagnose", help="Diagnose workstation issues")
    sub.add_parser("recover", help="Attempt safe automatic recovery")

    list_p = sub.add_parser("list", help="List registered components")
    list_p.add_argument("--category", help="Filter by category")

    args = parser.parse_args(argv)

    from jarvis.workstation import lifecycle, lifecycle_shell, operations, registry

    if args.command == "restore":
        return lifecycle_shell.restore(args.archive)

    lifecycle_commands = {
        "install": lambda: lifecycle_shell.install(),
        "configure": lifecycle_shell.configure,
        "start": lifecycle_shell.start,
        "stop": lifecycle_shell.stop,
        "update": lifecycle_shell.update,
        "backup": lifecycle_shell.backup,
        "verify": lifecycle_shell.verify,
        "hardware": lifecycle_shell.hardware,
        "doctor": lifecycle_shell.doctor,
    }
    if args.command in lifecycle_commands:
        return lifecycle_commands[args.command]()

    if args.command == "status":
        payload = lifecycle.status(force=True)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ready") else 1

    if args.command == "up":
        payload = lifecycle.up(
            getattr(args, "target", None), profile=getattr(args, "profile", None)
        )
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "down":
        payload = lifecycle.down(
            getattr(args, "target", None), profile=getattr(args, "profile", None)
        )
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "restart":
        payload = lifecycle.restart(args.target)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "diagnose":
        payload = operations.diagnose(force=True)
        print(operations.format_report(force=True))
        return 0 if payload.get("ok") else 1

    if args.command == "recover":
        payload = operations.recover_safe()
        print(operations.format_report(force=True))
        return 0 if payload.get("ok") else 1

    if args.command == "list":
        items = registry.all_components(category=getattr(args, "category", None))
        for comp in items:
            mark = "●" if comp.healthy() else "○"
            managed = "managed" if comp.managed else "observed"
            print(f"{mark} {comp.id:16} {comp.category:12} {managed:8} {comp.label}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
