"""Response Composer — merge multi-capability results into one assistant reply.

Presentation/orchestration only. Does not own organs, Cap Bus, or routing.
"""

from __future__ import annotations

import re
from typing import Any

_SOURCE_FOOTER = re.compile(
    r"\n*_Source: AI Platform Mission Control \(live\)\._\s*$",
    re.I,
)
_HEADER_LINE = re.compile(r"^#{1,3}\s+.+$", re.M)
_HR = re.compile(r"^\s*-{3,}\s*$", re.M)


def _clean_part(text: str, *, capability: str = "") -> str:
    t = (text or "").strip()
    t = _SOURCE_FOOTER.sub("", t).strip()
    t = _HR.sub("", t)
    # Keep reference document/section titles; strip only for other organs
    if capability != "reference":
        t = _HEADER_LINE.sub("", t).strip()
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def compose_natural(parts: list[dict[str, Any]]) -> str:
    """Merge successful capability messages into one coherent reply.

    Failed capabilities contribute an honest note; they never discard
    successful results.
    """
    successful: list[str] = []
    notes: list[str] = []
    for part in parts:
        cap = str(part.get("capability") or "capability")
        if part.get("ok") and (part.get("message") or "").strip():
            successful.append(_clean_part(str(part["message"]), capability=cap))
        else:
            err = part.get("error") or part.get("message") or "unavailable"
            notes.append(f"{cap.title()} information could not be retrieved ({err}).")

    if not successful and not notes:
        return "I could not assemble an answer from the required capabilities."

    body = "\n\n".join(p for p in successful if p)
    if notes:
        if body:
            body = body.rstrip() + "\n\n" + "\n".join(notes)
        else:
            body = "\n".join(notes)
    return body.strip() + "\n"
