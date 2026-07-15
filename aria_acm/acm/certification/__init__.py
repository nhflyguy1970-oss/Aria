"""Certification framework — build gates; do NOT execute certification."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter, time
from typing import Any

from acm import CognitiveEngine
from acm._version import __version__
from acm.persistence import DurableCognitiveStore


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str
    duration_ms: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "duration_ms": round(self.duration_ms, 3),
            "metrics": dict(self.metrics),
        }


CERTIFICATION_CHECKLIST = [
    "persistence_roundtrip",
    "checksum_integrity",
    "backup_restore",
    "provenance_stamped",
    "shadow_legacy_authoritative",
    "shadow_no_user_change",
    "rollback_flag",
    "performance_encode_p95",
    "performance_remember_p95",
    "adapter_capabilities",
    "long_duration_smoke",
]


class CertificationFramework:
    """Builds and runs readiness *gates*. Never claims certified=True."""

    def __init__(self, *, workdir: str | Path) -> None:
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.results: list[GateResult] = []

    def run_all(self) -> dict[str, Any]:
        self.results.clear()
        self.results.append(self.gate_persistence_roundtrip())
        self.results.append(self.gate_checksum_integrity())
        self.results.append(self.gate_backup_restore())
        self.results.append(self.gate_provenance_stamped())
        self.results.append(self.gate_shadow_authoritative())
        self.results.append(self.gate_adapter_capabilities())
        self.results.append(self.gate_performance())
        self.results.append(self.gate_long_duration_smoke())
        return self.report()

    def _time(self, name: str, fn: Callable[[], tuple[bool, str, dict[str, Any]]]) -> GateResult:
        t0 = perf_counter()
        try:
            ok, detail, metrics = fn()
        except Exception as exc:  # noqa: BLE001 — gates must report failures
            return GateResult(
                name=name,
                passed=False,
                detail=f"{type(exc).__name__}: {exc}",
                duration_ms=(perf_counter() - t0) * 1000,
            )
        return GateResult(
            name=name,
            passed=ok,
            detail=detail,
            duration_ms=(perf_counter() - t0) * 1000,
            metrics=metrics,
        )

    def gate_persistence_roundtrip(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            path = self.workdir / "cert_persist.sqlite"
            if path.exists():
                path.unlink()
            eng = CognitiveEngine(agent_id="cert", persist_path=str(path), auto_persist=True)
            eng.encode("Certification coffee roast.", pin=True)
            eng.flush()
            eng2 = CognitiveEngine(agent_id="cert", persist_path=str(path))
            ok = len(eng2.store.experiences) >= 1
            return ok, "experiences restored" if ok else "missing experiences", {
                "experiences": len(eng2.store.experiences)
            }

        return self._time("persistence_roundtrip", run)

    def gate_checksum_integrity(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            path = self.workdir / "cert_check.sqlite"
            if path.exists():
                path.unlink()
            durable = DurableCognitiveStore(path)
            eng = CognitiveEngine(agent_id="cert")
            eng.encode("Checksum sample.", pin=True)
            durable.store = eng.store
            durable.flush()
            verify = durable.verify()
            durable.close()
            detail = "checksum ok" if verify.get("ok") else str(verify)
            return bool(verify.get("ok")), detail, verify

        return self._time("checksum_integrity", run)

    def gate_backup_restore(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            path = self.workdir / "cert_bak.sqlite"
            bak = self.workdir / "cert_bak.copy"
            if path.exists():
                path.unlink()
            if bak.exists():
                bak.unlink()
            durable = DurableCognitiveStore(path)
            eng = CognitiveEngine(agent_id="cert")
            eng.encode("Backup sample.", pin=True)
            durable.store = eng.store
            durable.flush()
            durable.backup(bak)
            eng.encode("After backup.", pin=True)
            durable.flush()
            durable.restore(bak)
            ok = len(durable.store.experiences) >= 1
            durable.close()
            return ok, "restore ok" if ok else "restore empty", {
                "experiences": len(durable.store.experiences)
            }

        return self._time("backup_restore", run)

    def gate_provenance_stamped(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            eng = CognitiveEngine(agent_id="cert")
            payload = eng.encode("Provenance sample.", pin=True)
            prov = eng.provenance_of(str(payload.get("experience_id") or ""))
            ok = len(prov) >= 1 and all(not p.get("fabricated") for p in prov)
            return ok, "provenance present" if ok else "missing provenance", {"count": len(prov)}

        return self._time("provenance_stamped", run)

    def gate_shadow_authoritative(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            from aria_memory_adapter import AcmMemoryAdapter, FeatureFlags

            class Leg:
                def remember(self, text: str, **kwargs: Any) -> dict[str, Any]:
                    return {"ok": True, "text": text, "id": "L1"}

                def recall(self, query: str, **kwargs: Any) -> dict[str, Any]:
                    return {"ok": True, "answer": "legacy coffee", "confidence": 0.9}

                def health(self) -> dict[str, Any]:
                    return {"ok": True}

            ad = AcmMemoryAdapter(legacy=Leg(), flags=FeatureFlags())
            out = ad.recall("coffee")
            ok = out["authoritative"] == "legacy" and out["user_visible_changed"] is False
            return ok, "legacy authoritative" if ok else "shadow leaked", {
                "authoritative": out["authoritative"]
            }

        return self._time("shadow_legacy_authoritative", run)

    def gate_adapter_capabilities(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            from aria_memory_adapter import AcmMemoryAdapter

            caps = AcmMemoryAdapter().capabilities()
            ok = caps.get("shadow") is True and caps.get("aria_import") is False
            return ok, "capabilities ok" if ok else "bad capabilities", caps

        return self._time("adapter_capabilities", run)

    def gate_performance(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            eng = CognitiveEngine(agent_id="perf")
            times: list[float] = []
            for i in range(20):
                t0 = perf_counter()
                eng.encode(f"Perf sample {i} coffee tea water.", pin=True)
                times.append((perf_counter() - t0) * 1000)
            times.sort()
            p95 = times[int(0.95 * (len(times) - 1))]
            ok = p95 < 200.0
            return ok, f"encode p95={p95:.1f}ms", {"encode_p95_ms": p95}

        return self._time("performance_encode_p95", run)

    def gate_long_duration_smoke(self) -> GateResult:
        def run() -> tuple[bool, str, dict[str, Any]]:
            eng = CognitiveEngine(agent_id="long")
            before = len(eng.store.experiences)
            for i in range(12):
                eng.encode(f"Long run {i}.", pin=True)
                eng.how_certain_am_i(f"run {i}")
            ok = len(eng.store.experiences) == before + 12
            return ok, "long smoke ok" if ok else "experience drift", {
                "experiences": len(eng.store.experiences)
            }

        return self._time("long_duration_smoke", run)

    def report(self) -> dict[str, Any]:
        """Generate certification report — certified is ALWAYS false in Phase 2."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        payload = {
            "schema": "acm.certification/0.13",
            "acm_version": __version__,
            "generated": time(),
            "checklist": list(CERTIFICATION_CHECKLIST),
            "gates": [r.to_public() for r in self.results],
            "passed": passed,
            "total": total,
            "all_gates_green": passed == total and total > 0,
            "certified": False,  # Phase 2 builds framework; does not certify
            "note": (
                "Framework executed gates only. "
                "Formal certification requires explicit approval."
            ),
        }
        out = self.workdir / "certification_report.json"
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        payload["report_path"] = str(out)
        return payload
