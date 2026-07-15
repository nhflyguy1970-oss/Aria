"""M2 Harvest — migrate legacy MemoryStore history INTO vendored ACM.

Blueprint: docs/acm_integration/DATA_MIGRATION_PLAN.md

Rules:
- Operator-triggered only (never automatic / background).
- Direction: INTO ACM only (Supremacy Rule 5).
- Legacy remains authoritative for user-visible cognition through M2.
- Do not invent lineage. Do not modify ACM organ cognition.
- Idempotent via context tag legacy_id:<id>.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aria_core import acm_bridge

BATCH_SIZE_DEFAULT = 500

# Tags / namespaces skipped (KEEP-HOST / non-autobiography)
_SKIP_TAGS = frozenset(
    {
        "telemetry",
        "tool-outcome",
        "tool_outcome",
        "diagnostic",
        "diagnostics",
    }
)
_SKIP_NAMESPACES = frozenset({"tools"})

_LEGACY_ID_RE = re.compile(r"^legacy_id:(.+)$")


@dataclass
class HarvestReport:
    ok: bool = True
    freeze_ts: float = 0.0
    legacy_checksum: str = ""
    source_count: int = 0
    p0_count: int = 0
    p0_eligible: int = 0
    p0_mapped: int = 0
    imported: int = 0
    skipped_existing: int = 0
    skipped_policy: int = 0
    skipped_empty: int = 0
    encode_failures: int = 0
    revised: int = 0
    unresolved_supersedes: int = 0
    goals_opened: int = 0
    identity_proposals: int = 0
    identity_assented: int = 0
    journal_imported: int = 0
    preference_imported: int = 0
    project_imported: int = 0
    provenance_ok: int = 0
    provenance_missing: int = 0
    batches: int = 0
    duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    mapping: dict[str, str] = field(default_factory=dict)  # legacy_id -> experience_id
    notes: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "freeze_ts": self.freeze_ts,
            "legacy_checksum": self.legacy_checksum,
            "source_count": self.source_count,
            "p0_count": self.p0_count,
            "p0_eligible": self.p0_eligible,
            "p0_mapped": self.p0_mapped,
            "imported": self.imported,
            "skipped_existing": self.skipped_existing,
            "skipped_policy": self.skipped_policy,
            "skipped_empty": self.skipped_empty,
            "encode_failures": self.encode_failures,
            "revised": self.revised,
            "unresolved_supersedes": self.unresolved_supersedes,
            "goals_opened": self.goals_opened,
            "identity_proposals": self.identity_proposals,
            "identity_assented": self.identity_assented,
            "journal_imported": self.journal_imported,
            "preference_imported": self.preference_imported,
            "project_imported": self.project_imported,
            "provenance_ok": self.provenance_ok,
            "provenance_missing": self.provenance_missing,
            "batches": self.batches,
            "duration_ms": self.duration_ms,
            "errors": list(self.errors)[:50],
            "mapped_count": len(self.mapping),
            "notes": list(self.notes)[:20],
            "authoritative": "legacy",
            "primary_enabled": False,
            "completeness_rate": (
                round(self.p0_mapped / self.p0_eligible, 4) if self.p0_eligible else None
            ),
        }


_LAST_REPORT: HarvestReport | None = None


def last_harvest_report() -> dict[str, Any] | None:
    return _LAST_REPORT.to_public() if _LAST_REPORT else None


def _parse_ts(ts: Any) -> float:
    if ts is None:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    text = str(ts).strip()
    if not text:
        return 0.0
    try:
        from datetime import datetime

        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _is_journal(entry: dict[str, Any]) -> bool:
    try:
        from jarvis.modules.memory_common import is_journal_entry

        return bool(is_journal_entry(entry))
    except Exception:
        tags = {str(t).lower() for t in (entry.get("tags") or [])}
        ns = str(entry.get("namespace") or "").lower()
        return "journal" in tags or ns.startswith("journal")


def _should_skip(entry: dict[str, Any]) -> str | None:
    content = str(entry.get("content") or "").strip()
    if not content:
        return "empty"
    tags = {str(t).lower() for t in (entry.get("tags") or [])}
    if tags & _SKIP_TAGS:
        return "telemetry"
    ns = str(entry.get("namespace") or "").lower()
    if ns in _SKIP_NAMESPACES:
        return "namespace_policy"
    etype = str(entry.get("type") or "")
    if etype in ("strategy",) and ns in ("tools", "jarvis"):
        return "host_policy_strategy"
    return None


def _priority(entry: dict[str, Any]) -> str:
    etype = str(entry.get("type") or "fact")
    ns = str(entry.get("namespace") or "default")
    tags = {str(t).lower() for t in (entry.get("tags") or [])}
    if etype in ("fact", "preference", "note", "auto") or ns == "profile" or "superseded" in tags:
        return "P0"
    if (
        _is_journal(entry)
        or etype == "project"
        or ns
        in (
            "experience",
            "relationships",
            "teaching",
            "corrections",
            "observed",
            "workflows",
            "journal-learned",
        )
        or ns.startswith("project")
    ):
        return "P1"
    return "P2"


def _encode_kind(entry: dict[str, Any]) -> str:
    etype = str(entry.get("type") or "fact")
    ns = str(entry.get("namespace") or "")
    tags = {str(t).lower() for t in (entry.get("tags") or [])}
    if etype == "preference":
        return "preference"
    if etype == "identity" or (ns == "profile" and ("identity" in tags or "name" in tags)):
        return "identity"
    if ns == "profile" and etype in ("fact", "note"):
        # High-impact profile facts may still be identity-classified by ACM
        return (
            "identity"
            if any(k in (entry.get("content") or "").lower() for k in ("my name", "i am", "i'm"))
            else "experience"
        )
    return "experience"


def _context_tags(entry: dict[str, Any]) -> tuple[str, ...]:
    tags = [str(t) for t in (entry.get("tags") or []) if t]
    ns = entry.get("namespace")
    out: list[str] = []
    for t in tags:
        if str(t).startswith("revises:"):
            continue
        out.append(str(t))
    if ns:
        out.append(f"ns:{ns}")
    etype = str(entry.get("type") or "fact")
    out.append(f"legacy_type:{etype}")
    out.append(f"legacy_id:{entry.get('id')}")
    out.append("provenance:legacy_import")
    if _is_journal(entry):
        out.append("journal")
    # explicit parent link convention (known lineage only)
    revises = _revises_legacy_id(entry)
    if revises:
        out.append(f"revises_legacy:{revises}")
    return tuple(dict.fromkeys(out))


def _revises_legacy_id(entry: dict[str, Any]) -> str | None:
    for t in entry.get("tags") or []:
        s = str(t)
        if s.startswith("revises:"):
            return s.split(":", 1)[1].strip() or None
    meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
    for key in ("revises_legacy_id", "supersedes", "revises_id"):
        if meta.get(key):
            return str(meta[key])
    return None


def _legacy_id_from_experience(exp: Any) -> str | None:
    """Return the harvest legacy_id tag (last wins if multiple — should be unique post-fix)."""
    tags = list(getattr(exp, "context_tags", ()) or ())
    found: str | None = None
    for t in tags:
        m = _LEGACY_ID_RE.match(str(t))
        if m:
            found = m.group(1)
    meta = exp.meta_dict() if hasattr(exp, "meta_dict") else {}
    if meta.get("legacy_id"):
        return str(meta["legacy_id"])
    return found


def find_experience_by_legacy_id(engine: Any, legacy_id: str) -> str | None:
    for exp in engine.store.experiences.values():
        if _legacy_id_from_experience(exp) == legacy_id:
            return exp.id
    return None


def index_legacy_ids(engine: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    for exp in engine.store.experiences.values():
        lid = _legacy_id_from_experience(exp)
        if lid:
            out[lid] = exp.id
    return out


def _stamp_legacy_import(engine: Any, experience_id: str, legacy_id: str) -> bool:
    from aria_acm.acm.provenance import ProvenanceSource, stamp_provenance

    stamp_provenance(
        engine.store,
        artifact_kind="experience",
        artifact_id=experience_id,
        origin=ProvenanceSource.LEGACY_IMPORT,
        experience_ids=[experience_id],
        explain=f"Harvested from Aria MemoryStore legacy_id={legacy_id}",
    )
    # attach metadata on provenance record
    for rec in engine.store.provenance.values():
        if rec.artifact_id == experience_id and rec.origin == ProvenanceSource.LEGACY_IMPORT:
            rec.metadata["legacy_id"] = legacy_id
            rec.fabricated = False
            return True
    return False


def _verify_provenance(engine: Any, experience_id: str) -> bool:
    try:
        rows = engine.provenance_of(experience_id)
        if not rows:
            return False
        return all(not r.get("fabricated") for r in rows)
    except Exception:
        return False


def export_legacy_entries() -> tuple[list[dict[str, Any]], str]:
    """Export MemoryStore entries + checksum of stable serialization."""
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore()
    entries = store.list_entries() if hasattr(store, "list_entries") else []
    # Stable ordering for checksum
    serialized = json.dumps(entries, sort_keys=True, default=str)
    checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return list(entries), checksum


def _sort_for_harvest(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Superseded (older corrections) before active; oldest→newest within groups."""

    def key(e: dict[str, Any]) -> tuple[int, float]:
        tags = {str(t).lower() for t in (e.get("tags") or [])}
        superseded = 0 if "superseded" in tags else 1
        return (superseded, _parse_ts(e.get("timestamp")))

    return sorted(entries, key=key)


def harvest_into_acm(
    *,
    dry_run: bool = False,
    batch_size: int = BATCH_SIZE_DEFAULT,
    assent_identity: bool = True,
    priorities: frozenset[str] | None = None,
    entries: list[dict[str, Any]] | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Operator harvest: MemoryStore → ACM Experiences (idempotent).

    Does not flip ARIA_ACM_PRIMARY. Does not delete legacy. Does not auto-start.
    """
    global _LAST_REPORT
    prios = priorities or frozenset({"P0", "P1"})
    t0 = time.perf_counter()
    report = HarvestReport(freeze_ts=time.time())
    report.notes.append("authoritative remains legacy through M2")

    if entries is None:
        source, checksum = export_legacy_entries()
    else:
        source = list(entries)
        checksum = hashlib.sha256(
            json.dumps(source, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
    report.legacy_checksum = checksum
    report.source_count = len(source)

    selected: list[dict[str, Any]] = []
    for e in source:
        reason = _should_skip(e)
        if reason == "empty":
            report.skipped_empty += 1
            continue
        if reason:
            report.skipped_policy += 1
            continue
        p = _priority(e)
        if p == "P0":
            report.p0_count += 1
        if p not in prios:
            report.skipped_policy += 1
            continue
        selected.append(e)

    selected = _sort_for_harvest(selected)

    if dry_run:
        report.notes.append(f"dry_run selected={len(selected)}")
        report.duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        report.ok = True
        _LAST_REPORT = report
        return report.to_public()

    engine = acm_bridge.get_engine()
    # Preflight ACM backup snapshot when durable
    try:
        if engine.durable is not None:
            engine.flush(kind="pre_harvest")
    except Exception as exc:
        report.notes.append(f"pre_harvest_flush:{type(exc).__name__}")

    existing = index_legacy_ids(engine)
    report.mapping.update(existing)

    batch: list[dict[str, Any]] = []
    for entry in selected:
        batch.append(entry)
        if len(batch) >= max(1, batch_size):
            _process_batch(engine, batch, report, assent_identity=assent_identity)
            report.batches += 1
            batch = []
            try:
                if engine.durable is not None:
                    engine.flush(kind="harvest_batch")
            except Exception as exc:
                report.ok = False
                report.errors.append(f"batch_flush:{type(exc).__name__}")
                break
    if batch and report.ok:
        _process_batch(engine, batch, report, assent_identity=assent_identity)
        report.batches += 1
        try:
            if engine.durable is not None:
                engine.flush(kind="harvest_final")
        except Exception as exc:
            report.notes.append(f"final_flush:{type(exc).__name__}")

    # Completeness vs P0 expected mapping
    p0_ids = {str(e.get("id")) for e in selected if _priority(e) == "P0" and e.get("id")}
    report.p0_eligible = len(p0_ids)
    report.p0_mapped = sum(1 for i in p0_ids if i in report.mapping)
    if report.p0_eligible:
        rate = report.p0_mapped / report.p0_eligible
        report.notes.append(f"p0_mapped={report.p0_mapped}/{report.p0_eligible} rate={rate:.4f}")
        if rate < 0.995:
            gap = report.p0_eligible - report.p0_mapped
            if gap > report.encode_failures:
                report.ok = False
                report.errors.append(f"completeness_below_gate rate={rate:.4f}")

    report.duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    _LAST_REPORT = report
    public = report.to_public()
    if report_path:
        path = Path(report_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(public, indent=2), encoding="utf-8")
        report.notes.append(f"report_written:{path}")
        public = report.to_public()
    return public


def _process_batch(
    engine: Any,
    batch: list[dict[str, Any]],
    report: HarvestReport,
    *,
    assent_identity: bool,
) -> None:
    for entry in batch:
        legacy_id = str(entry.get("id") or "")
        if not legacy_id:
            report.skipped_empty += 1
            continue
        if legacy_id in report.mapping:
            report.skipped_existing += 1
            continue
        existing = find_experience_by_legacy_id(engine, legacy_id)
        if existing:
            report.mapping[legacy_id] = existing
            report.skipped_existing += 1
            continue

        revises_legacy = _revises_legacy_id(entry)
        revises_exp = report.mapping.get(revises_legacy or "") if revises_legacy else None
        if revises_legacy and not revises_exp:
            report.unresolved_supersedes += 1

        kind = _encode_kind(entry)
        tags = _context_tags(entry)
        t_start = _parse_ts(entry.get("timestamp")) or None
        try:
            # Isolate ContextFrame so prior harvest tags do not bleed (literal ACM merge behavior).
            from aria_acm.acm.context.frame import ContextFrame

            engine.context = ContextFrame()
            result = engine.encode(
                str(entry.get("content") or ""),
                kind=kind,
                pin=True,
                context_tags=tags,
                assent=False,
                revises_id=revises_exp,
                t_start=t_start,
            )
        except Exception as exc:
            report.encode_failures += 1
            report.errors.append(f"encode:{legacy_id}:{type(exc).__name__}")
            continue

        if not (result.get("encoded") or result.get("experience_id")):
            report.encode_failures += 1
            report.errors.append(f"encode_skip:{legacy_id}:{result.get('reason')}")
            continue

        exp_id = str(result.get("experience_id"))
        report.mapping[legacy_id] = exp_id
        report.imported += 1
        if revises_exp:
            report.revised += 1
        if _is_journal(entry):
            report.journal_imported += 1
        if str(entry.get("type")) == "preference":
            report.preference_imported += 1
        if str(entry.get("type")) == "project" or str(entry.get("namespace") or "").startswith(
            "project"
        ):
            report.project_imported += 1
            try:
                engine.open_goal(
                    (str(entry.get("content") or "")[:80] or f"project:{legacy_id}"),
                    importance=0.6,
                )
                report.goals_opened += 1
            except Exception as exc:
                report.notes.append(f"goal:{type(exc).__name__}")

        if _stamp_legacy_import(engine, exp_id, legacy_id):
            if _verify_provenance(engine, exp_id):
                report.provenance_ok += 1
            else:
                report.provenance_missing += 1
        else:
            report.provenance_missing += 1

        # Identity high-impact assent
        identity = result.get("identity") if isinstance(result.get("identity"), dict) else {}
        proposal_id = identity.get("proposal_id")
        if proposal_id:
            report.identity_proposals += 1
            if assent_identity:
                try:
                    ass = engine.assent_identity(str(proposal_id))
                    if ass.get("assented"):
                        report.identity_assented += 1
                except Exception as exc:
                    report.errors.append(f"assent:{type(exc).__name__}")
