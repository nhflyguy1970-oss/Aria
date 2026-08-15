"""Phase 1 authorized cleanup — only positively identified test/QA/cert artifacts.

Never deletes ambiguous Health/ACM/owner records. Jeff authorized this repair
phase; scans still never auto-delete on their own.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.integrity_product.tags import looks_like_dev_label

logger = logging.getLogger("jarvis.integrity_product.phase1")

PRESERVED: list[dict[str, Any]] = []


def _preserve(store: str, identifier: str, reason: str) -> None:
    PRESERVED.append({"store": store, "id": identifier, "reason": reason})


def _clean_health() -> dict[str, Any]:
    from jarvis.health_product.store import purge_known_smoke_records

    purged = purge_known_smoke_records(force=True)
    _preserve("health", "Vitamin D3 medication med_39bcc7df3187", "owner provenance manual/user_entered")
    _preserve("health", "dose_d79ad2f5dce9 Phase 7 residency morning dose", "ambiguous — real med, cert-flavored note")
    _preserve("health", "dose_6b1d8df5280b Phase 7 walk2 afternoon dose", "ambiguous — real med, cert-flavored note")
    _preserve("health", "dose_b7b3e3c3b1c1 residency morning", "ambiguous — real med, cert-flavored note")
    _preserve("health", "energy vitals 2026-08-06", "ambiguous cadence; legitimate data type")
    _preserve("health", "activity act_bc278fd2891d walking", "ambiguous")
    _preserve("health", "replayed vitals batches 2026-08-07", "ambiguous — do not auto-delete plausible vitals")
    _preserve("health", "check-in chk_df57c3a42785", "plausible vitals; no test token")
    _preserve("health", "encrypted backup bak_7a69c9914d45", "contains mixed history; do not auto-delete backups")
    return {"ok": True, **purged}


def _clean_planner() -> dict[str, Any]:
    from jarvis.planner_store import purge_qa_planner

    result = purge_qa_planner()
    _preserve("planner", "9e3ace063d pick up wool yarn for fly tying", "ambiguous — plausible owner task")
    return {"ok": True, **result}


def _clean_journal() -> dict[str, Any]:
    from jarvis.modules.journal import BulletJournal

    j = BulletJournal()
    result = j.purge_qa_content()
    return {"ok": True, **result}


def _clean_activity() -> dict[str, Any]:
    from jarvis.activity_inbox import reclassify_inbox

    return reclassify_inbox()


def _clean_knowledge_registry() -> dict[str, Any]:
    path = DATA_DIR / "knowledge" / "registry.json"
    if not path.is_file():
        return {"ok": True, "removed": 0}
    data = json.loads(path.read_text(encoding="utf-8"))
    sources = data.get("sources") or {}
    removed = []
    if isinstance(sources, dict):
        for key, src in list(sources.items()):
            blob = json.dumps(src, default=str) if isinstance(src, dict) else str(src)
            if looks_like_dev_label(f"{key} {blob}") or "oc-cert" in f"{key} {blob}".lower():
                removed.append(key)
                del sources[key]
        data["sources"] = sources
    if removed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "removed": removed}


def _clean_search() -> dict[str, Any]:
    path = DATA_DIR / "search_product" / "saved.json"
    if not path.is_file():
        return {"ok": True, "removed": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "unreadable"}
    removed = 0
    if isinstance(data, list):
        kept = [x for x in data if not looks_like_dev_label(json.dumps(x, default=str))]
        removed = len(data) - len(kept)
        data = kept
    elif isinstance(data, dict):
        items = data.get("searches") or data.get("items") or data.get("saved")
        if isinstance(items, list):
            kept = [x for x in items if not looks_like_dev_label(json.dumps(x, default=str))]
            removed = len(items) - len(kept)
            key = "searches" if "searches" in data else ("items" if "items" in data else "saved")
            data[key] = kept
    if removed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "removed": removed}


def _clean_dashboard_cache() -> dict[str, Any]:
    path = DATA_DIR / "dashboard_product" / "last_good_home.json"
    if path.is_file():
        path.unlink()
        return {"ok": True, "removed": True}
    return {"ok": True, "removed": False}


def _clean_flytying_history() -> dict[str, Any]:
    path = DATA_DIR / "flytying_product" / "history.jsonl"
    if not path.is_file():
        return {"ok": True, "removed": 0}
    kept = []
    removed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if looks_like_dev_label(line):
            removed += 1
            continue
        kept.append(line)
    if removed:
        path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    sessions = DATA_DIR / "flytying_product" / "sessions.json"
    sess_removed = 0
    if sessions.is_file():
        try:
            data = json.loads(sessions.read_text(encoding="utf-8"))
        except Exception:
            data = None
        if isinstance(data, dict):
            items = data.get("sessions") or data.get("items")
            if isinstance(items, list):
                new_items = []
                for s in items:
                    blob = json.dumps(s, default=str)
                    if looks_like_dev_label(blob) or '"recipe_id": "demo"' in blob or "Demo Adams" in blob:
                        sess_removed += 1
                        continue
                    new_items.append(s)
                key = "sessions" if "sessions" in data else "items"
                data[key] = new_items
                sessions.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "history_removed": removed, "sessions_removed": sess_removed}


def _clean_files_via_scan() -> dict[str, Any]:
    from jarvis.integrity_product.remediate import apply_safe_remediations
    from jarvis.integrity_product.scanner import run_scan

    scan = run_scan(force=True, trigger="phase1_cleanup")
    findings = [f for f in (scan.get("findings") or []) if f.get("safe_to_remove")]
    return apply_safe_remediations(findings)


def _iter_gallery_entries(data: Any) -> list[tuple[Any, dict[str, Any]]]:
    if isinstance(data, list):
        return [(i, it) for i, it in enumerate(data) if isinstance(it, dict)]
    if isinstance(data, dict):
        items = data.get("items") or data.get("images")
        if isinstance(items, list):
            return [(i, it) for i, it in enumerate(items) if isinstance(it, dict)]
        return [(k, v) for k, v in data.items() if isinstance(v, dict)]
    return []


def _retag_gallery() -> dict[str, Any]:
    path = DATA_DIR / "gallery_product" / "metadata.json"
    if not path.is_file():
        return {"ok": True, "retagged": 0, "removed_test_images": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "unreadable"}
    retagged = 0
    removed_keys: list[Any] = []
    removed_files: list[str] = []
    for key, it in _iter_gallery_entries(data):
        blob = json.dumps(it, default=str)
        prompt = str(it.get("prompt") or "")
        proj = str(it.get("project") or "")
        if looks_like_dev_label(prompt):
            removed_keys.append(key)
            name = str(it.get("name") or key)
            for folder in (
                DATA_DIR / "generated",
                DATA_DIR / "gallery_product" / "images",
                DATA_DIR / "gallery",
            ):
                candidate = folder / name
                if candidate.is_file():
                    candidate.unlink()
                    removed_files.append(str(candidate.relative_to(DATA_DIR)))
            continue
        if looks_like_dev_label(proj) or "oc-cert" in proj.lower():
            it["project"] = ""
            it["qa_project_cleared"] = proj
            retagged += 1
    if isinstance(data, list):
        data = [it for i, it in enumerate(data) if i not in removed_keys]
    elif isinstance(data, dict) and isinstance(data.get("items"), list):
        data["items"] = [it for i, it in enumerate(data["items"]) if i not in removed_keys]
    elif isinstance(data, dict) and isinstance(data.get("images"), list):
        data["images"] = [it for i, it in enumerate(data["images"]) if i not in removed_keys]
    elif isinstance(data, dict):
        for k in removed_keys:
            data.pop(k, None)
    if retagged or removed_keys:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "retagged": retagged,
        "removed_test_images": len(removed_keys),
        "removed_files": removed_files,
    }


def _clean_search_sessions() -> dict[str, Any]:
    from jarvis.search_product.history import is_qa_search_query

    path = DATA_DIR / "search_product" / "sessions.json"
    if not path.is_file():
        return {"ok": True, "removed": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "unreadable"}
    items = data.get("sessions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return {"ok": True, "removed": 0}
    kept = [s for s in items if isinstance(s, dict) and not is_qa_search_query(str(s.get("query") or ""))]
    removed = len(items) - len(kept)
    if removed:
        payload = {"sessions": kept} if isinstance(data, dict) else kept
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "removed": removed}


def _clean_document_imports() -> dict[str, Any]:
    path = DATA_DIR / "document_imports.json"
    if not path.is_file():
        return {"ok": True, "removed": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "error": "unreadable"}
    items = data.get("imports") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return {"ok": True, "removed": 0}
    kept = []
    removed = []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "")
        p = str(it.get("path") or "")
        if looks_like_dev_label(f"{name} {p}"):
            removed.append(name or p)
            continue
        kept.append(it)
    if removed:
        if isinstance(data, dict):
            data["imports"] = kept
            payload = data
        else:
            payload = kept
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"ok": True, "removed": removed}


def _clean_browser_test_screenshots() -> dict[str, Any]:
    folder = DATA_DIR / "browser_screenshots"
    if not folder.is_dir():
        return {"ok": True, "removed": 0}
    removed = []
    for path in folder.iterdir():
        if not path.is_file():
            continue
        if re.match(r"^(e2e|nav|test)-\d+", path.name, re.I):
            path.unlink()
            removed.append(path.name)
    return {"ok": True, "removed": removed}


def run_phase1_cleanup() -> dict[str, Any]:
    PRESERVED.clear()
    _preserve("acm", "ARIA-REPAIR-MEM-* / ARIA-FINAL-MEMORY-* / oc-cert-project / wf_probe tokens", "ACM is protected — designed forget requires Jeff approval")
    _preserve("health", "encrypted backup bak_7a69c9914d45", "contains mixed history; do not auto-delete backups")
    _preserve("documents", "hf qEEvzFck… filename in documents/imports", "possible secret — Jeff review")
    _preserve("coding", "Write a long essay about rivers…", "ambiguous stop-button test")
    _preserve("gallery", "image_20260807_095030.png and image_20260807_112111.png", "retag only — images plausibly owner; metadata tag is test")
    _preserve("flytying", "prototype-anchor-nymph-924c6f3e7e8a.md", "ambiguous recipe filename; do not auto-delete")
    _preserve("planner", "9e3ace063d pick up wool yarn for fly tying", "ambiguous — plausible owner task")

    actions = {
        "health": _clean_health(),
        "planner": _clean_planner(),
        "journal": _clean_journal(),
        "activity": _clean_activity(),
        "knowledge": _clean_knowledge_registry(),
        "search": _clean_search(),
        "dashboard_cache": _clean_dashboard_cache(),
        "flytying": _clean_flytying_history(),
        "gallery_retag": _retag_gallery(),
        "search_sessions": _clean_search_sessions(),
        "document_imports": _clean_document_imports(),
        "browser_screenshots": _clean_browser_test_screenshots(),
        "files": _clean_files_via_scan(),
    }
    from jarvis.integrity_product.scanner import invalidate_cache, run_scan

    invalidate_cache()
    verify = run_scan(force=True, trigger="phase1_verify")
    return {
        "ok": True,
        "actions": actions,
        "preserved": PRESERVED,
        "verify": {
            "status": verify.get("status"),
            "score": (verify.get("score") or {}).get("overall"),
            "findings": len(verify.get("findings") or []),
            "by_category": (verify.get("counts") or {}).get("by_category"),
        },
    }
