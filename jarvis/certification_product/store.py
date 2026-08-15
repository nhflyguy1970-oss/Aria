"""Persistent evidence store under data/certification/."""

from __future__ import annotations

import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

CERT_ROOT = DATA_DIR / "certification"
RUNS_DIR = CERT_ROOT / "runs"
INDEX_FILE = CERT_ROOT / "index.json"
LATEST_FILE = CERT_ROOT / "latest_run.json"
UNVERIFIED_READY_BLOCKER = (
    "READY_TO_SHIP invalidated: missing image_lifecycle generated-asset evidence files"
)


def _ensure() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    tmp.replace(path)


def _image_lifecycle_evidence_present(run_id: str, manifest: dict[str, Any]) -> bool:
    feature = (manifest.get("features") or {}).get("image_lifecycle") or {}
    if feature.get("status") != "PASS":
        return False
    screenshots = run_dir(run_id) / "screenshots"
    marker = screenshots / "IMAGE_FILE_EVIDENCE.txt"
    if not marker.is_file() or marker.stat().st_size < 1:
        return False
    image_exts = {".png", ".jpg", ".jpeg", ".webp"}
    return any(
        p.is_file() and p.suffix.lower() in image_exts and p.stat().st_size > 0
        for p in screenshots.iterdir()
    )


def _invalidate_run_if_needed(run_id: str) -> tuple[dict[str, Any] | None, bool]:
    path = RUNS_DIR / run_id / "manifest.json"
    man = _read_json(path, None)
    if not isinstance(man, dict):
        return None, False
    if man.get("gate") != "READY_TO_SHIP":
        return man, False
    if _image_lifecycle_evidence_present(run_id, man):
        return man, False
    blockers = list(man.get("blockers") or [])
    if UNVERIFIED_READY_BLOCKER not in blockers:
        blockers.append(UNVERIFIED_READY_BLOCKER)
    man.update(
        {
            "gate": "DO_NOT_SHIP",
            "blockers": blockers,
            "invalidated_gate": "READY_TO_SHIP",
            "invalidated_reason": UNVERIFIED_READY_BLOCKER,
            "invalidated_at": time.time(),
        }
    )
    _write_json(path, man)
    return man, True


def invalidate_unverified_ready_runs() -> dict[str, Any]:
    _ensure()
    idx = _read_json(INDEX_FILE, {"runs": []})
    run_ids = {str(row.get("id")) for row in idx.get("runs") or [] if row.get("id")}
    latest = _read_json(LATEST_FILE, None)
    if isinstance(latest, dict) and latest.get("id"):
        run_ids.add(str(latest["id"]))
    for path in RUNS_DIR.glob("*/manifest.json"):
        run_ids.add(path.parent.name)

    invalidated: list[str] = []
    manifests: dict[str, dict[str, Any]] = {}
    for run_id in sorted(run_ids):
        man, changed = _invalidate_run_if_needed(run_id)
        if man:
            manifests[run_id] = man
        if changed:
            invalidated.append(run_id)

    changed_index = False
    for row in idx.get("runs") or []:
        run_id = str(row.get("id") or "")
        man = manifests.get(run_id)
        if not man:
            continue
        if row.get("gate") != man.get("gate") or row.get("status") != man.get("status"):
            row["gate"] = man.get("gate")
            row["status"] = man.get("status")
            row["finished_at"] = man.get("finished_at")
            changed_index = True
    if changed_index:
        _write_json(INDEX_FILE, idx)

    latest_id = str(latest.get("id")) if isinstance(latest, dict) and latest.get("id") else ""
    if latest_id and latest_id in manifests:
        man = manifests[latest_id]
        if latest.get("gate") != man.get("gate") or latest.get("status") != man.get("status"):
            _write_json(LATEST_FILE, {"id": latest_id, "gate": man.get("gate"), "status": man.get("status")})

    return {"ok": True, "invalidated": invalidated, "count": len(invalidated)}


def list_runs(*, limit: int = 40) -> list[dict[str, Any]]:
    _ensure()
    invalidate_unverified_ready_runs()
    idx = _read_json(INDEX_FILE, {"runs": []})
    runs = idx.get("runs") or []
    return list(runs)[:limit]


def get_run(run_id: str) -> dict[str, Any] | None:
    data, _changed = _invalidate_run_if_needed(run_id)
    return data


def latest_run() -> dict[str, Any] | None:
    invalidate_unverified_ready_runs()
    data = _read_json(LATEST_FILE, None)
    if isinstance(data, dict) and data.get("id"):
        return get_run(str(data["id"])) or data
    runs = list_runs(limit=1)
    return get_run(runs[0]["id"]) if runs else None


def create_run(*, label: str = "", mode: str = "evidence") -> dict[str, Any]:
    _ensure()
    run_id = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    root = RUNS_DIR / run_id
    for sub in ("assertions", "api", "screenshots", "logs", "files", "replay", "coverage"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": run_id,
        "label": label or f"Certification {run_id}",
        "mode": mode,
        "schema_version": 1,
        "started_at": time.time(),
        "started_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "finished_at": None,
        "status": "running",
        "gate": "PENDING",
        "features": {},
        "counts": {
            "assertions": 0,
            "pass": 0,
            "fail": 0,
            "api_calls": 0,
            "screenshots": 0,
            "files_verified": 0,
        },
        "coverage": {},
        "blockers": [],
        "evidence_root": str(root),
    }
    _write_json(root / "manifest.json", manifest)
    idx = _read_json(INDEX_FILE, {"runs": []})
    runs = idx.get("runs") or []
    runs.insert(0, {"id": run_id, "label": manifest["label"], "started_at": manifest["started_at"], "status": "running"})
    idx["runs"] = runs[:100]
    _write_json(INDEX_FILE, idx)
    _write_json(LATEST_FILE, {"id": run_id})
    return manifest


def run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


def append_jsonl(run_id: str, relative: str, row: dict[str, Any]) -> Path:
    path = run_dir(run_id) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return path


def write_text(run_id: str, relative: str, text: str) -> Path:
    path = run_dir(run_id) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_bytes(run_id: str, relative: str, data: bytes) -> Path:
    path = run_dir(run_id) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def update_manifest(run_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    man = get_run(run_id) or {}
    man.update(patch)
    _write_json(run_dir(run_id) / "manifest.json", man)
    idx = _read_json(INDEX_FILE, {"runs": []})
    for row in idx.get("runs") or []:
        if row.get("id") == run_id:
            row["status"] = man.get("status")
            row["gate"] = man.get("gate")
            row["finished_at"] = man.get("finished_at")
            break
    _write_json(INDEX_FILE, idx)
    _write_json(LATEST_FILE, {"id": run_id, "gate": man.get("gate"), "status": man.get("status")})
    return man


def list_assertions(run_id: str) -> list[dict[str, Any]]:
    path = run_dir(run_id) / "assertions" / "assertions.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def list_api_calls(run_id: str) -> list[dict[str, Any]]:
    path = run_dir(run_id) / "api" / "calls.jsonl"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def list_evidence_files(run_id: str) -> list[dict[str, Any]]:
    root = run_dir(run_id)
    if not root.is_dir():
        return []
    files = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            files.append(
                {
                    "path": str(p.relative_to(root)),
                    "bytes": p.stat().st_size,
                    "name": p.name,
                }
            )
    return files


def ingest_legacy_probes() -> dict[str, Any]:
    """Index prior probe JSON files as historical evidence references."""
    _ensure()
    found = []
    for p in sorted(CERT_ROOT.glob("*.json")):
        if p.name in ("index.json", "latest_run.json"):
            continue
        found.append({"name": p.name, "path": str(p), "bytes": p.stat().st_size})
    _write_json(CERT_ROOT / "legacy_probes.json", {"probes": found, "ts": time.time()})
    return {"ok": True, "count": len(found), "probes": found}


def package_zip(run_id: str) -> Path | None:
    root = run_dir(run_id)
    if not root.is_dir():
        return None
    out = CERT_ROOT / f"evidence_package_{run_id}"
    archive = shutil.make_archive(str(out), "zip", root_dir=str(root))
    return Path(archive)
