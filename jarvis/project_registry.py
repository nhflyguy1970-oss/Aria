"""Named project workspace registry — data/projects/{slug}/meta.json."""

from __future__ import annotations

import json
import logging
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.project_registry")

PROJECTS_ROOT = DATA_DIR / "projects"
SUBDIRS = ("cad", "exports", "browser", "images")

# QA / certification / probe leftovers must never appear in the production picker.
_QA_SLUG_RE = re.compile(
    r"(^qa[-_]|[-_]qa[-_]|cert-proj[-_]|oc-cert|onetruth-proj[-_]|smoke[-_]|certification[-_]|[-_]probe[-_]|^probe[-_])",
    re.I,
)
_QA_TITLE_RE = re.compile(
    r"(qa\s+workflow|\boc\s*cert\b|cert\s+proj\b|cert\s+project\b|onetruth\s+proj\b|smoke\s+test\b|ship\s*probe|wf[_\s-]?probe)",
    re.I,
)
_QA_DESC_RE = re.compile(r"(lead\s+qa\s+workflow\s+probe|workflow\s+probe|certification\s+test)", re.I)


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


def is_qa_artifact(meta: dict[str, Any] | None, *, title: str = "", description: str = "") -> bool:
    """True for automated QA/cert/probe projects — never show in production UI."""
    meta = meta or {}
    if meta.get("qa_artifact") is True:
        return True
    origin = str(meta.get("origin") or "").strip().lower()
    if origin in ("qa", "certification", "smoke", "demo", "test", "probe"):
        return True
    slug = str(meta.get("slug") or "")
    tit = str(meta.get("title") or title or "")
    desc = str(meta.get("description") or description or "")
    if _QA_SLUG_RE.search(slug):
        return True
    if _QA_TITLE_RE.search(tit) or _QA_DESC_RE.search(desc) or _QA_DESC_RE.search(tit):
        return True
    return False


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


def _identity_fields(slug: str) -> dict[str, str]:
    """Canonical namespaces — one slug is the single authority."""
    s = _slugify(slug)
    return {
        "memory_namespace": s,
        "knowledge_namespace": f"project:{s}",
        "checkpoint_namespace": s,
        "journal_slug": s,
    }


def create_project(
    title: str | None,
    *,
    description: str = "",
    git_path: str | None = None,
    qa_artifact: bool = False,
    origin: str | None = None,
) -> dict[str, Any]:
    slug = _slugify(title)
    if meta_path(slug).is_file():
        base = slug
        n = 2
        while meta_path(f"{base}-{n}").is_file():
            n += 1
        slug = f"{base}-{n}"
    now = _now()
    title = str(title or slug).strip()
    desc = str(description or "").strip()
    tagged = bool(qa_artifact) or is_qa_artifact(
        {"slug": slug, "title": title, "description": desc, "origin": origin or ""}
    )
    from jarvis.production_guard import LIVE_DATA_ROOT, ProductionIsolationError, looks_like_test_payload

    try:
        live_projects = Path(PROJECTS_ROOT).resolve().relative_to(LIVE_DATA_ROOT)
        live_projects = True
    except (ValueError, OSError):
        live_projects = False
    if live_projects and (tagged or looks_like_test_payload(title, desc, slug, origin)):
        raise ProductionIsolationError(
            "Refusing to create a QA/certification project in the live workspace."
        )
    meta: dict[str, Any] = {
        "slug": slug,
        "title": title,
        "description": desc,
        "created": now,
        "updated": now,
        "last_opened": "",
        "archived": False,
        "git_path": git_path,
        **_identity_fields(slug),
    }
    if tagged:
        meta["qa_artifact"] = True
        meta["origin"] = (origin or "qa").strip() or "qa"
        # Keep cert suites able to search before archive, but never surface in the picker.
        logger.info("Tagged project %s as QA artifact (origin=%s)", slug, meta["origin"])
    _write_meta(slug, meta)
    try:
        from jarvis.project_journal import ProjectJournal

        ProjectJournal(slug).ensure(title=meta["title"])
    except Exception:
        pass
    return get_project(slug) or meta


def get_project(slug: str | None) -> dict[str, Any] | None:
    path = meta_path(slug)
    if not path.is_file():
        return None
    meta = _read_meta(path)
    s = _slugify(slug)
    # Migrate legacy metas to unified identity (preserve existing projects)
    dirty = False
    for k, v in _identity_fields(s).items():
        if meta.get(k) != v:
            meta[k] = v
            dirty = True
    if "last_opened" not in meta:
        meta["last_opened"] = ""
        dirty = True
    if dirty:
        try:
            _write_meta(s, {k: v for k, v in meta.items() if k != "paths"})
        except Exception:
            pass
    meta["paths"] = {
        "root": str(project_dir(slug)),
        "cad": str(project_dir(slug) / "cad"),
        "exports": str(project_dir(slug) / "exports"),
        "browser": str(project_dir(slug) / "browser"),
    }
    return meta


def touch_project_opened(slug: str) -> bool:
    meta = get_project(slug)
    if not meta:
        return False
    meta["last_opened"] = _now()
    _write_meta(slug, {k: v for k, v in meta.items() if k != "paths"})
    return True


def update_project(
    slug: str,
    *,
    title: str | None = None,
    description: str | None = None,
    git_path: str | None = None,
) -> dict[str, Any] | None:
    meta = get_project(slug)
    if not meta:
        return None
    if title is not None:
        meta["title"] = str(title).strip() or meta.get("title") or slug
    if description is not None:
        meta["description"] = str(description).strip()
    if git_path is not None:
        meta["git_path"] = str(git_path).strip() or None
    meta.update(_identity_fields(slug))
    _write_meta(slug, {k: v for k, v in meta.items() if k != "paths"})
    return get_project(slug)


def rename_project(slug: str, new_title: str) -> dict[str, Any] | None:
    """Rename display title only — slug remains the identity authority."""
    return update_project(slug, title=new_title)


def list_projects(*, include_archived: bool = False, include_qa: bool = False) -> list[dict[str, Any]]:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    out: list[dict[str, Any]] = []
    for child in sorted(PROJECTS_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_"):
            continue
        meta = get_project(child.name)
        if not meta:
            continue
        if meta.get("archived") and not include_archived:
            continue
        if not include_qa and is_qa_artifact(meta):
            continue
        out.append(meta)
    out.sort(key=lambda m: m.get("updated") or "", reverse=True)
    return out


def archive_project(slug: str, *, archived: bool = True) -> bool:
    meta = get_project(slug)
    if not meta:
        return False
    meta["archived"] = bool(archived)
    _write_meta(slug, {k: v for k, v in meta.items() if k != "paths"})
    return True


def delete_project(slug: str) -> bool:
    """Remove project workspace + journal entry. Used to purge QA leftovers."""
    s = _slugify(slug)
    root = project_dir(s)
    if not root.is_dir() and not meta_path(s).is_file():
        return False
    try:
        from jarvis.active_project import get_active_slug, set_active_slug

        if get_active_slug() == s:
            set_active_slug("")
    except Exception:
        pass
    if root.is_dir():
        shutil.rmtree(root, ignore_errors=True)
    try:
        from jarvis.project_journal import PROJECTS_DIR, INDEX_FILE, list_projects as journal_list

        jp = PROJECTS_DIR / f"{s}.json"
        if jp.is_file():
            jp.unlink(missing_ok=True)
        if INDEX_FILE.is_file():
            remaining = [p for p in journal_list() if p.get("slug") != s]
            INDEX_FILE.write_text(
                json.dumps({"projects": remaining}, indent=2),
                encoding="utf-8",
            )
    except Exception as exc:
        logger.debug("Journal cleanup for %s: %s", s, exc)
    return True


def purge_qa_artifacts() -> list[str]:
    """Delete known QA/cert/probe projects from the live registry. Returns removed slugs."""
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    removed: list[str] = []
    for child in list(PROJECTS_ROOT.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        meta = get_project(child.name) or {"slug": child.name, "title": child.name}
        if is_qa_artifact(meta):
            if delete_project(child.name):
                removed.append(child.name)
    return removed


def import_git_repo(path: str | None, *, title: str | None = None) -> dict[str, Any]:
    from jarvis.git_util import is_repo

    repo = Path(path or "").expanduser().resolve()
    if not repo.is_dir() or not is_repo(repo):
        raise ValueError(f"Not a git repository: {repo}")
    name = str(title or repo.name).strip()
    meta = create_project(name, git_path=str(repo))
    # Knowledge sync can take minutes on a large live checkout (e.g. Aria itself).
    # Never block the Import Repository request — owner UI must stay responsive.
    try:
        import threading

        label = meta.get("title") or name

        def _sync_bg() -> None:
            try:
                from jarvis.knowledge.git_sync import sync_repository

                sync_repository(repo, force=False, label=label)
            except Exception:
                pass

        threading.Thread(target=_sync_bg, name=f"project-git-sync:{meta.get('slug')}", daemon=True).start()
    except Exception:
        pass
    return meta


def registry_snapshot(*, include_qa: bool = False, include_archived: bool = False) -> dict[str, Any]:
    from jarvis.active_project import get_active_slug

    projects = list_projects(include_archived=include_archived, include_qa=include_qa)
    return {
        "enabled": True,
        "root": str(PROJECTS_ROOT),
        "active": get_active_slug(),
        "projects": projects,
        "count": len(list_projects(include_archived=True, include_qa=include_qa)),
    }
