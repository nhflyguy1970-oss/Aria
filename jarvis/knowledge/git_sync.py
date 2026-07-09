"""Git repository sync — first-class knowledge sources with incremental indexing."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.git_util import current_branch, has_local_changes, is_repo, log_oneline, status as git_status

logger = logging.getLogger("jarvis.knowledge.git_sync")

REPOS_STATE_FILE = DATA_DIR / "knowledge" / "git_repos.json"
REPOS_INDEX_ROOT = DATA_DIR / "knowledge" / "repos"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run(cmd: list[str], cwd: Path, timeout: int = 60) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, check=False)
        return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()
    except Exception as exc:
        return 1, str(exc)


def _repo_id(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]


def _head_commit(repo: Path) -> str:
    code, out = _run(["git", "rev-parse", "HEAD"], repo)
    return out if code == 0 else ""


def _remote_url(repo: Path) -> str:
    code, out = _run(["git", "remote", "get-url", "origin"], repo)
    return out if code == 0 else ""


def _changed_files_since(repo: Path, old_head: str) -> list[str]:
    if not old_head:
        return []
    code, out = _run(["git", "diff", "--name-only", old_head, "HEAD"], repo)
    if code != 0:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def _open_pull_requests(repo: Path) -> list[dict[str, str]]:
    if not shutil.which("gh"):
        return []
    code, out = _run(
        ["gh", "pr", "list", "--json", "number,title,state,headRefName,baseRefName,url", "--limit", "10"],
        repo,
        timeout=30,
    )
    if code != 0:
        return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


@dataclass
class GitRepoState:
    id: str
    path: str
    label: str
    namespace: str = ""
    branch: str = ""
    head: str = ""
    remote: str = ""
    dirty: bool = False
    last_indexed: str = ""
    last_sync: str = ""
    last_successful_sync: str = ""
    chunk_count: int = 0
    document_count: int = 0
    indexing_status: str = "unknown"
    health: str = "unknown"
    errors: list[str] = field(default_factory=list)
    open_prs: list[dict[str, str]] = field(default_factory=list)
    project_slug: str = ""

    @property
    def retrieval_available(self) -> bool:
        return self.chunk_count > 0 and self.indexing_status == "indexed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GitRepoState:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _load_state() -> dict[str, Any]:
    if not REPOS_STATE_FILE.is_file():
        return {"repos": {}, "updated_at": ""}
    try:
        return json.loads(REPOS_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"repos": {}, "updated_at": ""}


def _save_state(data: dict[str, Any]) -> None:
    REPOS_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utc_now()
    REPOS_STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def discover_repositories() -> list[Path]:
    """All git repositories Aria should track."""
    repos: dict[str, Path] = {}

    if is_repo(PROJECT_ROOT):
        repos[str(PROJECT_ROOT.resolve())] = PROJECT_ROOT.resolve()

    try:
        from jarvis.project_registry import list_projects

        for meta in list_projects(include_archived=False):
            git_path = str(meta.get("git_path") or "").strip()
            if git_path:
                p = Path(git_path).expanduser().resolve()
                if p.is_dir() and is_repo(p):
                    repos[str(p)] = p
    except Exception as exc:
        logger.debug("Project repo discovery: %s", exc)

    extra = os.getenv("JARVIS_GIT_WATCH_REPOS", "")
    for part in extra.split(":"):
        part = part.strip()
        if not part:
            continue
        p = Path(part).expanduser().resolve()
        if p.is_dir() and is_repo(p):
            repos[str(p)] = p

    return list(repos.values())


def index_path_for_repo(repo: Path) -> Path:
    return REPOS_INDEX_ROOT / _repo_id(repo) / "code_index.json"


def sync_repository(repo: Path, *, force: bool = False, label: str = "") -> GitRepoState:
    """Sync one repository — metadata, change detection, incremental index."""
    repo = repo.resolve()
    rid = _repo_id(repo)
    state_data = _load_state()
    prev = GitRepoState.from_dict(state_data.get("repos", {}).get(rid, {})) if state_data.get("repos") else None
    prev_head = prev.head if prev else ""

    errors: list[str] = []
    branch = current_branch(repo)
    head = _head_commit(repo)
    dirty = has_local_changes(repo)
    remote = _remote_url(repo)
    prs = _open_pull_requests(repo)

    namespace = f"git:{rid}"
    project_slug = ""
    try:
        from jarvis.project_registry import list_projects

        for meta in list_projects(include_archived=True):
            gp = str(meta.get("git_path") or "").strip()
            if gp and Path(gp).expanduser().resolve() == repo:
                project_slug = str(meta.get("slug") or "")
                namespace = f"project:{project_slug}"
                if not label:
                    label = str(meta.get("title") or project_slug)
                break
    except Exception:
        pass

    if not label:
        label = repo.name

    changed = _changed_files_since(repo, prev_head) if prev_head and head != prev_head else []
    needs_index = force or not prev_head or head != prev_head or dirty or not index_path_for_repo(repo).is_file()

    chunk_count = prev.chunk_count if prev else 0
    indexing_status = "unknown"

    if needs_index:
        try:
            from jarvis.knowledge.repo_index import build_repo_index

            chunk_count = build_repo_index(
                repo,
                index_path=index_path_for_repo(repo),
                changed_files=changed if changed and not force else None,
            )
            indexing_status = "indexed"
        except Exception as exc:
            errors.append(str(exc)[:200])
            indexing_status = "error"
    else:
        indexing_status = "indexed"

    now = _utc_now()
    st = GitRepoState(
        id=rid,
        path=str(repo),
        label=label,
        namespace=namespace,
        branch=branch,
        head=head,
        remote=remote,
        dirty=dirty,
        last_indexed=now if needs_index and not errors else (prev.last_indexed if prev else ""),
        last_sync=now,
        last_successful_sync=now if not errors else (prev.last_successful_sync if prev else ""),
        chunk_count=chunk_count,
        document_count=chunk_count,
        indexing_status=indexing_status,
        health="healthy" if not errors else "error",
        errors=errors,
        open_prs=prs,
        project_slug=project_slug,
    )

    state_data.setdefault("repos", {})[rid] = st.to_dict()
    _save_state(state_data)
    _register_in_knowledge_registry(st)
    return st


def _register_in_knowledge_registry(st: GitRepoState) -> None:
    try:
        from jarvis.knowledge.registry import register_external_source

        register_external_source(
            source_id=f"git-{st.id}",
            source_type="git_repository",
            label=st.label,
            location=st.path,
            namespace=st.namespace,
            indexing_status=st.indexing_status,
            embedding_status="ready" if st.chunk_count else "none",
            document_count=st.chunk_count,
            chunk_count=st.chunk_count,
            last_indexed=st.last_indexed,
            last_sync=st.last_sync,
            last_successful_sync=st.last_successful_sync,
            health=st.health,
            errors=st.errors,
            retrieval_available=st.chunk_count > 0 and st.indexing_status == "indexed",
            metadata={
                "branch": st.branch,
                "head": st.head[:12],
                "remote": st.remote,
                "dirty": st.dirty,
                "open_prs": st.open_prs[:5],
                "project_slug": st.project_slug,
                "index_file": str(index_path_for_repo(Path(st.path))),
            },
        )
    except Exception as exc:
        logger.debug("Knowledge registry update for git repo: %s", exc)


def sync_all(*, force: bool = False) -> dict[str, Any]:
    repos = discover_repositories()
    results: list[dict[str, Any]] = []
    for repo in repos:
        try:
            st = sync_repository(repo, force=force)
            results.append({"ok": st.health != "error", "repo": st.label, "state": st.to_dict()})
        except Exception as exc:
            results.append({"ok": False, "repo": str(repo), "error": str(exc)[:200]})

    try:
        from jarvis.knowledge.registry import sync_registry

        sync_registry()
    except Exception:
        pass

    ok = all(r.get("ok") for r in results) if results else True
    return {"ok": ok, "repos": len(results), "results": results}


def list_repo_states() -> list[GitRepoState]:
    data = _load_state()
    return [GitRepoState.from_dict(v) for v in (data.get("repos") or {}).values()]


def repo_summary_markdown() -> str:
    states = list_repo_states()
    if not states:
        return "No git repositories indexed yet. Run **git sync** or register a project with a git path."
    lines = ["## Git repositories", ""]
    for st in states:
        mark = "●" if st.retrieval_available else "○"
        dirty = " (dirty)" if st.dirty else ""
        prs = f" · {len(st.open_prs)} PR(s)" if st.open_prs else ""
        lines.append(
            f"{mark} **{st.label}** — `{st.branch}` @ `{st.head[:8]}` — "
            f"{st.chunk_count} chunks{dirty}{prs}"
        )
    return "\n".join(lines)
