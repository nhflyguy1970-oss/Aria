"""Safe remediations for known development artifacts — Jeff-approved only."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.integrity_product import store
from jarvis.integrity_product.scanner import invalidate_cache, run_scan

logger = logging.getLogger("jarvis.integrity_product.remediate")


def _remove_path(rel: str) -> dict[str, Any]:
    path = DATA_DIR / rel
    if not path.exists():
        return {"ok": True, "skipped": True, "path": str(path), "detail": "already gone"}
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return {"ok": True, "removed": True, "path": str(path)}
    except OSError as exc:
        return {"ok": False, "path": str(path), "error": str(exc)}


def apply_safe_remediations(findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Remove only findings marked safe_to_remove with known remediation refs.
    Never touches unconfirmed user data categories without allow-listed refs.
    """
    if findings is None:
        findings = (run_scan(force=True, trigger="pre_repair").get("findings") or [])

    actions: list[dict[str, Any]] = []
    preserved_note = "User Health/ACM/Projects/Journal/Planner/Calendar/Gallery left untouched unless listed as QA artifact."

    # Projects
    slugs = [
        str(f.get("ref", {}).get("slug") or "")
        for f in findings
        if f.get("category") == "projects" and f.get("safe_to_remove") and f.get("ref", {}).get("slug")
    ]
    if slugs:
        try:
            from jarvis.project_registry import delete_project

            for slug in slugs:
                ok = delete_project(slug)
                actions.append({"kind": "project", "slug": slug, "ok": ok})
        except Exception as exc:
            actions.append({"kind": "project", "ok": False, "error": str(exc)})

    # Health known smoke rows
    health_refs = [
        f.get("ref") or {}
        for f in findings
        if f.get("category") == "health" and f.get("safe_to_remove") and (f.get("ref") or {}).get("id")
    ]
    if health_refs:
        try:
            from jarvis.health_product.store import delete_by_id, purge_known_smoke_records

            # Prefer allow-listed purge first
            purged = purge_known_smoke_records(force=True)
            actions.append({"kind": "health_purge_known", **purged})
            for ref in health_refs:
                table, item_id = ref.get("table"), ref.get("id")
                if not table or not item_id:
                    continue
                # Skip if already in known purge list result
                already = any(
                    r.get("table") == table and r.get("id") == item_id for r in (purged.get("removed") or [])
                )
                if already:
                    continue
            # Extra smoke-like unconfirmed rows — never auto-delete Health
            # heuristics. Only allow-listed known smoke IDs are removed here.
            actions.append(
                {
                    "kind": "health_row_preserved",
                    "table": table,
                    "id": item_id,
                    "ok": True,
                    "detail": "Heuristic Health finding preserved for Jeff review",
                }
            )
        except Exception as exc:
            actions.append({"kind": "health", "ok": False, "error": str(exc)})

    # Files / workflows / journal / documents / audio paths
    _ALLOWED_EXACT = {
        "qa_wf",
        "qa_ocr_sample.png",
        "workflows/demo-skill-check.json",
        "uploads/final-cert.csv",
        "certification/SHIP_CERT_PROBE.txt",
        "certification",
        "automation_product/learned_workflows/demo-skill-check.json",
        "automation_product/workflow_dags/retrydemo.json",
        "documents/imports/QA_Aria_Resume.txt",
        "documents/imports/QA_Aria_Resume-2.txt",
        "documents/uploads/fnaccept_qa.txt",
        "mission_control/series/test0.json",
        "mission_control/series/test1.json",
        "mission_control/series/test2.json",
        "mission_control/series/test3.json",
        "mission_control/series/test4.json",
        "mission_control/series/test5.json",
        "mission_control/series/test6.json",
        "mission_control/series/test7.json",
    }
    _ALLOWED_PREFIXES = (
        "journal/projects/qa-",
        "journal/projects/cert-proj-",
        "journal/projects/onetruth-proj-",
        "journal/projects/smoke-",
        "documents/imports/QA_",
        "documents/imports/Smoke_",
        "documents/imports/Cert_",
        "documents/imports/Demo_",
        "documents/uploads/fnaccept",
        "uploads/test",
        "uploads/data-live-test",
        "audio/generated/QA_",
        "audio/generated/Voice_smoke_",
        "audio/generated/Ship_certification_",
        "audio/generated/ARIA_audit_test",
        "audio/generated/Hello_ARIA_voice_test",
        "audio/generated/Stored_via_ACM_ARIA-EXC",
        "audio/generated/Stored_via_ACM_exact_acceptance",
        "audio/generated/Stored_via_ACM_What_is_the_ARIA-EXC",
        "mission_control/series/test",
    )
    removed_doc_paths: list[str] = []
    for f in findings:
        if not f.get("safe_to_remove"):
            continue
        rel = (f.get("ref") or {}).get("rel")
        if not rel:
            continue
        rel_s = str(rel).replace("\\", "/").lstrip("/")
        if ".." in rel_s:
            actions.append({"kind": "path", "rel": rel_s, "ok": False, "error": "path traversal blocked"})
            continue
        if rel_s not in _ALLOWED_EXACT and not any(rel_s.startswith(p) for p in _ALLOWED_PREFIXES):
            actions.append({"kind": "path", "rel": rel_s, "ok": False, "error": "not on allow-list"})
            continue
        result = _remove_path(rel_s)
        actions.append({"kind": "path", **result})
        if result.get("removed") and rel_s.startswith("documents/imports/"):
            removed_doc_paths.append(str(DATA_DIR / rel_s))

    if removed_doc_paths:
        try:
            from jarvis.document_services import IMPORTS_FILE, _load_json, _save_json

            data = _load_json(IMPORTS_FILE, {"imports": []})
            imports = list(data.get("imports") or [])
            before = len(imports)
            removed_set = set(removed_doc_paths)
            imports = [
                e
                for e in imports
                if str(e.get("path") or "") not in removed_set
                and not str(e.get("name") or "").startswith("QA_")
            ]
            _save_json(IMPORTS_FILE, {"imports": imports})
            actions.append(
                {
                    "kind": "document_imports_index",
                    "ok": True,
                    "detail": f"pruned {before - len(imports)} import index entr(y/ies)",
                }
            )
        except Exception as exc:
            actions.append({"kind": "document_imports_index", "ok": False, "error": str(exc)})

    # Planner tasks
    for f in findings:
        if f.get("category") != "planner" or not f.get("safe_to_remove"):
            continue
        tid = (f.get("ref") or {}).get("id")
        if not tid:
            continue
        try:
            from jarvis import planner_store

            fn = getattr(planner_store, "delete_task", None) or getattr(planner_store, "remove_task", None)
            if not fn:
                actions.append({"kind": "planner", "id": tid, "ok": False, "error": "no delete_task API"})
                continue
            ok = bool(fn(tid))
            actions.append({"kind": "planner", "id": tid, "ok": ok})
        except Exception as exc:
            actions.append({"kind": "planner", "id": tid, "ok": False, "error": str(exc)})

    invalidate_cache()
    verify = run_scan(force=True, trigger="post_repair")
    remaining = sum(1 for f in (verify.get("findings") or []) if f.get("safe_to_remove"))
    result = {
        "ok": remaining == 0 or all(a.get("ok") for a in actions if "ok" in a),
        "actions": actions,
        "remaining_artifacts": remaining,
        "verify_status": verify.get("status"),
        "preserved": preserved_note,
        "rollback_available": False,
        "rollback_note": "File/project deletions are not auto-rolled-back; Health rows can be restored from Health backup if needed.",
    }
    store.append_history(
        {
            "event": "repair",
            "approved": True,
            "actions": len(actions),
            "remaining": remaining,
            "verify_status": verify.get("status"),
            "ok": result["ok"],
        }
    )
    if remaining == 0:
        store.append_history({"event": "repair_verified", "ok": True, "status": "clean"})
    return result
