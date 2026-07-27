"""Persist active project workspace slug and apply unified identity effects."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.active_project")

ACTIVE_FILE = DATA_DIR / "active_project.json"


def coding_root_for_slug(slug: str | None) -> Path | None:
    from jarvis.project_registry import get_project, project_dir

    meta = get_project(slug or "")
    if not meta:
        return None
    git_path = str(meta.get("git_path") or "").strip()
    if git_path:
        p = Path(git_path).expanduser()
        if p.is_dir():
            return p.resolve()
    root = (meta.get("paths") or {}).get("root") or str(project_dir(slug or ""))
    p = Path(root)
    if p.is_dir():
        return p.resolve()
    return None


def identity_for_slug(slug: str | None) -> dict[str, Any]:
    """Single authority map for a project slug (empty slug = cleared workspace)."""
    from jarvis.project_registry import get_project, project_dir

    slug = (slug or "").strip()
    if not slug:
        return {
            "slug": "",
            "memory_namespace": "default",
            "knowledge_namespace": "",
            "coding_root": "",
            "git_path": "",
            "browser_session": str(browser_session_dir_for("")),
            "workspace_root": "",
            "checkpoint_namespace": "default",
        }
    meta = get_project(slug) or {}
    root = coding_root_for_slug(slug)
    git_path = str(meta.get("git_path") or "").strip()
    if not git_path and root:
        git_path = str(root)
    return {
        "slug": slug,
        "title": meta.get("title") or slug,
        "memory_namespace": slug,
        "knowledge_namespace": f"project:{slug}",
        "coding_root": str(root) if root else "",
        "git_path": git_path,
        "browser_session": str(browser_session_dir_for(slug)),
        "workspace_root": str(project_dir(slug)),
        "checkpoint_namespace": slug,
        "archived": bool(meta.get("archived")),
    }


def browser_session_dir_for(slug: str | None) -> Path:
    from jarvis.project_registry import PROJECTS_ROOT, project_dir

    slug = (slug or "").strip()
    if not slug:
        path = PROJECTS_ROOT / "_default" / "browser"
    else:
        path = project_dir(slug) / "browser"
    path.mkdir(parents=True, exist_ok=True)
    return path


def apply_active_project_effects(assistant, slug: str | None) -> dict[str, Any]:
    """Apply unified identity to session. Returns effects report (never silent)."""
    identity = identity_for_slug(slug)
    effects: dict[str, Any] = {"ok": True, "slug": identity["slug"], "changed": {}, "errors": []}

    def _note(label: str, fn, *args):
        try:
            fn(*args)
            effects["changed"][label] = args[0] if args else True
        except Exception as exc:
            effects["ok"] = False
            effects["errors"].append(f"{label}: {exc}")
            log.warning("apply_active_project_effects %s failed: %s", label, exc)

    ns = identity["memory_namespace"]
    _note("memory_namespace", assistant.session.note_memory_namespace, ns)
    effects["changed"]["checkpoint_namespace"] = ns
    kn = identity["knowledge_namespace"]
    if hasattr(assistant.session, "note_knowledge_namespace"):
        _note("knowledge_namespace", assistant.session.note_knowledge_namespace, kn)
    if hasattr(assistant.session, "note_project_slug"):
        _note("project_slug", assistant.session.note_project_slug, identity["slug"])
    if identity["coding_root"]:
        _note("coding_root", assistant.session.note_coding_root, identity["coding_root"])
    else:
        _note("coding_root", assistant.session.note_coding_root, "")
    if kn and hasattr(assistant.session, "note_knowledge"):
        try:
            assistant.session.note_knowledge(identity["slug"])
            effects["changed"]["knowledge_slug"] = identity["slug"]
        except Exception as exc:
            effects["errors"].append(f"knowledge_slug: {exc}")

    effects["identity"] = identity
    effects["browser_session"] = identity["browser_session"]
    effects["git_path"] = identity["git_path"]
    effects["workspace_root"] = identity["workspace_root"]
    return effects


def get_active_slug() -> str:
    if not ACTIVE_FILE.is_file():
        return ""
    try:
        data = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
        return str(data.get("slug") or "").strip()
    except (json.JSONDecodeError, OSError):
        return ""


def set_active_slug(slug: str | None) -> dict[str, Any]:
    from jarvis.project_registry import get_project, touch_project_opened

    slug = str(slug or "").strip()
    if slug:
        meta = get_project(slug)
        if not meta:
            raise ValueError(f"Unknown project: {slug}")
        if meta.get("archived"):
            raise ValueError(f"Project is archived: {slug}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"slug": slug}
    ACTIVE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    effects: dict[str, Any] = {"ok": True, "slug": slug, "changed": {}, "errors": []}
    try:
        from jarvis.assistant_instance import get_assistant

        effects = apply_active_project_effects(get_assistant(), slug)
    except Exception as exc:
        effects = {"ok": False, "slug": slug, "changed": {}, "errors": [str(exc)]}
        log.warning("set_active_slug effects failed: %s", exc)

    if slug:
        try:
            touch_project_opened(slug)
        except Exception as exc:
            effects.setdefault("errors", []).append(f"last_opened: {exc}")

    payload["effects"] = effects
    return payload


def get_active_project():
    slug = get_active_slug()
    if not slug:
        return None
    from jarvis.project_registry import get_project

    return get_project(slug)


def browser_session_dir() -> str:
    return str(browser_session_dir_for(get_active_slug()))
