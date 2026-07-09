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
_MIN_SHADOW_AGREEMENT_RATE = 0.95


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


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").lower() in ("1", "true", "yes")


def current_mode() -> str:
    if _env_truthy("JARVIS_PLATFORM_DATA_AUTHORITATIVE"):
        return "platform_authoritative"
    mode = str(_load().get("mode") or "dual_write")
    return mode if mode in _MODES else "dual_write"


def platform_data_authoritative() -> bool:
    return current_mode() == "platform_authoritative"


def apply_cutover_state_on_startup() -> dict[str, Any]:
    """Hydrate authoritative env from persisted cutover state before platform attach."""
    state = _load()
    mode = str(state.get("mode") or "dual_write")
    if mode != "platform_authoritative":
        return {"applied": False, "mode": mode}

    if not _env_truthy("JARVIS_PLATFORM_DATA_AUTHORITATIVE"):
        os.environ["JARVIS_PLATFORM_DATA_AUTHORITATIVE"] = "1"

    logger.info(
        "Platform cutover state hydrated from %s (mode=platform_authoritative)",
        _CUTOVER_FILE,
    )
    return {
        "applied": True,
        "mode": "platform_authoritative",
        "cutover_file": str(_CUTOVER_FILE),
    }


def _check_memory_layer() -> tuple[dict[str, Any], list[str], list[str]]:
    layer: dict[str, Any] = {"ok": True}
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") != "1":
        layer["ok"] = False
        blockers.append("platform memory adapter not attached")
        return layer, blockers, warnings

    metrics: dict[str, Any] = {}
    try:
        from aiplatform.applications.memory.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        layer["metrics"] = metrics
        failures = int(metrics.get("verification_failures") or 0)
        if failures > 0:
            layer["ok"] = False
            blockers.append(f"memory verification failures: {failures}")
    except Exception as exc:
        layer["ok"] = False
        warnings.append(f"memory metrics unavailable: {exc}")

    try:
        from aiplatform.applications.manager import manager as application_manager
        from aiplatform.applications.memory.validator import namespace_status

        app = application_manager.get(_APPLICATION_ID)
        if app is not None:
            required, bridged, missing = namespace_status(app)
            layer["namespaces"] = {
                "required": required,
                "bridged": bridged,
                "missing": missing,
            }
            if missing:
                layer["ok"] = False
                blockers.append(f"memory namespaces not bridged: {', '.join(missing)}")
    except Exception as exc:
        warnings.append(f"memory namespace check unavailable: {exc}")

    return layer, blockers, warnings


def _check_semantic_layer() -> tuple[dict[str, Any], list[str], list[str]]:
    layer: dict[str, Any] = {"ok": True, "attached": False}
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") != "1":
        layer["skipped"] = True
        return layer, blockers, warnings

    layer["attached"] = True
    try:
        from aiplatform.applications.semantic.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        layer["metrics"] = metrics
        read_failures = int(metrics.get("read_verification_failures") or 0)
        embed_failures = int(metrics.get("embedding_verification_failures") or 0)
        verify_failures = int(metrics.get("verification_failures") or 0)
        if read_failures > 0:
            layer["ok"] = False
            blockers.append(f"semantic read verification failures: {read_failures}")
        if embed_failures > 0:
            layer["ok"] = False
            blockers.append(f"semantic embedding verification failures: {embed_failures}")
        if verify_failures > 0:
            layer["ok"] = False
            blockers.append(f"semantic verification failures: {verify_failures}")
    except Exception as exc:
        layer["ok"] = False
        warnings.append(f"semantic metrics unavailable: {exc}")

    return layer, blockers, warnings


def _check_knowledge_layer() -> tuple[dict[str, Any], list[str], list[str]]:
    layer: dict[str, Any] = {"ok": True, "attached": False}
    blockers: list[str] = []
    warnings: list[str] = []

    if os.getenv("JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED") != "1":
        layer["skipped"] = True
        return layer, blockers, warnings

    layer["attached"] = True
    try:
        from aiplatform.applications.knowledge_retrieval.metrics import metrics_view

        metrics = metrics_view(_APPLICATION_ID).to_dict()
        layer["metrics"] = metrics
        failures = int(metrics.get("retrieval_verification_failures") or 0)
        if failures > 0:
            layer["ok"] = False
            blockers.append(f"knowledge retrieval verification failures: {failures}")

        comparisons = int(metrics.get("shadow_retrieval_comparisons") or 0)
        agreements = int(metrics.get("retrieval_agreements") or 0)
        if comparisons > 0:
            rate = agreements / comparisons
            layer["shadow_agreement_rate"] = round(rate, 4)
            if rate < _MIN_SHADOW_AGREEMENT_RATE:
                layer["ok"] = False
                blockers.append(
                    f"knowledge shadow agreement too low: {rate:.1%} "
                    f"(minimum {_MIN_SHADOW_AGREEMENT_RATE:.0%})"
                )
    except Exception as exc:
        layer["ok"] = False
        warnings.append(f"knowledge metrics unavailable: {exc}")

    return layer, blockers, warnings


def _check_backfill_gate() -> tuple[dict[str, Any], list[str], list[str]]:
    state = _load()
    stats = state.get("backfill_stats") or {}
    layer = {
        "ok": True,
        "completed_at": state.get("backfill_completed_at") or "",
        "stats": stats,
    }
    blockers: list[str] = []
    warnings: list[str] = []

    if not layer["completed_at"]:
        layer["ok"] = False
        blockers.append("memory backfill has not completed")
    else:
        errors = int(stats.get("errors") or 0)
        total = int(stats.get("total") or 0)
        mirrored = int(stats.get("mirrored") or 0)
        if errors > 0:
            layer["ok"] = False
            blockers.append(f"memory backfill errors: {errors}")
        elif total > 0 and mirrored < total:
            layer["ok"] = False
            blockers.append(f"memory backfill incomplete: {mirrored}/{total} mirrored")

    return layer, blockers, warnings


def verify_data_parity() -> dict[str, Any]:
    """Compare legacy memory inventory with backfill stats."""
    state = _load()
    stats = state.get("backfill_stats") or {}
    legacy_count = 0
    error = ""
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        if hasattr(mem, "list_entries"):
            legacy_count = len(mem.list_entries())
    except Exception as exc:
        error = str(exc)[:200]

    mirrored = int(stats.get("mirrored") or 0)
    total = int(stats.get("total") or 0)
    ok = not error and legacy_count == mirrored and (total == 0 or total == legacy_count)
    return {
        "ok": ok,
        "legacy_count": legacy_count,
        "mirrored": mirrored,
        "backfill_total": total,
        "error": error,
    }


def verify_readiness(*, persist: bool = True) -> dict[str, Any]:
    """Check whether platform cutover is safe."""
    blockers: list[str] = []
    warnings: list[str] = []
    layers: dict[str, Any] = {}

    if _env_truthy("JARVIS_DISABLE_PLATFORM_ATTACHMENT"):
        blockers.append("platform attachment disabled")

    if os.getenv("JARVIS_PLATFORM_ATTACHED") != "1":
        blockers.append("platform infrastructure not attached")

    legacy_path = Path(os.getenv("JARVIS_LEGACY_DATA_DIR", str(DATA_DIR)))
    if not legacy_path.is_dir():
        blockers.append(f"legacy data dir missing: {legacy_path}")

    platform_path = os.getenv("JARVIS_PLATFORM_DATA_DIR", "")
    if not platform_path:
        blockers.append("platform data dir not configured")
    elif not Path(platform_path).is_dir():
        blockers.append(f"platform data dir missing: {platform_path}")

    memory_layer, mem_blockers, mem_warnings = _check_memory_layer()
    layers["memory"] = memory_layer
    blockers.extend(mem_blockers)
    warnings.extend(mem_warnings)

    semantic_layer, sem_blockers, sem_warnings = _check_semantic_layer()
    layers["semantic"] = semantic_layer
    blockers.extend(sem_blockers)
    warnings.extend(sem_warnings)

    knowledge_layer, know_blockers, know_warnings = _check_knowledge_layer()
    layers["knowledge"] = knowledge_layer
    blockers.extend(know_blockers)
    warnings.extend(know_warnings)

    backfill_layer, backfill_blockers, backfill_warnings = _check_backfill_gate()
    layers["backfill"] = backfill_layer
    blockers.extend(backfill_blockers)
    warnings.extend(backfill_warnings)

    parity = verify_data_parity()
    layers["parity"] = parity
    if not parity.get("ok") and parity.get("legacy_count", 0) > 0:
        blockers.append(
            "memory parity mismatch: "
            f"legacy={parity.get('legacy_count')} mirrored={parity.get('mirrored')}"
        )

    ready = not blockers
    result = {
        "ready": ready,
        "blockers": blockers,
        "warnings": warnings,
        "layers": layers,
        "ts": time.time(),
    }
    if persist:
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
        verification = verify_readiness()
        if not verification.get("ready"):
            return {
                "ok": False,
                "error": "cutover blocked after backfill",
                "verification": verification,
                "backfill": backfill,
            }

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
