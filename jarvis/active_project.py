"""Persist active project workspace slug."""

from __future__ import annotations

import json
from pathlib import Path

from jarvis.config import DATA_DIR

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


def apply_active_project_effects(assistant, slug: str | None) -> None:
    assistant.session.note_memory_namespace("default")
    if not slug:
        return
    root = coding_root_for_slug(slug)
    if root:
        assistant.session.note_coding_root(str(root))


def get_active_slug() -> str:
    if not ACTIVE_FILE.is_file():
        return ""
    try:
        data = json.loads(ACTIVE_FILE.read_text(encoding="utf-8"))
        return str(data.get("slug") or "").strip()
    except (json.JSONDecodeError, OSError):
        return ""


def set_active_slug(slug: str | None) -> dict[str, str]:
    from jarvis.project_registry import get_project

    slug = str(slug or "").strip()
    if slug:
        meta = get_project(slug)
        if not meta:
            raise ValueError(f"Unknown project: {slug}")
        if meta.get("archived"):
            raise ValueError(f"Project is archived: {slug}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"slug": slug}
    ACTIVE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        from jarvis.assistant_instance import get_assistant

        apply_active_project_effects(get_assistant(), slug)
    except Exception:
        pass
    return payload


def get_active_project():
    slug = get_active_slug()
    if not slug:
        return None
    from jarvis.project_registry import get_project

    return get_project(slug)


def browser_session_dir() -> str:
    slug = get_active_slug()
    from jarvis.project_registry import PROJECTS_ROOT, project_dir

    if not slug:
        path = PROJECTS_ROOT / "_default" / "browser"
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    path = project_dir(slug) / "browser"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
