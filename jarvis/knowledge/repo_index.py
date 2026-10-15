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


EMBED_BATCH = 32


def _key(text: str) -> str:
    import hashlib

    return hashlib.sha1(text[:2000].encode("utf-8", "ignore")).hexdigest()


def _embed_new(chunks: list[dict], known: dict[str, list[float]], root: Path, check_cancel) -> int:
    """Give every chunk its embedding, reusing ``known`` ones (keyed by text) and embedding the
    rest in batches. Returns how many were embedded now.

    Every scheduled sync of a repo with uncommitted changes used to re-embed the whole repo one
    chunk per request: 21,084 requests for ARIA, ~40 min of continuous RTX load, every 30 min
    (2026-10-14: 70-86% RTX utilization while ARIA was idle)."""
    todo: list[dict] = []
    for c in chunks:
        c["repo"] = str(root)
        vec = known.get(_key(c["text"]))
        if vec:
            c["embedding"] = vec
        else:
            todo.append(c)
    if not todo:
        return 0
    try:
        from jarvis.ollama_runtime import chat_priority_active
    except Exception:  # noqa: BLE001
        chat_priority_active = lambda: False  # noqa: E731
    done = 0
    with llm.embed_session():
        for i in range(0, len(todo), EMBED_BATCH):
            check_cancel()
            batch = todo[i:i + EMBED_BATCH]
            if chat_priority_active():
                vectors: list[list[float]] = []  # never compete with a chat stream; next sync fills these
            else:
                try:
                    vectors = llm.embed_batch([c["text"][:2000] for c in batch])
                except llm.EmbeddingError as exc:
                    logger.warning("Repository index: embedding unavailable (%s); will retry next sync", exc)
                    vectors = []
            for c, vec in zip(batch, vectors or [[]] * len(batch)):
                c["embedding"] = vec
                if vec:
                    known[_key(c["text"])] = vec
                    done += 1
    return done


def build_repo_index(
    root: Path,
    *,
    index_path: Path,
    changed_files: list[str] | None = None,
    cancel_check=None,
) -> int:
    """Build or incrementally update a repository code index.

    Chunks whose text is unchanged keep their stored embedding, so a rebuild only embeds what
    actually changed."""
    def check_cancel():
        if cancel_check is not None and cancel_check():
            raise InterruptedError("Repository indexing cancelled for ARIA shutdown")

    check_cancel()
    root = root.resolve()
    old = _load_chunks(index_path)
    known = {_key(c.get("text") or ""): c["embedding"] for c in old if c.get("embedding") and c.get("text")}
    if changed_files:
        chunks = [c for c in old if c.get("source") not in set(changed_files)]
        fresh: list[dict] = []
        for rel in changed_files:
            check_cancel()
            path = root / rel
            if not _should_index(path, root):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            fresh.extend(_chunks(text, rel))
        embedded = _embed_new(fresh, known, root, check_cancel)
        chunks.extend(fresh)
    else:
        chunks = []
        for p in root.rglob("*"):
            check_cancel()
            if not _should_index(p, root):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            chunks.extend(_chunks(text, str(p.relative_to(root))))
        embedded = _embed_new(chunks, known, root, check_cancel)
    check_cancel()
    _save_chunks(index_path, chunks)
    logger.info("Repository index %s: %d chunks, %d embedded now", root.name, len(chunks), embedded)
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
