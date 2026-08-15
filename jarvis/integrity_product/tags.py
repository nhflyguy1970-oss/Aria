"""Metadata helpers — every QA object should carry these fields when possible."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jarvis.integrity_product.terminology import ARTIFACT_TYPES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def artifact_metadata(
    *,
    artifact_type: str,
    creation_reason: str,
    created_by: str = "aria",
    environment: str = "qa",
    qa_run_id: str = "",
    smoke_id: str = "",
    certification_id: str = "",
    expiration: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical metadata block for development artifacts."""
    kind = (artifact_type or "qa").strip().lower()
    if kind not in ARTIFACT_TYPES:
        kind = "qa"
    meta = {
        "qa_artifact": True,
        "artifact_type": kind,
        "origin": kind if kind != "temporary" else "qa",
        "environment": (environment or "qa").strip().lower() or "qa",
        "created_by": created_by or "aria",
        "creation_reason": (creation_reason or "").strip() or "development",
        "created_at": _now(),
        "qa_run_id": qa_run_id or "",
        "smoke_id": smoke_id or "",
        "certification_id": certification_id or "",
        "expiration": expiration or "",
    }
    if extra:
        meta.update({k: v for k, v in extra.items() if k not in meta or v})
    return meta


def looks_like_dev_label(text: str | None) -> bool:
    """Heuristic for titles/names that are clearly development-only."""
    import re

    t = (text or "").strip().lower()
    if not t:
        return False
    if re.search(
        r"\b(lorem\s+ipsum|placeholder|dummy|fake\s+notif|sample\s+ocr|"
        r"qa\s+workflow|cert\s+proj|onetruth\s+proj|smoke\s+test|"
        r"lead\s+qa|workflow\s+probe|demo-skill-check|"
        r"qa\s+aria\s+cross|aria\s+cross\s+event|"
        r"qa_full|qa-task-|consis_|p64jl_|p64test|p64verify|p64mem|"
        r"cert-bullet|cert-mood|cert-gratitude|cert-cal-|cert-journal|"
        r"oc-direct|oc-cert|wf_probe|audit-room|"
        r"workflow-cal-event|ariacross\d*|ariavalidation\d*|"
        r"jdiag-|enter-test-|replace-probe-|api-check-|direct-\d|"
        r"seq\d+-|certj-|pytest journal|broken_calc|ship-j-|"
        r"phase\s*7\s*residency|fnaccept\s+doc|xyzzyqqq)\b",
        t,
    ):
        return True
    if re.search(
        r"\b(aria-repair|aria-final|aria-triage|aria-jeff-rw|ariaok-|aria-exp|aria-exc|"
        r"audit-room|oc-cert-project|wf_probe|p64testmed|p64verify)\b",
        t,
    ):
        return True
    if re.match(
        r"^(qa|cert|smoke|demo|test|prototype|sample|consis|p64jl|onetruth|"
        r"jdiag|enter-test|replace-probe|api-check|seq\d+|certj|workflow-cal|ship-j|"
        r"aria-repair|aria-final|aria-triage|audit-room)[-_\s]",
        t,
    ):
        return True
    # Timestamped probe tokens: name-1785443121242 or name-name-1785…
    if re.match(r"^[a-z][a-z0-9_-]{1,40}-\d{10,}$", t):
        return True
    if re.search(r"-\d{10,}$", t) and re.search(r"\b(aria-|qa-|cert-|audit-|p64|oc-|wf_|fnaccept)", t):
        return True
    if "xyzzyqqq" in t or "fnaccept" in t or "aria-exc" in t or "aria-exp" in t:
        return True
    return False
