"""Document learning — ingest files/URLs/OCR text and teach ARIA durable lessons."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jarvis import llm
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.document_pipeline import (
    DOCUMENT_EXTENSIONS,
    DOCUMENTS_DIR,
    ParsedDocument,
    documents_dir,
    html_to_text,
    low_text_warning,
    parse_document,
    parse_text_content,
    _title_from_html,
)

log = logging.getLogger("jarvis.document_learning")

LEARNING_NAMESPACE = "learned"
DOCUMENT_LEARN_TAG = "document-learn"
REGISTRY_FILE = DATA_DIR / "document_learning.json"
_MAX_EXTRACT_CHARS = int(__import__("os").getenv("JARVIS_DOC_LEARN_CHARS", "14000"))
_MAX_FACTS = int(__import__("os").getenv("JARVIS_DOC_LEARN_FACTS", "8"))

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
_LEARN_DOC = re.compile(
    r"\b(learn from|study|read and learn|memorize|teach yourself from|ingest and learn)\b",
    re.I,
)
_INGEST_DOC = re.compile(
    r"\b(ingest (?:this )?(?:doc|document|file|pdf|page)|add (?:this )?to (?:my )?(?:document )?library)\b",
    re.I,
)
_LEARN_RECALL = re.compile(
    r"\b(what did i learn from (?:documents?|files?|pdfs?|the library)|"
    r"what have you learned from (?:documents?|my files?)|document learning recall)\b",
    re.I,
)
_LEARN_RECALL_QUERY = re.compile(
    r"(?:what did i learn from (?:documents?|files?|pdfs?)(?: about)?|"
    r"what have you learned from (?:documents?|my files?)(?: about)?|"
    r"document learning recall(?: about)?)\s+(.+)$",
    re.I,
)


@dataclass
class IngestResult:
    ok: bool
    title: str
    path: str
    source_type: str
    chars: int = 0
    message: str = ""
    url: str = ""
    source_id: str = ""


@dataclass
class LearnResult:
    ok: bool
    title: str
    path: str
    source_type: str
    lessons: list[str] = field(default_factory=list)
    message: str = ""
    url: str = ""
    source_id: str = ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (text or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:60] or "document")


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_FILE.is_file():
        return {"sources": []}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("sources"), list):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt document learning registry: %s", exc)
    return {"sources": []}


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(REGISTRY_FILE)
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _source_id(title: str, path: str = "", url: str = "") -> str:
    raw = f"{title}|{path}|{url}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _register_source(
    *,
    title: str,
    path: str,
    source_type: str,
    chars: int,
    url: str = "",
    learned: bool = False,
    lessons: int = 0,
) -> str:
    data = _load_registry()
    sid = _source_id(title, path, url)
    entry = {
        "id": sid,
        "title": title,
        "path": path,
        "type": source_type,
        "url": url,
        "chars": chars,
        "ingested_at": _utc_now(),
        "learned_at": _utc_now() if learned else "",
        "lessons": lessons,
    }
    sources = [s for s in data.get("sources", []) if s.get("id") != sid]
    sources.insert(0, entry)
    data["sources"] = sources[:200]
    _save_registry(data)
    return sid


def list_sources(*, limit: int = 50) -> list[dict[str, Any]]:
    return list(_load_registry().get("sources", []))[:limit]


def learning_stats() -> dict[str, Any]:
    sources = list_sources(limit=500)
    learned = [s for s in sources if s.get("learned_at")]
    return {
        "total_sources": len(sources),
        "learned_sources": len(learned),
        "total_lessons": sum(int(s.get("lessons") or 0) for s in sources),
        "namespace": LEARNING_NAMESPACE,
    }


def resolve_document_path(raw: str) -> str:
    """Resolve a document path against project, data, uploads, and library."""
    upload_dir = DATA_DIR / "uploads"

    text = (raw or "").strip()
    if not text:
        return ""
    p = Path(text)
    if p.is_absolute() and p.exists():
        return str(p)
    for base in (PROJECT_ROOT, DATA_DIR, upload_dir, documents_dir()):
        candidate = (base / text).resolve()
        if candidate.exists():
            return str(candidate)
    resolved = p.expanduser()
    return str(resolved) if resolved.exists() else ""


def parse_url_from_message(message: str) -> str:
    m = _URL_RE.search((message or "").strip())
    return (m.group(0).rstrip(".,);]") if m else "")


def is_learn_from_document(message: str) -> bool:
    return bool(_LEARN_DOC.search((message or "").strip()))


def is_ingest_document(message: str) -> bool:
    return bool(_INGEST_DOC.search((message or "").strip()))


def is_document_learn_recall(message: str) -> bool:
    return bool(_LEARN_RECALL.search((message or "").strip()))


def parse_document_learn_recall_query(message: str) -> str:
    m = _LEARN_RECALL_QUERY.search((message or "").strip())
    return (m.group(1).strip() if m else "").rstrip("?.!")


def _document_path_in_message(message: str) -> str:
    exts = "|".join(ext.lstrip(".") for ext in sorted(DOCUMENT_EXTENSIONS))
    if m := re.search(
        rf"\b(?:file|document|pdf|attached|open|in)\s+[`'\"]?([\w./-]+\.(?:{exts}))[`'\"]?",
        message,
        re.I,
    ):
        return m.group(1)
    paths = re.findall(rf"[`'\"]?([\w./-]+\.(?:{exts}))[`'\"]?", message, re.I)
    return paths[-1] if paths else ""


def _copy_to_library(src: Path) -> Path:
    root = documents_dir()
    dest = root / src.name
    if dest.resolve() == src.resolve():
        return src
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        for n in range(2, 1000):
            candidate = root / f"{stem}_{n}{suffix}"
            if not candidate.exists():
                dest = candidate
                break
    shutil.copy2(src, dest)
    return dest


def _save_text_to_library(text: str, *, title: str, subdir: str = "") -> Path:
    root = documents_dir()
    folder = root / subdir if subdir else root
    folder.mkdir(parents=True, exist_ok=True)
    slug = _slugify(title)
    dest = folder / f"{slug}.txt"
    if dest.exists():
        for n in range(2, 1000):
            candidate = folder / f"{slug}_{n}.txt"
            if not candidate.exists():
                dest = candidate
                break
    dest.write_text(text, encoding="utf-8")
    return dest


def _reindex_library() -> int:
    from jarvis.documents_rag import build_index

    return len(build_index(force=True))


def _source_type_for_path(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return ext or "file"


def ingest_file(path: str | Path, *, copy_to_library: bool = True) -> IngestResult:
    raw = Path(path).expanduser()
    resolved = resolve_document_path(str(raw)) or str(raw)
    p = Path(resolved)
    if not p.exists():
        return IngestResult(False, p.name, str(p), "file", message=f"File not found: {p}")

    try:
        if copy_to_library and p.suffix.lower() in DOCUMENT_EXTENSIONS:
            stored = _copy_to_library(p)
            doc = parse_document(stored)
            stored_path = str(stored)
        else:
            doc = parse_document(p)
            stored_path = str(p)
    except Exception as exc:
        return IngestResult(False, p.name, str(p), _source_type_for_path(p), message=str(exc))

    sid = _register_source(
        title=doc.title,
        path=stored_path,
        source_type=_source_type_for_path(Path(stored_path)),
        chars=doc.char_count,
    )
    chunks = _reindex_library()
    return IngestResult(
        True,
        doc.title,
        stored_path,
        _source_type_for_path(Path(stored_path)),
        chars=doc.char_count,
        message=f"Indexed **{doc.title}** ({doc.char_count:,} chars, {chunks} chunks).",
        source_id=sid,
    )


def fetch_web_page(url: str) -> tuple[str, str]:
    """Return (title, plain text) from a URL."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Jarvis/1.0 (+document-learning)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
    except urllib.error.URLError as exc:
        raise ValueError(f"Could not fetch URL: {exc}") from exc

    charset = "utf-8"
    if "charset=" in ctype:
        m = re.search(r"charset=([^\s;]+)", ctype)
        if m:
            charset = m.group(1).strip("\"'")
    text = raw.decode(charset, errors="ignore")
    if "html" in ctype or "<html" in text.lower():
        title = _title_from_html(text) or urlparse(url).netloc or "web page"
        return title, html_to_text(text)
    title = urlparse(url).path.rsplit("/", 1)[-1] or urlparse(url).netloc or "web page"
    return title, text.strip()


def ingest_url(url: str) -> IngestResult:
    url = (url or "").strip()
    if not url:
        return IngestResult(False, "", "", "web", message="URL required.")
    try:
        title, text = fetch_web_page(url)
    except ValueError as exc:
        return IngestResult(False, "", "", "web", url=url, message=str(exc))
    if not text.strip():
        return IngestResult(False, title, "", "web", url=url, message="No text extracted from page.")

    dest = _save_text_to_library(text, title=title, subdir="web")
    doc = parse_document(dest)
    sid = _register_source(
        title=doc.title,
        path=str(dest),
        source_type="web",
        chars=doc.char_count,
        url=url,
    )
    chunks = _reindex_library()
    return IngestResult(
        True,
        doc.title,
        str(dest),
        "web",
        chars=doc.char_count,
        url=url,
        message=f"Saved web page **{doc.title}** ({doc.char_count:,} chars, {chunks} chunks).",
        source_id=sid,
    )


def ingest_text(text: str, *, title: str = "OCR document", source_type: str = "ocr") -> IngestResult:
    cleaned = (text or "").strip()
    if not cleaned:
        return IngestResult(False, title, "", source_type, message="No text to ingest.")
    subdir = "ocr" if source_type == "ocr" else "text"
    dest = _save_text_to_library(cleaned, title=title, subdir=subdir)
    doc = parse_document(dest)
    sid = _register_source(
        title=doc.title,
        path=str(dest),
        source_type=source_type,
        chars=doc.char_count,
    )
    chunks = _reindex_library()
    return IngestResult(
        True,
        doc.title,
        str(dest),
        source_type,
        chars=doc.char_count,
        message=f"Saved **{doc.title}** ({doc.char_count:,} chars, {chunks} chunks).",
        source_id=sid,
    )


def extract_document_learnings(text: str, *, title: str = "", max_facts: int | None = None) -> list[str]:
    """Use LLM to pull durable facts/procedures from document text."""
    excerpt = (text or "").strip()
    if not excerpt:
        return []
    if len(excerpt) > _MAX_EXTRACT_CHARS:
        excerpt = excerpt[:_MAX_EXTRACT_CHARS] + "…"
    limit = max_facts if max_facts is not None else _MAX_FACTS
    prompt = (
        f"Extract up to {limit} durable facts, rules, or procedures from this document. "
        "Each item must be a complete standalone sentence useful for future answers. "
        "Skip page numbers, boilerplate, and vague summaries. "
        'Return JSON only: {"facts": ["fact1", "fact2"]}. '
        "Empty array if nothing substantive.\n\n"
        f"Document: {title or 'untitled'}\n\n{excerpt}"
    )
    try:
        raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        facts = [f.strip() for f in data.get("facts", []) if isinstance(f, str) and len(f.strip()) > 8]
        return facts[:limit]
    except Exception as exc:
        log.warning("Document learning extract failed: %s", exc)
        return []


def _store_lessons(memory, facts: list[str], *, title: str, source_type: str) -> list[str]:
    from jarvis.explicit_teaching import TeachIntent, apply_explicit_teaching, infer_teaching_kind

    stored: list[str] = []
    src_tag = f"doc-source:{_slugify(title)[:32]}"
    for fact in facts:
        kind = infer_teaching_kind(fact)
        intent = TeachIntent(kind=kind, content=fact)
        try:
            result = apply_explicit_teaching(
                memory,
                intent,
                namespace=LEARNING_NAMESPACE,
                extra_tags=[DOCUMENT_LEARN_TAG, src_tag, f"doc-type:{source_type}"],
            )
            stored.append(result.content)
        except ValueError as exc:
            log.debug("Skip lesson: %s", exc)
    return stored


def learn_from_document(
    memory,
    doc: ParsedDocument,
    *,
    source_type: str = "file",
    url: str = "",
) -> LearnResult:
    warn = low_text_warning(doc)
    if warn and doc.char_count < 40:
        return LearnResult(
            False,
            doc.title,
            doc.path,
            source_type,
            message=warn,
            url=url,
        )

    facts = extract_document_learnings(doc.full_text, title=doc.title)
    if not facts:
        return LearnResult(
            False,
            doc.title,
            doc.path,
            source_type,
            message="Could not extract lessons from this document.",
            url=url,
        )

    lessons = _store_lessons(memory, facts, title=doc.title, source_type=source_type)
    sid = _register_source(
        title=doc.title,
        path=doc.path,
        source_type=source_type,
        chars=doc.char_count,
        url=url,
        learned=True,
        lessons=len(lessons),
    )
    return LearnResult(
        True,
        doc.title,
        doc.path,
        source_type,
        lessons=lessons,
        message=f"Learned **{len(lessons)}** lesson(s) from **{doc.title}**.",
        url=url,
        source_id=sid,
    )


def learn_from_file(memory, path: str | Path, *, ingest: bool = True) -> LearnResult:
    ing = ingest_file(path, copy_to_library=ingest) if ingest else None
    if ingest and not ing.ok:
        return LearnResult(False, ing.title, ing.path, ing.source_type, message=ing.message)
    resolved = ing.path if ing and ing.ok else resolve_document_path(str(path))
    if not resolved:
        return LearnResult(False, "", str(path), "file", message="Document not found.")
    try:
        doc = parse_document(resolved)
    except Exception as exc:
        return LearnResult(False, Path(resolved).name, resolved, "file", message=str(exc))
    return learn_from_document(memory, doc, source_type=_source_type_for_path(Path(resolved)))


def learn_from_url(memory, url: str) -> LearnResult:
    ing = ingest_url(url)
    if not ing.ok:
        return LearnResult(False, ing.title, ing.path, "web", message=ing.message, url=url)
    doc = parse_document(ing.path)
    result = learn_from_document(memory, doc, source_type="web", url=url)
    return result


def learn_from_text(memory, text: str, *, title: str = "OCR document") -> LearnResult:
    ing = ingest_text(text, title=title, source_type="ocr")
    if not ing.ok:
        return LearnResult(False, title, "", "ocr", message=ing.message)
    doc = parse_document(ing.path)
    return learn_from_document(memory, doc, source_type="ocr")


def list_document_learnings(memory, *, query: str = "", limit: int = 25) -> list[dict]:
    entries = memory.list_entries(entry_type="teaching", namespace=LEARNING_NAMESPACE)
    entries = [e for e in entries if DOCUMENT_LEARN_TAG in (e.get("tags") or [])]
    if query:
        q = query.lower()
        entries = [e for e in entries if q in e.get("content", "").lower()]
        if not entries and llm.embed_available():
            hits = memory.search(query, limit=limit, namespace=LEARNING_NAMESPACE)
            seen: set[str] = set()
            for h in hits:
                if DOCUMENT_LEARN_TAG in (h.get("tags") or []) and h["id"] not in seen:
                    entries.append(h)
                    seen.add(h["id"])
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def document_learning_context_for_chat(memory, message: str, *, limit: int = 4) -> str:
    from jarvis.trust_memory import filter_trusted_content

    q = (message or "").strip()
    if len(q) < 6:
        return ""
    hits = list_document_learnings(memory, query=q, limit=limit)
    if not hits:
        words = [w for w in re.findall(r"[a-z]{4,}", q.lower())]
        stop = {"what", "when", "where", "should", "would", "could", "about", "there", "this", "that", "with", "from"}
        words = [w for w in words if w not in stop][:6]
        if words:
            pool = list_document_learnings(memory, limit=40)
            hits = [e for e in pool if any(w in e.get("content", "").lower() for w in words)][:limit]
    if not hits:
        return ""
    lines = []
    for e in hits:
        line = filter_trusted_content(e.get("content", ""))
        if line:
            lines.append(f"- {line}")
    if not lines:
        return ""
    return "Relevant lessons from ingested documents:\n" + "\n".join(lines)


def format_learnings_markdown(entries: list[dict], *, sources: list[dict] | None = None) -> str:
    lines: list[str] = []
    if sources:
        lines.append("**Ingested sources**")
        for s in sources[:15]:
            title = s.get("title") or s.get("path", "document")
            typ = s.get("type", "file")
            lessons = s.get("lessons") or 0
            learned = "learned" if s.get("learned_at") else "indexed only"
            lines.append(f"- **{title}** ({typ}, {lessons} lessons, {learned})")
        lines.append("")
    if not entries:
        lines.append("_No document lessons stored yet._")
        return "\n".join(lines)
    lines.append("**Lessons from documents**")
    for e in entries:
        lines.append(f"• {e.get('content', '')}")
    return "\n".join(lines)
