"""Nightly self-upgrading knowledge — web research digests stored for ARIA."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from jarvis.config import PROJECT_ROOT
from jarvis.knowledge import (
    KNOWLEDGE_DIR,
    _utc_now,
    extract_key_points,
    remember_key_points,
    slugify,
)
from jarvis.modules.journal import _today

log = logging.getLogger("jarvis.knowledge_research")

RESEARCH_DIR = KNOWLEDGE_DIR / "research"
STATE_FILE = RESEARCH_DIR / "_state.json"
DAILY_RESEARCH_TAG = "daily-research"

Category = dict[str, Any]

_PROFILE_PREFIXES: dict[str, re.Pattern[str]] = {
    "interests": re.compile(r"^User often works on:\s*(.+?)\.?\s*$", re.I),
    "tech_stack": re.compile(r"^User's tech stack and tools:\s*(.+?)\.?\s*$", re.I),
    "role": re.compile(r"^User's role or background:\s*(.+?)\.?\s*$", re.I),
    "primary_use": re.compile(r"^User primarily uses Jarvis for\s*(.+?)\.?\s*$", re.I),
    "notes": re.compile(r"^User notes for Jarvis:\s*(.+?)\.?\s*$", re.I),
    "location": re.compile(r"^User is based in\s*(.+?)\.?\s*$", re.I),
    "learning_goals": re.compile(r"^User wants to learn about:\s*(.+?)\.?\s*$", re.I),
    "work_context": re.compile(r"^User's work context:\s*(.+?)\.?\s*$", re.I),
    "expertise_areas": re.compile(r"^User already knows:\s*(.+?)\.?\s*$", re.I),
}

_PRIMARY_USE_QUERIES: dict[str, list[str]] = {
    "coding": ["AI coding assistant tools news", "IDE developer productivity updates"],
    "writing": ["writing assistant AI tools news", "document productivity software updates"],
    "research": ["research workflow tools news", "learning and knowledge management updates"],
    "creative": ["AI image video generation tools news", "creative software updates"],
    "data": ["data analysis Python tools news", "spreadsheet automation updates"],
}

_TOPIC_SPLIT = re.compile(r"[,;\n]+|\band\b", re.I)


def _split_topic_phrases(text: str) -> list[str]:
    parts: list[str] = []
    for chunk in _TOPIC_SPLIT.split(text or ""):
        phrase = chunk.strip(" .")
        if len(phrase) >= 3:
            parts.append(phrase)
    return parts


def _profile_field_values(memory_store) -> dict[str, str]:
    if memory_store is None:
        return {}
    values: dict[str, str] = {}
    for entry in memory_store.list_entries(namespace="profile"):
        tags = entry.get("tags") or []
        content = (entry.get("content") or "").strip()
        if not content or "summary" in tags:
            continue
        for field in _PROFILE_PREFIXES:
            if field not in tags:
                continue
            m = _PROFILE_PREFIXES[field].match(content)
            values[field] = (m.group(1) if m else content).strip()
    return values


def _profile_topic_phrases(memory_store) -> list[str]:
    """Distinct research phrases derived from profile questionnaire answers."""
    fields = _profile_field_values(memory_store)
    seen: set[str] = set()
    phrases: list[str] = []

    def add(raw: str) -> None:
        key = raw.lower()
        if key in seen or len(raw) < 3:
            return
        seen.add(key)
        phrases.append(raw)

    for chunk in _split_topic_phrases(fields.get("interests", "")):
        add(chunk)
    for chunk in _split_topic_phrases(fields.get("learning_goals", "")):
        add(chunk)
    for chunk in _split_topic_phrases(fields.get("tech_stack", "")):
        add(chunk)
    if work := fields.get("work_context", "").strip():
        add(work[:80])
    if role := fields.get("role", "").strip():
        add(role)
    if notes := fields.get("notes", "").strip():
        for chunk in _split_topic_phrases(notes):
            add(chunk)
        if len(notes) >= 12 and len(_split_topic_phrases(notes)) <= 1:
            add(notes[:80])
    if loc := fields.get("location", "").strip():
        if len(loc) >= 3:
            add(f"local news and events {loc}")

    primary_raw = fields.get("primary_use", "").strip().lower().replace(" ", "_")
    for q in _PRIMARY_USE_QUERIES.get(primary_raw, []):
        add(q)

    return phrases[:16]


def _profile_research_categories(memory_store) -> list[Category]:
    month = datetime.now().strftime("%B %Y")
    year = datetime.now().year
    categories: list[Category] = []
    for phrase in _profile_topic_phrases(memory_store):
        slug_base = slugify(phrase)[:48] or "topic"
        cat_id = f"profile_{slug_base.replace('-', '_')}"
        categories.append({
            "id": cat_id,
            "slug": f"profile-{slug_base}",
            "title": phrase[:80],
            "kind": "profile",
            "source": "questionnaire",
            "queries": [
                f"{phrase} news {month}",
                f"{phrase} latest updates {year}",
                f"{phrase} tips best practices",
            ],
        })
    return categories


def _base_categories() -> list[Category]:
    year = datetime.now().year
    month = datetime.now().strftime("%B %Y")
    return [
        {
            "id": "ai_news",
            "slug": "ai-news",
            "title": "AI news",
            "kind": "stack",
            "queries": [
                f"artificial intelligence news {month}",
                "open source LLM news this week",
                "AI agents tools news",
            ],
        },
        {
            "id": "ollama",
            "slug": "ollama-updates",
            "title": "Ollama updates",
            "kind": "stack",
            "queries": [
                "Ollama release notes new version",
                f"Ollama changelog {year}",
                "Ollama blog update models",
            ],
            "local_context": _ollama_context,
        },
        {
            "id": "zorin",
            "slug": "zorin-updates",
            "title": "Zorin OS updates",
            "kind": "stack",
            "queries": [
                "Zorin OS update release",
                f"Zorin OS {year} news",
                "Zorin OS security updates",
            ],
            "local_context": _os_context,
        },
        {
            "id": "dependencies",
            "slug": "dependency-updates",
            "title": "Dependency updates",
            "kind": "stack",
            "queries_fn": _dependency_queries,
            "local_context": _dependency_context,
        },
        {
            "id": "cad_print",
            "slug": "cad-print",
            "title": "CAD & 3D printing",
            "kind": "stack",
            "queries": [
                "OrcaSlicer Linux CLI headless slice",
                "Moonraker API upload start print",
                "Klipper printer status API",
                "build123d export STL tutorial",
            ],
        },
        {
            "id": "intel_geopolitics",
            "slug": "intel-geopolitics",
            "title": "Geopolitics & policy",
            "kind": "intel",
            "queries": [
                f"technology policy regulation news {month}",
                "semiconductor export controls news",
                "AI regulation news this week",
            ],
        },
        {
            "id": "intel_security",
            "slug": "intel-security",
            "title": "Security & privacy",
            "kind": "intel",
            "queries": [
                "cybersecurity news this week",
                "Linux security CVE highlights",
                "privacy tech news",
            ],
        },
        {
            "id": "intel_opensource",
            "slug": "intel-open-source",
            "title": "Open source ecosystem",
            "kind": "intel",
            "queries": [
                "open source project releases this week",
                "GitHub trending developer tools",
                "Linux desktop news",
            ],
        },
        {
            "id": "intel_hardware",
            "slug": "intel-hardware",
            "title": "Hardware & chips",
            "kind": "intel",
            "queries": [
                "GPU AI accelerator news",
                "AMD Intel NVIDIA product news",
                "PC hardware news this week",
            ],
        },
        {
            "id": "personal_flytying",
            "slug": "fly-tying",
            "title": "Fly tying",
            "kind": "personal",
            "queries": [
                "fly tying pattern news",
                "trout fly fishing hatch report",
                "new fly tying materials techniques",
            ],
        },
        {
            "id": "personal_comfyui",
            "slug": "comfyui",
            "title": "ComfyUI & diffusion",
            "kind": "personal",
            "queries": [
                "ComfyUI workflow nodes update",
                "Stable Diffusion model release",
                "AnimateDiff ComfyUI news",
            ],
        },
        {
            "id": "personal_coding_agents",
            "slug": "coding-agents",
            "title": "Coding agents",
            "kind": "personal",
            "queries": [
                "AI coding agent tools news",
                "Cursor IDE agent features",
                "Claude Code developer tools news",
            ],
        },
        {
            "id": "personal_home_auto",
            "slug": "home-automation",
            "title": "Home automation",
            "kind": "personal",
            "queries": [
                "Home Assistant release notes",
                "smart home Matter protocol news",
                "Kasa Tapo smart bulb updates",
            ],
        },
        {
            "id": "personal_local_ai",
            "slug": "local-ai",
            "title": "Local AI stack",
            "kind": "personal",
            "queries": [
                "local LLM inference optimization",
                "Whisper faster-whisper updates",
                "self-hosted AI assistant news",
            ],
        },
    ]


def _categories(*, memory=None) -> list[Category]:
    """Stack + intel + personal categories, plus profile-derived topics when memory is available."""
    if memory is None:
        try:
            from jarvis.modules.memory import create_memory_store

            memory = create_memory_store()
        except Exception:
            memory = None
    return _base_categories() + _profile_research_categories(memory)


def list_research_categories(*, memory=None) -> list[dict[str, str]]:
    return [
        {
            "id": c["id"],
            "slug": c["slug"],
            "title": c["title"],
            "kind": c.get("kind", "stack"),
            "source": c.get("source", "builtin"),
        }
        for c in _categories(memory=memory)
    ]


def research_enabled() -> bool:
    return os.getenv("JARVIS_KNOWLEDGE_RESEARCH_DAILY", "1").lower() not in ("0", "false", "off", "no")


def research_hour() -> int:
    try:
        return int(os.getenv("JARVIS_KNOWLEDGE_RESEARCH_HOUR", "23"))
    except ValueError:
        return 23


def auto_remember() -> bool:
    return os.getenv("JARVIS_KNOWLEDGE_RESEARCH_REMEMBER", "1").lower() not in ("0", "false", "off", "no")


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        return {"days": {}, "last_run_day": ""}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("days", {})
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt knowledge research state: %s", exc)
    return {"days": {}, "last_run_day": ""}


def _save_state(data: dict[str, Any]) -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(STATE_FILE)
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _already_ran(day: str | None = None) -> bool:
    d = day or _today()
    data = _load_state()
    return bool(data.get("days", {}).get(d, {}).get("completed"))


def _category_slugs() -> list[str]:
    return [c["slug"] for c in _categories()]


def _nightly_category_ids(day: str | None = None, *, memory=None) -> list[str]:
    """Stack categories every night; rotate 4 intel + all personal + all profile topics."""
    d = day or _today()
    cats = _categories(memory=memory)
    stack = [c["id"] for c in cats if c.get("kind", "stack") == "stack"]
    intel = [c["id"] for c in cats if c.get("kind") == "intel"]
    personal = [c["id"] for c in cats if c.get("kind") == "personal"]
    profile = [c["id"] for c in cats if c.get("kind") == "profile"]
    if not intel:
        return stack + personal + profile
    day_num = 0
    try:
        day_num = int(d.split("-")[2])
    except (IndexError, ValueError):
        day_num = datetime.now().day
    chunk = 4
    start = (day_num - 1) % max(1, len(intel))
    rotated: list[str] = []
    for i in range(min(chunk, len(intel))):
        rotated.append(intel[(start + i) % len(intel)])
    return stack + rotated + personal + profile


def _all_categories() -> list[Category]:
    return _categories()


def _intel_categories() -> list[Category]:
    return [c for c in _categories() if c.get("kind") == "intel"]


def _categories_for_run(day: str | None = None) -> list[str]:
    return _nightly_category_ids(day)


def _sync_day_state(state: dict[str, Any], day: str, slug: str) -> None:
    """Keep last_run_day and completed aligned with _already_ran() after each category."""
    day_state = state.setdefault("days", {}).setdefault(day, {})
    day_state[slug] = datetime.now(timezone.utc).isoformat()
    ran_slugs = [s for s in _category_slugs() if s in day_state]
    if len(ran_slugs) == len(_category_slugs()):
        day_state["completed"] = True
        day_state["at"] = datetime.now(timezone.utc).isoformat()
        day_state["categories"] = ran_slugs
    state["last_run_day"] = day


def _mark_ran(day: str, results: list[dict[str, Any]]) -> None:
    data = _load_state()
    day_state = data.setdefault("days", {}).setdefault(day, {})
    for r in results:
        slug = r.get("slug")
        if slug and r.get("ok") and not r.get("skipped"):
            day_state[slug] = datetime.now(timezone.utc).isoformat()
    day_state["completed"] = True
    day_state["at"] = datetime.now(timezone.utc).isoformat()
    day_state["categories"] = [r.get("slug") for r in results if r.get("ok") and r.get("slug")]
    data["last_run_day"] = day
    _save_state(data)


def _ollama_context() -> str:
    lines: list[str] = []
    try:
        from jarvis.ollama_health import ollama_version

        ver = ollama_version()
        if ver:
            lines.append(f"Installed Ollama: {'.'.join(str(x) for x in ver)}")
    except Exception:
        pass
    ollama = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    lines.append(f"Ollama host: {ollama}")
    return "\n".join(lines)


def _os_context() -> str:
    try:
        return Path("/etc/os-release").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _read_requirements_names(limit: int = 8) -> list[str]:
    names: list[str] = []
    for rel in ("requirements.txt", "requirements-optional.txt"):
        path = PROJECT_ROOT / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkg = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip()
            if pkg and pkg not in names:
                names.append(pkg)
            if len(names) >= limit:
                return names
    return names


def _dependency_context() -> str:
    lines: list[str] = []
    for rel in ("requirements.txt", "requirements-optional.txt"):
        path = PROJECT_ROOT / rel
        if path.is_file():
            lines.append(f"**{rel}** (project root):\n```\n{path.read_text(encoding='utf-8')[:1800]}\n```")
    try:
        proc = subprocess.run(
            [os.environ.get("PIP", "pip"), "list", "--format=freeze"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            pkgs = proc.stdout.strip().splitlines()[:40]
            lines.append("**Installed (pip freeze, partial):**\n" + "\n".join(pkgs))
    except (OSError, subprocess.TimeoutExpired):
        pass
    lines.append(_ollama_context())
    return "\n\n".join(lines)


def _dependency_queries() -> list[str]:
    year = datetime.now().year
    pkgs = _read_requirements_names(6)
    queries = [f"{pkg} python package latest release {year}" for pkg in pkgs]
    queries.append(f"PyTorch ROCm release notes {year}")
    queries.append("ComfyUI stable update release")
    return queries[:8]


def _collect_results(queries: list[str], *, per_query: int = 4) -> list[dict]:
    from jarvis import web_search
    from jarvis.profiles import web_search_disabled

    if web_search_disabled():
        return []
    seen: set[str] = set()
    merged: list[dict] = []
    for query in queries:
        if not query:
            continue
        try:
            hits = web_search.search(query, limit=per_query)
        except Exception as exc:
            log.debug("Search failed for %r: %s", query, exc)
            continue
        for hit in hits:
            url = (hit.get("url") or "").strip()
            if url:
                if url in seen:
                    continue
                seen.add(url)
            merged.append({**hit, "search_query": query})
        if len(merged) >= 16:
            break
    return merged[:16]


def build_daily_digest(
    title: str,
    results: list[dict],
    *,
    day: str,
    local_context: str = "",
) -> str:
    from jarvis import llm, web_search

    if not results and not local_context:
        return (
            f"## {day}\n\n"
            "### Summary\n\n"
            "No web results found (offline profile or search unavailable).\n"
        )

    context = web_search.format_results_for_llm(results) if results else "(no web hits)"
    system = (
        "You write nightly knowledge digests for a personal AI assistant (ARIA). "
        "Focus on what is NEW or CHANGED since typical daily use. "
        "Use markdown with:\n"
        "### Summary (2-3 sentences)\n"
        "### Key updates (bullet list, include version numbers when known)\n"
        "### Suggested follow-ups (optional bullets — install, read, or test)\n"
        "Use ONLY the snippets and local context. Say when information is uncertain."
    )
    user = (
        f"Category: {title}\nDate: {day}\n\n"
        f"Local context:\n{local_context or '(none)'}\n\n"
        f"Web snippets:\n{context}"
    )
    try:
        body = llm.ask(llm.general_model(), [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]).strip()
    except Exception as exc:
        body = f"### Summary\n\nDigest synthesis failed: {exc}\n\n### Raw snippets\n\n{context[:3000]}"
    if not body.startswith("##"):
        body = f"## {day}\n\n{body}"
    elif not body.startswith(f"## {day}"):
        body = f"## {day}\n\n{body}"
    return body[:6000]


def _parse_front_matter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    try:
        meta = json.loads(parts[1])
    except json.JSONDecodeError:
        meta = {}
    return meta, parts[2].strip()


def append_research_digest(
    slug: str,
    title: str,
    day: str,
    section: str,
    results: list[dict],
) -> dict[str, str]:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    path = RESEARCH_DIR / f"{slugify(slug)}.md"
    meta = {
        "topic": title,
        "slug": slugify(slug),
        "category": slugify(slug),
        "updated": _utc_now(),
        "last_day": day,
        "source_count": len(results),
    }
    front = "---\n" + json.dumps(meta, indent=2) + "\n---\n\n"
    if path.is_file():
        old_meta, old_body = _parse_front_matter(path.read_text(encoding="utf-8"))
        if old_meta:
            meta = {**old_meta, **meta}
        combined = front + section.strip() + "\n\n---\n\n" + old_body
    else:
        combined = front + section.strip() + "\n"
    if len(combined) > 120_000:
        combined = combined[:120_000] + "\n\n… (trimmed older sections)\n"
    path.write_text(combined, encoding="utf-8")
    rel = f"knowledge/research/{path.name}"
    return {"path": str(path), "relative_path": rel, "slug": slugify(slug)}


def get_category(category_id: str, *, memory=None) -> Category | None:
    for cat in _categories(memory=memory):
        if cat["id"] == category_id or cat["slug"] == category_id:
            return cat
    return None


def research_category(
    category_id: str,
    *,
    day: str | None = None,
    memory=None,
    force: bool = False,
) -> dict[str, Any]:
    cat = get_category(category_id, memory=memory)
    if not cat:
        return {"ok": False, "message": f"Unknown research category: {category_id}"}

    d = day or _today()
    slug = cat["slug"]
    state = _load_state()
    day_state = state.setdefault("days", {}).setdefault(d, {})
    if not force and day_state.get(slug):
        return {"ok": True, "slug": slug, "skipped": True, "message": "Already researched today."}

    queries_fn: Callable[[], list[str]] | None = cat.get("queries_fn")
    queries = queries_fn() if queries_fn else list(cat.get("queries") or [])
    local_fn: Callable[[], str] | None = cat.get("local_context")
    local_context = local_fn() if local_fn else ""

    results = _collect_results(queries)
    section = build_daily_digest(cat["title"], results, day=d, local_context=local_context)
    saved = append_research_digest(slug, cat["title"], d, section, results)

    remembered = 0
    if auto_remember() and memory is not None:
        try:
            pts = extract_key_points(section)[:4]
            if pts:
                stored = remember_key_points(memory, cat["title"], pts, slug=slug)
                remembered = len(stored)
        except Exception as exc:
            log.debug("Remember research digest skipped: %s", exc)

    _sync_day_state(state, d, slug)
    _save_state(state)

    return {
        "ok": True,
        "id": cat["id"],
        "slug": slug,
        "title": cat["title"],
        "day": d,
        "result_count": len(results),
        "remembered": remembered,
        "path": saved["path"],
        "message": f"Researched **{cat['title']}** for {d}.",
    }


def run_nightly_research(
    *,
    day: str | None = None,
    memory=None,
    force: bool = False,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    if not research_enabled() and not force:
        return [{"ok": False, "message": "Nightly knowledge research disabled."}]

    d = day or _today()
    if not force and _already_ran(d):
        return [{"ok": True, "skipped": True, "message": f"Already completed research for {d}."}]

    ids = categories or _nightly_category_ids(d, memory=memory)
    results: list[dict[str, Any]] = []
    for cid in ids:
        try:
            results.append(research_category(cid, day=d, memory=memory, force=force))
        except Exception as exc:
            log.warning("Knowledge research failed for %s: %s", cid, exc)
            results.append({"ok": False, "id": cid, "message": str(exc)})

    ok_results = [r for r in results if r.get("ok") and not r.get("skipped")]
    if ok_results or force:
        _mark_ran(d, results)
    return results


def run_scheduled(now: datetime | None = None, *, memory=None) -> list[dict[str, Any]]:
    if not research_enabled():
        return []
    now = now or datetime.now()
    if now.hour != research_hour() or now.minute >= 15:
        return []
    return run_nightly_research(memory=memory)


def run_startup_catchup(*, memory=None) -> list[dict[str, Any]]:
    if not research_enabled():
        return []
    if _already_ran():
        return []
    now = datetime.now()
    if now.hour >= research_hour():
        return run_nightly_research(memory=memory)
    return []


def list_research_briefs() -> list[dict[str, str]]:
    if not RESEARCH_DIR.is_dir():
        return []
    items: list[dict[str, str]] = []
    for path in sorted(RESEARCH_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, _ = _parse_front_matter(path.read_text(encoding="utf-8")[:4000])
        items.append({
            "slug": path.stem,
            "title": meta.get("topic") or path.stem.replace("-", " ").title(),
            "updated": meta.get("updated", ""),
            "last_day": meta.get("last_day", ""),
            "path": str(path),
        })
    return items
