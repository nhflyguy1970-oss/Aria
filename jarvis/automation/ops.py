"""Continuous workstation automation — nightly maintenance jobs."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("jarvis.automation")

_LAST_RUN_FILE = None


def _runs_dir():
    from jarvis.config import DATA_DIR

    return DATA_DIR / "automation"


def _results_all_ok(results: list[dict[str, Any]]) -> bool:
    """A maintenance job must explicitly report ok=True to count as success."""
    return all(entry.get("ok") is True for entry in results)


def _smoke_tests_requested(*, smoke_tests: bool) -> bool:
    return smoke_tests or os.getenv("JARVIS_MAINTENANCE_SMOKE_TESTS", "0") == "1"


def _step_knowledge_sync() -> dict[str, Any]:
    from jarvis.knowledge.registry import sync_registry

    kr = sync_registry()
    return {
        "job": "knowledge_sync",
        "ok": bool(kr.get("ok")),
        "detail": kr.get("source_count"),
    }


def _step_knowledge_ingest() -> dict[str, Any] | None:
    from jarvis.knowledge.ingestion import maybe_scheduled_ingest

    ing = maybe_scheduled_ingest()
    if not ing:
        return None
    ok = ing.get("ok") if "ok" in ing else True
    return {"job": "knowledge_ingest", "ok": bool(ok), **ing}


def _step_git_sync() -> dict[str, Any]:
    from jarvis.knowledge.git_sync import sync_all

    gs = sync_all(force=False)
    return {"job": "git_sync", "ok": bool(gs.get("ok")), "repos": gs.get("repos")}


def _step_memory_consolidate() -> dict[str, Any]:
    from jarvis.assistant_instance import get_assistant
    from jarvis.memory.hierarchy import consolidate

    mem = get_assistant().memory
    c = consolidate(mem, dry_run=False)
    ok = c.get("ok") if "ok" in c else True
    return {"job": "memory_consolidate", "ok": bool(ok), **c}


def _step_workstation() -> list[dict[str, Any]]:
    from jarvis.workstation.operations import diagnose, recover_safe

    diag = diagnose(force=True)
    results = [
        {
            "job": "workstation_diagnose",
            "ok": bool(diag.get("ok")),
            "critical": diag.get("critical", 0),
            "warnings": diag.get("warnings", 0),
        }
    ]
    if not diag.get("ok"):
        rec = recover_safe(max_attempts=2)
        results.append({"job": "workstation_recover", "ok": bool(rec.get("ok"))})
    return results


def _append_step(
    results: list[dict[str, Any]],
    *,
    job: str,
    fn,
) -> None:
    try:
        entry = fn()
        if entry is None:
            return
        if isinstance(entry, list):
            results.extend(entry)
        else:
            results.append(entry)
    except Exception as exc:
        results.append({"job": job, "ok": False, "error": str(exc)[:200]})


def run_maintenance(*, smoke_tests: bool = False) -> dict[str, Any]:
    """Run continuous ops: knowledge sync, workstation diagnose, optional test smoke."""
    results: list[dict[str, Any]] = []
    started = time.time()

    _append_step(results, job="knowledge_sync", fn=_step_knowledge_sync)
    _append_step(results, job="knowledge_ingest", fn=_step_knowledge_ingest)
    _append_step(results, job="git_sync", fn=_step_git_sync)
    _append_step(results, job="memory_consolidate", fn=_step_memory_consolidate)
    _append_step(results, job="workstation_diagnose", fn=_step_workstation)

    if _smoke_tests_requested(smoke_tests=smoke_tests):
        results.append(_run_smoke_tests())

    elapsed = int((time.time() - started) * 1000)
    ok = _results_all_ok(results)
    payload = {"ok": ok, "elapsed_ms": elapsed, "results": results, "ts": time.time()}
    _persist_run(payload)
    return payload


def _run_smoke_tests() -> dict[str, Any]:
    try:
        from jarvis.env_loader import PROJECT_ROOT

        venv_python = PROJECT_ROOT / "venv" / "bin" / "python"
        if not venv_python.is_file():
            alt = PROJECT_ROOT / ".venv" / "bin" / "python"
            venv_python = alt if alt.is_file() else Path(sys.executable)

        proc = subprocess.run(
            [
                str(venv_python),
                "-m",
                "pytest",
                "tests/test_workstation.py",
                "tests/test_knowledge_registry.py",
                "-q",
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "job": "smoke_tests",
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-500:],
        }
    except Exception as exc:
        return {"job": "smoke_tests", "ok": False, "error": str(exc)[:200]}


def _persist_run(payload: dict[str, Any]) -> None:
    import json

    d = _runs_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / "last_maintenance.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def last_maintenance() -> dict[str, Any]:
    import json

    path = _runs_dir() / "last_maintenance.json"
    if not path.is_file():
        return {"ok": False, "message": "no maintenance runs yet"}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "message": "corrupt maintenance log"}


def maybe_nightly_maintenance(now) -> None:
    """Hook for proactive scheduler — run at configured hour once per day."""
    if os.getenv("JARVIS_NIGHTLY_MAINTENANCE", "1") == "0":
        return
    try:
        hour = int(os.getenv("JARVIS_MAINTENANCE_HOUR", "2"))
    except ValueError:
        hour = 2
    if now.hour != hour or now.minute > 10:
        return

    from jarvis.config import DATA_DIR

    stamp_file = DATA_DIR / "automation" / "last_nightly_day.txt"
    day = now.date().isoformat()
    if stamp_file.is_file() and stamp_file.read_text(encoding="utf-8").strip() == day:
        return
    stamp_file.parent.mkdir(parents=True, exist_ok=True)
    stamp_file.write_text(day, encoding="utf-8")
    logger.info("Running nightly workstation maintenance")
    run_maintenance(smoke_tests=os.getenv("JARVIS_MAINTENANCE_SMOKE_TESTS", "1") == "1")
