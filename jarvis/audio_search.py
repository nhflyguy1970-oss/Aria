"""Search indexed audio transcripts."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from jarvis.config import DATA_DIR

INDEX_FILE = DATA_DIR / "audio" / "transcript_index.json"


def _load() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict]) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def index_transcript(path: str, transcript: str, *, title: str = "") -> dict:
    entries = _load()
    path = str(Path(path).resolve())
    entry = {
        "path": path,
        "title": title or Path(path).name,
        "transcript": transcript.strip(),
        "indexed": datetime.now().isoformat(),
    }
    entries = [e for e in entries if e.get("path") != path]
    entries.insert(0, entry)
    _save(entries[:500])
    return entry


def search(query: str, limit: int = 20) -> list[dict]:
    q = query.strip().lower()
    if not q:
        return []
    out: list[dict] = []
    for e in _load():
        text = f"{e.get('title', '')} {e.get('transcript', '')}".lower()
        if q in text or all(w in text for w in re.findall(r"\w+", q)):
            snippet = e.get("transcript", "")[:240]
            out.append({**e, "snippet": snippet})
        if len(out) >= limit:
            break
    return out
