"""Safe storage migration — isolate rules, DAGs, and learned workflows."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from jarvis.automation.paths import (
    LEARNED_INDEX_FILE,
    LEARNED_WATCH_FILE,
    LEARNED_WORKFLOWS_DIR,
    LEGACY_RULES_FILE,
    LEGACY_WORKFLOWS_DIR,
    RULES_FILE,
    WORKFLOW_DAGS_DIR,
    ensure_dirs,
)

log = logging.getLogger("jarvis.automation.migrate")


def _is_dag_schema(data: dict[str, Any]) -> bool:
    return isinstance(data.get("steps"), list) and (
        "entry" in data or any(isinstance(s, dict) and "action" in s for s in data.get("steps") or [])
    ) and "slug" not in data


def _is_learned_schema(data: dict[str, Any]) -> bool:
    return "slug" in data or (isinstance(data.get("steps"), list) and data.get("count") is not None)


def migrate_storage(*, force: bool = False) -> dict[str, Any]:
    """Migrate legacy shared folders into isolated namespaces. Idempotent."""
    ensure_dirs()
    marker = RULES_FILE.parent / ".migration_v1_done"
    report: dict[str, Any] = {
        "ok": True,
        "rules_copied": False,
        "dags_moved": 0,
        "learned_moved": 0,
        "index_copied": False,
        "skipped": False,
        "notes": [],
    }
    if marker.is_file() and not force:
        report["skipped"] = True
        report["notes"].append("migration already done")
        return report

    # Rules: copy legacy → product rules file if product empty
    if LEGACY_RULES_FILE.is_file() and (force or not RULES_FILE.is_file()):
        try:
            shutil.copy2(LEGACY_RULES_FILE, RULES_FILE)
            report["rules_copied"] = True
        except OSError as exc:
            report["notes"].append(f"rules copy failed: {exc}")

    # Split DATA_DIR/workflows
    if LEGACY_WORKFLOWS_DIR.is_dir():
        for path in sorted(LEGACY_WORKFLOWS_DIR.glob("*.json")):
            if path.name in ("index.json", "_watch_state.json"):
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                report["notes"].append(f"skip unreadable {path.name}: {exc}")
                continue
            if not isinstance(data, dict):
                continue
            if _is_dag_schema(data):
                dest = WORKFLOW_DAGS_DIR / path.name
                if not dest.exists() or force:
                    shutil.copy2(path, dest)
                    report["dags_moved"] += 1
            elif _is_learned_schema(data):
                dest = LEARNED_WORKFLOWS_DIR / path.name
                if not dest.exists() or force:
                    shutil.copy2(path, dest)
                    report["learned_moved"] += 1
            else:
                # Ambiguous: keep a copy in learned (historical default) and note it
                dest = LEARNED_WORKFLOWS_DIR / path.name
                if not dest.exists() or force:
                    shutil.copy2(path, dest)
                    report["learned_moved"] += 1
                    report["notes"].append(f"ambiguous schema treated as learned: {path.name}")

        # index + watch
        legacy_index = LEGACY_WORKFLOWS_DIR / "index.json"
        if legacy_index.is_file() and (force or not LEARNED_INDEX_FILE.is_file()):
            shutil.copy2(legacy_index, LEARNED_INDEX_FILE)
            report["index_copied"] = True
        legacy_watch = LEGACY_WORKFLOWS_DIR / "_watch_state.json"
        if legacy_watch.is_file() and (force or not LEARNED_WATCH_FILE.is_file()):
            shutil.copy2(legacy_watch, LEARNED_WATCH_FILE)

    try:
        marker.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        pass
    log.info("automation storage migration: %s", report)
    return report
