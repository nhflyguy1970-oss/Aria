"""Which project a coding request is about — from records, never from guesses.

A project is usable by a coding agent only when it is in ARIA's project
registry with a git path the owner confirmed. ARIA, Fly Tying Reference and
BlackFly are recognised *by name*; their paths are not built in. When one is
not registered, ARIA reports the candidate location it found and where that
evidence came from, and asks the owner to confirm — it does not register it.

Agent settings live on the project record (``agent_settings``):
  test_command     the command ARIA runs to verify changes (owner-set)
  protected_paths  production data that must not change during a run
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Recognised names → canonical key. Paths are never inferred from these.
KNOWN = {
    "aria": ("aria", "jarvis", "aria assistant"),
    "fly-tying-reference": ("fly tying reference", "fly-tying reference", "ftr", "fly tying app",
                            "fly tying application", "fly tying reference application"),
    "blackfly": ("blackfly", "black fly", "blackfly scraper"),
}
TITLES = {"aria": "ARIA", "fly-tying-reference": "Fly Tying Reference", "blackfly": "BlackFly"}


def _registry():
    from jarvis import project_registry

    return project_registry


def known_key(text: str) -> str:
    low = (text or "").lower()
    for key, names in KNOWN.items():
        if any(re.search(rf"\b{re.escape(n)}\b", low) for n in names):
            return key
    return ""


def _record(meta: dict[str, Any]) -> dict[str, Any] | None:
    path = str(meta.get("git_path") or "").strip()
    if not path:
        return None
    settings = dict(meta.get("agent_settings") or {})
    return {
        "slug": meta.get("slug"),
        "title": meta.get("title") or meta.get("slug"),
        "path": str(Path(path).expanduser()),
        "purpose": meta.get("description") or "",
        "test_command": str(settings.get("test_command") or ""),
        "test_verification": settings.get("test_verification") or {},
        "protected_paths": list(settings.get("protected_paths") or []),
        "allowed_agents": list(settings.get("allowed_agents") or []),
        "inventory": settings.get("inventory") or {},
        "known_as": known_key(f"{meta.get('slug')} {meta.get('title')}"),
        "memory_namespace": meta.get("memory_namespace") or meta.get("slug"),
        "source": "project registry",
    }


def get(slug: str) -> dict[str, Any] | None:
    meta = _registry().get_project(slug or "")
    return _record(meta) if meta else None


def registered() -> list[dict[str, Any]]:
    out = []
    for meta in _registry().list_projects():
        rec = _record(meta)
        if rec:
            out.append(rec)
    return out


def resolve(text: str, *, session=None) -> dict[str, Any]:
    """{"project": record} | {"unregistered": key, "candidate": {...}} | {"ambiguous": [...]} | {}"""
    key = known_key(text)
    regs = registered()
    if key:
        matches = [r for r in regs if r["known_as"] == key]
        if len(matches) == 1:
            return {"project": matches[0], "how": f"named in the request ({TITLES[key]})"}
        if len(matches) > 1:
            return {"ambiguous": matches}
        return {"unregistered": key, "candidate": candidate(key)}
    low = (text or "").lower()
    named = [r for r in regs if r["title"] and re.search(rf"\b{re.escape(str(r['title']).lower())}\b", low)]
    if len(named) == 1:
        return {"project": named[0], "how": "named in the request"}
    slug = getattr(session, "project_slug", "") if session is not None else ""
    if not slug:
        try:
            from jarvis.active_project import get_active_slug

            slug = get_active_slug() or ""
        except Exception:
            slug = ""
    if slug and (rec := get(slug)):
        return {"project": rec, "how": "the active project"}
    return {}


def candidate(key: str) -> dict[str, Any]:
    """Where a known project appears to live, with the evidence. Not a registration."""
    from jarvis.config import PROJECT_ROOT

    home = Path.home()
    if key == "aria":
        return {"path": str(PROJECT_ROOT), "evidence": "the directory ARIA itself runs from"}
    launchers = {
        "fly-tying-reference": (home / ".local/bin/ftr-backup", r'APP_DIR="\$\{FTR_APP_DIR:-([^}"]+)\}"'),
        "blackfly": (home / ".local/bin/blackfly-scraper", r'"(/[^"]+/fly_fishing_project)/blackfly_gui\.py"'),
    }
    if key in launchers:
        launcher, pattern = launchers[key]
        try:
            m = re.search(pattern, launcher.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            m = None
        if m:
            return {"path": m.group(1), "evidence": f"referenced by {launcher}"}
    return {"path": "", "evidence": "no local evidence found"}


def register(path: str, *, title: str, test_command: str = "", protected_paths: list[str] | None = None,
             purpose: str = "", inventory: dict[str, Any] | None = None, test_verification: dict | None = None,
             allowed_agents: list[str] | None = None) -> dict[str, Any]:
    """Owner action: add a confirmed git repository to the registry.

    Uses ``create_project`` rather than ``import_git_repo``: registration must not
    start a background knowledge sync of the repository — indexing a project is a
    separate, explicit decision.
    """
    from jarvis.git_util import is_repo

    repo = Path(path).expanduser().resolve()
    if not repo.is_dir() or not is_repo(repo):
        raise ValueError(f"Not a git repository: {repo}")
    reg = _registry()
    existing = [p for p in reg.list_projects() if str(Path(str(p.get("git_path") or "")).expanduser()) == str(repo)]
    meta = existing[0] if existing else reg.create_project(title, description=purpose, git_path=str(repo))
    settings = {
        "test_command": test_command,
        "protected_paths": list(protected_paths or []),
        "allowed_agents": list(allowed_agents or []),
        "inventory": dict(inventory or {}),
        "test_verification": dict(test_verification or {}),
    }
    reg.update_project(meta["slug"], agent_settings=settings, description=purpose or None)
    return get(meta["slug"]) or {}
