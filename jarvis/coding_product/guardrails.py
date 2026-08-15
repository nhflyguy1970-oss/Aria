"""Coding-root guardrails — never leave write location ambiguous."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _norm(path: str | Path | None) -> str:
    if not path:
        return ""
    try:
        return str(Path(path).expanduser().resolve())
    except OSError:
        return str(path).strip()


def assess_coding_root(assistant: Any | None = None) -> dict[str, Any]:
    """Return active project / coding root / repo / branch with warnings."""
    from jarvis.active_project import get_active_slug, identity_for_slug

    slug = ""
    try:
        slug = get_active_slug() or ""
    except Exception:
        slug = ""
    identity = identity_for_slug(slug)
    project_root = _norm(identity.get("coding_root") or identity.get("git_path") or "")
    session_root = ""
    engine_root = ""
    if assistant is not None:
        try:
            session_root = _norm(getattr(assistant.session, "coding_root", "") or "")
        except Exception:
            session_root = ""
        try:
            engine_root = _norm(assistant.coding._base())
        except Exception:
            engine_root = ""

    # Prefer project identity, then session, then engine base
    active_root = project_root or session_root or engine_root
    roots_seen = {r for r in (project_root, session_root, engine_root) if r}

    warnings: list[dict[str, str]] = []
    severity = "ok"

    if not active_root:
        warnings.append(
            {
                "code": "no_coding_root",
                "level": "error",
                "message": "No coding root selected. Open Projects and set an active workspace before applying changes.",
            }
        )
        severity = "error"
    elif len(roots_seen) > 1:
        warnings.append(
            {
                "code": "multiple_roots",
                "level": "warn",
                "message": (
                    "Multiple coding roots detected "
                    f"(project={project_root or '—'}, session={session_root or '—'}, "
                    f"engine={engine_root or '—'}). Writes use the engine base."
                ),
            }
        )
        severity = "warn" if severity == "ok" else severity

    if project_root and engine_root and project_root != engine_root:
        try:
            Path(engine_root).relative_to(project_root)
            outside = False
        except ValueError:
            outside = True
        if outside:
            warnings.append(
                {
                    "code": "root_outside_project",
                    "level": "error",
                    "message": (
                        f"Engine write base `{engine_root}` is outside the active project "
                        f"coding root `{project_root}`. Unexpected location — confirm before Apply."
                    ),
                }
            )
            severity = "error"

    if active_root and engine_root and active_root != engine_root and severity == "ok":
        warnings.append(
            {
                "code": "unexpected_write_location",
                "level": "warn",
                "message": f"Writes go to `{engine_root}` (engine base), not `{active_root}`.",
            }
        )
        severity = "warn"

    repo = False
    branch = ""
    git_status = ""
    if active_root or engine_root:
        try:
            import subprocess

            from jarvis import git_util

            root_path = Path(engine_root or active_root)
            repo = git_util.is_repo(root_path)
            if repo:
                branch = git_util.current_branch(root_path) or ""
                # Bound UI status — full-tree `git status` can hang the Coding Room.
                st = subprocess.run(
                    ["git", "-C", str(root_path), "status", "-sb"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                )
                git_status = ((st.stdout or "") + (st.stderr or "")).strip()[:500]
        except Exception as exc:
            warnings.append(
                {
                    "code": "git_unavailable",
                    "level": "info",
                    "message": f"Git summary unavailable: {exc}",
                }
            )

    return {
        "ok": severity != "error",
        "severity": severity,
        "active_project": {
            "slug": identity.get("slug") or "",
            "title": identity.get("title") or identity.get("slug") or "",
        },
        "coding_root": active_root,
        "project_coding_root": project_root,
        "session_coding_root": session_root,
        "engine_base": engine_root,
        "write_target": engine_root or active_root,
        "repository": {
            "is_repo": repo,
            "path": engine_root or active_root,
            "branch": branch,
            "status_short": git_status,
        },
        "warnings": warnings,
        "ambiguous": severity != "ok",
    }


def guardrail_banner(assessment: dict[str, Any] | None = None, assistant: Any | None = None) -> str:
    """Human-readable one-liner for UI banners."""
    a = assessment or assess_coding_root(assistant)
    if a.get("severity") == "error":
        msgs = [w["message"] for w in a.get("warnings") or [] if w.get("level") == "error"]
        return msgs[0] if msgs else "Coding root not safe to write."
    if a.get("warnings"):
        return a["warnings"][0]["message"]
    root = a.get("write_target") or a.get("coding_root") or "—"
    branch = (a.get("repository") or {}).get("branch") or ""
    proj = (a.get("active_project") or {}).get("title") or (a.get("active_project") or {}).get("slug") or "—"
    extra = f" · {branch}" if branch else ""
    return f"Coding in {proj} → `{root}`{extra}"
