"""Proposal quality brief — pre-Apply operator summary."""

from __future__ import annotations

from typing import Any


_SENSITIVE_HINTS = (
    "auth",
    "password",
    "secret",
    "token",
    "migrate",
    "schema",
    "database",
    "payment",
    "delete",
    "rmtree",
    "drop table",
    "permission",
    "security",
)


def build_quality_brief(
    proposal: dict[str, Any],
    *,
    base_path: str | None = None,
    test_impact: str = "",
) -> dict[str, Any]:
    """Build a concise risk/confidence brief for a proposal."""
    files = proposal.get("files") or []
    if not files and proposal.get("path"):
        files = [{"path": proposal["path"], "code": proposal.get("code", "")}]

    paths = [str(f.get("path") or "") for f in files if f.get("path")]
    deletes = [str(f.get("path")) for f in files if f.get("delete") and f.get("path")]
    total_lines = 0
    for f in files:
        code = f.get("code") or ""
        total_lines += len(code.splitlines())

    syntax_ok = proposal.get("syntax_ok")
    mode = proposal.get("mode") or "propose"
    blob = " ".join(paths + [proposal.get("explanation") or "", mode]).lower()
    breaking = bool(deletes) or any(h in blob for h in _SENSITIVE_HINTS)

    # Heuristic risk
    risk = "low"
    risk_score = 0.2
    if len(paths) >= 5 or total_lines > 400:
        risk = "medium"
        risk_score = 0.5
    if len(paths) >= 10 or total_lines > 1200 or breaking or deletes:
        risk = "high"
        risk_score = 0.8
    if syntax_ok is False:
        risk = "high"
        risk_score = max(risk_score, 0.85)

    confidence = 0.75
    if syntax_ok is False:
        confidence = 0.35
    elif syntax_ok is True:
        confidence = 0.82
    if mode in ("agent", "refactor") and len(paths) > 3:
        confidence = min(confidence, 0.65)
    if proposal.get("verified") is True:
        confidence = min(0.95, confidence + 0.1)

    suggested_verify: list[str] = []
    if any(p.endswith(".py") for p in paths):
        suggested_verify.append("Run syntax check on changed Python files")
        suggested_verify.append("Run related pytest targets")
    if any(p.endswith((".js", ".mjs", ".ts", ".tsx")) for p in paths):
        suggested_verify.append("Run lint / syntax check on JS/TS files")
    if any("test_" in p or p.startswith("tests/") for p in paths):
        suggested_verify.append("Execute the modified tests")
    if not suggested_verify:
        suggested_verify.append("Spot-check the diff and re-open affected UI/API paths")
    if breaking:
        suggested_verify.insert(0, "Review breaking-change / security-sensitive paths carefully")

    recommended_tests: list[str] = []
    if test_impact:
        for line in test_impact.splitlines():
            line = line.strip().lstrip("-* ").strip()
            if line and ("test" in line.lower() or line.endswith(".py")):
                recommended_tests.append(line[:200])
        recommended_tests = recommended_tests[:8]

    return {
        "ok": True,
        "files_affected": paths,
        "file_count": len(paths),
        "lines_proposed": total_lines,
        "deletes": deletes,
        "estimated_risk": risk,
        "risk_score": round(risk_score, 2),
        "confidence": round(confidence, 2),
        "confidence_label": (
            "high" if confidence >= 0.75 else "medium" if confidence >= 0.5 else "low"
        ),
        "breaking_change_warning": breaking,
        "breaking_reasons": [
            *(["Includes file deletions"] if deletes else []),
            *(["Touches sensitive / auth / schema paths"] if breaking and not deletes else []),
        ],
        "suggested_verification_steps": suggested_verify,
        "recommended_tests": recommended_tests,
        "syntax_ok": syntax_ok,
        "mode": mode,
        "summary": (proposal.get("explanation") or "")[:300],
        "write_base": base_path or "",
    }


def brief_for_id(assistant: Any, proposal_id: str) -> dict[str, Any]:
    prop = (assistant.pending_proposals or {}).get(proposal_id)
    if not prop:
        from jarvis.coding_product.history import get_proposal

        hist = get_proposal(proposal_id)
        if not hist:
            return {"ok": False, "error": "Proposal not found"}
        prop = {
            "files": hist.get("files_payload") or [{"path": p, "code": ""} for p in (hist.get("files") or [])],
            "explanation": hist.get("summary"),
            "syntax_ok": hist.get("syntax_ok"),
            "mode": hist.get("mode"),
        }
    base = ""
    try:
        base = str(assistant.coding._base())
    except Exception:
        pass
    impact = ""
    try:
        from jarvis.coding_test_impact import format_test_impact
        from jarvis import fs

        py_files = [
            fs.resolve_path(f["path"], base=assistant.coding._base())
            for f in (prop.get("files") or [])
            if (f.get("path") or "").endswith(".py")
        ]
        impact = format_test_impact(py_files, assistant.coding._base()) or ""
    except Exception:
        impact = ""
    brief = build_quality_brief(prop, base_path=base, test_impact=impact)
    brief["proposal_id"] = proposal_id
    return brief
