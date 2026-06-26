"""Simple RAG over project markdown and text docs."""

from pathlib import Path

from jarvis import llm
from jarvis.config import DATA_DIR, PROJECT_ROOT, SKIP_DIRS

RAG_INDEX = DATA_DIR / "rag_index.json"
DOC_GLOBS = ("README.md", "UPGRADES.md", "DEPENDENCIES.md", "**/*.md", "**/*.txt")
MAX_CHUNK = 1200


def _chunks(text: str, source: str) -> list[dict]:
    parts = []
    for i in range(0, len(text), MAX_CHUNK):
        chunk = text[i : i + MAX_CHUNK].strip()
        if chunk:
            parts.append({"source": source, "text": chunk})
    return parts


def build_index(root: Path | None = None) -> list[dict]:
    root = root or PROJECT_ROOT
    chunks: list[dict] = []
    for pattern in ("README.md", "UPGRADES.md", "DEPENDENCIES.md"):
        p = root / pattern
        if p.exists():
            chunks.extend(_chunks(p.read_text(encoding="utf-8", errors="ignore"), str(p.relative_to(root))))
    for p in root.rglob("*.md"):
        if any(s in p.parts for s in SKIP_DIRS):
            continue
        if p.stat().st_size > 100_000:
            continue
        try:
            chunks.extend(_chunks(p.read_text(encoding="utf-8", errors="ignore"), str(p.relative_to(root))))
        except OSError:
            pass
    for c in chunks:
        c["embedding"] = llm.embed_text(c["text"])
    import json
    RAG_INDEX.parent.mkdir(parents=True, exist_ok=True)
    RAG_INDEX.write_text(json.dumps(chunks, indent=0), encoding="utf-8")
    return chunks


def _load_index() -> list[dict]:
    import json
    if RAG_INDEX.exists():
        try:
            return json.loads(RAG_INDEX.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return build_index()


def search(query: str, limit: int = 5) -> list[dict]:
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
    return [c for s, c in scored[:limit] if s > 0.25]


def context_for_query(query: str) -> tuple[str, list[str]]:
    """Return (context text for LLM, warnings for user)."""
    warnings: list[str] = []
    if not llm.embed_available():
        warnings.append(
            f"Semantic doc search unavailable — embed model `{llm.embed_model()}` not responding."
        )
        return "", warnings
    hits = search(query, limit=4)
    if not hits:
        return "", warnings
    ctx = "Project documentation:\n" + "\n---\n".join(
        f"[{h['source']}]\n{h['text']}" for h in hits
    )
    return ctx, warnings


def embed_warning() -> str | None:
    if llm.embed_available():
        return None
    return f"Embed model `{llm.embed_model()}` unavailable — semantic memory and RAG disabled."
