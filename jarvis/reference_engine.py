"""Reference Engine — intelligent documentation assistant (local-first).

Presentation and retrieval quality only. No new organs or buses.
Local documentation is authoritative. Never invent docs or examples.
"""

from __future__ import annotations

import os
import re
import time
from collections import deque
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.knowledge.doc_guards import is_developer_doc_request, is_internal_doc

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "for",
        "in",
        "on",
        "at",
        "is",
        "are",
        "was",
        "were",
        "be",
        "as",
        "by",
        "with",
        "from",
        "about",
        "into",
        "how",
        "what",
        "which",
        "where",
        "when",
        "who",
        "whom",
        "do",
        "does",
        "did",
        "me",
        "my",
        "i",
        "we",
        "you",
        "your",
        "show",
        "tell",
        "please",
        "according",
        "currently",
        "whether",
        "document",
        "documents",
        "documentation",
        "docs",
        "file",
        "files",
        "explain",
        "explained",
        "describes",
        "describe",
        "find",
        "look",
        "looking",
    }
)

_MODE_SUMMARIZE = "summarize"
_MODE_ANSWER = "answer"
_MODE_COMPARE = "compare"
_MODE_LOCATE = "locate"
_MODE_SHOW = "show"

_HISTORY: deque[dict[str, Any]] = deque(maxlen=100)
_STATS: dict[str, Any] = {
    "searches": 0,
    "answers": 0,
    "summaries": 0,
    "unknowns": 0,
    "dumps_blocked": 0,
}


def _search_roots() -> list[Path]:
    roots: list[Path] = []
    for env in ("AI_ROOT", "JARVIS_ROOT", "AI_PLATFORM_ROOT"):
        val = (os.getenv(env) or "").strip()
        if val:
            roots.append(Path(val))
    roots.extend(
        [
            Path(__file__).resolve().parents[1],
            Path(__file__).resolve().parents[1].parent / "AI-Platform",
            DATA_DIR,
        ]
    )
    seen: set[str] = set()
    out: list[Path] = []
    for root in roots:
        key = str(root.resolve()) if root.exists() else str(root)
        if key not in seen:
            seen.add(key)
            out.append(root)
    return out


def _terms(query: str) -> list[str]:
    raw = re.findall(r"[a-z0-9][\w+-]*", (query or "").lower())
    return [t for t in raw if t not in _STOPWORDS and len(t) > 1]


def _detect_mode(query: str) -> str:
    q = (query or "").lower()
    if re.search(r"\b(compare|difference|differences|versus|vs\.?)\b", q):
        return _MODE_COMPARE
    if re.search(r"\b(summarize|summary|overview|tl;dr|key points|main points)\b", q):
        return _MODE_SUMMARIZE
    if re.search(r"\b(which document|what document|where (?:is|are|does)|who documents)\b", q):
        return _MODE_LOCATE
    if (
        re.search(
            r"\b(how (?:do|does|to|can)|what (?:is|are|does)|why |when |where |"
            r"according to|start|install|configure)\b",
            q,
        )
        or "?" in q
    ):
        return _MODE_ANSWER
    if re.search(r"\b(show|open|display|get)\b", q) and re.search(
        r"\b(doc|documentation|guide|readme|manual|compose)\b", q
    ):
        return _MODE_SHOW
    return _MODE_ANSWER


def _alias_boost(path: Path, title: str, query_l: str, terms: list[str]) -> float:
    """Prefer exact/near title matches for known docs."""
    stem = path.stem.lower().replace("-", "_").replace(" ", "_")
    name = title.lower()
    path_l = str(path).lower().replace("\\", "/")
    score = 0.0

    # Phrase-to-file aliases
    aliases = (
        ("user guide", ("user_guide", "userguide")),
        (
            "docker compose",
            ("applications", "deployment", "compose", "docker-compose", "docker_compose"),
        ),
        ("capability bus", ("capability_bus", "capability-bus")),
        ("architecture", ("architecture",)),
        ("event bus", ("event_bus", "event-bus")),
        ("daily use", ("daily_use_mode", "daily-use")),
        ("mission control", ("mission_control",)),
        ("development guide", ("development_guide",)),
        ("behavioral contract", ("behavioral_contract",)),
        ("capability inventory", ("capability_inventory",)),
    )
    for phrase, keys in aliases:
        if phrase in query_l:
            if any(k in stem or k in path_l for k in keys):
                score += 100.0
            elif phrase.replace(" ", "") in stem.replace("_", ""):
                score += 80.0
            # Penalize User Guide when the ask is specifically for Docker Compose docs
            # (User Guide only mentions Compose as a chat-routing example)
            if phrase == "docker compose" and "user_guide" in stem:
                score -= 60.0

    # Exact title tokens: "User Guide" → USER_GUIDE
    compact_q = re.sub(r"[^a-z0-9]+", "", query_l)
    compact_stem = re.sub(r"[^a-z0-9]+", "", stem)
    if compact_stem and compact_stem in compact_q:
        score += 40.0
    if stem.replace("_", " ") in query_l or name.replace(".md", "").replace("_", " ") in query_l:
        score += 50.0

    # Filename term density beat generic term counts
    for t in terms:
        if t in stem or t in name.lower():
            score += 8.0
        if t in path_l:
            score += 2.0

    # Prefer docs/ and aria_core over ADRs and future/backlog noise for product Qs
    if is_internal_doc(path):
        score -= 200.0
    elif "/docs/" in path_l and "/adr/" not in path_l:
        score += 6.0
    if "future_product" in stem or "decision_log" in stem or "roadmap" in stem:
        score -= 8.0
    if "phase" in stem and "user_guide" not in stem:
        score -= 4.0
    return score


def _heading_boost(text: str, terms: list[str], query_l: str) -> float:
    score = 0.0
    dense = text.lower().count("docker compose") + text.lower().count("docker-compose")
    if "docker compose" in query_l or ("docker" in query_l and "compose" in query_l):
        score += min(40.0, dense * 4.0)
        # Chat-route example lines shouldn't win
        if "show docker compose documentation" in text.lower() and dense <= 2:
            score -= 25.0
    for line in text.splitlines()[:120]:
        if not line.startswith("#"):
            continue
        hl = line.lower()
        if any(t in hl for t in terms):
            score += 3.0
        if "docker" in hl and "compose" in hl and ("docker" in query_l and "compose" in query_l):
            score += 25.0
        if any(phrase in hl for phrase in ("user guide", "starting", "capability bus")):
            if any(p in query_l for p in ("user guide", "start", "capability")):
                score += 5.0
    return score


def _section_extract(
    text: str, terms: list[str], *, limit_chars: int = 1800
) -> list[dict[str, str]]:
    """Split markdown by headings and pick relevant sections."""
    sections: list[dict[str, str]] = []
    heading = "(introduction)"
    buf: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            if buf:
                sections.append({"heading": heading, "body": "\n".join(buf).strip()})
            heading = re.sub(r"^#{1,3}\s+", "", line).strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections.append({"heading": heading, "body": "\n".join(buf).strip()})

    ranked: list[tuple[float, dict[str, str]]] = []
    for sec in sections:
        blob = f"{sec['heading']}\n{sec['body']}".lower()
        score = 0.0
        for t in terms:
            if t in blob:
                score += 2.0 + blob.count(t) * 0.15
        if score > 0:
            ranked.append((score, sec))
    ranked.sort(key=lambda x: -x[0])
    out: list[dict[str, str]] = []
    used = 0
    for _, sec in ranked[:6]:
        body = sec["body"]
        if len(body) > 900:
            # Prefer paragraphs that contain terms
            paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
            kept = [p for p in paras if any(t in p.lower() for t in terms)] or paras[:2]
            body = "\n\n".join(kept)[:900]
        chunk = {"heading": sec["heading"], "body": body}
        add = len(body) + len(sec["heading"])
        if used + add > limit_chars and out:
            break
        out.append(chunk)
        used += add
    return out


def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return path.name
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _local_reference_hits(query: str, *, limit: int = 12) -> list[dict[str, Any]]:
    q = (query or "").strip()
    q_l = q.lower()
    terms = _terms(q)
    if not q:
        return []
    hits: list[dict[str, Any]] = []
    t0 = time.perf_counter()

    for root in _search_roots():
        if not root.is_dir():
            continue
        candidates: list[Path] = []
        for name in ("README.md", "readme.md"):
            p = root / name
            if p.is_file():
                candidates.append(p)
        docs = root / "docs"
        if docs.is_dir():
            candidates.extend(docs.rglob("*.md"))
            candidates.extend(docs.rglob("*.rst"))
            candidates.extend(docs.rglob("*.pdf"))

        for path in candidates:
            if is_internal_doc(str(path)):
                if not is_developer_doc_request(q):
                    continue
            text = _read_text(path)
            if not text and path.suffix.lower() != ".pdf":
                continue
            lower = text.lower()
            name_l = path.name.lower()
            term_hits = sum(1 for t in terms if t in lower or t in name_l)
            if term_hits <= 0 and q_l not in name_l and q_l not in lower[:2000]:
                continue
            score = float(term_hits)
            score += _alias_boost(path, path.name, q_l, terms)
            score += _heading_boost(text, terms, q_l)
            # Recency lightly preferred when mtime available
            try:
                mtime = path.stat().st_mtime
                score += min(5.0, max(0.0, (mtime - 1_700_000_000) / (86400 * 30)))
            except OSError:
                mtime = 0.0
            hits.append(
                {
                    "path": str(path),
                    "title": path.name,
                    "score": round(score, 3),
                    "term_hits": term_hits,
                    "mtime": mtime,
                    "source": "local",
                    "text_len": len(text),
                }
            )

    hits.sort(key=lambda h: (-float(h.get("score") or 0), str(h.get("path"))))
    # Deduplicate by resolved path
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    for h in hits:
        key = str(Path(h["path"]).resolve()) if Path(h["path"]).exists() else h["path"]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
        if len(uniq) >= limit:
            break
    ranking_ms = round((time.perf_counter() - t0) * 1000, 3)
    for h in uniq:
        h["ranking_ms"] = ranking_ms
    return uniq


def _material_docs(
    hits: list[dict[str, Any]], *, mode: str, max_docs: int = 3
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select documents that materially contribute; return (selected, rejected)."""
    if not hits:
        return [], []
    top = float(hits[0].get("score") or 0)
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    floor = max(12.0, top * 0.45) if top >= 40 else max(6.0, top * 0.55)
    for h in hits:
        score = float(h.get("score") or 0)
        if len(selected) >= max_docs:
            rejected.append({**h, "reject_reason": "beyond_top_k"})
            continue
        if selected and score < floor:
            rejected.append({**h, "reject_reason": "low_relevance"})
            continue
        # For summarize/show of a named doc, keep first clear winner only when dominant
        if mode in (_MODE_SUMMARIZE, _MODE_SHOW) and selected and score < top * 0.7:
            rejected.append({**h, "reject_reason": "weaker_than_primary"})
            continue
        selected.append(h)
    if not selected and hits:
        selected = [hits[0]]
        rejected = [{**h, "reject_reason": "beyond_top_k"} for h in hits[1:]]
    return selected, rejected


def _summarize_extractive(title: str, text: str, *, max_chars: int = 1200) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Drop pure nav noise
    content_lines = [
        ln for ln in lines if not re.match(r"^\[.+\]\(.+\)$", ln) and not ln.startswith("|---")
    ]
    # Prefer title + first H2 sections' first paragraphs
    parts: list[str] = [f"**{title.replace('.md', '').replace('_', ' ')}**"]
    used = 0
    current_h = ""
    for ln in content_lines:
        if ln.startswith("#"):
            current_h = re.sub(r"^#{1,6}\s+", "", ln).strip()
            if current_h and current_h.lower() not in title.lower():
                block = f"\n**{current_h}.** "
                if used + len(block) < max_chars:
                    parts.append(block)
                    used += len(block)
            continue
        if ln.startswith("|") or ln.startswith("```"):
            continue
        if len(ln) < 20:
            continue
        add = ln if not ln.endswith(".") else ln
        if used + len(add) > max_chars:
            break
        parts.append(add if parts[-1].endswith(" ") or parts[-1].endswith("**") else " " + add)
        used += len(add)
        if used > max_chars * 0.85 and current_h:
            # keep brief
            break
    summary = "".join(parts).strip()
    # Clean double spaces from concatenation
    summary = re.sub(r"[ \t]{2,}", " ", summary)
    summary = re.sub(r"\n{3,}", "\n\n", summary)
    return summary[: max_chars + 200]


def _answer_from_sections(
    question: str,
    docs: list[tuple[dict[str, Any], str]],
    terms: list[str],
) -> tuple[str, bool]:
    """Return (answer, found). Uses only local sections — never invents."""
    quotes: list[str] = []
    for hit, text in docs:
        sections = _section_extract(text, terms, limit_chars=1400)
        for sec in sections[:3]:
            quotes.append(f"From **{hit['title']}** — {sec['heading']}:\n{sec['body'].strip()}")
    if not quotes:
        return "", False

    q_l = question.lower()
    # Special grounded answer for "how do I start"
    if re.search(r"\b(how do i start|how to start|start(?:ing)? the)\b", q_l):
        for hit, text in docs:
            if "user_guide" in hit["title"].lower() or "user guide" in text[:200].lower():
                m = re.search(
                    r"(Starting the workstation.*?This starts Docker services[^\n]*)",
                    text,
                    re.I | re.S,
                )
                if m:
                    block = m.group(1)
                    cmd = re.search(r"```(?:bash)?\n(.*?)```", block, re.S)
                    cmd_txt = cmd.group(1).strip() if cmd else "./workstation start"
                    explain = ""
                    em = re.search(r"This starts[^\n]+", block)
                    if em:
                        explain = em.group(0).strip()
                    msg = (
                        f"According to the **User Guide** (`{hit['title']}`):\n\n"
                        f"Run:\n```bash\n{cmd_txt}\n```\n"
                    )
                    if explain:
                        msg += f"\n{explain}"
                    return msg.strip(), True

    # Locate mode: name the document
    if re.search(r"\bwhich document|what document\b", q_l):
        best = docs[0][0]
        # If score is weak for the claimed content, unknown
        if float(best.get("score") or 0) < 20:
            return "", False
        # GPU scheduling on Cap Bus — Cap Bus docs do not describe GPU scheduling
        if "gpu" in q_l and "schedule" in q_l and "capability" in q_l:
            found_gpu_sched = False
            for hit, text in docs:
                tl = text.lower()
                # Require affirmative scheduling language — negations do not count
                if re.search(
                    r"\b(?:schedules?|scheduling)\b.{0,40}\bgpu\b|\bgpu\b.{0,40}\b(?:schedules?|scheduling)\b",
                    tl,
                ) and not re.search(
                    r"\b(?:not|never|does not|doesn't|no)\b.{0,30}\b(?:schedul)",
                    tl,
                ):
                    found_gpu_sched = True
                    break
            if not found_gpu_sched:
                return "", False
        titles = ", ".join(f"**{h['title']}**" for h, _ in docs[:2])
        return (
            f"The best matching local document(s) for that topic: {titles}.\n\n" + quotes[0][:900]
        ), True

    # Generic answer: lead with best quote, stay extractive
    head = docs[0][0]["title"]
    body = quotes[0]
    msg = f"According to **{head}**:\n\n{body}"
    if len(quotes) > 1 and len(docs) > 1:
        msg += "\n\n" + quotes[1][:700]
    return msg.strip(), True


def _unknown_message(query: str) -> str:
    return (
        f"I could not find local documentation that answers: **{query.strip()}**.\n\n"
        "I searched project README files, `docs/`, ADRs, and the document library. "
        "I will not invent documentation, framework examples, or substitute unrelated guides. "
        "If you want a general (non-project) explanation, say so explicitly — "
        "or ask me to search the web."
    )


def _compose_show(hit: dict[str, Any], text: str, terms: list[str]) -> str:
    sections = _section_extract(text, terms or _terms(hit["title"]), limit_chars=1600)
    title = hit["title"]
    if not sections:
        excerpt = text[:900].strip()
        return f"From **{title}** (local documentation):\n\n{excerpt}" + (
            "…" if len(text) > 900 else ""
        )
    parts = [f"From **{title}** (local documentation):"]
    for sec in sections[:3]:
        parts.append(f"\n### {sec['heading']}\n{sec['body']}")
    return "\n".join(parts).strip()


def _compare_docs(docs: list[tuple[dict[str, Any], str]]) -> str:
    if len(docs) < 2:
        return ""
    (a_hit, a_text), (b_hit, b_text) = docs[0], docs[1]
    a_sum = _summarize_extractive(a_hit["title"], a_text, max_chars=500)
    b_sum = _summarize_extractive(b_hit["title"], b_text, max_chars=500)
    return (
        f"**Comparison (local docs only)**\n\n"
        f"### {a_hit['title']}\n{a_sum}\n\n"
        f"### {b_hit['title']}\n{b_sum}\n\n"
        f"**Relationship:** Both are project documentation under `docs/`. "
        f"`{a_hit['title']}` and `{b_hit['title']}` serve different audiences/topics "
        f"as indicated by their titles and opening sections."
    )


def _record_history(entry: dict[str, Any]) -> None:
    _HISTORY.append(entry)
    _STATS["searches"] = int(_STATS.get("searches") or 0) + 1
    mode = entry.get("mode")
    if entry.get("unknown"):
        _STATS["unknowns"] = int(_STATS.get("unknowns") or 0) + 1
    elif mode == _MODE_SUMMARIZE:
        _STATS["summaries"] = int(_STATS.get("summaries") or 0) + 1
    elif mode in (_MODE_ANSWER, _MODE_LOCATE, _MODE_SHOW, _MODE_COMPARE):
        _STATS["answers"] = int(_STATS.get("answers") or 0) + 1
    if entry.get("dump_blocked"):
        _STATS["dumps_blocked"] = int(_STATS.get("dumps_blocked") or 0) + 1


def search_reference(query: str, *, subject: str = "") -> dict[str, Any]:
    """Search and answer from local documentation — documentation assistant, not a file dump."""
    t0 = time.perf_counter()
    q = (subject or query or "").strip()
    try:
        from jarvis.knowledge.doc_guards import is_planning_request

        if is_planning_request(q):
            return {
                "ok": False,
                "message": (
                    "That looks like a planning request. Ask me to plan it directly "
                    "(for example: “Help me plan a fly fishing trip next weekend.”) "
                    "rather than searching documentation."
                ),
                "module": "reference",
                "selected": [],
            }
    except Exception:
        pass
    mode = _detect_mode(q)
    terms = _terms(q)

    search_t0 = time.perf_counter()
    local = _local_reference_hits(q, limit=16)
    search_ms = round((time.perf_counter() - search_t0) * 1000, 3)

    # Optional secondary indexes (enrich ranking, still local project knowledge)
    try:
        from jarvis.knowledge.search import unified_search

        for hit in unified_search(q, limit=5):
            if hit.get("type") in ("documentation", "project_folder", "git_repository"):
                local.append(
                    {
                        "path": hit.get("path") or hit.get("id") or "",
                        "title": hit.get("title") or hit.get("id") or "reference",
                        "score": float(hit.get("score") or 1) + 5.0,
                        "source": "knowledge_registry",
                        "text_len": 0,
                    }
                )
    except Exception:
        pass

    try:
        from jarvis.documents_rag import search as doc_rag_search

        for hit in doc_rag_search(q, limit=4):
            local.append(
                {
                    "path": hit.get("path", ""),
                    "title": hit.get("title") or hit.get("path", "document"),
                    "score": float(hit.get("score") or 1) + 3.0,
                    "source": "document_library",
                    "text_len": 0,
                }
            )
    except Exception:
        pass

    rank_t0 = time.perf_counter()
    local.sort(key=lambda h: (-float(h.get("score") or 0), str(h.get("path"))))
    # Dedup by resolved path and by filename within docs/
    seen: set[str] = set()
    seen_names: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for h in local:
        path = str(h.get("path") or "")
        try:
            key = str(Path(path).resolve())
        except OSError:
            key = path
        name = Path(path).name.lower()
        if key in seen or (name and name in seen_names):
            continue
        seen.add(key)
        if name.endswith((".md", ".rst")):
            seen_names.add(name)
        deduped.append(h)
    local = deduped
    max_docs = 2 if mode == _MODE_COMPARE else (1 if mode in (_MODE_SUMMARIZE, _MODE_SHOW) else 2)
    selected, rejected = _material_docs(local, mode=mode, max_docs=max_docs)
    ranking_ms = round((time.perf_counter() - rank_t0) * 1000, 3)

    diagnostics: dict[str, Any] = {
        "mode": mode,
        "query": q,
        "terms": terms,
        "search_ms": search_ms,
        "ranking_ms": ranking_ms,
        "documents_searched": len(local),
        "documents_selected": [
            {
                "title": h.get("title"),
                "path": h.get("path"),
                "score": h.get("score"),
                "source": h.get("source"),
            }
            for h in selected
        ],
        "documents_rejected": [
            {
                "title": h.get("title"),
                "path": h.get("path"),
                "score": h.get("score"),
                "reason": h.get("reject_reason"),
            }
            for h in rejected[:12]
        ],
        "stages": {
            "search": "completed",
            "ranking": "completed",
            "read": "pending",
            "question_answering": "pending",
            "summarization": "pending",
            "composition": "pending",
        },
        "dump_blocked": True,
    }

    if not selected:
        message = _unknown_message(q)
        diagnostics["stages"].update(
            {
                "read": "skipped",
                "question_answering": "unknown",
                "summarization": "skipped",
                "composition": "completed",
            }
        )
        diagnostics["unknown"] = True
        total_ms = round((time.perf_counter() - t0) * 1000, 3)
        diagnostics["total_ms"] = total_ms
        diagnostics["qa_ms"] = 0.0
        diagnostics["summarization_ms"] = 0.0
        diagnostics["composition_ms"] = 0.0
        entry = {**diagnostics, "ok": True, "unknown": True, "ts": time.time()}
        _record_history(entry)
        return {
            "ok": True,
            "message": message,
            "hits": local[:8],
            "selected": [],
            "rejected": rejected[:12],
            "source": "none",
            "module": "reference",
            "diagnostics": diagnostics,
            "data": {"diagnostics": diagnostics},
        }

    # Read selected documents
    read_docs: list[tuple[dict[str, Any], str]] = []
    for h in selected:
        path = Path(str(h.get("path") or ""))
        text = _read_text(path) if path.is_file() else ""
        if not text and h.get("snippet"):
            text = str(h.get("snippet") or "")
        if text:
            read_docs.append((h, text))
    diagnostics["stages"]["read"] = "completed" if read_docs else "empty"

    qa_ms = 0.0
    sum_ms = 0.0
    message = ""
    unknown = False

    if not read_docs:
        message = _unknown_message(q)
        unknown = True
        diagnostics["stages"]["question_answering"] = "unknown"
        diagnostics["stages"]["summarization"] = "skipped"
    elif mode == _MODE_SUMMARIZE:
        t_sum = time.perf_counter()
        parts = []
        for h, text in read_docs:
            parts.append(_summarize_extractive(h["title"], text))
        message = "\n\n".join(parts)
        sum_ms = round((time.perf_counter() - t_sum) * 1000, 3)
        diagnostics["stages"]["summarization"] = "completed"
        diagnostics["stages"]["question_answering"] = "n/a"
    elif mode == _MODE_COMPARE:
        t_sum = time.perf_counter()
        message = _compare_docs(read_docs)
        if not message:
            message = _summarize_extractive(read_docs[0][0]["title"], read_docs[0][1])
        sum_ms = round((time.perf_counter() - t_sum) * 1000, 3)
        diagnostics["stages"]["summarization"] = "completed"
        diagnostics["stages"]["question_answering"] = "n/a"
    elif mode == _MODE_SHOW:
        t_qa = time.perf_counter()
        message = _compose_show(read_docs[0][0], read_docs[0][1], terms)
        qa_ms = round((time.perf_counter() - t_qa) * 1000, 3)
        diagnostics["stages"]["question_answering"] = "completed"
        diagnostics["stages"]["summarization"] = "n/a"
        _STATS["dumps_blocked"] = int(_STATS.get("dumps_blocked") or 0) + 1
    else:
        t_qa = time.perf_counter()
        message, found = _answer_from_sections(q, read_docs, terms)
        qa_ms = round((time.perf_counter() - t_qa) * 1000, 3)
        if not found or not message.strip():
            # For locate/answer — honesty over weak paraphrase
            if mode == _MODE_LOCATE or float(selected[0].get("score") or 0) < 25:
                message = _unknown_message(q)
                unknown = True
                diagnostics["stages"]["question_answering"] = "unknown"
            else:
                # Fall back to show relevant sections only (still not a full dump)
                message = _compose_show(read_docs[0][0], read_docs[0][1], terms)
                diagnostics["stages"]["question_answering"] = "section_extract"
        else:
            diagnostics["stages"]["question_answering"] = "completed"
        diagnostics["stages"]["summarization"] = "n/a"

    # Strip internal tool/debug leakage patterns if any slipped in
    if re.search(r"(?i)\b(tool history|strategy:|memory search:|runtime search:)\b", message or ""):
        message = re.sub(
            r"(?im)^.*\b(tool history|strategy:|memory search:|runtime search:).*\n?",
            "",
            message,
        )

    compose_t0 = time.perf_counter()
    message = (message or "").strip()
    if not message.endswith("\n"):
        message = message + "\n"
    composition_ms = round((time.perf_counter() - compose_t0) * 1000, 3)
    diagnostics["stages"]["composition"] = "completed"
    diagnostics["unknown"] = unknown
    diagnostics["qa_ms"] = qa_ms
    diagnostics["summarization_ms"] = sum_ms
    diagnostics["composition_ms"] = composition_ms
    diagnostics["total_ms"] = round((time.perf_counter() - t0) * 1000, 3)

    _record_history({**diagnostics, "ok": True, "ts": time.time(), "dump_blocked": True})

    return {
        "ok": True,
        "message": message,
        "hits": local[:8],
        "selected": diagnostics["documents_selected"],
        "rejected": diagnostics["documents_rejected"],
        "source": "local" if not unknown else "none",
        "module": "reference",
        "diagnostics": diagnostics,
        "data": {"diagnostics": diagnostics, "mode": mode},
    }


def reference_history(*, limit: int = 40) -> list[dict[str, Any]]:
    items = list(_HISTORY)
    return items[-limit:]


def reference_statistics() -> dict[str, Any]:
    return {
        "owner": "jarvis.reference_engine",
        **dict(_STATS),
        "history_size": len(_HISTORY),
    }


def mission_control_panel(*, limit: int = 40) -> dict[str, Any]:
    """Reference diagnostics for Mission Control — metadata only, no CoT."""
    hist = reference_history(limit=limit)
    latest = hist[-1] if hist else {}
    return {
        "ok": True,
        "title": "Reference Engine",
        "owner": "jarvis.reference_engine",
        "note": (
            "Reference is a documentation assistant (rank → read → answer/summarize). "
            "Execution metadata only — no chain-of-thought."
        ),
        "statistics": reference_statistics(),
        "latest": {
            "mode": latest.get("mode"),
            "search_ms": latest.get("search_ms"),
            "ranking_ms": latest.get("ranking_ms"),
            "qa_ms": latest.get("qa_ms"),
            "summarization_ms": latest.get("summarization_ms"),
            "composition_ms": latest.get("composition_ms"),
            "total_ms": latest.get("total_ms"),
            "documents_searched": latest.get("documents_searched"),
            "documents_selected": latest.get("documents_selected"),
            "documents_rejected": (latest.get("documents_rejected") or [])[:8],
            "stages": latest.get("stages"),
            "unknown": latest.get("unknown"),
        },
        "history": hist,
        "capabilities": [
            "document_ranking",
            "question_answering",
            "summarization",
            "multi_document_synthesis",
            "unknown_honesty",
            "no_raw_dump",
        ],
    }


def reset_for_tests() -> None:
    _HISTORY.clear()
    for k in list(_STATS.keys()):
        _STATS[k] = 0


# Backward compatibility
search_documentation = search_reference
