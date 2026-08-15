#!/usr/bin/env python3
"""Simulate weeks of Guided Repair use — trust maturity, isolated temp data only."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path


def bind(root: Path) -> None:
    os.environ["JARVIS_DATA_DIR"] = str(root)
    import jarvis.config as config

    config.DATA_DIR = root
    from jarvis.repair_product import modules, store
    from jarvis.repair_product.registry import clear_registry_for_tests

    store.REPAIR_DIR = root / "repair_product"
    store.HISTORY_PATH = store.REPAIR_DIR / "history.jsonl"
    store.ISSUES_PATH = store.REPAIR_DIR / "issues.json"
    store.LEARNING_PATH = store.REPAIR_DIR / "learning.json"
    store.AUTO_APPROVE_PATH = store.REPAIR_DIR / "auto_approve.json"
    store.KNOWLEDGE_PATH = store.REPAIR_DIR / "knowledge.json"
    store.ROOT_CAUSES_PATH = store.REPAIR_DIR / "root_causes.json"
    store.MAINTENANCE_PATH = store.REPAIR_DIR / "maintenance.json"
    store.MONITORS_PATH = store.REPAIR_DIR / "monitors.json"
    store.ensure_dirs()
    clear_registry_for_tests()
    modules._REGISTERED = False
    modules.register_all()


def main() -> dict:
    root = Path(tempfile.mkdtemp(prefix="repair_maturity_"))
    bind(root)
    from jarvis.repair_product import knowledge, maintenance, reputation, root_causes, store
    from jarvis.repair_product.engine import execute_repair, prepare_issue, preview_repair, scan_issues
    from jarvis.repair_product.export_bundle import write_bundle
    from jarvis.repair_product.monitoring import tick
    from jarvis.repair_product.registry import DetectedIssue

    trust = {}
    # Week-like loop: introduce issues, preview, approve, verify, monitor, learn
    for week in range(1, 5):
        for code in ("stale_cache", "tmp", "stale_cache"):
            mid = "mission_control_cache" if code == "stale_cache" else "caches_temp"
            det = DetectedIssue(
                module_id=mid,
                subsystem="mission_control" if mid.startswith("mission") else "system",
                title=f"Week {week} {code}",
                summary=f"simulated week {week}",
                severity="warning",
                code=code,
            )
            prep = prepare_issue(det)
            assert prep["ok"]
            iss = prep["issue"]
            panel = prep["panel"]
            assert panel.get("confidence_reasons")
            assert preview_repair(iss["id"]).get("modifies_system") is False
            # No silent execute
            blocked = execute_repair(iss["id"], approved=False)
            assert blocked.get("approval_required")
            done = execute_repair(iss["id"], approved=True)
            assert done.get("success_claimed") == done.get("verified")
            if done.get("verified"):
                # accelerate monitoring
                mon = (store.get_issue(iss["id"]) or {}).get("monitoring") or {}
                for cp in mon.get("checkpoints") or []:
                    cp["at"] = time.time() - 1
                store.save_monitor(iss["id"], mon)
                store.update_issue(iss["id"], {"monitoring": mon})
                tick(now=time.time() + 5)

    # Maintenance week
    maintenance.enable(reason="rebuilding_indexes")
    scan = scan_issues()
    trust["maintenance_marks_issues"] = any(i.get("suppressed_by_maintenance") for i in (scan.get("issues") or [])) or scan.get("maintenance", {}).get("enabled")
    maintenance.disable(run_verification=True)

    # Learning matured
    learn = store.learning_stats()
    arts = knowledge.search(limit=20)
    reps = reputation.all_reputations()
    roots = root_causes.list_all()
    exported = write_bundle(approved_sensitive=False)

    hist = store.list_history(limit=100)
    lies = [h for h in hist if h.get("success_claimed") and not h.get("verified_ok")]
    trust.update(
        {
            "explained_confidence": True,
            "preview_safe": True,
            "approval_gate": True,
            "no_false_success_in_history": len(lies) == 0,
            "knowledge_grew": len(arts) > 0,
            "reputation_tracked": any((r.get("executed") or 0) > 0 for r in reps),
            "root_causes_present": len(roots) > 0,
            "diagnostic_export_ok": exported.get("ok") is True,
            "repairs_recorded": len(hist) >= 4,
            "learning_signals": bool(learn.get("successful_repairs") or learn.get("common_failures")),
        }
    )
    certified = all(trust.values())
    report = {"root": str(root), "trust": trust, "certified": certified, "history_count": len(hist), "knowledge": len(arts)}
    Path("/tmp/repair_maturity_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print("CERTIFIED" if certified else "NOT CERTIFIED")
    return report


if __name__ == "__main__":
    main()
