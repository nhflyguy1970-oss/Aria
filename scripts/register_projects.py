#!/usr/bin/env python3
"""Register ARIA, Fly Tying Reference and BlackFly as coding-agent projects.

Read-only toward the projects: git status and file listings, and each test
command verified in a *disposable clone* inside a no-network, read-only-root
sandbox (the project's own venv is used read-only). Nothing is launched,
scraped, modified or restarted. The only write is ARIA's own project registry.

    python scripts/register_projects.py --dry-run --out inventory.json
    python scripts/register_projects.py --out inventory.json        # registers
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROJECTS = [
    {
        "title": "ARIA",
        "path": str(ROOT),
        "purpose": "Local-first AI assistant, memory, routing, tools, agents, and orchestration.",
        "test_command": "/media/jeff/AI/jarvis/venv/bin/python -m pytest -q -p no:cacheprovider",
        "protected": ["data/", "backups/", ".env", "data/jarvis.env", "scratch/", "/media/jeff/AI/aria-backups",
                      "/media/jeff/AI/jarvis-data-backups"],
        "services": ["jarvis.service (user unit, :8765)", "ollama :11434 (ARIA's models)"],
        "backups": ["backups/", "/media/jeff/AI/aria-backups", "/media/jeff/AI/jarvis-data-backups"],
    },
    {
        "title": "Fly Tying Reference",
        "path": "/media/jeff/C/fly_tying_reference",
        "purpose": "Offline fly-tying and fly-fishing reference application.",
        "test_command": "/media/jeff/C/fly_tying_reference/venv/bin/python -m pytest -q -p no:cacheprovider",
        "protected": ["data/", "reference_data/", "ftr-dual-gpu.conf", "fly-tying-reference-server.service",
                      "ftr-ai-text.service", "ftr-ai-vision.service"],
        "services": ["fly-tying-reference-server.service", "ftr-ai-text.service (:11435, CUDA)",
                     "ftr-ai-vision.service (:11436, Vulkan RX 7600)", "ftr-backup.timer / ftr-backup.path"],
        "backups": ["data/snapshots/", "data/repair_backups/", "ftr-backup → /mnt/wwn-0x5000c500e7af8167-part1 → cloud"],
    },
    {
        "title": "BlackFly",
        "path": "/media/jeff/C/fly_fishing_project",
        "purpose": "Fly-fishing recipe discovery, scraping, and data processing.",
        "test_command": "/media/jeff/C/fly_fishing_project/venv/bin/python -m unittest discover -s tests -t .",
        "protected": ["output/", "backups/", "blackfly.env", ".env", "config/", "bench_out/", ".aider.tags.cache.v4/",
                      "flyfish-stack.service"],
        "services": ["flyfish-stack.service (inactive at registration)", "ffp-backup.timer"],
        "backups": ["backups/", "ffp-backup.timer"],
    },
]


def sh(argv, cwd, timeout=120):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def inventory(p: dict) -> dict:
    path = Path(p["path"])
    git = {
        "head": sh(["git", "rev-parse", "HEAD"], path).stdout.strip(),
        "branch": sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], path).stdout.strip(),
        "uncommitted_entries": len(sh(["git", "status", "--porcelain"], path).stdout.splitlines()),
        "tracked_files": len(sh(["git", "ls-files"], path).stdout.splitlines()),
        "remote": sh(["git", "remote", "get-url", "origin"], path).stdout.strip().split("@")[-1],
    }
    dbs = []
    for directory, dirs, files in os.walk(path):
        rel_dir = Path(directory).relative_to(path)
        dirs[:] = sorted(d for d in dirs if d not in (".git", "venv", ".venv", "node_modules", "__pycache__",
                                                     ".mypy_cache") and len(rel_dir.parts) < 3)
        for name in sorted(files):
            f = Path(directory) / name
            if f.suffix in (".db", ".sqlite", ".sqlite3") and f.is_file():
                dbs.append(str(f.relative_to(path)))
    source = sorted({str(Path(x).parts[0]) for x in sh(["git", "ls-files", "*.py"], path).stdout.split()})
    return {
        "git": git,
        "source_roots": source[:40],
        "databases": dbs[:60],
        "databases_total": len(dbs),
        "config": [x for x in ("pyproject.toml", "pytest.ini", "requirements.txt", "config/", ".env.example",
                               "ftr-dual-gpu.conf") if (path / x).exists()],
        "credential_files": [x for x in ("blackfly.env", ".env", "data/jarvis.env") if (path / x).exists()],
        "services": p["services"],
        "backups": p["backups"],
        "production_data": [x for x in p["protected"] if x.endswith("/")],
    }


def verify_tests(p: dict, scratch: Path) -> dict:
    """Run the test command in a disposable clone, sandboxed (read-only root, no network)."""
    from jarvis.coding_agents import workspace

    os.environ["JARVIS_AGENT_WORKSPACES"] = str(scratch)
    ws = workspace.prepare(p["path"], f"verify-{p['title'].lower().replace(' ', '-')}-{int(time.time())}")
    # Some project tests explicitly invoke <checkout>/venv/bin/python. Supply
    # that toolchain in the clone; the sandbox mounts its source read-only.
    for name in ("venv", ".venv"):
        toolchain = Path(p["path"]) / name
        target = Path(ws["workspace"]) / name
        if toolchain.is_dir() and not target.exists():
            target.symlink_to(toolchain, target_is_directory=True)
    started = time.time()
    out = workspace.run_tests(ws["workspace"], p["test_command"], timeout=1800)
    if out.get("ran") and out.get("exit_code") not in (0, 1) and p.get("test_command_fallback"):
        out = workspace.run_tests(ws["workspace"], p["test_command_fallback"], timeout=1800)
        out["note"] = "primary command unusable; fallback used"
    tail = (out.get("output_tail") or "").strip().splitlines()
    return {
        "command": out.get("command"),
        "ran": out.get("ran"),
        "exit_code": out.get("exit_code"),
        "passed": out.get("passed"),
        "summary": next((line for line in reversed(tail) if any(k in line for k in ("passed", "failed", "OK", "FAILED", "Ran "))), ""),
        "seconds": round(time.time() - started, 1),
        "where": "disposable clone of HEAD " + ws["base_commit"][:10] + ", bwrap read-only root, no network",
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "error": out.get("error"),
        "output_log": out.get("output_log"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    scratch = Path(tempfile.mkdtemp(prefix="aria-project-verify-"))
    report = []
    for p in PROJECTS:
        if args.only and args.only.lower() not in p["title"].lower():
            continue
        path = Path(p["path"])
        entry = {"title": p["title"], "path": p["path"], "exists": path.is_dir(), "is_git": (path / ".git").exists()}
        if not (entry["exists"] and entry["is_git"]):
            entry["error"] = "missing or not a git repository — not registered"
            report.append(entry)
            continue
        entry["inventory"] = inventory(p)
        entry["test_verification"] = {} if args.skip_tests else verify_tests(p, scratch)
        print(json.dumps({"title": p["title"], "tests": entry["test_verification"].get("summary"),
                          "exit": entry["test_verification"].get("exit_code")}), flush=True)
        if not args.dry_run:
            from jarvis.coding_agents import projects

            rec = projects.register(p["path"], title=p["title"], purpose=p["purpose"],
                                    test_command=p["test_command"] if entry["test_verification"].get("passed")
                                    else p.get("test_command_fallback") or p["test_command"],
                                    protected_paths=p["protected"], inventory=entry["inventory"],
                                    test_verification=entry["test_verification"])
            entry["registered"] = {"slug": rec.get("slug"), "memory_namespace": rec.get("memory_namespace")}
        report.append(entry)
    Path(args.out).write_text(json.dumps(report, indent=1))
    print(json.dumps([{k: e.get(k) for k in ("title", "registered", "error")} for e in report], indent=1))


if __name__ == "__main__":
    main()
