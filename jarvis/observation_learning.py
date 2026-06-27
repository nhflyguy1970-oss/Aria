"""Observation learning — notes from terminal output, logs, screenshots, and cameras."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis import llm
from jarvis.config import DATA_DIR, PROJECT_ROOT

log = logging.getLogger("jarvis.observation_learning")

OBSERVATION_NAMESPACE = "observed"
OBSERVATION_TAG = "observation-learn"
REGISTRY_FILE = DATA_DIR / "observation_learning.json"
OBSERVATIONS_DIR = DATA_DIR / "observations"
SOURCE_TYPES = ("terminal", "log", "screenshot", "camera", "action_log")

_MAX_OBSERVE_CHARS = int(os.getenv("JARVIS_OBSERVE_CHARS", "12000"))
_MAX_NOTES = int(os.getenv("JARVIS_OBSERVE_NOTES", "6"))
_DEFAULT_LOG_LINES = int(os.getenv("JARVIS_OBSERVE_LOG_LINES", "200"))

_OBSERVE_CMD = re.compile(
    r"\b(observe|watch|take notes from|note what you see in)\b",
    re.I,
)
_OBSERVE_LOG = re.compile(
    r"\b(observe|watch|read|tail)\s+(?:the\s+)?(?:jarvis\s+)?(?:server\s+)?logs?\b",
    re.I,
)
_OBSERVE_TERMINAL = re.compile(
    r"\b(observe|watch|note)\s+(?:the\s+)?(?:terminal|command)\s*(?:output)?\b",
    re.I,
)
_OBSERVE_SCREENSHOT = re.compile(
    r"\b(observe|watch|note)\s+(?:this\s+)?(?:screenshot|screen|image|photo)\b",
    re.I,
)
_OBSERVE_CAMERA = re.compile(
    r"\b(observe|watch)\s+(?:the\s+)?(?:camera|webcam|feed)\b",
    re.I,
)
_OBSERVE_LAST_CMD = re.compile(
    r"\b(observe|note)\s+(?:the\s+)?last\s+(?:command|terminal)\b",
    re.I,
)
_OBSERVE_RECALL = re.compile(
    r"\b(what did you observe|what have you observed|observation recall|your observations)\b",
    re.I,
)
_OBSERVE_RECALL_QUERY = re.compile(
    r"(?:what did you observe(?: about)?|what have you observed(?: about)?|"
    r"observation recall(?: about)?|your observations(?: about)?)\s+(.+)$",
    re.I,
)

_OBSERVE_VISION_PROMPT = (
    "You are observing this screen or scene to help an assistant remember what happened. "
    "Describe apps/windows visible, errors or warnings, status indicators, and anything "
    "operationally important. Be factual and concise."
)


@dataclass
class ObserveResult:
    ok: bool
    title: str
    source_type: str
    notes: list[str] = field(default_factory=list)
    message: str = ""
    path: str = ""
    source_id: str = ""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (text or "").lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return (s[:48] or "observation")


def observations_dir() -> Path:
    OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    return OBSERVATIONS_DIR


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_FILE.is_file():
        return {"sources": []}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("sources"), list):
            return data
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Corrupt observation registry: %s", exc)
    return {"sources": []}


def _save_registry(data: dict[str, Any]) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    from jarvis.live_data_guard import assert_live_write_allowed

    assert_live_write_allowed(REGISTRY_FILE)
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _register_source(
    *,
    title: str,
    source_type: str,
    path: str = "",
    notes: int = 0,
) -> str:
    data = _load_registry()
    sid = hashlib.sha256(f"{title}|{source_type}|{path}|{time.time()}".encode()).hexdigest()[:12]
    entry = {
        "id": sid,
        "title": title,
        "type": source_type,
        "path": path,
        "notes": notes,
        "observed_at": _utc_now(),
    }
    sources = [s for s in data.get("sources", []) if s.get("id") != sid]
    sources.insert(0, entry)
    data["sources"] = sources[:300]
    _save_registry(data)
    return sid


def list_observation_sources(*, limit: int = 50) -> list[dict[str, Any]]:
    return list(_load_registry().get("sources", []))[:limit]


def observation_stats() -> dict[str, Any]:
    sources = list_observation_sources(limit=500)
    return {
        "total_sources": len(sources),
        "total_notes": sum(int(s.get("notes") or 0) for s in sources),
        "namespace": OBSERVATION_NAMESPACE,
        "by_type": _count_by_type(sources),
    }


def _count_by_type(sources: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in sources:
        t = (s.get("type") or "unknown").lower()
        counts[t] = counts.get(t, 0) + 1
    return counts


def is_observe_command(message: str) -> bool:
    return bool(_OBSERVE_CMD.search((message or "").strip()))


def is_observe_log(message: str) -> bool:
    return bool(_OBSERVE_LOG.search((message or "").strip()))


def is_observe_terminal(message: str) -> bool:
    return bool(_OBSERVE_TERMINAL.search((message or "").strip()))


def is_observe_screenshot(message: str) -> bool:
    return bool(_OBSERVE_SCREENSHOT.search((message or "").strip()))


def is_observe_camera(message: str) -> bool:
    return bool(_OBSERVE_CAMERA.search((message or "").strip()))


def is_observe_last_command(message: str) -> bool:
    return bool(_OBSERVE_LAST_CMD.search((message or "").strip()))


def is_observation_recall(message: str) -> bool:
    return bool(_OBSERVE_RECALL.search((message or "").strip()))


def parse_observation_recall_query(message: str) -> str:
    m = _OBSERVE_RECALL_QUERY.search((message or "").strip())
    return (m.group(1).strip() if m else "").rstrip("?.!")


def parse_terminal_text(message: str) -> str:
    """Extract pasted terminal output after a colon or fenced block."""
    text = (message or "").strip()
    if m := re.search(r"```(?:bash|sh|text|console)?\n([\s\S]+?)```", text):
        return m.group(1).strip()
    for pat in (
        r"observe (?:terminal|command)(?: output)?:\s*([\s\S]+)$",
        r"terminal output:\s*([\s\S]+)$",
        r"```\n([\s\S]+)$",
    ):
        m = re.match(pat, text, re.I)
        if m:
            return m.group(1).strip()
    return ""


def _tail_file(path: Path, *, max_lines: int = _DEFAULT_LOG_LINES, max_chars: int = _MAX_OBSERVE_CHARS) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Log not found: {path}")
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise ValueError(f"Could not read log: {exc}") from exc
    tail = "\n".join(lines[-max_lines:])
    if len(tail) > max_chars:
        tail = tail[-max_chars:]
    return tail.strip()


def resolve_log_path(message: str = "") -> Path:
    """Pick a log file from the message or defaults."""
    lower = (message or "").lower()
    if m := re.search(r"[`'\"]?([\w./-]+\.log)[`'\"]?", message or "", re.I):
        candidate = Path(m.group(1)).expanduser()
        if candidate.is_file():
            return candidate
        for base in (PROJECT_ROOT, DATA_DIR, DATA_DIR / "logs"):
            resolved = (base / candidate).resolve()
            if resolved.is_file():
                return resolved
    if "serve" in lower:
        p = DATA_DIR / "logs" / "serve.log"
        if p.is_file():
            return p
    from jarvis.logging_config import log_file_path

    primary = log_file_path()
    if primary.is_file():
        return primary
    root_log = PROJECT_ROOT / "jarvis.log"
    if root_log.is_file():
        return root_log
    raise FileNotFoundError("No log file found — set JARVIS_LOG_FILE or check data/logs/")


def _save_observation_text(text: str, *, subdir: str, title: str) -> Path:
    folder = observations_dir() / subdir
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = folder / f"{_slugify(title)}_{stamp}.txt"
    dest.write_text(text, encoding="utf-8")
    return dest


def extract_observation_notes(
    text: str,
    *,
    source_type: str,
    title: str = "",
    max_notes: int | None = None,
) -> list[str]:
    excerpt = (text or "").strip()
    if not excerpt:
        return []
    if len(excerpt) > _MAX_OBSERVE_CHARS:
        excerpt = excerpt[-_MAX_OBSERVE_CHARS:]
    limit = max_notes if max_notes is not None else _MAX_NOTES
    prompt = (
        f"You are extracting durable observation notes from {source_type} data for an AI assistant. "
        f"Write up to {limit} concise notes an operator would want remembered later: errors, "
        "state changes, warnings, successful outcomes, UI status, or environment facts. "
        "Skip noise, timestamps-only lines, and duplicate info. "
        'Return JSON only: {"notes": ["note1", "note2"]}. Empty array if nothing worth keeping.\n\n'
        f"Source: {title or source_type}\n\n{excerpt}"
    )
    try:
        raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        notes = [n.strip() for n in data.get("notes", []) if isinstance(n, str) and len(n.strip()) > 6]
        return notes[:limit]
    except Exception as exc:
        log.warning("Observation extract failed: %s", exc)
        return []


def _store_notes(memory, notes: list[str], *, source_type: str, title: str) -> list[str]:
    stored: list[str] = []
    src_tag = f"observe-source:{_slugify(title)[:28]}"
    for note in notes:
        body = note.strip()
        if not body:
            continue
        prefix = f"[{source_type}] " if not body.lower().startswith(f"[{source_type}]") else ""
        content = f"{prefix}{body}"
        try:
            memory.add(
                "note",
                content,
                tags=[OBSERVATION_TAG, src_tag, f"observe-type:{source_type}"],
                namespace=OBSERVATION_NAMESPACE,
            )
            stored.append(content)
        except ValueError as exc:
            log.debug("Skip observation note: %s", exc)
    return stored


def observe_text(
    memory,
    text: str,
    *,
    source_type: str,
    title: str,
    save_raw: bool = True,
) -> ObserveResult:
    if source_type not in SOURCE_TYPES:
        source_type = "terminal"
    cleaned = (text or "").strip()
    if not cleaned:
        return ObserveResult(False, title, source_type, message="Nothing to observe.")

    saved_path = ""
    if save_raw:
        subdir = {"log": "logs", "screenshot": "screenshots", "camera": "camera"}.get(source_type, source_type)
        saved_path = str(_save_observation_text(cleaned, subdir=subdir, title=title))

    notes = extract_observation_notes(cleaned, source_type=source_type, title=title)
    if not notes:
        return ObserveResult(
            False,
            title,
            source_type,
            message="Nothing substantive to note from that observation.",
            path=saved_path,
        )

    stored = _store_notes(memory, notes, source_type=source_type, title=title)
    sid = _register_source(title=title, source_type=source_type, path=saved_path, notes=len(stored))
    return ObserveResult(
        True,
        title,
        source_type,
        notes=stored,
        message=f"Recorded **{len(stored)}** observation note(s) from **{title}**.",
        path=saved_path,
        source_id=sid,
    )


def observe_log(memory, *, message: str = "", lines: int | None = None) -> ObserveResult:
    path = resolve_log_path(message)
    tail = _tail_file(path, max_lines=lines or _DEFAULT_LOG_LINES)
    title = path.name
    return observe_text(memory, tail, source_type="log", title=title)


def observe_action_log(memory, *, limit: int = 50) -> ObserveResult:
    from jarvis.action_log import list_actions

    rows = list_actions(limit=limit)
    if not rows:
        return ObserveResult(False, "action_log", "action_log", message="Action log is empty.")
    lines = []
    for r in rows:
        ts = r.get("time", "")
        event = r.get("event") or r.get("action") or "event"
        detail = r.get("detail") or r.get("message") or ""
        mod = r.get("module") or ""
        lines.append(f"{ts} [{mod}] {event}: {detail}")
    blob = "\n".join(lines)
    return observe_text(memory, blob, source_type="action_log", title="action_log")


def observe_terminal(memory, text: str, *, title: str = "terminal") -> ObserveResult:
    return observe_text(memory, text, source_type="terminal", title=title)


def observe_screenshot(memory, vision, path: str) -> ObserveResult:
    p = Path(path).expanduser()
    if not p.is_file():
        return ObserveResult(False, p.name, "screenshot", message=f"Image not found: {p}")

    folder = observations_dir() / "screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = folder / f"{p.stem}_{stamp}{p.suffix or '.jpg'}"
    shutil.copy2(p, dest)

    description = vision.analyze(_OBSERVE_VISION_PROMPT, str(dest))
    if description.startswith("ERROR:"):
        return ObserveResult(False, p.stem, "screenshot", message=description, path=str(dest))

    ocr = vision.ocr(str(dest))
    parts = [f"Visual description:\n{description}"]
    if ocr and not ocr.startswith("ERROR:") and ocr.strip().lower() not in ("no text", "no text."):
        parts.append(f"Visible text:\n{ocr}")
    blob = "\n\n".join(parts)
    result = observe_text(memory, blob, source_type="screenshot", title=p.stem, save_raw=False)
    result.path = str(dest)
    if result.ok:
        _register_source(title=p.stem, source_type="screenshot", path=str(dest), notes=len(result.notes))
    return result


def capture_camera_frame(*, device: str | None = None) -> Path:
    """Grab one frame from a V4L2 device or RTSP URL via ffmpeg."""
    dev = (device or os.getenv("JARVIS_CAMERA_DEVICE", "/dev/video0")).strip()
    folder = observations_dir() / "camera"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = folder / f"camera_{stamp}.jpg"

    if dev.startswith("rtsp://") or dev.startswith("http://") or dev.startswith("https://"):
        cmd = [
            "ffmpeg", "-y", "-rtsp_transport", "tcp", "-i", dev,
            "-frames:v", "1", "-q:v", "2", str(dest),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-f", "v4l2", "-i", dev,
            "-frames:v", "1", "-q:v", "2", str(dest),
        ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0 or not dest.is_file():
        err = (proc.stderr or proc.stdout or "").strip()[-400:]
        raise ValueError(err or f"Camera capture failed for {dev}")
    return dest


def observe_camera(memory, vision, *, device: str | None = None) -> ObserveResult:
    try:
        frame = capture_camera_frame(device=device)
    except ValueError as exc:
        return ObserveResult(False, "camera", "camera", message=str(exc))
    result = observe_screenshot(memory, vision, str(frame))
    result.source_type = "camera"
    if result.ok:
        result.title = "camera"
        result.message = result.message.replace("screenshot", "camera")
    return result


def list_observations(memory, *, query: str = "", source_type: str | None = None, limit: int = 25) -> list[dict]:
    entries = memory.list_entries(entry_type="note", namespace=OBSERVATION_NAMESPACE)
    entries = [e for e in entries if OBSERVATION_TAG in (e.get("tags") or [])]
    if source_type and source_type in SOURCE_TYPES:
        tag = f"observe-type:{source_type}"
        entries = [e for e in entries if tag in (e.get("tags") or [])]
    if query:
        q = query.lower()
        entries = [e for e in entries if q in e.get("content", "").lower()]
        if not entries and llm.embed_available():
            hits = memory.search(query, limit=limit, namespace=OBSERVATION_NAMESPACE)
            seen: set[str] = set()
            for h in hits:
                if OBSERVATION_TAG in (h.get("tags") or []) and h["id"] not in seen:
                    entries.append(h)
                    seen.add(h["id"])
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def observation_context_for_chat(memory, message: str, *, limit: int = 4) -> str:
    from jarvis.trust_memory import filter_trusted_content

    q = (message or "").strip()
    if len(q) < 6:
        return ""
    hits = list_observations(memory, query=q, limit=limit)
    if not hits:
        words = [w for w in re.findall(r"[a-z]{4,}", q.lower())]
        stop = {"what", "when", "where", "should", "would", "could", "about", "there", "this", "that", "with", "from"}
        words = [w for w in words if w not in stop][:6]
        if words:
            pool = list_observations(memory, limit=40)
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
    return "Relevant observations (from logs/screens/terminal):\n" + "\n".join(lines)


def format_observations_markdown(entries: list[dict], *, sources: list[dict] | None = None) -> str:
    lines: list[str] = []
    if sources:
        lines.append("**Observation sources**")
        for s in sources[:12]:
            title = s.get("title") or s.get("type", "source")
            typ = s.get("type", "?")
            notes = s.get("notes") or 0
            lines.append(f"- **{title}** ({typ}, {notes} notes)")
        lines.append("")
    if not entries:
        lines.append("_No observation notes yet._")
        return "\n".join(lines)
    lines.append("**Observation notes**")
    for e in entries:
        lines.append(f"• {e.get('content', '')}")
    return "\n".join(lines)
