"""Learn-about topics: multi-search, brief, save under data/knowledge/, inject in chat."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from jarvis.config import DATA_DIR

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
MAX_BRIEF_CHARS = 8000
MAX_CONTEXT_CHARS = 2800


def slugify(topic: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (topic or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:80] or "topic")


def is_learn_command(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return False
    if re.match(r"^learn about:\s*.+", text, re.I):
        return True
    lower = text.lower()
    return bool(
        re.search(
            r"\b(learn about|research topic|study up on|go learn about|deep dive on)\b",
            lower,
        )
    )


def parse_learn_topic(message: str) -> str:
    text = (message or "").strip()
    for pat in (
        r"^learn about:\s*(.+)$",
        r"^(?:please\s+)?learn about[:\s]+(.+)$",
        r"^(?:research|study up on|go learn about|deep dive on)[:\s]+(.+)$",
    ):
        m = re.match(pat, text, re.I | re.S)
        if m:
            return m.group(1).strip()
    return re.sub(
        r"^(please\s+)?(learn about|research topic|study up on|go learn about|deep dive on)[:\s]*",
        "",
        text,
        flags=re.I,
    ).strip() or text


def search_queries(topic: str) -> list[str]:
    t = (topic or "").strip()
    if not t:
        return []
    candidates = [t, f"what is {t}", f"{t} overview guide"]
    seen: set[str] = set()
    out: list[str] = []
    for q in candidates:
        key = q.lower()
        if key not in seen:
            seen.add(key)
            out.append(q)
    return out[:3]


def collect_search_results(topic: str, *, per_query: int = 4) -> list[dict]:
    from jarvis import web_search

    seen_urls: set[str] = set()
    merged: list[dict] = []
    for query in search_queries(topic):
        hits = web_search.search(query, limit=per_query)
        for hit in hits:
            url = (hit.get("url") or "").strip()
            if url:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
            merged.append({**hit, "search_query": query})
    return merged[:14]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_brief(topic: str, results: list[dict]) -> str:
    from jarvis import llm, web_search

    if not results:
        return (
            f"# {topic}\n\n"
            "No web results were found. Try again later, check web search setup, "
            "or run `./venv/bin/pip install ddgs`."
        )

    context = web_search.format_results_for_llm(results)
    system = (
        "You write research briefs for a personal assistant. Use ONLY the search snippets. "
        "Be accurate; say when information is thin. Use markdown with these sections:\n"
        "## Overview\n## Key points (bullet list)\n## Details\n## Gaps (what is missing or uncertain)\n"
        "Do not invent facts."
    )
    user = f"Topic: {topic}\n\nWeb snippets:\n{context}"
    try:
        body = llm.ask(llm.general_model(), [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]).strip()
    except Exception as exc:
        body = f"## Overview\n\nCould not synthesize brief: {exc}\n\n## Raw snippets\n\n{context[:4000]}"
    if not body.startswith("#"):
        body = f"# {topic}\n\n{body}"
    return body[:MAX_BRIEF_CHARS]


def _format_sources(results: list[dict]) -> str:
    lines = ["## Sources"]
    for i, r in enumerate(results, 1):
        title = r.get("title") or "Result"
        url = r.get("url") or ""
        line = f"{i}. **{title}**"
        if url:
            line += f" — {url}"
        lines.append(line)
    return "\n".join(lines)


def save_brief(topic: str, body: str, results: list[dict]) -> dict:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(topic)
    path = KNOWLEDGE_DIR / f"{slug}.md"
    meta = {
        "topic": topic,
        "slug": slug,
        "updated": _utc_now(),
        "source_count": len(results),
    }
    sources_block = _format_sources(results)
    if "## Sources" not in body:
        body = f"{body.rstrip()}\n\n{sources_block}\n"

    front = "---\n" + json.dumps(meta, indent=2) + "\n---\n\n"
    path.write_text(front + body.strip() + "\n", encoding="utf-8")
    try:
        rel = path.relative_to(DATA_DIR)
    except ValueError:
        rel = Path("knowledge") / path.name
    return {
        "path": str(path),
        "relative_path": str(rel).replace("\\", "/"),
        "slug": slug,
        "topic": topic,
    }


def extract_key_points(body: str, *, max_points: int = 6) -> list[str]:
    text = body or ""
    section = ""
    if m := re.search(r"## Key points[^\n]*\n(.*?)(?:\n## |\Z)", text, re.I | re.S):
        section = m.group(1)
    bullets = re.findall(r"^[-*]\s+(.+)$", section, re.M)
    if not bullets:
        bullets = re.findall(r"^[-*]\s+(.+)$", text, re.M)
    cleaned: list[str] = []
    for b in bullets:
        line = re.sub(r"\*\*", "", b).strip()
        if line and line not in cleaned:
            cleaned.append(line)
        if len(cleaned) >= max_points:
            break
    return cleaned


def load_brief(slug: str) -> dict | None:
    path = KNOWLEDGE_DIR / f"{slugify(slug)}.md"
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8")
    topic = slugify(slug).replace("-", " ")
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = json.loads(parts[1])
                topic = meta.get("topic") or topic
            except json.JSONDecodeError:
                meta = {}
            body = parts[2].strip()
        else:
            meta = {}
    else:
        meta = {}
    return {
        "slug": slugify(slug),
        "topic": topic,
        "path": str(path),
        "relative_path": f"knowledge/{path.name}",
        "body": body,
        "meta": meta,
        "key_points": extract_key_points(body),
    }


def list_topics() -> list[dict]:
    if not KNOWLEDGE_DIR.is_dir():
        return []
    items: list[dict] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        brief = load_brief(path.stem)
        if brief:
            items.append({
                "slug": brief["slug"],
                "topic": brief["topic"],
                "path": brief["path"],
                "updated": (brief.get("meta") or {}).get("updated", ""),
            })
    return items


def remember_key_points(memory, topic: str, points: list[str] | None = None, *, slug: str = "") -> list[str]:
    slug = slug or slugify(topic)
    brief = load_brief(slug)
    pts = points or (brief.get("key_points") if brief else []) or []
    if not pts and brief:
        pts = extract_key_points(brief.get("body", ""))
    stored: list[str] = []
    tag = slug[:40]
    label = (brief or {}).get("topic") or topic or slug.replace("-", " ")
    for point in pts[:8]:
        text = f"About {label}: {point}"
        memory.add("fact", text, tags=["knowledge", tag])
        stored.append(point)
    return stored


def learn_topic(topic: str) -> dict:
    """Multi-search, synthesize brief, save to data/knowledge/."""
    topic = (topic or "").strip()
    if not topic:
        return {"ok": False, "message": "Tell me what to learn about — e.g. `learn about: Movidius VPU`."}

    results = collect_search_results(topic)
    body = build_brief(topic, results)
    saved = save_brief(topic, body, results)
    key_points = extract_key_points(body)

    return {
        "ok": True,
        "topic": topic,
        "slug": saved["slug"],
        "path": saved["path"],
        "relative_path": saved["relative_path"],
        "result_count": len(results),
        "key_points": key_points,
        "body": body,
        "message": body,
    }


def _score_topic(query: str, slug: str, topic: str, body: str) -> float:
    words = {w for w in re.findall(r"[a-z0-9]{3,}", query.lower())}
    if not words:
        return 0.0
    hay = f"{slug} {topic} {body[:1200]}".lower()
    hits = sum(1 for w in words if w in hay)
    slug_words = set(slug.split("-"))
    slug_hits = len(words & slug_words)
    return hits + slug_hits * 2


def match_topics(query: str, *, limit: int = 2) -> list[dict]:
    items = list_topics()
    if not items:
        return []
    scored = []
    for item in items:
        brief = load_brief(item["slug"])
        if not brief:
            continue
        score = _score_topic(query, item["slug"], item["topic"], brief.get("body", ""))
        if score > 0:
            scored.append((score, brief))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in scored[:limit]]


def context_for_query(query: str, *, max_chars: int = MAX_CONTEXT_CHARS) -> tuple[str, list[str]]:
    """Return context block for chat when a saved topic matches."""
    warnings: list[str] = []
    hits = match_topics(query, limit=2)
    if not hits:
        return "", warnings
    parts = ["Saved knowledge (prefer this over guessing):"]
    budget = max_chars
    for brief in hits:
        excerpt = brief.get("body", "")
        if len(excerpt) > 1400:
            excerpt = excerpt[:1400] + "\n… (truncated)"
        block = f"**{brief['topic']}** (`{brief['relative_path'] if 'relative_path' in brief else brief['slug']}`)\n{excerpt}"
        if len(block) > budget:
            block = block[:budget] + "\n…"
        parts.append(block)
        budget -= len(block)
        if budget < 200:
            break
    return "\n\n".join(parts), warnings
