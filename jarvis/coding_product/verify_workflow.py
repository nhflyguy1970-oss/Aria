"""Post-apply verification workflow — requires operator approval before execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any


VERIFY_ACTIONS = ("syntax", "lint", "tests", "build", "summary")


def build_verify_offer(
    *,
    applied_paths: list[str],
    base: Path | str | None = None,
    proposal_id: str = "",
) -> dict[str, Any]:
    """Offer verification choices after Apply (never auto-run)."""
    paths = [p for p in applied_paths if p]
    py = [p for p in paths if p.endswith(".py")]
    js = [p for p in paths if p.endswith((".js", ".mjs", ".cjs", ".ts", ".tsx"))]
    options = [
        {
            "id": "syntax",
            "label": "Syntax check",
            "description": "Parse/check changed files for syntax errors",
            "recommended": True,
        },
        {
            "id": "tests",
            "label": "Run tests",
            "description": "Run related pytest targets for changed Python files",
            "recommended": bool(py),
            "available": bool(py),
        },
        {
            "id": "lint",
            "label": "Lint",
            "description": "Run available linters on changed files",
            "recommended": False,
        },
        {
            "id": "build",
            "label": "Build",
            "description": "Run project build if a runner is configured",
            "recommended": False,
        },
        {
            "id": "summary",
            "label": "Verification summary",
            "description": "Collect a short status of checks without running heavy suites",
            "recommended": True,
        },
    ]
    return {
        "ok": True,
        "requires_approval": True,
        "proposal_id": proposal_id,
        "applied_paths": paths,
        "base": str(base or ""),
        "options": options,
        "message": "Choose verification steps. Nothing runs until you approve.",
        "js_hint": bool(js),
    }


def run_verify(
    assistant: Any,
    *,
    actions: list[str],
    paths: list[str] | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    """Execute operator-approved verification actions."""
    if not approved:
        return {
            "ok": False,
            "error": "Verification requires explicit operator approval.",
            "requires_approval": True,
        }
    base = assistant.coding._base()
    from jarvis import fs
    from jarvis.coding_verify import verify_python_files
    from jarvis.syntax_check import check_files, format_diagnostics

    selected = [a for a in actions if a in VERIFY_ACTIONS]
    if not selected:
        return {"ok": False, "error": "No valid verification actions selected."}

    target_paths = paths or []
    if not target_paths and getattr(assistant, "last_apply_backups", None):
        target_paths = [b.get("path") for b in assistant.last_apply_backups if b.get("path")]

    results: dict[str, Any] = {}
    overall_ok = True

    if "summary" in selected:
        results["summary"] = {
            "paths": target_paths,
            "base": str(base),
            "note": "Summary only — other selected actions run below.",
        }

    file_items = []
    for p in target_paths:
        try:
            content = fs.read_file(p, base=base)
            if content.startswith("ERROR:"):
                continue
            file_items.append({"path": p, "code": content})
        except Exception:
            continue

    if "syntax" in selected:
        diags = check_files(file_items, base, deep=False, skip_typecheck=True) if file_items else []
        summary = format_diagnostics(diags) if diags else "**syntax:** ok (nothing to check)"
        has_err = any(getattr(d, "severity", None) == "error" or (isinstance(d, dict) and d.get("severity") == "error") for d in diags)
        results["syntax"] = {"ok": not has_err, "message": summary}
        overall_ok = overall_ok and not has_err

    if "lint" in selected:
        # Deep syntax_check approximates lint for local appliance
        diags = check_files(file_items, base, deep=True, skip_typecheck=True) if file_items else []
        summary = format_diagnostics(diags) if diags else "**lint:** ok"
        has_err = any(getattr(d, "severity", None) == "error" or (isinstance(d, dict) and d.get("severity") == "error") for d in diags)
        results["lint"] = {"ok": not has_err, "message": summary}
        overall_ok = overall_ok and not has_err

    if "tests" in selected:
        py_files = [
            fs.resolve_path(p, base=base)
            for p in target_paths
            if p.endswith(".py") and not Path(p).name.startswith("test_")
        ]
        msg = verify_python_files(py_files, base, run_scripts=False) if py_files else "No Python sources to test."
        failed = "failed" in (msg or "").lower() or "syntax check failed" in (msg or "").lower()
        results["tests"] = {"ok": not failed, "message": msg or "No tests run."}
        overall_ok = overall_ok and not failed

    if "build" in selected:
        try:
            from jarvis.project_runner import runner_info, run_script

            info = runner_info(base) or {}
            build_cmd = info.get("build") or info.get("build_script")
            if build_cmd:
                # Prefer documenting; only run if path-like script exists
                script = Path(base) / str(build_cmd)
                if script.is_file():
                    result = run_script(script, base, timeout=120)
                    results["build"] = {
                        "ok": result.returncode == 0,
                        "message": ((result.stdout or "") + (result.stderr or ""))[:2000],
                    }
                    overall_ok = overall_ok and result.returncode == 0
                else:
                    results["build"] = {
                        "ok": True,
                        "message": f"Build script configured as `{build_cmd}` but not executed (path missing). Approve a specific script in Chat if needed.",
                        "skipped": True,
                    }
            else:
                results["build"] = {
                    "ok": True,
                    "message": "No build runner configured for this project.",
                    "skipped": True,
                }
        except Exception as exc:
            results["build"] = {"ok": False, "message": str(exc)}
            overall_ok = False

    status = "passed" if overall_ok else "failed"
    return {
        "ok": overall_ok,
        "verification_status": status,
        "results": results,
        "actions": selected,
        "paths": target_paths,
        "message": f"Verification {status}.",
        "requires_approval": False,
    }
