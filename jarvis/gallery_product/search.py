"""Search over filename, prompts, tags, and optional vision metadata."""

from __future__ import annotations

from typing import Any


def matches_query(row: dict[str, Any], query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    # Restricted rows: only match on name (no caption leak) — name still ok
    haystacks = [
        row.get("name") or "",
        row.get("kind") or "",
    ]
    if not row.get("restricted"):
        haystacks.extend(
            [
                row.get("prompt") or "",
                row.get("caption") or "",
                " ".join(row.get("tags") or []) if isinstance(row.get("tags"), list) else "",
                (row.get("meta") or {}).get("vision_description") or "",
                (row.get("meta") or {}).get("enhanced_prompt") or "",
                (row.get("meta") or {}).get("ocr_text") or "",
                (row.get("meta") or {}).get("project") or "",
            ]
        )
    blob = " ".join(str(h) for h in haystacks).lower()
    tokens = [t for t in q.split() if t]
    return all(t in blob for t in tokens)
