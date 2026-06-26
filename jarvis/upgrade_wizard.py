"""Upgrade Jarvis wizard — propose, verify in isolation, apply with snapshot, rollback."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.router import is_meta_self_question

log = logging.getLogger("jarvis")

SESSION_FILE = DATA_DIR / "upgrade_wizard.json"
SNAPSHOT_DIR = DATA_DIR / "upgrade_snapshots"

ALLOWED_PREFIXES = ("jarvis/", "tests/")
BLOCKED_PATH_PARTS = (
    "data/",
    "/data/",
    "journal",
    "memory.json",
    "chat_settings",
    "bullet_journal",
    "uploads/",
    "upgrade_snapshots",
)

RESTART_PREFIXES = (
    "jarvis/gui/",
    "jarvis/daemon.py",
    "jarvis/assistant.py",
    "jarvis/router.py",
    "main.py",
)


def requires_jarvis_restart(files: list[dict]) -> bool:
    for entry in files or []:
        rel = normalize_rel_path(entry.get("path") or "")
        if not rel or entry.get("delete"):
            continue
        if any(rel.startswith(p) or rel == p.rstrip("/") for p in RESTART_PREFIXES):
            return True
    return False

GUARDRAIL_PROMPT = (
    "You are upgrading the local Jarvis application (Python package under jarvis/ and tests/ only). "
    "NEVER modify live user data under data/ (journal, memory, chat branches, uploads). "
    "Use minimal, focused diffs. Match existing code style."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_session_data() -> dict:
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_session_data(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_session() -> dict | None:
    active = _load_session_data().get("active")
    return dict(active) if active else None


def save_session(session: dict) -> None:
    data = _load_session_data()
    data["active"] = session
    _save_session_data(data)


def clear_session() -> None:
    data = _load_session_data()
    data.pop("active", None)
    _save_session_data(data)


def normalize_rel_path(path: str) -> str:
    p = (path or "").strip().replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


def validate_proposal_paths(files: list[dict]) -> tuple[bool, list[str]]:
    """Ensure upgrade only touches jarvis/ and tests/, never live user data."""
    errors: list[str] = []
    if not files:
        return False, ["Proposal has no files."]

    for item in files:
        rel = normalize_rel_path(item.get("path") or "")
        if not rel:
            errors.append("Missing file path in proposal.")
            continue
        lower = rel.lower()
        if any(part in lower for part in BLOCKED_PATH_PARTS):
            errors.append(f"Blocked path (live user data): `{rel}`")
            continue
        if not any(lower.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            errors.append(f"Only `jarvis/` and `tests/` may change — not `{rel}`")
    return len(errors) == 0, errors


_UPGRADE_COMMAND = re.compile(
    r"^(?:please\s+)?(?:"
    r"upgrade:\s*.+|"
    r"upgrade jarvis\b|"
    r"upgrade yourself\b|"
    r"improve jarvis\b|"
    r"jarvis upgrade\b|"
    r"self-?upgrade\b"
    r")",
    re.I | re.S,
)


def is_upgrade_task(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    if _UPGRADE_COMMAND.match(text):
        return True
    if is_meta_self_question(text):
        return False
    lower = text.lower()
    return bool(
        re.search(
            r"\b(upgrade jarvis|upgrade yourself|improve jarvis|jarvis upgrade|self-?upgrade wizard)\b",
            lower,
        )
    )


def parse_upgrade_task(message: str) -> str:
    text = (message or "").strip()
    m = re.match(r"^upgrade:\s*(.+)$", text, re.I | re.S)
    if m:
        return m.group(1).strip()
    for pat in (
        r"^(?:upgrade jarvis|improve jarvis|jarvis upgrade)[:\s]+(.+)$",
        r"^upgrade yourself[:\s]+(.+)$",
        r"^self-?upgrade[:\s]+(.+)$",
    ):
        m = re.match(pat, text, re.I | re.S)
        if m:
            return m.group(1).strip()
    return re.sub(
        r"^(please\s+)?(upgrade jarvis|upgrade yourself|improve jarvis)[:\s]*",
        "",
        text,
        flags=re.I,
    ).strip() or text


def create_snapshot(files: list[dict], *, task: str = "", proposal_id: str = "") -> dict[str, Any]:
    """Copy current on-disk contents for all proposal paths before apply."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    dest = SNAPSHOT_DIR / snap_id
    dest.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    for item in files:
        rel = normalize_rel_path(item.get("path") or "")
        if not rel:
            continue
        src = PROJECT_ROOT / rel
        entry: dict[str, Any] = {"path": rel, "existed": src.is_file()}
        if src.is_file():
            snap_file = dest / rel
            snap_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, snap_file)
            entry["snapshot"] = str(snap_file.relative_to(dest))
        manifest.append(entry)

    meta = {
        "id": snap_id,
        "created": _utc_now(),
        "task": task[:500],
        "proposal_id": proposal_id,
        "version": datetime.now(timezone.utc).strftime("%Y.%m.%d-%H%M"),
        "files": manifest,
    }
    (dest / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def rollback_snapshot(snapshot_id: str | None = None) -> tuple[bool, str, list[str]]:
    """Restore files from a wizard snapshot."""
    sid = (snapshot_id or "").strip()
    session = get_session()
    if not sid and session:
        sid = session.get("snapshot_id") or ""
    if not sid:
        return False, "No upgrade snapshot to roll back.", []

    dest = SNAPSHOT_DIR / sid
    manifest_path = dest / "manifest.json"
    if not manifest_path.is_file():
        return False, f"Snapshot not found: {sid}", []

    meta = json.loads(manifest_path.read_text(encoding="utf-8"))
    restored: list[str] = []
    for entry in meta.get("files") or []:
        rel = entry.get("path") or ""
        target = PROJECT_ROOT / rel
        if entry.get("existed"):
            snap_rel = entry.get("snapshot") or rel
            snap_file = dest / snap_rel
            if not snap_file.is_file():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snap_file, target)
            restored.append(rel)
        elif target.exists():
            target.unlink()
            restored.append(f"{rel} (removed new file)")

    if session and session.get("snapshot_id") == sid:
        session["rolled_back"] = True
        session["step"] = "rolled_back"
        save_session(session)

    return True, f"Rolled back **{len(restored)}** file(s) from snapshot `{sid}`.", restored


def _ruff_check(paths: list[str]) -> tuple[bool, str]:
    py_paths = [p for p in paths if p.endswith(".py")]
    if not py_paths:
        return True, ""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", *py_paths],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return True, f"(ruff skipped: {exc})"
    if proc.returncode == 0:
        return True, "ruff: clean"
    out = (proc.stdout or proc.stderr or "").strip()[:1200]
    return False, f"ruff failed:\n```\n{out}\n```"


def _pytest_for_changes(changed_paths: list[str]) -> tuple[bool, str]:
    from jarvis.code_context import _find_test_files
    from jarvis.project_runner import run_pytest

    targets: set[str] = set()
    for rel in changed_paths:
        for t in _find_test_files(rel, PROJECT_ROOT):
            targets.add(t)

    if not targets:
        targets = {"tests/test_chat_router.py", "tests/test_trust_memory.py"}

    cmd_targets = sorted(targets)[:12]
    result = run_pytest(
        *cmd_targets,
        PROJECT_ROOT,
        timeout=300,
        extra_args=["-q", "--tb=line", "--no-header"],
    )
    combined = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    if result.returncode == 0:
        return True, f"pytest passed ({len(cmd_targets)} file(s))"
    excerpt = combined[-1500:] if len(combined) > 1500 else combined
    return False, f"pytest failed:\n```\n{excerpt}\n```"


def verify_proposal(proposal: dict, *, base: Path | None = None) -> tuple[bool, str]:
    """Syntax, ruff, and targeted pytest before apply."""
    from jarvis.coding_verify import verify_file_changes

    base = base or PROJECT_ROOT
    files = proposal.get("files") or []
    ok_paths, errors = validate_proposal_paths(files)
    if not ok_paths:
        return False, "Path guard failed:\n" + "\n".join(f"- {e}" for e in errors)

    ok, detail = verify_file_changes(files, base, mode="agent")
    parts = [detail] if detail else []

    changed = [normalize_rel_path(f.get("path") or "") for f in files if not f.get("delete")]
    ruff_ok, ruff_msg = _ruff_check(changed)
    if ruff_msg:
        parts.append(f"**{ruff_msg}**")
    if not ruff_ok:
        return False, "\n\n".join(parts)

    if not ok:
        return False, "\n\n".join(parts)

    py_ok, py_msg = _pytest_for_changes(changed)
    parts.append(f"**{py_msg}**")
    return py_ok, "\n\n".join(parts)


def wizard_status() -> dict[str, Any]:
    session = get_session()
    snapshots = []
    if SNAPSHOT_DIR.is_dir():
        for p in sorted(SNAPSHOT_DIR.iterdir(), reverse=True)[:8]:
            if p.is_dir() and (p / "manifest.json").is_file():
                try:
                    meta = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
                    snapshots.append({
                        "id": meta.get("id", p.name),
                        "created": meta.get("created"),
                        "task": meta.get("task", "")[:80],
                        "files": len(meta.get("files") or []),
                    })
                except (json.JSONDecodeError, OSError):
                    continue
    return {
        "active": session,
        "snapshots": snapshots,
        "guardrails": {
            "allowed": list(ALLOWED_PREFIXES),
            "blocked": list(BLOCKED_PATH_PARTS),
        },
    }
