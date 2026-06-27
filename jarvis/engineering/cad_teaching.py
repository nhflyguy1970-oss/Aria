"""CAD teaching mode — store parametric patterns and rules."""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p5_flags import cad_teaching_enabled

PATTERNS_FILE = DATA_DIR / "engineering" / "cad_patterns.json"


def _load() -> dict[str, Any]:
    if not PATTERNS_FILE.is_file():
        return {"patterns": []}
    try:
        return json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"patterns": []}


def _save(data: dict[str, Any]) -> None:
    PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PATTERNS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def parse_teach_cad(message: str) -> dict[str, str] | None:
    raw = (message or "").strip()
    m = re.match(
        r"^(?:please\s+)?teach\s+cad\s*(?:(rule|pattern|procedure))\s*:?\s*(.+)$",
        raw,
        re.I | re.S,
    )
    if m:
        return {"kind": m.group(1).lower(), "text": m.group(2).strip()}
    m = re.match(r"^(?:please\s+)?teach\s+cad\s*:?\s*(.+)$", raw, re.I | re.S)
    if m:
        text = m.group(1).strip()
        kind = "rule" if re.search(r"\b(never|always|must|clearance|tolerance)\b", text, re.I) else "pattern"
        return {"kind": kind, "text": text}
    return None


def record_pattern(text: str, *, kind: str = "pattern", source: str = "teach") -> dict[str, Any]:
    if not cad_teaching_enabled():
        return {"ok": False, "error": "CAD teaching disabled"}
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "Empty pattern"}
    data = _load()
    row = {
        "id": uuid.uuid4().hex[:10],
        "kind": (kind or "pattern")[:20],
        "text": text[:2000],
        "source": source,
        "created": time.time(),
    }
    patterns = list(data.get("patterns") or [])
    patterns.append(row)
    data["patterns"] = patterns[-200:]
    _save(data)
    return {"ok": True, "pattern": row}


def list_patterns(*, query: str = "", limit: int = 50) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    rows = list(_load().get("patterns") or [])
    if q:
        rows = [r for r in rows if q in (r.get("text") or "").lower() or q in (r.get("kind") or "")]
    rows.sort(key=lambda r: r.get("created", 0), reverse=True)
    return rows[:limit]


def patterns_context_for_prompt(prompt: str = "", *, limit: int = 6) -> str:
    rows = list_patterns(query=prompt, limit=limit)
    if not rows and prompt:
        rows = list_patterns(limit=limit)
    if not rows:
        return ""
    lines = [f"- [{r.get('kind', 'pattern')}] {r.get('text', '')[:240]}" for r in rows[:limit]]
    return "User-taught CAD patterns (follow when generating):\n" + "\n".join(lines)
