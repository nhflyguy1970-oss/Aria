"""Production Integrity Score — informational, always backed by evidence."""

from __future__ import annotations

from typing import Any

from jarvis.integrity_product.terminology import STATUS_ATTENTION, STATUS_CLEAN, STATUS_WARNING

# Jeff-facing sections (Mission Control expansion).
SECTIONS = (
    "workspace",
    "health",
    "projects",
    "documents",
    "gallery",
    "planner",
    "calendar",
    "notifications",
    "mission_control",
    "certification",
)

# Map finding.category → score section(s)
_CATEGORY_TO_SECTIONS: dict[str, tuple[str, ...]] = {
    "health": ("health", "workspace"),
    "projects": ("projects", "workspace"),
    "documents": ("documents", "workspace"),
    "gallery": ("gallery", "workspace"),
    "planner": ("planner", "workspace"),
    "calendar": ("calendar", "workspace"),
    "notifications": ("notifications", "workspace"),
    "files": ("workspace", "certification"),
    "workflows": ("workspace", "certification"),
    "journal": ("workspace",),
}


def _section_status(count: int, *, healthish: bool = False) -> str:
    if count <= 0:
        return STATUS_CLEAN
    if healthish or count >= 3:
        return STATUS_ATTENTION
    return STATUS_WARNING


def compute_score(scan: dict[str, Any] | None) -> dict[str, Any]:
    """
    Overall 0–100 integrity score. Informational only — never hides findings.
    100 = clean. Deductions scale with severity/category; evidence always attached.
    """
    scan = scan or {}
    findings = list(scan.get("findings") or [])
    by_cat = dict((scan.get("counts") or {}).get("by_category") or {})

    score = 100
    deductions: list[dict[str, Any]] = []
    for f in findings:
        cat = str(f.get("category") or "other")
        uncertain = bool(f.get("uncertain") or not f.get("safe_to_remove"))
        if uncertain:
            delta = 5 if cat == "health" else 3
        elif cat == "health":
            delta = 20
        elif cat in ("projects", "documents", "gallery"):
            delta = 10
        elif cat in ("workflows", "files", "journal"):
            delta = 6
        else:
            delta = 5
        score -= delta
        deductions.append(
            {
                "title": f.get("title"),
                "category": cat,
                "delta": -delta,
                "confidence": f.get("confidence"),
                "evidence": (f.get("evidence") or [])[:3],
            }
        )
    score = max(0, min(100, score))

    section_counts: dict[str, int] = {s: 0 for s in SECTIONS}
    section_evidence: dict[str, list[str]] = {s: [] for s in SECTIONS}
    for f in findings:
        cat = str(f.get("category") or "other")
        targets = _CATEGORY_TO_SECTIONS.get(cat, ("workspace",))
        for sec in targets:
            section_counts[sec] = section_counts.get(sec, 0) + 1
            if len(section_evidence[sec]) < 5:
                section_evidence[sec].append(str(f.get("title") or cat))

    sections: dict[str, Any] = {}
    for sec in SECTIONS:
        n = section_counts.get(sec, 0)
        st = _section_status(n, healthish=(sec == "health" and n > 0))
        sections[sec] = {
            "status": st,
            "artifacts": n,
            "evidence": section_evidence.get(sec) or ([] if n == 0 else ["see findings"]),
        }

    # Certification section: dirty workspace = attention for ship readiness
    if findings:
        sections["certification"] = {
            "status": STATUS_ATTENTION if any(f.get("category") == "health" for f in findings) or len(findings) >= 3 else STATUS_WARNING,
            "artifacts": len(findings),
            "evidence": [f"READY_TO_SHIP blocked while {len(findings)} development artifact(s) remain"],
        }
    else:
        sections["certification"] = {
            "status": STATUS_CLEAN,
            "artifacts": 0,
            "evidence": ["No development artifacts — certification integrity gate clear"],
        }

    overall_status = scan.get("status") or (STATUS_CLEAN if score == 100 else STATUS_WARNING if score >= 70 else STATUS_ATTENTION)
    return {
        "overall": score,
        "status": overall_status,
        "max": 100,
        "informational_only": True,
        "hides_problems": False,
        "artifacts": len(findings),
        "by_category": by_cat,
        "deductions": deductions[:40],
        "sections": sections,
        "note": "Score never hides problems. Open findings and Guided Repair for details.",
    }
