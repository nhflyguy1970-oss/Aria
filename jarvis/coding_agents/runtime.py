"""Availability requires a version/policy-bound, measured execution certificate."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

from jarvis.config import DATA_DIR

FILE = DATA_DIR / "coding_agent_runtime.json"


def policy_hash() -> str:
    root = Path(__file__).parent
    return hashlib.sha256(
        b"".join(
            (root / n).read_bytes()
            for n in (
                "oci.py",
                "rpc_worker.py",
                "transport.py",
                "runtime.py",
                "runs.py",
                "discovery.py",
                "adapters.py",
                "workspace.py",
                "supervisor.py",
            )
        )
    ).hexdigest()


def history_hash(agent: str, data: dict) -> str:
    summary = (data.get("summary") or {}).get(agent) or {}
    safety = {k: summary.get(k, 0) for k in ("violations", "outside_attempts")}
    safety["history"] = [
        row for row in data.get("associated_boundary_history", []) if row.get("agent") == agent
    ]
    return hashlib.sha256(json.dumps(safety, sort_keys=True).encode()).hexdigest()


def run_boundary_history(agent: str) -> list[str]:
    """Read durable violations, including a crash before certificate quarantine."""
    database = FILE.parent / "coding_agents.db"
    if not database.exists():
        return []
    conn = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=1)
    try:
        return [
            row[0]
            for row in conn.execute(
                "SELECT id FROM runs WHERE agent=? AND status='boundary_violation' ORDER BY id",
                (agent,),
            )
        ]
    finally:
        conn.close()


def run_history_hash(agent: str) -> str:
    return hashlib.sha256(json.dumps(run_boundary_history(agent)).encode()).hexdigest()


def compatibility(agent: str, binary: str, version: str) -> dict:
    try:
        record = json.loads(FILE.read_text())[agent]
        if (
            record.get("state") != "verified"
            or record.get("backend") != "oci"
            or record.get("version") != version
            or record.get("policy_sha256") != policy_hash()
            or record.get("binary_sha256")
            != hashlib.sha256(Path(binary).resolve().read_bytes()).hexdigest()
        ):
            return {
                "state": "disabled",
                "reason": record.get("reason") or "execution certificate is absent or stale",
            }
        if record.get("native_binary") and hashlib.sha256(
            Path(record["native_binary"]).read_bytes()
        ).hexdigest() != record.get("native_sha256"):
            return {
                "state": "disabled",
                "reason": "native CLI installation changed since certification",
            }
        live_history = run_boundary_history(agent)
        if live_history and (
            not record.get("boundary_history_reviewed")
            or record.get("run_boundary_history_sha256") != run_history_hash(agent)
        ):
            return {
                "state": "disabled",
                "reason": "unreviewed durable run boundary violation",
                "boundary_runs": live_history,
            }
        benchmark = DATA_DIR / "coding_agent_benchmark.json"
        data = json.loads(benchmark.read_text()) if benchmark.is_file() else {}
        safety = (data.get("summary") or {}).get(agent) or {}
        if (safety.get("violations") or safety.get("outside_attempts")) and (
            not record.get("boundary_history_reviewed")
            or record.get("boundary_history_sha256") != history_hash(agent, data)
        ):
            return {
                "state": "disabled",
                "reason": "unresolved or newly recorded historical boundary violation",
            }
        if record.get("quota") == "exhausted":
            return {
                **record,
                "state": "disabled",
                "reason": "subscription quota exhausted; requires a new availability check",
            }
        return record
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        return {
            "state": "disabled",
            "reason": "no proven execution compatibility under the required boundary",
        }


def unavailable(agent: str, reason: str, *, quota: bool = False) -> None:
    """Persist capacity/transport failures separately from benchmark correctness."""
    import fcntl

    FILE.parent.mkdir(parents=True, exist_ok=True)
    with FILE.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            data = json.loads(FILE.read_text())
        except FileNotFoundError:
            data = {}
        record = data.setdefault(agent, {})
        record.update(state="disabled", reason=reason, unavailable_at=time.time())
        if quota:
            record["quota"] = "exhausted"
        temp = FILE.with_name(FILE.name + ".tmp")
        temp.write_text(json.dumps(data, indent=2))
        temp.chmod(0o600)
        os.replace(temp, FILE)
