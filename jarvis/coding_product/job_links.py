"""Job Center deep-link helpers for coding jobs (Coding owns results; Job Center owns queue UX)."""

from __future__ import annotations

from typing import Any


def coding_job_deep_links(job: dict[str, Any] | None) -> dict[str, Any]:
    """Build navigation targets for a coding job row."""
    job = job or {}
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    proposal_id = (
        result.get("proposal_id")
        or job.get("proposal_id")
        or ""
    )
    project_slug = job.get("project_slug") or ""
    return {
        "coding_home": "coding",
        "job_center": "jobs",
        "proposal": f"proposal:{proposal_id}" if proposal_id else "",
        "chat": "chat",
        "verify": "coding:verify" if proposal_id or job.get("done") else "",
        "undo": "coding:undo" if job.get("done") and result.get("type") == "applied" else "coding:undo",
        "project": f"projects:{project_slug}" if project_slug else "projects",
        "proposal_id": proposal_id,
    }


def enrich_coding_job(job: dict[str, Any]) -> dict[str, Any]:
    out = dict(job)
    links = coding_job_deep_links(job)
    out["deep_links"] = links
    if links.get("proposal_id"):
        out["proposal_id"] = links["proposal_id"]
    return out
