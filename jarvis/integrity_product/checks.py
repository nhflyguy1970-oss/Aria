"""Lightweight Production Integrity checks — read-only, never delete."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.integrity_product.tags import looks_like_dev_label

# Paths under DATA_DIR that are known development leftovers (safe to recommend removal).
_KNOWN_DEV_PATHS = (
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
)

# Audio filenames that are clearly smoke/cert/QA probes (basename match).
_QA_AUDIO_RE = re.compile(
    r"^(QA_|Voice_smoke_|Ship_certification_|ARIA_audit_test|Hello_ARIA_voice_test|"
    r"Stored_via_ACM_ARIA-EXC|Stored_via_ACM_exact_acceptance_token)",
    re.I,
)

_QA_DOC_NAME_RE = re.compile(r"(QA_|Smoke_|Cert_|Demo_|placeholder_|fnaccept)", re.I)

_HEALTH_SMOKE_NAMES = frozenset(
    {
        "metformin",  # only when confirmed=0 + empty provenance (see check)
        "vitamin d",
    }
)

_PLANNER_TITLE_RE = re.compile(
    r"^(qa\b|smoke\b|cert\b|demo\b|test\s+task|lorem|placeholder|example\s+task)",
    re.I,
)


def _finding(
    *,
    category: str,
    artifact_type: str,
    title: str,
    path: str = "",
    evidence: list[str] | None = None,
    confidence: float = 0.95,
    safe_to_remove: bool = True,
    remediation: str = "",
    ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "category": category,
        "artifact_type": artifact_type,
        "title": title,
        "path": path,
        "evidence": evidence or [],
        "confidence": round(max(0.05, min(0.99, confidence)), 3),
        "safe_to_remove": bool(safe_to_remove),
        "remediation": remediation or "Remove development artifact after Jeff approves.",
        "ref": ref or {},
        "uncertain": False,
    }


def check_qa_projects() -> list[dict[str, Any]]:
    from jarvis.project_registry import is_qa_artifact, list_projects

    out: list[dict[str, Any]] = []
    try:
        projects = list_projects(include_archived=True, include_qa=True)
    except Exception as exc:
        return [
            _finding(
                category="projects",
                artifact_type="qa",
                title="Could not scan projects",
                evidence=[str(exc)],
                confidence=0.4,
                safe_to_remove=False,
            )
        ]
    for meta in projects:
        if not is_qa_artifact(meta):
            continue
        out.append(
            _finding(
                category="projects",
                artifact_type=str(meta.get("origin") or meta.get("artifact_type") or "qa"),
                title=f"QA/cert project: {meta.get('title') or meta.get('slug')}",
                path=str((meta.get("paths") or {}).get("root") or meta.get("slug") or ""),
                evidence=[
                    f"slug={meta.get('slug')}",
                    f"origin={meta.get('origin')}",
                    f"qa_artifact={meta.get('qa_artifact')}",
                    f"archived={meta.get('archived')}",
                    f"description={(meta.get('description') or '')[:80]}",
                ],
                confidence=0.99 if meta.get("qa_artifact") else 0.95,
                remediation="Delete QA project workspace and journal entry (preserve unrelated projects).",
                ref={"slug": meta.get("slug")},
            )
        )
    return out


def check_health_smoke() -> list[dict[str, Any]]:
    """Flag only clear smoke/probe PHR rows — never Jeff's confirmed records."""
    out: list[dict[str, Any]] = []
    try:
        from jarvis.health_product import store
        from jarvis.health_product.store import _KNOWN_SMOKE_ROWS
    except Exception:
        return out

    # Exact known smoke IDs still present
    for table, item_id in _KNOWN_SMOKE_ROWS:
        try:
            row = store.get_by_id(table, item_id) if hasattr(store, "get_by_id") else None
            if not row:
                # fall back to raw
                conn = store.connect()
                try:
                    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
                finally:
                    conn.close()
            if row:
                out.append(
                    _finding(
                        category="health",
                        artifact_type="smoke",
                        title=f"Known smoke Health row: {table}/{item_id}",
                        path=str(store.DB_PATH),
                        evidence=[f"table={table}", f"id={item_id}", "listed in _KNOWN_SMOKE_ROWS"],
                        confidence=0.99,
                        remediation="Remove known smoke PHR row only (force purge of allow-listed IDs).",
                        ref={"table": table, "id": item_id},
                    )
                )
        except Exception:
            continue

    # Heuristic: unconfirmed meds/supplements with empty provenance matching smoke names
    try:
        for table in ("medications", "supplements"):
            rows = store.list_table(table, limit=200) if hasattr(store, "list_table") else []
            for row in rows or []:
                name = str(row.get("name") or "").strip().lower()
                confirmed = int(row.get("confirmed") or 0)
                provenance = row.get("provenance")
                if confirmed:
                    continue
                if name not in _HEALTH_SMOKE_NAMES:
                    continue
                if provenance:
                    continue
                rid = row.get("id")
                if any(f.get("ref", {}).get("id") == rid for f in out):
                    continue
                out.append(
                    _finding(
                        category="health",
                        artifact_type="smoke",
                        title=f"Unconfirmed smoke-like Health {table}: {row.get('name')}",
                        path=str(store.DB_PATH),
                        evidence=[
                            f"id={rid}",
                            "confirmed=0",
                            "provenance empty",
                            f"name matches known smoke fixture ({name})",
                        ],
                        confidence=0.92,
                        remediation="Remove unconfirmed smoke-like PHR row after Jeff confirms it is not real.",
                        ref={"table": table, "id": rid},
                    )
                )
    except Exception:
        pass

    # Scan dose logs / check-ins / events for harness tokens. Never flag ambiguous owner values.
    try:
        conn = store.connect()
        try:
            for table, col in (("dose_logs", "name"), ("dose_logs", "notes"), ("events", "detail")):
                try:
                    extra = ", name" if table == "dose_logs" else ""
                    rows = conn.execute(f"SELECT id, {col} AS val{extra} FROM {table}").fetchall()
                except Exception:
                    continue
                for row in rows or []:
                    val = str(row["val"] or "")
                    residency_note = bool(re.search(r"residency|phase\s*7", val, re.I))
                    if not looks_like_dev_label(val) and not (
                        table == "dose_logs" and col == "notes" and residency_note
                    ):
                        continue
                    rid = row["id"]
                    if any(f.get("ref", {}).get("id") == rid for f in out):
                        continue
                    name = str(row["name"] if "name" in row.keys() else "")
                    notes_only = table == "dose_logs" and col == "notes" and name and not looks_like_dev_label(name)
                    finding = _finding(
                        category="health",
                        artifact_type="certification",
                        title=f"{'Ambiguous' if notes_only else 'Test'} Health {table}: {val[:80]}",
                        path=str(store.DB_PATH),
                        evidence=[f"id={rid}", f"{col}={val[:120]}"] + ([f"name={name}"] if name else []),
                        confidence=0.6 if notes_only else 0.97,
                        safe_to_remove=not notes_only,
                        remediation=(
                            "Preserve — real medication with certification-flavored note; Jeff must decide."
                            if notes_only
                            else "Remove positively identified test PHR row."
                        ),
                        ref={"table": table, "id": rid},
                    )
                    if notes_only:
                        finding["uncertain"] = True
                    out.append(finding)
            try:
                checks = conn.execute("SELECT id, payload FROM checkins").fetchall()
            except Exception:
                checks = []
            for row in checks or []:
                payload = str(row["payload"] or "")
                if not looks_like_dev_label(payload):
                    continue
                rid = row["id"]
                if any(f.get("ref", {}).get("id") == rid for f in out):
                    continue
                out.append(
                    _finding(
                        category="health",
                        artifact_type="certification",
                        title=f"Test Health check-in: {rid}",
                        path=str(store.DB_PATH),
                        evidence=[f"id={rid}", payload[:160]],
                        confidence=0.97,
                        remediation="Remove positively identified test check-in.",
                        ref={"table": "checkins", "id": rid},
                    )
                )
            try:
                baks = conn.execute("SELECT id, notes, kind FROM backups").fetchall()
            except Exception:
                baks = []
            for row in baks or []:
                notes = str(row["notes"] or "")
                if not (looks_like_dev_label(notes) or re.search(r"residency", notes, re.I)):
                    continue
                rid = row["id"]
                finding = _finding(
                    category="health",
                    artifact_type="certification",
                    title=f"Ambiguous Health backup: {rid}",
                    path=str(store.DB_PATH),
                    evidence=[f"id={rid}", f"kind={row['kind']}", notes[:160]],
                    confidence=0.55,
                    safe_to_remove=False,
                    remediation="Preserve encrypted Health backup — Jeff must decide. Never auto-delete backups.",
                    ref={"table": "backups", "id": rid},
                )
                finding["uncertain"] = True
                out.append(finding)
        finally:
            conn.close()
    except Exception:
        pass
    return out


def check_known_dev_paths() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rel in _KNOWN_DEV_PATHS:
        path = DATA_DIR / rel
        if path.exists():
            out.append(
                _finding(
                    category="files",
                    artifact_type="temporary" if "qa_" in rel else "certification" if "cert" in rel else "demo",
                    title=f"Development leftover path: {rel}",
                    path=str(path),
                    evidence=[f"exists under DATA_DIR/{rel}", f"is_dir={path.is_dir()}"],
                    confidence=0.98,
                    remediation=f"Remove {rel} (known QA/cert/demo leftover).",
                    ref={"rel": rel},
                )
            )
    return out


def check_planner_examples() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        from jarvis.planner_store import list_tasks

        tasks = list_tasks(include_completed=True, include_qa=True) or []
    except Exception:
        tasks = []
    for task in tasks:
        title = str(task.get("title") or task.get("text") or "")
        if not (_PLANNER_TITLE_RE.search(title) or looks_like_dev_label(title)):
            # Also respect explicit tags
            tags = task.get("tags") or task.get("labels") or []
            origin = str(task.get("origin") or task.get("artifact_type") or "").lower()
            if origin not in ("qa", "smoke", "demo", "certification", "test") and not (
                isinstance(tags, list) and any(str(t).lower() in ("qa", "smoke", "demo") for t in tags)
            ):
                if not task.get("qa_artifact"):
                    continue
        out.append(
            _finding(
                category="planner",
                artifact_type=str(task.get("origin") or "qa"),
                title=f"Example/QA planner task: {title[:80]}",
                evidence=[f"id={task.get('id')}", f"title={title[:120]}"],
                confidence=0.9 if task.get("qa_artifact") else 0.85,
                remediation="Remove QA/example planner task only.",
                ref={"id": task.get("id")},
            )
        )
    try:
        import sqlite3

        from jarvis.planner_store import DB_PATH

        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, title FROM events WHERE COALESCE(deleted, 0) = 0"
            ).fetchall()
        for row in rows:
            title = str(row["title"] or "")
            if not looks_like_dev_label(title):
                continue
            out.append(
                _finding(
                    category="planner",
                    artifact_type="qa",
                    title=f"Example/QA planner event: {title[:80]}",
                    evidence=[f"id={row['id']}", f"title={title[:120]}"],
                    confidence=0.9,
                    remediation="Remove QA/example planner event only.",
                    ref={"id": row["id"], "kind": "event"},
                )
            )
    except Exception:
        pass
    return out


def check_demo_workflows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rel, slug in (
        ("workflows/demo-skill-check.json", "demo-skill-check"),
        ("automation_product/learned_workflows/demo-skill-check.json", "demo-skill-check"),
        ("automation_product/workflow_dags/retrydemo.json", "retrydemo"),
    ):
        path = DATA_DIR / rel
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            name = str((data or {}).get("name") or path.name)
        except Exception:
            name = path.name
        out.append(
            _finding(
                category="workflows",
                artifact_type="demo",
                title=f"Demo/QA workflow: {name}",
                path=str(path),
                evidence=[f"rel={rel}", f"slug={slug}"],
                confidence=0.97,
                remediation=f"Remove {rel}.",
                ref={"rel": rel, "slug": slug},
            )
        )
    return out


def check_qa_documents() -> list[dict[str, Any]]:
    """Documents library must not surface QA/smoke import leftovers."""
    out: list[dict[str, Any]] = []
    imports_dir = DATA_DIR / "documents" / "imports"
    if imports_dir.is_dir():
        for path in imports_dir.iterdir():
            if not path.is_file():
                continue
            if not _QA_DOC_NAME_RE.search(path.name) and not looks_like_dev_label(path.name):
                # Content sniff for tiny probe files
                try:
                    if path.stat().st_size < 4096:
                        text = path.read_text(encoding="utf-8", errors="ignore").lower()
                        if "local fs test" in text or "qa resume content" in text:
                            pass
                        else:
                            continue
                    else:
                        continue
                except Exception:
                    continue
            rel = f"documents/imports/{path.name}"
            out.append(
                _finding(
                    category="documents",
                    artifact_type="qa",
                    title=f"QA document in library: {path.name}",
                    path=str(path),
                    evidence=[f"rel={rel}", "appears in Documents product listing"],
                    confidence=0.98,
                    remediation="Remove QA document import; leave Jeff's real documents untouched.",
                    ref={"rel": rel},
                )
            )
    for folder, rel_prefix in (
        (DATA_DIR / "documents" / "uploads", "documents/uploads"),
        (DATA_DIR / "uploads", "uploads"),
    ):
        if not folder.is_dir():
            continue
        for path in folder.iterdir():
            if not path.is_file():
                continue
            if not (_QA_DOC_NAME_RE.search(path.name) or looks_like_dev_label(path.name) or path.name.startswith("test")):
                continue
            rel = f"{rel_prefix}/{path.name}"
            out.append(
                _finding(
                    category="documents",
                    artifact_type="qa",
                    title=f"QA upload: {path.name}",
                    path=str(path),
                    evidence=[f"rel={rel}"],
                    confidence=0.95,
                    remediation="Remove QA upload; leave owner files untouched.",
                    ref={"rel": rel},
                )
            )
    # Also flag known paths even if already listed via _KNOWN_DEV_PATHS (dedupe by path later)
    return out


def check_qa_audio() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    audio_dir = DATA_DIR / "audio" / "generated"
    if not audio_dir.is_dir():
        return out
    for path in audio_dir.iterdir():
        if not path.is_file():
            continue
        if not (_QA_AUDIO_RE.search(path.name) or looks_like_dev_label(path.name)):
            continue
        rel = f"audio/generated/{path.name}"
        out.append(
            _finding(
                category="files",
                artifact_type="smoke",
                title=f"QA/smoke audio artifact: {path.name}",
                path=str(path),
                evidence=[f"rel={rel}"],
                confidence=0.96,
                remediation="Remove smoke/cert voice probe audio.",
                ref={"rel": rel},
            )
        )
    return out


def check_journal_smoke() -> list[dict[str, Any]]:
    """Flag journal project files and live bullets that are QA/cert residue."""
    out: list[dict[str, Any]] = []
    root = DATA_DIR / "journal" / "projects"
    if root.is_dir():
        for path in root.glob("*.json"):
            if path.name == "index.json":
                continue
            stem = path.stem.lower()
            if re.match(r"^(qa-|cert-proj-|onetruth-proj-|smoke-)", stem) or looks_like_dev_label(stem):
                out.append(
                    _finding(
                        category="journal",
                        artifact_type="qa",
                        title=f"QA journal project file: {path.name}",
                        path=str(path),
                        evidence=[f"stem={stem}"],
                        confidence=0.96,
                        remediation="Remove QA journal project file (user journals untouched).",
                        ref={"rel": f"journal/projects/{path.name}"},
                    )
                )
    bujo = DATA_DIR / "journal" / "bullet_journal.json"
    if bujo.is_file():
        try:
            data = json.loads(bujo.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        daily = (data or {}).get("daily_log") or {}
        if isinstance(daily, dict):
            for day, page in daily.items():
                for b in (page or {}).get("bullets") or []:
                    if not isinstance(b, dict):
                        continue
                    content = str(b.get("content") or "")
                    if not looks_like_dev_label(content):
                        continue
                    out.append(
                        _finding(
                            category="journal",
                            artifact_type="qa",
                            title=f"QA journal bullet: {content[:80]}",
                            path=str(bujo),
                            evidence=[f"day={day}", f"id={b.get('id')}", content[:120]],
                            confidence=0.95,
                            remediation="Remove QA journal bullet (owner bullets untouched).",
                            ref={"id": b.get("id"), "day": day},
                        )
                    )
    return out


def check_knowledge_orphans() -> list[dict[str, Any]]:
    """Registry sources pointing at deleted QA project folders."""
    out: list[dict[str, Any]] = []
    path = DATA_DIR / "knowledge" / "registry.json"
    if not path.is_file():
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return out
    sources = (data or {}).get("sources") or {}
    if not isinstance(sources, dict):
        return out
    for key, src in sources.items():
        if not isinstance(src, dict):
            continue
        label = str(src.get("label") or "")
        loc = str(src.get("location") or src.get("path") or "")
        ns = str(src.get("namespace") or "")
        blob = f"{label} {loc} {ns} {key}"
        if not looks_like_dev_label(blob) and "oc-cert" not in blob.lower():
            continue
        out.append(
            _finding(
                category="projects",
                artifact_type="certification",
                title=f"Orphan QA knowledge source: {label or key}",
                path=str(path),
                evidence=[f"key={key}", f"location={loc}", f"namespace={ns}"],
                confidence=0.96,
                remediation="Remove orphan QA knowledge registry entry.",
                ref={"key": key},
            )
        )
    return out


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for f in findings:
        key = str(f.get("path") or "") + "|" + str((f.get("ref") or {}).get("rel") or "") + "|" + str(f.get("title") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


ALL_CHECKS = (
    check_qa_projects,
    check_health_smoke,
    check_known_dev_paths,
    check_demo_workflows,
    check_qa_documents,
    check_qa_audio,
    check_planner_examples,
    check_journal_smoke,
    check_knowledge_orphans,
)
