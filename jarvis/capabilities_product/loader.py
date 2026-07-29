"""Load / unload / enable pipeline with structured reports."""

from __future__ import annotations

import time
from typing import Any

from jarvis.capabilities_product import policy as cap_policy
from jarvis.capabilities_product.history import record_activity
from jarvis.capabilities_product.status_bus import set_capabilities_state


def _report_base() -> dict[str, Any]:
    return {
        "ok": True,
        "loaded": [],
        "skipped": [],
        "disabled": [],
        "failed": [],
        "warnings": [],
        "duration_ms": 0,
        "dependencies": {},
    }


def load_capability(cap_id: str, *, hot: bool = False) -> dict[str, Any]:
    """Load a single capability by id (sdk:*, host:* soft)."""
    started = time.perf_counter()
    report = _report_base()
    if cap_policy.is_quarantined(cap_id):
        report["ok"] = False
        report["failed"].append({"id": cap_id, "error": "quarantined"})
        report["warnings"].append("Acknowledge quarantine before loading.")
        report["duration_ms"] = int((time.perf_counter() - started) * 1000)
        return report

    if not cap_policy.is_enabled(cap_id, trust="trusted_local", default=False) and not cap_id.startswith("host:"):
        # Host defaults on; others need enabled
        if not cap_id.startswith("host:"):
            report["disabled"].append(cap_id)
            report["ok"] = False
            report["duration_ms"] = int((time.perf_counter() - started) * 1000)
            return report

    try:
        if cap_id.startswith("sdk:"):
            from pathlib import Path

            from jarvis.intelligence import plugin_sdk
            from jarvis.capabilities_product.contributions import register_contributions

            pid = cap_id.split(":", 1)[1]
            target = None
            for d in plugin_sdk.discover_plugin_dirs():
                try:
                    m = plugin_sdk.read_manifest(d)
                    if m.id == pid:
                        target = d
                        break
                except Exception:
                    continue
            if target is None:
                raise FileNotFoundError(f"capability not found: {cap_id}")
            if hot:
                # Best-effort reload of module
                import importlib
                import sys

                for key in list(sys.modules):
                    if key == pid or key.startswith(pid + "."):
                        sys.modules.pop(key, None)
            loaded = plugin_sdk.load_plugin(Path(target))
            if loaded.error:
                raise RuntimeError(loaded.error)
            register_contributions(cap_id, loaded.manifest)
            report["loaded"].append(cap_id)
            record_activity("load", capability_id=cap_id, message=f"Loaded {cap_id}")
            try:
                from jarvis.router_table import invalidate_router_table

                invalidate_router_table()
            except Exception:
                pass
        elif cap_id.startswith("host:"):
            from jarvis.extensibility.loader import load_extensions

            load_extensions(force=False)
            report["loaded"].append(cap_id)
            report["warnings"].append("Host extensions load with the process; enable/disable applies on next full reload.")
            record_activity("load", capability_id=cap_id, message=f"Host capability present: {cap_id}")
        elif cap_id.startswith("platform:"):
            try:
                from aiplatform.plugins.manager import plugins as plugin_manager

                pid = cap_id.split(":", 1)[1]
                ok = plugin_manager.load(pid)
                if not ok:
                    raise RuntimeError(f"platform load failed: {pid}")
                report["loaded"].append(cap_id)
            except Exception as exc:
                raise RuntimeError(str(exc)) from exc
        else:
            report["skipped"].append({"id": cap_id, "reason": "layer_does_not_support_file_load"})
            report["warnings"].append(f"{cap_id} is managed by its native layer.")
        set_capabilities_state("idle", detail=f"loaded {cap_id}")
    except Exception as exc:
        cap_policy.record_failure(cap_id, str(exc))
        report["ok"] = False
        report["failed"].append({"id": cap_id, "error": str(exc)})
        record_activity("load_failed", capability_id=cap_id, message=str(exc))
        set_capabilities_state("error", detail=str(exc), error=str(exc))
    report["duration_ms"] = int((time.perf_counter() - started) * 1000)
    return report


def load_all_enabled(*, include_sdk: bool = True) -> dict[str, Any]:
    started = time.perf_counter()
    report = _report_base()
    set_capabilities_state("loading", detail="Loading enabled capabilities")

    # Host: respect disabled list by reloading with filter (loader consults policy)
    try:
        from jarvis.extensibility.loader import load_extensions

        load_extensions(force=True)
        report["loaded"].append("host:*")
    except Exception as exc:
        report["failed"].append({"id": "host:*", "error": str(exc)})
        report["ok"] = False

    if include_sdk:
        try:
            from jarvis.intelligence import plugin_sdk
            from jarvis.capabilities_product.contributions import register_contributions

            for d in plugin_sdk.discover_plugin_dirs():
                try:
                    m = plugin_sdk.read_manifest(d)
                    cap_id = f"sdk:{m.id}"
                    if cap_policy.is_quarantined(cap_id):
                        report["skipped"].append({"id": cap_id, "reason": "quarantined"})
                        continue
                    if not cap_policy.is_enabled(cap_id, trust="trusted_local"):
                        report["disabled"].append(cap_id)
                        continue
                    if cap_policy.is_lazy(cap_id):
                        report["skipped"].append({"id": cap_id, "reason": "lazy"})
                        continue
                    loaded = plugin_sdk.load_plugin(d)
                    if loaded.error:
                        cap_policy.record_failure(cap_id, loaded.error)
                        report["failed"].append({"id": cap_id, "error": loaded.error})
                        report["ok"] = False
                    else:
                        register_contributions(cap_id, loaded.manifest)
                        report["loaded"].append(cap_id)
                except Exception as exc:
                    report["failed"].append({"id": str(d), "error": str(exc)})
                    report["ok"] = False
            try:
                from jarvis.router_table import invalidate_router_table

                invalidate_router_table()
            except Exception:
                pass
        except Exception as exc:
            report["failed"].append({"id": "sdk:*", "error": str(exc)})
            report["ok"] = False

    report["duration_ms"] = int((time.perf_counter() - started) * 1000)
    record_activity("load_all", message=f"loaded={len(report['loaded'])} failed={len(report['failed'])}")
    set_capabilities_state("idle" if report["ok"] else "error", detail="load_all complete")
    return report


def enable_capability(cap_id: str, *, load_now: bool = True) -> dict[str, Any]:
    entry = cap_policy.set_enabled(cap_id, True)
    record_activity("enable", capability_id=cap_id, message=f"Enabled {cap_id}")
    result: dict[str, Any] = {"ok": True, "id": cap_id, "entry": entry, "restart_required": False}
    if cap_id.startswith("host:"):
        result["restart_required"] = True
        result["message"] = "Host extension enable is persisted; restart Aria (or force reload) to apply fully."
    elif load_now:
        result["load"] = load_capability(cap_id)
        result["ok"] = bool(result["load"].get("ok"))
    return result


def disable_capability(cap_id: str) -> dict[str, Any]:
    from jarvis.capabilities_product.contributions import unregister_contributions

    entry = cap_policy.set_enabled(cap_id, False)
    unregister_contributions(cap_id)
    record_activity("disable", capability_id=cap_id, message=f"Disabled {cap_id}")
    restart_required = cap_id.startswith("host:")
    return {
        "ok": True,
        "id": cap_id,
        "entry": entry,
        "restart_required": restart_required,
        "message": (
            "Disabled. Host extensions may remain imported until process restart."
            if restart_required
            else "Disabled and contributions unregistered."
        ),
    }


def hot_reload_capability(cap_id: str) -> dict[str, Any]:
    """Hot reload trusted local SDK capabilities only."""
    if not cap_id.startswith("sdk:"):
        return {
            "ok": False,
            "message": "Hot reload is only supported for Trusted Local (sdk) capabilities.",
        }
    from jarvis.capabilities_product.registry import get_capability

    info = get_capability(cap_id) or {}
    trust = info.get("trust") or "trusted_local"
    if trust not in ("trusted_local", "first_party", "built_in", "experimental"):
        return {"ok": False, "message": f"Hot reload blocked for trust level: {trust}"}
    report = load_capability(cap_id, hot=True)
    record_activity("hot_reload", capability_id=cap_id, message="Hot reload attempted")
    return report
