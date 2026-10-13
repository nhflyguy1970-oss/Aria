"""Protected-path boundary for coding-agent runs.

Two layers. Prevention: no protected path may be mounted into the agent's
sandbox (checked before launch, from the container's own inspected mounts).
Detection: a complete per-file inventory of every protected root before and
after the run, so a change names the exact file.

ARIA keeps working while a run is in progress and writes its own state under
DATA_DIR (the run's ledger rows and logs, metrics, background databases). A
change is therefore attributed instead of compared as one digest:

* registered ARIA runtime state is recorded as a runtime write;
* a few security-relevant controller files are accepted only when a validator
  proves the change is one ARIA itself makes (the current run's ledger rows,
  a certificate being disabled, owner sessions being used or revoked, the
  scheduler recording when an automation rule last ran);
* everything else (credentials, owner security, plugins, code, backups, user
  files, anything unregistered, any added or removed file outside runtime
  state) is a violation.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sqlite3
import stat
from pathlib import Path
from typing import Any

MAX_FILES = 2_000_000  # beyond this the inventory is refused, never truncated

# Paths relative to DATA_DIR that ARIA writes on its own while a run is live.
RUNTIME_STATE = (
    "coding_agent_runtime.lock",
    "coding_agents.launch.lock",
    "launch.lock",
    "gui_shell.lock",
    "logs/*",
    "mission_control/*",
    "continuity.db", "continuity.db-wal", "continuity.db-shm",
    "missions.db", "missions.db-wal", "missions.db-shm",
    "acm/cognitive.db", "acm/cognitive.db-wal", "acm/cognitive.db-shm",
    "memory.db-wal", "memory.db-shm",
    "memory_vectors.db-wal", "memory_vectors.db-shm",
    "health_product/health.db", "health_product/health.db-wal", "health_product/health.db-shm",
    "integrity_product/last_scan.json", "integrity_product/history.jsonl",
    "dashboard_product/last_good_home.json",
    "capabilities_product/activity.json",
    "automation_product/run_history.json",
    "activity/inbox.jsonl",
    "*_product/activity_outbox.jsonl",
)

# Never runtime state, whatever RUNTIME_STATE matches.
SENSITIVE = (
    "*.env", "*secret*", "*token*", "*credential*", "*oauth*", "*vault*",
    "*.key", "*.pem", "security/*", "plugins/*",
    "*.py", "*.sh", "*.js", "*.so",
)

LEDGER = ("coding_agents.db", "coding_agents.db-wal", "coding_agents.db-shm", "coding_agents.db-journal")
CERTIFICATE = "coding_agent_runtime.json"
OWNER_SESSIONS = "security/owner/sessions.json"
AUTOMATION_RULES = "automation_product/rules.json"
TERMINAL = ("completed", "verified", "unverified", "tests_failed", "no_changes", "failed", "timeout",
            "cancelled", "interrupted", "boundary_violation", "refused")


class BoundaryError(RuntimeError):
    pass


def _match(rel: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(rel, p) for p in patterns)


def _signature(path: str) -> str:
    st = os.lstat(path)
    link = os.readlink(path) if stat.S_ISLNK(st.st_mode) else ""
    # ctime cannot be set back by an unprivileged writer, unlike mtime.
    raw = f"{st.st_mode}|{st.st_size}|{st.st_mtime_ns}|{st.st_ctime_ns}|{st.st_ino}|{link}"
    return hashlib.blake2b(raw.encode(), digest_size=12).hexdigest()


def _inventory(root: Path) -> dict[str, str]:
    if root.is_symlink() or not root.is_dir():
        return {str(root): _signature(str(root))}
    out: dict[str, str] = {}

    def unreadable(err: OSError) -> None:
        out[str(err.filename)] = f"unreadable:{err.errno}"

    for dirpath, dirnames, filenames in os.walk(root, onerror=unreadable, followlinks=False):
        links = [d for d in dirnames if os.path.islink(os.path.join(dirpath, d))]
        for name in (*filenames, *links):
            path = os.path.join(dirpath, name)
            try:
                out[path] = _signature(path)
            except OSError as exc:
                out[path] = f"unreadable:{exc.errno}"
        if len(out) > MAX_FILES:
            raise BoundaryError(f"protected path {root} has more than {MAX_FILES} files; refusing to run unverified")
    return out


def _ledger_view(db: Path, run_id: str) -> dict[str, str]:
    """Hash of every finished run's receipt and events; the current run is excluded."""
    conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        conn.row_factory = sqlite3.Row
        view = {}
        for row in conn.execute("SELECT * FROM runs WHERE id != ? ORDER BY id", (run_id,)):
            if row["status"] not in TERMINAL:
                continue
            events = conn.execute("SELECT ts, kind, detail FROM events WHERE run_id=? ORDER BY ts, kind, detail",
                                  (row["id"],)).fetchall()
            body = json.dumps([dict(row), [tuple(e) for e in events]], default=str, sort_keys=True)
            view[row["id"]] = hashlib.sha256(body.encode()).hexdigest()
        return view
    finally:
        conn.close()


def _views(data_dir: Path, run_id: str, roots: dict[str, Any]) -> dict[str, Any]:
    """Content views of the validated controller files that lie inside a protected root."""
    covered = set()
    for entries in roots.values():
        covered.update(entries or ())
    views: dict[str, Any] = {}
    for rel, load in ((LEDGER[0], lambda p: _ledger_view(p, run_id)),
                      (CERTIFICATE, lambda p: json.loads(p.read_text())),
                      (OWNER_SESSIONS, lambda p: json.loads(p.read_text())),
                      (AUTOMATION_RULES, lambda p: json.loads(p.read_text()))):
        path = data_dir / rel
        if str(path) in covered:
            try:
                views[rel] = load(path)
            except (OSError, ValueError, sqlite3.Error) as exc:
                views[rel] = {"unreadable": type(exc).__name__}
    return views


def snapshot(paths: list[str], *, data_dir: Path, run_id: str) -> dict[str, Any]:
    roots = {raw: (_inventory(Path(raw)) if Path(raw).exists() or Path(raw).is_symlink() else None)
             for raw in paths}
    return {"roots": roots, "views": _views(Path(data_dir), run_id, roots)}


def summary(snap: dict[str, Any]) -> dict[str, Any]:
    """Compact receipt form: per root file count and digest of the full inventory."""
    out: dict[str, Any] = {}
    for raw, entries in snap["roots"].items():
        if entries is None:
            out[raw] = None
            continue
        body = json.dumps(sorted(entries.items()), separators=(",", ":"))
        out[raw] = {"files": len(entries), "digest": hashlib.sha256(body.encode()).hexdigest()}
    return out


def _certificate_downgrade_only(before: Any, after: Any) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict) or "unreadable" in after:
        return False
    for agent in set(before) | set(after):
        old, new = before.get(agent), after.get(agent)
        if old == new:
            continue
        if not isinstance(new, dict) or new.get("state") == "verified":
            return False  # only ARIA's own disabling write can happen during a run
    return True


def _sessions_used_or_revoked(before: Any, after: Any) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if set(after) - {"sessions"} or set(before) - {"sessions"}:
        return False
    old, new = before.get("sessions") or {}, after.get("sessions") or {}
    for key, row in new.items():
        prior = old.get(key)
        if not isinstance(prior, dict) or not isinstance(row, dict) or set(row) != set(prior):
            return False  # a session was added or reshaped
        if any(row[k] != prior[k] for k in row if k != "last_active"):
            return False
        if float(row.get("last_active") or 0) < float(prior.get("last_active") or 0):
            return False
    return True


def _automation_bookkeeping_only(before: Any, after: Any) -> bool:
    """The scheduler records when a rule last fired; nothing else about a rule may change."""
    if not isinstance(before, dict) or not isinstance(after, dict) or set(before) != set(after):
        return False
    if any(before[k] != after[k] for k in before if k != "rules"):
        return False
    old, new = before.get("rules"), after.get("rules")
    if not isinstance(old, list) or not isinstance(new, list) or len(old) != len(new):
        return False
    bookkeeping = {"last_run", "last_status"}
    for prior, rule in zip(old, new):
        if not isinstance(prior, dict) or not isinstance(rule, dict) or set(prior) - bookkeeping != set(rule) - bookkeeping:
            return False
        if any(prior[k] != rule[k] for k in prior if k not in bookkeeping):
            return False
    return True


def _ledger_history_intact(before: Any, after: Any) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict) or "unreadable" in after:
        return False
    return all(after.get(run_id) == digest for run_id, digest in before.items())


def compare(before: dict[str, Any], after: dict[str, Any], *, data_dir: Path) -> dict[str, Any]:
    data_dir = Path(data_dir)
    changed: list[str] = []
    for raw in set(before["roots"]) | set(after["roots"]):
        old, new = before["roots"].get(raw), after["roots"].get(raw)
        if old is None or new is None:
            if old != new:
                changed.append(raw)
            continue
        changed += [p for p in set(old) | set(new) if old.get(p) != new.get(p)]

    validated = {
        LEDGER: lambda: _ledger_history_intact(before["views"].get(LEDGER[0]), after["views"].get(LEDGER[0])),
        (CERTIFICATE,): lambda: _certificate_downgrade_only(before["views"].get(CERTIFICATE),
                                                             after["views"].get(CERTIFICATE)),
        (OWNER_SESSIONS,): lambda: _sessions_used_or_revoked(before["views"].get(OWNER_SESSIONS),
                                                              after["views"].get(OWNER_SESSIONS)),
        (AUTOMATION_RULES,): lambda: _automation_bookkeeping_only(before["views"].get(AUTOMATION_RULES),
                                                                   after["views"].get(AUTOMATION_RULES)),
    }
    verdicts: dict[tuple[str, ...], bool] = {}
    violations, runtime_writes, controller_writes = [], [], []
    for path in sorted(changed):
        try:
            rel = Path(path).relative_to(data_dir).as_posix()
        except ValueError:
            violations.append(path)  # outside ARIA's data dir nothing is runtime state
            continue
        group = next((names for names in validated if rel in names), None)
        if group is not None:
            if group not in verdicts:
                verdicts[group] = bool(validated[group]())
            (controller_writes if verdicts[group] else violations).append(path)
        elif _match(rel, RUNTIME_STATE) and not _match(rel, SENSITIVE):
            existed = any(path in (r or {}) for r in before["roots"].values())
            present = any(path in (r or {}) for r in after["roots"].values())
            # Log rotation and SQLite sidecars come and go; other runtime state is rewritten in place.
            churn = rel.startswith("logs/") or rel.endswith(("-wal", "-shm", ".lock"))
            (runtime_writes if (existed and present) or churn else violations).append(path)
        else:
            violations.append(path)
    return {
        "violations": violations,
        "runtime_writes": runtime_writes,
        "controller_writes": controller_writes,
        "checked_files": sum(len(r or {}) for r in after["roots"].values()),
    }


def exposed(mount_sources: list[str], protected: list[str]) -> list[str]:
    """Protected paths reachable through a sandbox mount (either containing the other)."""
    hits = []
    for source in mount_sources:
        src = Path(os.path.realpath(source))
        for raw in protected:
            prot = Path(os.path.realpath(raw))
            if src == prot or prot in src.parents or src in prot.parents:
                hits.append(f"{source} exposes {raw}")
    return hits
