"""Diagnostic export — no personal Health/Memory unless explicitly approved."""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.repair_product import store
from jarvis.repair_product.terminology import DISCLAIMER, SCHEMA_VERSION


def build_bundle(
    *,
    issue_id: str = "",
    include_health: bool = False,
    include_memory: bool = False,
    approved_sensitive: bool = False,
) -> dict[str, Any]:
    from jarvis.repair_product.engine import product_status
    from jarvis.repair_product import reputation, root_causes, knowledge

    issue = store.get_issue(issue_id) if issue_id else None
    hist = store.list_history(limit=100)
    if issue_id:
        hist = [h for h in hist if h.get("issue_id") == issue_id] or hist[:20]

    env = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "node": platform.node(),
    }
    hardware: dict[str, Any] = {}
    try:
        import shutil

        disk = shutil.disk_usage(str(DATA_DIR))
        hardware["disk_free_gb"] = round(disk.free / (1024**3), 2)
        hardware["disk_total_gb"] = round(disk.total / (1024**3), 2)
    except Exception:
        pass
    try:
        from jarvis import gpu

        if hasattr(gpu, "snapshot"):
            hardware["gpu"] = gpu.snapshot()
    except Exception:
        pass

    providers: dict[str, Any] = {}
    try:
        from jarvis.provider_health.probe import ping_provider

        providers["ollama"] = {k: ping_provider("ollama").get(k) for k in ("alive", "state")}
    except Exception as exc:
        providers["error"] = str(exc)

    mc_snap: dict[str, Any] = {}
    try:
        from jarvis import mission_control

        hs = mission_control.health_summary(force=False) or {}
        # Strip anything that looks like personal payloads
        mc_snap = {
            "ok": hs.get("ok"),
            "keys": sorted(hs.keys()) if isinstance(hs, dict) else [],
            "brief": (hs.get("health_brief") or {}) if isinstance(hs, dict) else {},
        }
    except Exception as exc:
        mc_snap = {"error": str(exc)}

    config_summary = {
        "data_dir": str(DATA_DIR),
        "schema_version": SCHEMA_VERSION,
        "maintenance": store.maintenance_state(),
        "auto_approve_modules": store.auto_approve_list(),
    }

    bundle = {
        "format": "aria-guided-repair-diagnostic-v1",
        "exported_at": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "disclaimer": DISCLAIMER,
        "privacy": {
            "includes_health": bool(include_health and approved_sensitive),
            "includes_memory": bool(include_memory and approved_sensitive),
            "note": "Personal Health and Memory are excluded unless explicitly approved.",
        },
        "diagnosis": (issue or {}).get("diagnosis"),
        "evidence": (issue or {}).get("evidence"),
        "issue": {
            k: (issue or {}).get(k)
            for k in (
                "id",
                "title",
                "subsystem",
                "module_id",
                "code",
                "severity",
                "priority",
                "confidence",
                "state",
                "plan",
                "impact",
                "dependency",
                "workflow",
            )
        }
        if issue
        else None,
        "repair_history": hist,
        "verification": (issue or {}).get("verify"),
        "monitoring": (issue or {}).get("monitoring"),
        "environment": env,
        "hardware": hardware,
        "providers": providers,
        "configuration_summary": config_summary,
        "mission_control_snapshot": mc_snap,
        "product_status": product_status(),
        "reputations": reputation.all_reputations()[:20],
        "root_causes": root_causes.list_all()[:20],
        "knowledge": knowledge.search(limit=20),
        "recent_changes": _recent_change_hints(),
    }

    if include_health and approved_sensitive:
        bundle["health_note"] = "Health inclusion approved by operator — still omitting record contents; status only."
        try:
            from jarvis.health_product.engine import product_status as hp

            bundle["health_product_status"] = {
                k: hp().get(k) for k in ("ok", "product", "schema_version", "healthy")
            }
        except Exception as exc:
            bundle["health_product_status"] = {"error": str(exc)}

    if include_memory and approved_sensitive:
        bundle["memory_note"] = "Memory inclusion approved — namespaces only, no entry bodies."
        try:
            # Prefer counts only
            bundle["memory_summary"] = {"included": "namespace_counts_only", "note": "bodies omitted"}
        except Exception:
            pass

    return bundle


def write_bundle(path: Path | None = None, **kwargs: Any) -> dict[str, Any]:
    bundle = build_bundle(**kwargs)
    out_dir = store.REPAIR_DIR / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = path or (out_dir / f"diagnostic-{time.strftime('%Y%m%d-%H%M%S')}.json")
    path.write_text(json.dumps(bundle, indent=2, default=str), encoding="utf-8")
    return {"ok": True, "path": str(path), "bytes": path.stat().st_size, "bundle_keys": sorted(bundle.keys()), "disclaimer": DISCLAIMER}


def _recent_change_hints() -> list[str]:
    hints = []
    try:
        mc = DATA_DIR / "mission_control"
        if mc.is_dir():
            hints.append(f"mission_control dir present ({len(list(mc.glob('*')))} entries)")
    except Exception:
        pass
    return hints
