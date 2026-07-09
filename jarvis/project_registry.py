"""Named project workspace registry — data/projects/{slug}/meta.json."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

PROJECTS_ROOT = DATA_DIR / "projects"
SUBDIRS = ("cad", "exports", "browser")


def _slugify(name: str | None) -> str:
    s = re.sub(r"[^\w\s-]", "", str(name or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s or "project")[:48]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def project_dir(slug: str | None) -> Path:
    return PROJECTS_ROOT / _slugify(slug)


def meta_path(slug: str | None) -> Path:
    return project_dir(slug) / "meta.json"


def _read_meta(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _write_meta(slug: str, meta: dict[str, Any]) -> None:
    root = project_dir(slug)
    root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (root / sub).mkdir(exist_ok=True)
    meta["slug"] = _slugify(slug)
    meta["updated"] = _now()
    meta_path(slug).write_text(json.dumps(meta, indent=2), encoding="utf-8")


def create_project(title: str | None, *, description: str = "", git_path: str | None = None) -> dict[str, Any]:
    slug = _slugify(title)
    if meta_path(slug).is_file():
        base = slug
        n = 2
        while meta_path(f"{base}-{n}").is_file():
            n += 1
        slug = f"{base}-{n}"
    now = _now()
    title = str(title or slug).strip()
    meta = {
        "slug": slug,
        "title": title,
        "description": str(description or "").strip(),
        "created": now,
        "updated": now,
        "archived": False,
        "git_path": git_path,
    }
    _write_meta(slug, meta)
    try:
        from jarvis.project_journal import ProjectJournal

        ProjectJournal(slug).ensure(title=meta["title"])
    except Exception:
        pass
    return meta


def get_project(slug: str | None) -> dict[str, Any] | None:
    path = meta_path(slug)
    if not path.is_file():
        return None
    meta = _read_meta(path)
    meta["paths"] = {
        "root": str(project_dir(slug)),
        "cad": str(project_dir(slug) / "cad"),
        "exports": str(project_dir(slug) / "exports"),
        "browser": str(project_dir(slug) / "browser"),
    }
    return meta


def list_projects(*, include_archived: bool = False) -> list[dict[str, Any]]:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    for child in sorted(PROJECTS_ROOT.iterdir()):
        if not child.is_dir():
            continue
        meta = get_project(child.name)
        if not meta:
            continue
        if meta.get("archived") and not include_archived:
            continue
        out.append(meta)
    out.sort(key=lambda m: m.get("updated") or "", reverse=True)
    return out


def archive_project(slug: str, *, archived: bool = True) -> bool:
    meta = get_project(slug)
    if not meta:
        return False
    meta["archived"] = bool(archived)
    _write_meta(slug, meta)
    return True


def import_git_repo(path: str | None, *, title: str | None = None) -> dict[str, Any]:
    from jarvis.git_util import is_repo

    repo = Path(path or "").expanduser().resolve()
    if not repo.is_dir() or not is_repo(repo):
        raise ValueError(f"Not a git repository: {repo}")
    name = str(title or repo.name).strip()
    meta = create_project(name, git_path=str(repo))
    try:
        from jarvis.knowledge.git_sync import sync_repository

        sync_repository(repo, force=True, label=meta.get("title") or name)
    except Exception:
        pass
    return meta


def registry_snapshot() -> dict[str, Any]:
    from jarvis.active_project import get_active_slug

    projects = list_projects()
    return {
        "enabled": True,
        "root": str(PROJECTS_ROOT),
        "active": get_active_slug(),
        "projects": projects,
        "count": len(list_projects(include_archived=True)),
    }
