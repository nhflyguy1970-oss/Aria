"""Reusable procedure skills — install, repair, and ops playbooks."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, PROJECT_ROOT

log = logging.getLogger("jarvis.skills")

SKILLS_DIR = DATA_DIR / "skills"
INDEX_FILE = SKILLS_DIR / "index.json"
DEFAULTS_DIR = Path(__file__).resolve().parent / "skill_defaults"
SKILL_TAG = "skill-db"

_STEP_TYPES = frozenset({"command", "check", "note", "script"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (text or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:80] or "skill")


def exec_enabled() -> bool:
    return os.getenv("JARVIS_SKILL_EXEC", "").lower() in ("1", "true", "yes")


def _load_index() -> dict[str, Any]:
    if not INDEX_FILE.is_file():
        return {"skills": {}}
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("skills", {})
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt skills index: %s", exc)
    return {"skills": {}}


def _save_index(data: dict[str, Any]) -> None:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(INDEX_FILE)
    INDEX_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _skill_path(slug: str) -> Path:
    return SKILLS_DIR / f"{slugify(slug)}.json"


def ensure_default_skills() -> list[str]:
    """Copy bundled defaults into data/skills/ when missing."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    if not DEFAULTS_DIR.is_dir():
        return installed
    index = _load_index()
    for path in sorted(DEFAULTS_DIR.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        slug = slugify(raw.get("slug") or path.stem)
        dest = _skill_path(slug)
        if dest.is_file():
            continue
        skill = _normalize_skill(raw, slug=slug)
        _write_skill_file(skill)
        index["skills"][slug] = {
            "name": skill["name"],
            "tags": skill.get("tags") or [],
            "updated": skill.get("updated"),
        }
        installed.append(slug)
    if installed:
        _save_index(index)
    return installed


def _normalize_skill(data: dict[str, Any], *, slug: str = "") -> dict[str, Any]:
    slug = slugify(slug or data.get("slug") or data.get("name") or "skill")
    steps = []
    for i, step in enumerate(data.get("steps") or []):
        if isinstance(step, str):
            steps.append({"type": "command", "title": f"Step {i + 1}", "command": step})
            continue
        if not isinstance(step, dict):
            continue
        stype = (step.get("type") or "command").strip().lower()
        if stype not in _STEP_TYPES:
            stype = "command"
        steps.append({
            "type": stype,
            "title": (step.get("title") or f"Step {i + 1}").strip(),
            "command": (step.get("command") or "").strip(),
            "script": (step.get("script") or "").strip(),
            "text": (step.get("text") or step.get("note") or "").strip(),
        })
    now = _utc_now()
    return {
        "slug": slug,
        "name": (data.get("name") or slug.replace("-", " ").title()).strip(),
        "description": (data.get("description") or "").strip(),
        "tags": [t.strip().lower() for t in (data.get("tags") or []) if str(t).strip()],
        "steps": steps,
        "created_at": data.get("created_at") or now,
        "updated": now,
        "version": int(data.get("version") or 1),
    }


def _write_skill_file(skill: dict[str, Any]) -> None:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    path = _skill_path(skill["slug"])
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(path)
    path.write_text(json.dumps(skill, indent=2), encoding="utf-8")


def save_skill(
    name: str,
    *,
    description: str = "",
    steps: list[Any] | None = None,
    tags: list[str] | None = None,
    slug: str = "",
) -> dict[str, Any]:
    ensure_default_skills()
    skill = _normalize_skill({
        "slug": slug or name,
        "name": name,
        "description": description,
        "steps": steps or [],
        "tags": tags or [],
    })
    existing = load_skill(skill["slug"])
    if existing:
        skill["created_at"] = existing.get("created_at") or skill["created_at"]
        skill["version"] = int(existing.get("version") or 1) + 1
    _write_skill_file(skill)
    index = _load_index()
    index["skills"][skill["slug"]] = {
        "name": skill["name"],
        "tags": skill.get("tags") or [],
        "updated": skill["updated"],
    }
    _save_index(index)
    return skill


def load_skill(slug: str) -> dict[str, Any] | None:
    ensure_default_skills()
    path = _skill_path(slug)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def delete_skill(slug: str) -> bool:
    path = _skill_path(slug)
    if not path.is_file():
        return False
    path.unlink()
    index = _load_index()
    index.get("skills", {}).pop(slugify(slug), None)
    _save_index(index)
    return True


def list_skills(*, query: str = "") -> list[dict[str, Any]]:
    ensure_default_skills()
    items: list[dict[str, Any]] = []
    for path in sorted(SKILLS_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        skill = load_skill(path.stem)
        if skill:
            items.append(skill)
    q = (query or "").strip().lower()
    if not q:
        return items
    words = {w for w in re.findall(r"[a-z0-9]{2,}", q)}
    scored: list[tuple[float, dict[str, Any]]] = []
    for skill in items:
        hay = " ".join([
            skill.get("slug", ""),
            skill.get("name", ""),
            skill.get("description", ""),
            " ".join(skill.get("tags") or []),
        ]).lower()
        hits = sum(1 for w in words if w in hay)
        if hits or q in hay:
            scored.append((hits + (2 if q in hay else 0), skill))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored]


def resolve_skill(query: str) -> dict[str, Any] | None:
    q = (query or "").strip()
    if not q:
        return None
    slug = slugify(q)
    direct = load_skill(slug)
    if direct:
        return direct
    hits = list_skills(query=q)
    if hits:
        return hits[0]
    # "docker repair" -> docker-repair
    alt = slugify(q.replace(" skill", ""))
    return load_skill(alt)


def format_skill_markdown(skill: dict[str, Any]) -> str:
    lines = [
        f"**{skill.get('name')}** (`{skill.get('slug')}`)",
        "",
        (skill.get("description") or "_No description._"),
        "",
        "**Steps**",
    ]
    for i, step in enumerate(skill.get("steps") or [], 1):
        stype = step.get("type", "command")
        title = step.get("title") or f"Step {i}"
        if stype == "note":
            lines.append(f"{i}. _{title}_ — {step.get('text') or step.get('command')}")
        elif stype == "script":
            lines.append(f"{i}. **{title}** — `{step.get('script')}`")
        else:
            cmd = step.get("command") or step.get("script") or ""
            lines.append(f"{i}. **{title}** (`{stype}`) — `{cmd}`")
    tags = skill.get("tags") or []
    if tags:
        lines.extend(["", f"Tags: {', '.join(tags)}"])
    return "\n".join(lines)


def _blocked_command(cmd: str) -> str | None:
    lower = cmd.lower()
    if any(tok in lower for tok in ("rm -rf /", "mkfs", ":(){", "dd if=", "> /dev/sd")):
        return "Blocked destructive pattern."
    if re.search(r"\$\(|`", cmd):
        return "Command substitution not allowed."
    if ";" in cmd and "&&" not in cmd:
        return "Use && instead of ; for chaining."
    return None


def _resolve_script(script: str) -> Path | None:
    rel = script.strip().lstrip("./")
    if not rel.startswith("scripts/"):
        return None
    path = (PROJECT_ROOT / rel).resolve()
    try:
        path.relative_to((PROJECT_ROOT / "scripts").resolve())
    except ValueError:
        return None
    return path if path.is_file() else None


def run_skill_step(
    step: dict[str, Any],
    *,
    dry_run: bool = True,
    timeout: int = 300,
) -> dict[str, Any]:
    stype = (step.get("type") or "command").lower()
    title = step.get("title") or "Step"

    if stype == "note":
        return {"ok": True, "type": "note", "title": title, "output": step.get("text") or ""}

    if stype == "script":
        script = step.get("script") or ""
        path = _resolve_script(script)
        if not path:
            return {"ok": False, "type": "script", "title": title, "error": f"Script not allowed or missing: {script}"}
        if dry_run:
            return {"ok": True, "type": "script", "title": title, "dry_run": True, "command": str(path)}
        try:
            proc = subprocess.run(
                ["bash", str(path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(PROJECT_ROOT),
            )
            out = ((proc.stdout or "") + (proc.stderr or "")).strip()[:4000]
            return {
                "ok": proc.returncode == 0,
                "type": "script",
                "title": title,
                "command": str(path),
                "exit_code": proc.returncode,
                "output": out,
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"ok": False, "type": "script", "title": title, "error": str(exc)}

    cmd = (step.get("command") or "").strip()
    if not cmd:
        return {"ok": True, "type": stype, "title": title, "output": "(empty)"}

    blocked = _blocked_command(cmd)
    if blocked:
        return {"ok": False, "type": stype, "title": title, "error": blocked}

    if dry_run:
        return {"ok": True, "type": stype, "title": title, "dry_run": True, "command": cmd}

    if not exec_enabled():
        return {
            "ok": False,
            "type": stype,
            "title": title,
            "error": "Skill execution disabled. Set JARVIS_SKILL_EXEC=1 in data/jarvis.env.",
        }

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()[:4000]
        ok = proc.returncode == 0 or stype == "check"
        return {
            "ok": ok,
            "type": stype,
            "title": title,
            "command": cmd,
            "exit_code": proc.returncode,
            "output": out,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "type": stype, "title": title, "error": str(exc)}


def run_skill(
    slug: str,
    *,
    dry_run: bool = True,
    stop_on_error: bool = True,
) -> dict[str, Any]:
    skill = resolve_skill(slug)
    if not skill:
        return {"ok": False, "message": f"No skill matching **{slug}**.", "slug": slugify(slug)}

    results: list[dict[str, Any]] = []
    for step in skill.get("steps") or []:
        result = run_skill_step(step, dry_run=dry_run)
        results.append(result)
        if not result.get("ok") and stop_on_error and (step.get("type") or "command") != "check":
            break

    failed = [
        r for r in results
        if not r.get("ok") and r.get("type") not in ("check", "note")
    ]
    ok = len(failed) == 0

    return {
        "ok": ok,
        "slug": skill["slug"],
        "name": skill["name"],
        "dry_run": dry_run,
        "results": results,
        "message": _format_run_summary(skill, results, dry_run=dry_run, ok=ok),
    }


def _format_run_summary(
    skill: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    dry_run: bool,
    ok: bool,
) -> str:
    mode = "Preview" if dry_run else "Run"
    status = "completed" if ok else "stopped with errors"
    lines = [f"**{mode}:** skill **{skill['name']}** (`{skill['slug']}`) — {status}", ""]
    for i, r in enumerate(results, 1):
        title = r.get("title") or f"Step {i}"
        if r.get("type") == "note":
            lines.append(f"{i}. {title}: {r.get('output', '')}")
            continue
        cmd = r.get("command") or ""
        if r.get("dry_run"):
            lines.append(f"{i}. **{title}** — would run: `{cmd}`")
            continue
        if r.get("error"):
            lines.append(f"{i}. **{title}** — error: {r['error']}")
            continue
        code = r.get("exit_code", 0)
        mark = "OK" if r.get("ok") else f"exit {code}"
        lines.append(f"{i}. **{title}** — {mark}")
        if r.get("output"):
            lines.append(f"```\n{r['output'][:1200]}\n```")
    if dry_run:
        lines.extend([
            "",
            "_Dry run only. Say **run docker repair skill confirm** to execute, "
            "or set `JARVIS_SKILL_EXEC=1`._",
        ])
    return "\n".join(lines)


def parse_skill_run_query(message: str) -> tuple[str, bool]:
    """Return (skill query, confirm/exec)."""
    text = (message or "").strip()
    confirm = bool(re.search(r"\b(confirm|execute|for real|actually run)\b", text, re.I))
    for pat in (
        r"\brun\s+(?:the\s+)?(.+?)\s+skill\b",
        r"\brun\s+skill[:\s]+(.+)",
        r"\bskill\s+run[:\s]+(.+)",
    ):
        m = re.search(pat, text, re.I)
        if m:
            q = m.group(1).strip()
            q = re.sub(r"\b(confirm|execute|for real|actually run)\b", "", q, flags=re.I).strip()
            return q, confirm
    return "", confirm


def parse_skill_save_message(message: str) -> dict[str, Any] | None:
    text = (message or "").strip()
    for pat in (
        r"^(?:save|define|create)\s+skill[:\s]+(.+)$",
        r"^skill[:\s]+save[:\s]+(.+)$",
    ):
        m = re.match(pat, text, re.I | re.S)
        if not m:
            continue
        body = m.group(1).strip()
        if " — " in body:
            name, rest = body.split(" — ", 1)
        elif " - " in body and not body.startswith("-"):
            name, rest = body.split(" - ", 1)
        elif ":" in body:
            name, rest = body.split(":", 1)
        else:
            name, rest = body, ""
        name = name.strip()
        rest = rest.strip()
        steps: list[dict[str, str]] = []
        description = ""
        for line in rest.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"^\d+[\).\]]\s+", line):
                step_text = re.sub(r"^\d+[\).\]]\s+", "", line).strip()
                steps.append({"type": "command", "title": f"Step {len(steps) + 1}", "command": step_text})
            elif line.lower().startswith("desc:"):
                description = line[5:].strip()
            elif not description and not steps:
                description = line
            else:
                steps.append({"type": "command", "title": f"Step {len(steps) + 1}", "command": line})
        return {"name": name, "description": description, "steps": steps}
    return None


def skills_context_for_query(query: str, *, max_chars: int = 1200) -> str:
    """Inject matching skill summaries into chat context."""
    hits = list_skills(query=query)[:2]
    if not hits:
        return ""
    parts = ["Matching procedure skills (say **run NAME skill** to preview/run):"]
    for skill in hits:
        parts.append(f"- **{skill['name']}** (`{skill['slug']}`): {skill.get('description', '')[:200]}")
    text = "\n".join(parts)
    return text[:max_chars]
