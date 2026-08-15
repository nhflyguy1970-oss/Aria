"""Certification engine — status, home, gate."""

from __future__ import annotations

from typing import Any

from jarvis.certification_product import store
from jarvis.certification_product.terminology import (
    BOUNDARIES,
    MENTAL_MODEL,
    REQUIRED_COVERAGE_PCT,
    REQUIRED_FEATURES,
    SCHEMA_VERSION,
    TERMINOLOGY,
)


def product_status() -> dict[str, Any]:
    latest = store.latest_run()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "schema_version": SCHEMA_VERSION,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
        "required_features": list(REQUIRED_FEATURES),
        "required_coverage_pct": REQUIRED_COVERAGE_PCT,
        "latest_gate": (latest or {}).get("gate") or "NO_RUN",
        "latest_run_id": (latest or {}).get("id"),
        "healthy": (latest or {}).get("gate") == "READY_TO_SHIP",
    }


def home_payload() -> dict[str, Any]:
    store.ingest_legacy_probes()
    latest = store.latest_run()
    runs = store.list_runs(limit=20)
    gate = (latest or {}).get("gate") or "NO_RUN"
    ready = gate == "READY_TO_SHIP"
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "home": TERMINOLOGY["home"],
        "note": BOUNDARIES["philosophy"],
        "release_readiness": "READY_TO_SHIP" if ready else ("SMOKE_PASS" if gate == "SMOKE_PASS" else "DO_NOT_SHIP"),
        "gate": gate,
        "latest": latest,
        "history": runs,
        "coverage": (latest or {}).get("coverage") or {},
        "blockers": (latest or {}).get("blockers") or [],
        "counts": (latest or {}).get("counts") or {},
        "required_features": list(REQUIRED_FEATURES),
        "required_coverage_pct": REQUIRED_COVERAGE_PCT,
        "legacy_probes": store._read_json(store.CERT_ROOT / "legacy_probes.json", {}).get("probes") or [],
        "diagnostics": product_status(),
    }


def run_detail(run_id: str) -> dict[str, Any]:
    man = store.get_run(run_id)
    if not man:
        return {"ok": False, "message": "Run not found"}
    return {
        "ok": True,
        "run": man,
        "assertions": store.list_assertions(run_id),
        "api_calls": store.list_api_calls(run_id),
        "evidence_files": store.list_evidence_files(run_id),
    }
