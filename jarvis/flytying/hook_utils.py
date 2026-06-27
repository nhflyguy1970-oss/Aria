"""Hook size parsing and normalization."""

from __future__ import annotations

import re
from typing import Any

_HOOK_SIZE_RE = re.compile(
    r"(?:#|size\s*|sz\.?\s*)?(\d{1,2})\s*(?:-\s*(\d{1,2}))?\s*(?:hook|dry|nymph|streamer|emerg|scud|curved|jig|barbless)?",
    re.I,
)


def parse_hook(hook: Any) -> dict[str, Any]:
    text = str(hook or "").strip()
    if not text:
        return {"raw": "", "size_min": None, "size_max": None, "size_label": ""}
    m = _HOOK_SIZE_RE.search(text)
    if not m:
        nums = re.findall(r"\d{1,2}", text)
        if nums:
            n = int(nums[0])
            return {"raw": text, "size_min": n, "size_max": n, "size_label": f"#{n}"}
        return {"raw": text, "size_min": None, "size_max": None, "size_label": text}
    lo = int(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    lo, hi = min(lo, hi), max(lo, hi)
    label = f"#{lo}" if lo == hi else f"#{lo}-{hi}"
    return {"raw": text, "size_min": lo, "size_max": hi, "size_label": label}


def hook_matches_filter(hook: Any, *, size: int | None = None) -> bool:
    if size is None:
        return True
    parsed = parse_hook(hook)
    lo, hi = parsed.get("size_min"), parsed.get("size_max")
    if lo is None or hi is None:
        return True
    return lo <= size <= hi
