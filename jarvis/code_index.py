"""Semantic search index over project source code."""

from __future__ import annotations

import json
from pathlib import Path

from jarvis import llm
from jarvis.config import DATA_DIR, PROJECT_ROOT, SKIP_DIRS

CODE_INDEX = DATA_DIR / "code_index.json"
CODE_GLOBS = (".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".rs", ".go", ".json", ".yaml", ".yml")
MAX_CHUNK = 800
MAX_FILE = 80_000
INDEX_SKIP = SKIP_DIRS | {"data", "generated", "uploads", "backups"}

_cache_chunks: list[dict] | None = None
_cache_mtime: float = 0.0


def _chunks(text: str, source: str) -> list[dict]:
    lines = text.splitlines()
    parts: list[dict] = []
    buf: list[str] = []
    buf_len = 0
    for line in lines:
        if buf_len + len(line) > MAX_CHUNK and buf:
            parts.append({"source": source, "text": "\n".join(buf)})
            buf = []
            buf_len = 0
        buf.append(line)
        buf_len += len(line) + 1
    if buf:
        parts.append({"source": source, "text": "\n".join(buf)})
    return parts


def _should_index(path: Path, root: Path) -> bool:
    if not path.is_file():
        return False
    if any(s in path.parts for s in INDEX_SKIP):
        return False
    if path.suffix.lower() not in CODE_GLOBS:
        return False
    try:
        if path.stat().st_size > MAX_FILE:
            return False
    except OSError:
        return False
    if path.resolve() == CODE_INDEX.resolve():
        return False
    return True


def build_index(root: Path | None = None) -> list[dict]:
    global _cache_chunks, _cache_mtime
    root = root or PROJECT_ROOT
    chunks: list[dict] = []
    for p in root.rglob("*"):
        if not _should_index(p, root):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(root))
        chunks.extend(_chunks(text, rel))

    for c in chunks:
        c["embedding"] = llm.embed_text(c["text"][:2000])

    CODE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    CODE_INDEX.write_text(json.dumps(chunks, indent=0), encoding="utf-8")
    _cache_chunks = chunks
    _cache_mtime = CODE_INDEX.stat().st_mtime if CODE_INDEX.exists() else 0.0
    return chunks


def _load_index() -> list[dict]:
    global _cache_chunks, _cache_mtime
    if CODE_INDEX.exists():
        mtime = CODE_INDEX.stat().st_mtime
        if _cache_chunks is not None and mtime == _cache_mtime:
            return _cache_chunks
        try:
            _cache_chunks = json.loads(CODE_INDEX.read_text(encoding="utf-8"))
            _cache_mtime = mtime
            return _cache_chunks
        except (json.JSONDecodeError, OSError):
            pass
    return build_index()


def invalidate_cache() -> None:
    global _cache_chunks, _cache_mtime
    _cache_chunks = None
    _cache_mtime = 0.0


def search(query: str, limit: int = 8, root: Path | None = None) -> list[dict]:
    chunks = _load_index()
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


def context_for_query(query: str, limit: int = 5) -> str:
    hits = search(query, limit=limit)
    if not hits:
        return ""
    return "Relevant code:\n" + "\n---\n".join(
        f"[{h['source']}]\n{h['text']}" for h in hits
    )
