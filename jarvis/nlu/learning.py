"""NLU learning from routing corrections — requires repeated confirmation."""

from __future__ import annotations

import json
import time
from difflib import SequenceMatcher
from typing import Any

from jarvis.config import DATA_DIR

_CORRECTIONS = DATA_DIR / "nlu_corrections.jsonl"
_CONFIRMATIONS_REQUIRED = 3


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def record_correction(
    *,
    prompt: str,
    original_intent: str,
    corrected_intent: str,
    context: str = "",
) -> dict[str, Any]:
    item = {
        "ts": time.time(),
        "prompt": prompt[:500],
        "original_intent": original_intent,
        "corrected_intent": corrected_intent,
        "context": (context or "")[:400],
    }
    _CORRECTIONS.parent.mkdir(parents=True, exist_ok=True)
    with _CORRECTIONS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return item


def lookup_learned_intent(prompt: str, *, threshold: float = 0.88) -> str | None:
    if not _CORRECTIONS.is_file():
        return None
    counts: dict[tuple[str, str], int] = {}
    try:
        lines = _CORRECTIONS.read_text(encoding="utf-8").splitlines()[-500:]
    except OSError:
        return None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        stored = str(item.get("prompt") or "")
        if _similar(prompt, stored) >= threshold:
            key = (stored, str(item.get("corrected_intent") or ""))
            counts[key] = counts.get(key, 0) + 1
    if not counts:
        return None
    best_key = max(counts, key=counts.get)
    if counts[best_key] >= _CONFIRMATIONS_REQUIRED:
        return best_key[1]
    return None


def list_corrections(*, limit: int = 50) -> list[dict[str, Any]]:
    if not _CORRECTIONS.is_file():
        return []
    try:
        lines = _CORRECTIONS.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
