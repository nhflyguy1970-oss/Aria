"""Vision history — searchable analysis ledger (shared censored/uncensored storage)."""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "vision_product" / "history.jsonl"
MAX_ENTRIES = 500

# Certification / smoke OCR probes must never surface in owner history.
_QA_VISION_RE = re.compile(
    r"qa_ocr_sample|"
    r"QA_OCR_|"
    r"ARIAQAOCR|"
    r"QAOCRINVOICE|"
    r"AriaCross\d+|"
    r"/qa_wf/|"
    r"data/certification|"
    r"\bsample\s+ocr\b|"
    r"\bocr\s+sample\b",
    re.I,
)


def is_qa_history_row(row: dict[str, Any] | None) -> bool:
    """True when a history row is certification/QA probe residue."""
    if not isinstance(row, dict):
        return False
    blob = " ".join(
        str(row.get(k) or "")
        for k in ("path", "thumbnail", "prompt", "analysis", "ocr", "import_target", "source")
    )
    return bool(_QA_VISION_RE.search(blob))


def add_entry(entry: dict[str, Any]) -> dict[str, Any]:
    row = {
        "id": entry.get("id") or uuid.uuid4().hex[:16],
        "ts": entry.get("ts") or time.time(),
        "path": entry.get("path") or "",
        "thumbnail": entry.get("thumbnail") or entry.get("path") or "",
        "prompt": (entry.get("prompt") or "")[:500],
        "analysis": (entry.get("analysis") or "")[:8000],
        "ocr": (entry.get("ocr") or "")[:8000],
        "task": entry.get("task") or "describe",
        "model": entry.get("model") or "",
        "latency_ms": int(entry.get("latency_ms") or 0),
        "confidence": entry.get("confidence"),
        "import_target": entry.get("import_target") or "",
        "source": entry.get("source") or "api",
        "uncensored_origin": bool(entry.get("uncensored_origin")),
        "compare_paths": entry.get("compare_paths") or [],
        "diff_path": entry.get("diff_path") or "",
    }
    if is_qa_history_row(row):
        # Never persist certification probes into the owner ledger.
        return row
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    _trim()
    return row


def _trim() -> None:
    if not HISTORY_FILE.is_file():
        return
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > MAX_ENTRIES:
            HISTORY_FILE.write_text("\n".join(lines[-MAX_ENTRIES:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def purge_qa_history() -> int:
    """Rewrite history.jsonl without QA/certification probe rows. Returns removed count."""
    if not HISTORY_FILE.is_file():
        return 0
    kept: list[str] = []
    removed = 0
    try:
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                kept.append(line)
                continue
            if is_qa_history_row(row):
                removed += 1
                continue
            kept.append(json.dumps(row, ensure_ascii=False))
        if removed:
            HISTORY_FILE.write_text(("\n".join(kept) + ("\n" if kept else "")), encoding="utf-8")
    except OSError:
        return 0
    return removed


def list_history(*, limit: int = 50, q: str = "", include_qa: bool = False) -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    q = (q or "").strip().lower()
    rows: list[dict[str, Any]] = []
    try:
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not include_qa and is_qa_history_row(row):
                continue
            if q:
                blob = " ".join(
                    str(row.get(k) or "")
                    for k in ("prompt", "analysis", "ocr", "path", "task", "model", "import_target")
                ).lower()
                if q not in blob:
                    continue
            rows.append(row)
    except OSError:
        return []
    rows.reverse()
    return rows[: max(1, min(limit, 200))]


def get_entry(entry_id: str) -> dict[str, Any] | None:
    for row in list_history(limit=500):
        if row.get("id") == entry_id:
            return row
    return None


def presentation_for_profile(
    entry: dict[str, Any],
    *,
    censored: bool,
    reveal: bool = False,
) -> dict[str, Any]:
    """
    Censored vs uncensored share storage. Presentation-only redaction.
    Never regenerate or delete original analysis.
    """
    out = dict(entry)
    if not censored or reveal or not entry.get("uncensored_origin"):
        out["redacted"] = False
        return out
    out["analysis"] = "[Restricted — reveal to view analysis]"
    out["ocr"] = "[Restricted — reveal to view OCR]"
    out["prompt"] = out.get("prompt") or "[Restricted]"
    out["redacted"] = True
    out["has_original"] = True
    return out
