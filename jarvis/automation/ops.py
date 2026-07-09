"""Continuous workstation automation — nightly maintenance jobs."""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any

logger = logging.getLogger("jarvis.automation")

_LAST_RUN_FILE = None


def _runs_dir():
    from jarvis.config import DATA_DIR

    return DATA_DIR / "automation"


def run_maintenance(*, smoke_tests: bool = False) -> dict[str, Any]:
    """Run continuous ops: knowledge sync, workstation diagnose, optional test smoke."""
    results: list[dict[str, Any]] = []
    started = time.time()

    try:
        from jarvis.knowledge.registry import sync_registry

        kr = sync_registry()
        results.append({"job": "knowledge_sync", "ok": kr.get("ok", False), "detail": kr.get("source_count")})
    except Exception as exc:
        results.append({"job": "knowledge_sync", "ok": False, "error": str(exc)[:200]})

    try:
        from jarvis.knowledge.ingestion import maybe_scheduled_ingest

        ing = maybe_scheduled_ingest()
        if ing:
            results.append({"job": "knowledge_ingest", **ing})
    except Exception as exc:
        results.append({"job": "knowledge_ingest", "ok": False, "error": str(exc)[:200]})

    try:
        from jarvis.knowledge.git_sync import sync_all

        gs = sync_all(force=False)
        results.append({"job": "git_sync", "ok": gs.get("ok", False), "repos": gs.get("repos")})
    except Exception as exc:
        results.append({"job": "git_sync", "ok": False, "error": str(exc)[:200]})

    try:
        from jarvis.workstation.operations import diagnose, recover_safe

        diag = diagnose(force=True)
        results.append({
            "job": "workstation_diagnose",
            "ok": diag.get("ok", False),
            "critical": diag.get("critical", 0),
            "warnings": diag.get("warnings", 0),
        })
        if not diag.get("ok"):
            rec = recover_safe(max_attempts=2)
            results.append({"job": "workstation_recover", "ok": rec.get("ok", False)})
    except Exception as exc:
        results.append({"job": "workstation_diagnose", "ok": False, "error": str(exc)[:200]})

    if smoke_tests or os.getenv("JARVIS_MAINTENANCE_SMOKE_TESTS", "0") == "1":
        results.append(_run_smoke_tests())

    elapsed = int((time.time() - started) * 1000)
    ok = all(r.get("ok") for r in results)
    payload = {"ok": ok, "elapsed_ms": elapsed, "results": results, "ts": time.time()}
    _persist_run(payload)
    return payload


def _run_smoke_tests() -> dict[str, Any]:
    try:
        from jarvis.env_loader import PROJECT_ROOT

        proc = subprocess.run(
            [".venv/bin/python", "-m", "pytest", "tests/test_workstation.py", "tests/test_knowledge_registry.py", "-q"],
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
    import json

    stamp_file = DATA_DIR / "automation" / "last_nightly_day.txt"
    day = now.date().isoformat()
    if stamp_file.is_file() and stamp_file.read_text(encoding="utf-8").strip() == day:
        return
    stamp_file.parent.mkdir(parents=True, exist_ok=True)
    stamp_file.write_text(day, encoding="utf-8")
    logger.info("Running nightly workstation maintenance")
    run_maintenance(smoke_tests=os.getenv("JARVIS_MAINTENANCE_SMOKE_TESTS", "1") == "1")
