"""Platform migration cutover — safe authority switch with rollback."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.platform_cutover")

_CUTOVER_FILE = DATA_DIR / "platform" / "cutover.json"
_APPLICATION_ID = "aria"
_MODES = frozenset({"legacy", "dual_write", "platform_authoritative"})


def _default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "mode": "dual_write",
        "backfill_completed_at": "",
        "enabled_at": "",
        "rollback_count": 0,
        "last_verification": {},
    }


def _load() -> dict[str, Any]:
    if not _CUTOVER_FILE.is_file():
        return _default_state()
    try:
        data = json.loads(_CUTOVER_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**_default_state(), **data}
    except (json.JSONDecodeError, OSError):
        pass
    return _default_state()


def _save(data: dict[str, Any]) -> None:
    _CUTOVER_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CUTOVER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def current_mode() -> str:
    if os.getenv("JARVIS_PLATFORM_DATA_AUTHORITATIVE", "").lower() in ("1", "true", "yes"):
        return "platform_authoritative"
    mode = str(_load().get("mode") or "dual_write")
    return mode if mode in _MODES else "dual_write"


def platform_data_authoritative() -> bool:
    return current_mode() == "platform_authoritative"


def status() -> dict[str, Any]:
    state = _load()
    verification = verify_readiness()
    return {
        "ok": True,
        "mode": current_mode(),
        "state": state,
        "verification": verification,
        "legacy_data_dir": os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR)),
        "platform_data_dir": os.getenv("JARVIS_PLATFORM_DATA_DIR", ""),
        "effective_data_dir": os.getenv("JARVIS_DATA_DIR", str(DATA_DIR)),
        "platform_attached": os.getenv("JARVIS_PLATFORM_ATTACHED") == "1",
        "memory_attached": os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1",
    }


def verify_readiness() -> dict[str, Any]:
    """Check whether platform cutover is safe."""
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        blockers.append("platform attachment disabled")

    if os.getenv("JARVIS_PLATFORM_ATTACHED") != "1":
        blockers.append("platform infrastructure not attached")

    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") != "1":
        warnings.append("platform memory adapter not attached")

    metrics: dict[str, Any] = {}
    try:
        from aiplatform.applications.memory.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        failures = int(metrics.get("verification_failures") or 0)
        if failures > 0:
            blockers.append(f"memory verification failures: {failures}")
    except Exception as exc:
        warnings.append(f"memory metrics unavailable: {exc}")

    legacy_path = Path(os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR)))
    if not legacy_path.is_dir():
        blockers.append(f"legacy data dir missing: {legacy_path}")

    platform_path = os.getenv("JARVIS_PLATFORM_DATA_DIR", "")
    if platform_path and not Path(platform_path).is_dir():
        warnings.append(f"platform data dir not created yet: {platform_path}")

    ready = not blockers
    result = {
        "ready": ready,
        "blockers": blockers,
        "warnings": warnings,
        "metrics": metrics,
        "ts": time.time(),
    }
    state = _load()
    state["last_verification"] = result
    _save(state)
    return result


def backfill_memory(*, dry_run: bool = False) -> dict[str, Any]:
    """Mirror existing legacy memory entries to platform storage."""
    if not os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1":
        return {"ok": False, "error": "platform memory not attached"}

    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        if not hasattr(mem, "list_entries"):
            return {"ok": False, "error": "memory store has no list_entries"}
        entries = mem.list_entries()
        if dry_run:
            return {"ok": True, "dry_run": True, "entries": len(entries)}

        from aiplatform.applications.memory.bridge import mirror_add

        mirrored = 0
        errors = 0
        for entry in entries:
            try:
                mirror_add(_APPLICATION_ID, entry)
                mirrored += 1
            except Exception as exc:
                errors += 1
                logger.debug("backfill entry failed: %s", exc)

        state = _load()
        state["backfill_completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state["backfill_stats"] = {"mirrored": mirrored, "errors": errors, "total": len(entries)}
        _save(state)
        return {"ok": errors == 0, "mirrored": mirrored, "errors": errors, "total": len(entries)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def enable_platform_authoritative(*, force_backfill: bool = False) -> dict[str, Any]:
    """Switch to platform-authoritative reads. Legacy data is never deleted."""
    verification = verify_readiness()
    if not verification.get("ready"):
        return {
            "ok": False,
            "error": "cutover blocked",
            "verification": verification,
        }

    state = _load()
    if force_backfill or not state.get("backfill_completed_at"):
        backfill = backfill_memory()
        if not backfill.get("ok"):
            return {"ok": False, "error": "backfill failed", "backfill": backfill}

    os.environ["JARVIS_PLATFORM_DATA_AUTHORITATIVE"] = "1"
    platform_dir = os.getenv("JARVIS_PLATFORM_DATA_DIR", "")
    if platform_dir:
        os.environ["JARVIS_DATA_DIR"] = platform_dir

    state["mode"] = "platform_authoritative"
    state["enabled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(state)
    logger.info("Platform data cutover enabled — platform authoritative, legacy preserved")
    return {
        "ok": True,
        "mode": "platform_authoritative",
        "message": "Platform is now authoritative. Legacy data preserved.",
    }


def rollback_to_legacy() -> dict[str, Any]:
    """Revert to legacy-authoritative mode without data loss."""
    legacy_dir = os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR))
    os.environ.pop("JARVIS_PLATFORM_DATA_AUTHORITATIVE", None)
    os.environ["JARVIS_DATA_DIR"] = legacy_dir

    state = _load()
    state["mode"] = "dual_write"
    state["rollback_count"] = int(state.get("rollback_count") or 0) + 1
    state["last_rollback_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _save(state)
    logger.info("Rolled back to legacy-authoritative mode")
    return {
        "ok": True,
        "mode": "dual_write",
        "message": "Rolled back to legacy-authoritative mode. Platform mirror continues on writes.",
    }


def format_status_markdown() -> str:
    snap = status()
    ver = snap.get("verification") or {}
    lines = [
        "## Platform Migration",
        f"**Mode:** `{snap.get('mode')}`",
        f"**Effective data:** `{snap.get('effective_data_dir')}`",
        f"**Ready for cutover:** {'yes' if ver.get('ready') else 'no'}",
    ]
    for blocker in ver.get("blockers") or []:
        lines.append(f"- blocker: {blocker}")
    for warning in ver.get("warnings") or []:
        lines.append(f"- warning: {warning}")
    return "\n".join(lines)
