"""Workflow learning — detect and store repeated action sequences."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.workflow_learning")

WORKFLOWS_DIR = DATA_DIR / "workflows"
INDEX_FILE = WORKFLOWS_DIR / "index.json"
WATCH_FILE = WORKFLOWS_DIR / "_watch_state.json"
WORKFLOW_TAG = "workflow-learn"
WORKFLOW_NAMESPACE = "workflows"

IGNORE_ACTIONS = frozenset({
    "chat",
    "greeting",
    "capabilities",
    "models_info",
    "clear",
    "recall",
    "memory_search",
    "teach_recall",
    "journal_learn_recall",
    "observation_recall",
    "correction_recall",
    "document_learn_recall",
    "knowledge_research_list",
    "skill_list",
    "workflow_list",
    "workflow_show",
    "workflow_learn",
    "workflow_scan",
    "morning_briefing",
})

_MIN_REPEATS_DEFAULT = 3
_MAX_SEQ_LEN_DEFAULT = 5
_GAP_SECONDS_DEFAULT = 1800


def min_repeats() -> int:
    try:
        return int(os.getenv("JARVIS_WORKFLOW_MIN_REPEATS", str(_MIN_REPEATS_DEFAULT)))
    except ValueError:
        return _MIN_REPEATS_DEFAULT


def max_seq_len() -> int:
    try:
        return int(os.getenv("JARVIS_WORKFLOW_MAX_STEPS", str(_MAX_SEQ_LEN_DEFAULT)))
    except ValueError:
        return _MAX_SEQ_LEN_DEFAULT


def gap_seconds() -> int:
    try:
        return int(os.getenv("JARVIS_WORKFLOW_GAP_SEC", str(_GAP_SECONDS_DEFAULT)))
    except ValueError:
        return _GAP_SECONDS_DEFAULT


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (text or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:72] or "workflow")


def workflow_enabled() -> bool:
    return os.getenv("JARVIS_WORKFLOW_LEARN", "1").lower() not in ("0", "false", "off", "no")


def auto_watch() -> bool:
    mode = os.getenv("JARVIS_AUTO_WORKFLOW_LEARN", "smart").lower()
    if mode in ("0", "false", "off", "no"):
        return False
    return mode in ("1", "true", "yes", "smart")


def auto_remember() -> bool:
    return os.getenv("JARVIS_AUTO_WORKFLOW_REMEMBER", "").lower() in ("1", "true", "yes")


def _ensure_dir() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> dict[str, Any]:
    if not INDEX_FILE.is_file():
        return {"workflows": {}}
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("workflows", {})
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt workflow index: %s", exc)
    return {"workflows": {}}


def _save_index(data: dict[str, Any]) -> None:
    _ensure_dir()
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(INDEX_FILE)
    INDEX_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _workflow_path(slug: str) -> Path:
    return WORKFLOWS_DIR / f"{slugify(slug)}.json"


def _load_watch() -> dict[str, Any]:
    if not WATCH_FILE.is_file():
        return {"recent": [], "patterns": {}}
    try:
        data = json.loads(WATCH_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("recent", [])
            data.setdefault("patterns", {})
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"recent": [], "patterns": {}}


def _save_watch(data: dict[str, Any]) -> None:
    _ensure_dir()
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(WATCH_FILE)
    WATCH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _normalize_detail(action: str, detail: str) -> str:
    text = (detail or "").strip()
    lower = text.lower()
    if action == "skill_run":
        if m := re.search(r"\brun\s+(.+?)\s+skill", text, re.I):
            return slugify(m.group(1))
        if m := re.search(r"skill[:\s]+([\w-]+)", lower):
            return slugify(m.group(1))
    if action == "coding_run_command":
        if m := re.search(r"\brun command[:\s]+(.+)", text, re.I):
            return m.group(1).strip()[:80]
    if action in ("learn_about", "web_search", "journal_log", "project_journal_log"):
        return text[:80]
    if action in ("generate_cad", "engineering_design", "slice_stl", "start_print"):
        return text[:80]
    if action == "ha_control":
        return text[:80]
    return re.sub(r"\s+", " ", text)[:60]


def action_step(action: str, detail: str = "", *, ok: bool = True) -> dict[str, Any]:
    act = (action or "").strip()
    norm = _normalize_detail(act, detail)
    return {
        "action": act,
        "detail": (detail or "")[:200],
        "detail_norm": norm,
        "ok": bool(ok),
        "key": f"{act}:{norm}" if norm else act,
    }


def _parse_log_rows(limit: int = 300) -> list[dict[str, Any]]:
    from jarvis.action_log import _load

    rows: list[dict[str, Any]] = []
    for row in _load()[-limit:]:
        act = (row.get("action") or row.get("event") or "").strip()
        if not act or act in IGNORE_ACTIONS:
            continue
        if row.get("event") and row.get("event") != "action" and not row.get("action"):
            continue
        if row.get("ok") is False:
            continue
        ts = row.get("time") or ""
        rows.append({
            "time": ts,
            "step": action_step(act, row.get("detail") or "", ok=row.get("ok", True)),
        })
    return rows


def _session_groups(rows: list[dict[str, Any]], *, gap_sec: int | None = None) -> list[list[dict[str, Any]]]:
    gap = gap_sec if gap_sec is not None else gap_seconds()
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    last_ts = 0.0
    for row in rows:
        ts_raw = row.get("time") or ""
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            ts = last_ts
        if current and last_ts and ts - last_ts > gap:
            groups.append(current)
            current = []
        current.append(row)
        if ts:
            last_ts = ts
    if current:
        groups.append(current)
    return groups


def _ngrams(steps: list[dict[str, Any]], n: int) -> list[tuple[str, ...]]:
    keys = [s["step"]["key"] for s in steps]
    out: list[tuple[str, ...]] = []
    for i in range(len(keys) - n + 1):
        out.append(tuple(keys[i : i + n]))
    return out


def _steps_from_keys(keys: tuple[str, ...], template: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_to_step = {s["step"]["key"]: s["step"] for s in template}
    steps: list[dict[str, Any]] = []
    for key in keys:
        st = key_to_step.get(key)
        if st:
            steps.append({
                "action": st["action"],
                "detail": st.get("detail") or "",
                "detail_norm": st.get("detail_norm") or "",
            })
        else:
            act, _, norm = key.partition(":")
            steps.append({"action": act, "detail": norm, "detail_norm": norm})
    return steps


def _workflow_name(steps: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for st in steps[:4]:
        act = (st.get("action") or "").replace("_", " ")
        norm = (st.get("detail_norm") or "").replace("-", " ")
        if norm and norm not in act:
            parts.append(f"{act} {norm}".strip())
        else:
            parts.append(act)
    label = " → ".join(p for p in parts if p)
    return (label[:100] or "Learned workflow").title()


def _slug_for_steps(steps: list[dict[str, Any]]) -> str:
    bits = [slugify((s.get("detail_norm") or s.get("action") or "step")[:24]) for s in steps[:4]]
    return slugify("-then-".join(bits))


def save_workflow(
    steps: list[dict[str, Any]],
    *,
    name: str = "",
    slug: str = "",
    count: int = 1,
    source: str = "learned",
) -> dict[str, Any]:
    if not steps:
        raise ValueError("Workflow needs at least one step.")
    slug = slugify(slug or _slug_for_steps(steps))
    now = _utc_now()
    existing = load_workflow(slug)
    wf = {
        "slug": slug,
        "name": name or (existing or {}).get("name") or _workflow_name(steps),
        "description": f"Learned from {count} repeated run(s).",
        "steps": steps,
        "count": int(count) + int((existing or {}).get("count") or 0) if existing else int(count),
        "source": source,
        "created_at": (existing or {}).get("created_at") or now,
        "updated": now,
        "last_seen": now,
    }
    if existing:
        wf["count"] = max(int(existing.get("count") or 0), int(count)) + 1
    _ensure_dir()
    path = _workflow_path(slug)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(path)
    path.write_text(json.dumps(wf, indent=2), encoding="utf-8")
    index = _load_index()
    index["workflows"][slug] = {
        "name": wf["name"],
        "steps": len(steps),
        "count": wf["count"],
        "updated": now,
    }
    _save_index(index)
    return wf


def load_workflow(slug: str) -> dict[str, Any] | None:
    if not slug or slug in {"index", "_watch_state"}:
        return None
    path = _workflow_path(slug)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    # Index / watch state files are not workflows.
    if "workflows" in data and "slug" not in data and "steps" not in data:
        return None
    if not (data.get("slug") or data.get("name") or data.get("steps")):
        return None
    return data


def delete_workflow(slug: str) -> bool:
    path = _workflow_path(slug)
    if not path.is_file():
        return False
    path.unlink()
    index = _load_index()
    index.get("workflows", {}).pop(slugify(slug), None)
    _save_index(index)
    return True


DEMO_WORKFLOW_SLUG = "demo-skill-check"


def ensure_demo_workflow() -> dict[str, Any] | None:
    """Seed a runnable demo workflow when none exist (manual test 22.2)."""
    existing = load_workflow(DEMO_WORKFLOW_SLUG)
    if existing:
        return existing
    return save_workflow(
        [
            {"action": "skill_list", "detail": "", "detail_norm": ""},
            {"action": "skill_run", "detail": "run install-docker skill", "detail_norm": "install-docker"},
        ],
        name="Demo: List skills → install-docker",
        slug=DEMO_WORKFLOW_SLUG,
        count=1,
        source="demo",
    )


def promote_watch_patterns(*, min_count: int | None = None) -> list[dict[str, Any]]:
    """Persist watch-state patterns that meet the repeat threshold."""
    threshold = min_count if min_count is not None else min(2, min_repeats())
    state = _load_watch()
    promoted: list[dict[str, Any]] = []
    for entry in (state.get("patterns") or {}).values():
        count = int(entry.get("count") or 0)
        steps = entry.get("steps") or []
        if count < threshold or len(steps) < 2:
            continue
        wf = save_workflow(steps, slug=_slug_for_steps(steps), count=count, source="watch_promote")
        promoted.append(wf)
    return promoted


def ensure_workflows_ready() -> dict[str, Any]:
    """Startup hook: demo seed + promote learned patterns."""
    promoted = promote_watch_patterns()
    demo = ensure_demo_workflow()
    items = list_workflows()
    return {"count": len(items), "promoted": len(promoted), "demo": demo.get("slug") if demo else None}


def list_workflows(*, query: str = "") -> list[dict[str, Any]]:
    _ensure_dir()
    items: list[dict[str, Any]] = []
    for path in sorted(WORKFLOWS_DIR.glob("*.json")):
        if path.name.startswith("_") or path.name == "index.json":
            continue
        wf = load_workflow(path.stem)
        if wf and (wf.get("slug") or wf.get("name")):
            items.append(wf)
    q = (query or "").strip().lower()
    if not q:
        return sorted(items, key=lambda w: w.get("count", 0), reverse=True)
    words = {w for w in re.findall(r"[a-z0-9]{2,}", q)}
    scored: list[tuple[float, dict[str, Any]]] = []
    for wf in items:
        hay = f"{wf.get('slug')} {wf.get('name')} {wf.get('description', '')}".lower()
        hits = sum(1 for w in words if w in hay)
        if hits or q in hay:
            scored.append((hits, wf))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [w for _, w in scored]


def resolve_workflow(query: str) -> dict[str, Any] | None:
    q = (query or "").strip()
    if not q:
        return None
    direct = load_workflow(q)
    if direct:
        return direct
    hits = list_workflows(query=q)
    return hits[0] if hits else None


def scan_action_log(*, min_repeats_count: int | None = None, limit: int = 400) -> list[dict[str, Any]]:
    """Find repeated action sequences in action_log and persist workflows."""
    threshold = min_repeats_count if min_repeats_count is not None else min_repeats()
    rows = _parse_log_rows(limit=limit)
    if len(rows) < 2:
        return []

    discovered: list[dict[str, Any]] = []
    counter: Counter[tuple[str, ...]] = Counter()
    templates: dict[tuple[str, ...], list[dict[str, Any]]] = {}

    for group in _session_groups(rows):
        for n in range(2, min(max_seq_len(), len(group)) + 1):
            for gram in _ngrams(group, n):
                counter[gram] += 1
                templates.setdefault(gram, group)

    for gram, count in counter.most_common():
        if count < threshold:
            continue
        steps = _steps_from_keys(gram, templates.get(gram, rows))
        if len(steps) < 2:
            continue
        slug = _slug_for_steps(steps)
        existing = load_workflow(slug)
        wf = save_workflow(steps, slug=slug, count=count, source="action_log_scan")
        discovered.append(wf)
        if existing:
            log.info("Updated workflow %s (count=%s)", slug, wf.get("count"))

    return discovered


def watch_action(action: str, detail: str = "", *, ok: bool = True) -> dict[str, Any] | None:
    """Record one action and learn bigrams/trigrams when repeats hit threshold."""
    if not workflow_enabled() or not auto_watch():
        return None
    act = (action or "").strip()
    if not act or act in IGNORE_ACTIONS or not ok:
        return None

    step = action_step(act, detail, ok=ok)
    state = _load_watch()
    recent: list[dict[str, Any]] = state.get("recent") or []
    recent.append({"time": _utc_now(), "step": step})
    recent = recent[-40:]
    state["recent"] = recent

    patterns: dict[str, Any] = state.setdefault("patterns", {})
    keys = [r["step"]["key"] for r in recent]
    learned: dict[str, Any] | None = None

    for n in range(2, min(max_seq_len(), len(keys)) + 1):
        gram = tuple(keys[-n:])
        pid = "|".join(gram)
        entry = patterns.get(pid) or {"count": 0, "steps": _steps_from_keys(gram, recent)}
        entry["count"] = int(entry.get("count") or 0) + 1
        entry["last_seen"] = _utc_now()
        patterns[pid] = entry
        if entry["count"] >= min_repeats():
            learned = save_workflow(
                entry["steps"],
                slug=_slug_for_steps(entry["steps"]),
                count=entry["count"],
                source="auto_watch",
            )

    state["patterns"] = {
        k: v for k, v in patterns.items()
        if int(v.get("count") or 0) >= 1
    }
    if len(state["patterns"]) > 200:
        top = sorted(
            state["patterns"].items(),
            key=lambda kv: int(kv[1].get("count") or 0),
            reverse=True,
        )[:200]
        state["patterns"] = dict(top)

    _save_watch(state)
    return learned


def remember_workflow(memory, workflow: dict[str, Any]) -> list[str]:
    stored: list[str] = []
    if not memory or not workflow:
        return stored
    name = workflow.get("name") or workflow.get("slug")
    steps_txt = " → ".join(
        f"{s.get('action')}" + (f" ({s.get('detail_norm')})" if s.get("detail_norm") else "")
        for s in workflow.get("steps") or []
    )
    text = f"Workflow **{name}**: {steps_txt}"
    memory.add("fact", text, namespace=WORKFLOW_NAMESPACE, tags=[WORKFLOW_TAG, workflow.get("slug", "")[:40]])
    stored.append(text)
    return stored


def format_workflow_markdown(wf: dict[str, Any]) -> str:
    lines = [
        f"**{wf.get('name')}** (`{wf.get('slug')}`)",
        "",
        wf.get("description") or "_Learned workflow._",
        "",
        f"Seen **{wf.get('count', 1)}** time(s) · source: `{wf.get('source', 'learned')}`",
        "",
        "**Steps**",
    ]
    for i, step in enumerate(wf.get("steps") or [], 1):
        act = step.get("action") or "?"
        norm = step.get("detail_norm") or step.get("detail") or ""
        lines.append(f"{i}. `{act}`" + (f" — {norm}" if norm else ""))
    lines.extend([
        "",
        '_Say **run workflow NAME** to preview, or **save workflow NAME as skill**._',
    ])
    return "\n".join(lines)


def _params_for_step(step: dict[str, Any]) -> dict[str, Any]:
    act = step.get("action") or ""
    norm = step.get("detail_norm") or ""
    detail = step.get("detail") or norm
    if act == "skill_run":
        return {"slug": norm, "confirm": False}
    if act == "coding_run_command":
        return {"command": norm or detail}
    if act in ("learn_about", "web_search"):
        return {"topic": norm, "query": norm}
    if act in ("journal_log", "project_journal_log"):
        return {"text": detail or norm}
    if act == "ha_control":
        return {"target": norm, "action": "toggle"}
    return {"text": detail or norm}


def run_workflow(slug: str, assistant=None, *, dry_run: bool = True) -> dict[str, Any]:
    wf = resolve_workflow(slug)
    if not wf:
        return {"ok": False, "message": f"No workflow matching **{slug}**."}

    results: list[dict[str, Any]] = []
    for i, step in enumerate(wf.get("steps") or [], 1):
        act = step.get("action") or ""
        params = _params_for_step(step)
        if dry_run or not assistant:
            results.append({
                "ok": True,
                "step": i,
                "action": act,
                "params": params,
                "dry_run": True,
            })
            continue
        try:
            from jarvis.handlers.registry import call_action, has_action

            if has_action(act):
                out = call_action(assistant, act, params, step.get("detail") or "")
            elif hasattr(assistant, f"_{act}"):
                out = getattr(assistant, f"_{act}")(params, step.get("detail") or "")
            else:
                out = {"ok": False, "message": f"No handler for {act}"}
            results.append({"ok": out.get("ok", True), "step": i, "action": act, "result": out})
            if not out.get("ok", True):
                break
        except Exception as exc:
            results.append({"ok": False, "step": i, "action": act, "error": str(exc)})
            break

    ok = all(r.get("ok", True) for r in results)
    mode = "Preview" if dry_run else "Run"
    lines = [f"**{mode}:** workflow **{wf['name']}** (`{wf['slug']}`)", ""]
    for r in results:
        if r.get("dry_run"):
            p = r.get("params") or {}
            extra = ", ".join(f"{k}={v!r}" for k, v in p.items() if v)
            lines.append(f"{r['step']}. `{r['action']}`" + (f" ({extra})" if extra else ""))
        elif r.get("error"):
            lines.append(f"{r['step']}. `{r['action']}` — error: {r['error']}")
        else:
            lines.append(f"{r['step']}. `{r['action']}` — OK")
    if dry_run:
        lines.append("\n_Add **confirm** to execute, e.g. **run workflow NAME confirm**._")

    return {
        "ok": ok,
        "slug": wf["slug"],
        "dry_run": dry_run,
        "results": results,
        "message": "\n".join(lines),
    }


def workflow_to_skill(slug: str) -> dict[str, Any]:
    from jarvis.skill_database import save_skill

    wf = resolve_workflow(slug)
    if not wf:
        return {"ok": False, "message": f"Workflow **{slug}** not found."}

    skill_steps: list[dict[str, str]] = []
    for i, step in enumerate(wf.get("steps") or [], 1):
        act = step.get("action") or ""
        norm = step.get("detail_norm") or step.get("detail") or ""
        title = f"{act}" + (f" ({norm})" if norm else "")
        if act == "coding_run_command" and norm:
            skill_steps.append({"type": "command", "title": title, "command": norm})
        elif act == "skill_run" and norm:
            skill_steps.append({
                "type": "note",
                "title": title,
                "text": f"Run skill: **{norm}** (say: run {norm} skill confirm)",
            })
        else:
            skill_steps.append({
                "type": "note",
                "title": title,
                "text": f"ARIA action `{act}`" + (f": {norm}" if norm else ""),
            })

    skill = save_skill(
        wf.get("name") or wf["slug"],
        description=f"Converted from learned workflow `{wf['slug']}` ({wf.get('count', 1)} repeats).",
        steps=skill_steps,
        tags=["workflow", wf["slug"]],
        slug=f"wf-{wf['slug']}"[:80],
    )
    return {"ok": True, "skill": skill, "message": f"Saved skill **{skill['name']}** (`{skill['slug']}`)."}


def workflows_context_for_query(query: str, *, max_chars: int = 900) -> str:
    hits = list_workflows(query=query)[:2]
    if not hits:
        return ""
    parts = ["Learned workflows (repeated action patterns):"]
    for wf in hits:
        parts.append(
            f"- **{wf['name']}** (`{wf['slug']}`, {wf.get('count', 1)}×): "
            + " → ".join(s.get("action", "?") for s in wf.get("steps") or [])
        )
    return "\n".join(parts)[:max_chars]


def is_workflow_recall(message: str) -> bool:
    lower = (message or "").lower()
    return bool(re.search(r"\b(learned workflows|workflow recall|what workflows)\b", lower))


def parse_workflow_run_query(message: str) -> tuple[str, bool]:
    text = (message or "").strip()
    confirm = bool(re.search(r"\b(confirm|execute|for real)\b", text, re.I))
    for pat in (
        r"\brun\s+(?:the\s+)?(.+?)\s+workflow\b",
        r"\brun\s+workflow[:\s]+(.+)",
        r"\bworkflow\s+run[:\s]+(.+)",
    ):
        m = re.search(pat, text, re.I)
        if m:
            q = re.sub(r"\b(confirm|execute|for real)\b", "", m.group(1), flags=re.I).strip()
            return q, confirm
    return "", confirm


def parse_workflow_to_skill_query(message: str) -> str:
    if m := re.search(r"\b(?:save|convert)\s+workflow\s+(.+?)\s+as\s+skill\b", message, re.I):
        return m.group(1).strip()
    if m := re.search(r"\bworkflow\s+to\s+skill[:\s]+(.+)", message, re.I):
        return m.group(1).strip()
    return ""
