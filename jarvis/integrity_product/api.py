"""Production Integrity HTTP API — /api/integrity/*"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/integrity/product")
    def integrity_product_status():
        from jarvis.integrity_product.scanner import product_status

        return product_status()

    @app.get("/api/integrity/home")
    def integrity_home():
        from jarvis.integrity_product.scanner import home_payload

        return home_payload()

    @app.post("/api/integrity/scan")
    def integrity_scan(trigger: str = "api"):
        from jarvis.integrity_product.scanner import run_scan

        return run_scan(force=True, trigger=trigger or "api")

    @app.get("/api/integrity/findings")
    def integrity_findings():
        from jarvis.integrity_product import store
        from jarvis.integrity_product.scanner import run_scan

        last = store.load_last_scan()
        if not last:
            last = run_scan(force=True, trigger="findings")
        return {
            "ok": True,
            "status": last.get("status"),
            "findings": last.get("findings") or [],
            "counts": last.get("counts") or {},
            "scanned_at": last.get("scanned_at"),
        }

    @app.get("/api/integrity/history")
    def integrity_history(limit: int = 40):
        from jarvis.integrity_product import store

        return {"ok": True, "history": store.list_history(limit=max(1, min(200, limit)))}

    @app.get("/api/integrity/mission")
    def integrity_mission():
        from jarvis.integrity_product.mission_bridge import integrity_mission_panel

        return {"ok": True, **integrity_mission_panel()}

    @app.get("/api/integrity/score")
    def integrity_score():
        from jarvis.integrity_product import store
        from jarvis.integrity_product.scanner import run_scan
        from jarvis.integrity_product.score import compute_score

        last = store.load_last_scan()
        if not last:
            last = run_scan(force=True, trigger="score")
        score = last.get("score") or compute_score(last)
        return {
            "ok": True,
            "score": score,
            "status": last.get("status"),
            "last_scan_at": last.get("scanned_at"),
            "artifacts_found": (last.get("counts") or {}).get("total", 0),
            "findings": last.get("findings") or [],
        }

    @app.post("/api/integrity/recommend-repair")
    def integrity_recommend_repair():
        """Create / refresh a Guided Repair issue for current findings (no execution)."""
        from jarvis.integrity_product.scanner import run_scan
        from jarvis.repair_product.engine import prepare_issue
        from jarvis.integrity_product.repair_module import ProductionIntegrityModule

        scan = run_scan(force=True, trigger="recommend_repair")
        mod = ProductionIntegrityModule()
        detected = mod.detect()
        if not detected:
            return {"ok": True, "clean": True, "message": "Production is clean — no repair needed.", "scan": scan}
        prepared = prepare_issue(detected[0])
        return {"ok": True, "clean": False, "scan": scan, **prepared}

    @app.post("/api/integrity/hooks/{event}")
    def integrity_hook(event: str):
        """Lifecycle hooks: startup | after_qa | after_certification | after_upgrade | after_migration | after_restore | daily."""
        from jarvis.integrity_product.scanner import run_scan

        allowed = {
            "startup",
            "after_qa",
            "after_certification",
            "after_upgrade",
            "after_migration",
            "after_restore",
            "daily",
        }
        ev = (event or "").strip().lower()
        if ev not in allowed:
            return JSONResponse(status_code=400, content={"ok": False, "message": f"unknown event; use {sorted(allowed)}"})
        scan = run_scan(force=True, trigger=ev)
        # Feed Guided Repair when dirty (recommendation only)
        recommended = None
        if not scan.get("clean"):
            try:
                from jarvis.repair_product.engine import prepare_issue
                from jarvis.integrity_product.repair_module import ProductionIntegrityModule

                detected = ProductionIntegrityModule().detect()
                if detected:
                    recommended = prepare_issue(detected[0])
            except Exception as exc:
                recommended = {"ok": False, "error": str(exc)}
        return {"ok": True, "event": ev, "scan": scan, "recommended_repair": recommended}
