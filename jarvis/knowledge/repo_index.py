"""Per-repository code index with incremental updates."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from jarvis import llm
from jarvis.code_index import _chunks, _should_index

logger = logging.getLogger("jarvis.knowledge.repo_index")


def _load_chunks(index_path: Path) -> list[dict]:
    if not index_path.is_file():
        return []
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_chunks(index_path: Path, chunks: list[dict]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(chunks, indent=0), encoding="utf-8")


def build_repo_index(
    root: Path,
    *,
    index_path: Path,
    changed_files: list[str] | None = None,
) -> int:
    """Build or incrementally update a repository code index."""
    root = root.resolve()
    if changed_files:
        chunks = _load_chunks(index_path)
        for rel in changed_files:
            chunks = [c for c in chunks if c.get("source") != rel]
            path = root / rel
            if not _should_index(path, root):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            new_chunks = _chunks(text, rel)
            for c in new_chunks:
                c["embedding"] = llm.embed_text(c["text"][:2000])
                c["repo"] = str(root)
            chunks.extend(new_chunks)
        _save_chunks(index_path, chunks)
        return len(chunks)

    chunks: list[dict] = []
    for p in root.rglob("*"):
        if not _should_index(p, root):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(root))
        for c in _chunks(text, rel):
            c["embedding"] = llm.embed_text(c["text"][:2000])
            c["repo"] = str(root)
            chunks.append(c)

    _save_chunks(index_path, chunks)
    return len(chunks)


def search_repo_index(index_path: Path, query: str, limit: int = 8) -> list[dict]:
    chunks = _load_chunks(index_path)
    if not chunks:
        return []
    q_emb = llm.embed_text(query)
    if not q_emb:
        return []
    scored = []
    for c in chunks:
        emb = c.get("embedding") or []
        if not emb:
            continue
        scored.append((llm.cosine_similarity(q_emb, emb), c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:limit] if s > 0.2]


def search_all_repos(query: str, limit: int = 8) -> list[dict]:
    from jarvis.knowledge.git_sync import REPOS_INDEX_ROOT

    hits: list[tuple[float, dict]] = []
    if not REPOS_INDEX_ROOT.is_dir():
        return []
    for index_file in REPOS_INDEX_ROOT.glob("*/code_index.json"):
        for h in search_repo_index(index_file, query, limit=limit):
            hits.append((float(h.get("score") or 0.8), {**h, "index_file": str(index_file)}))
    hits.sort(key=lambda x: x[0], reverse=True)
    return [h for _, h in hits[:limit]]
