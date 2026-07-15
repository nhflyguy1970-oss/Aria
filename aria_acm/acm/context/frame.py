"""Context frame — situates meaning (M0-minimal)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ContextFrame:
    tags: tuple[str, ...] = ()
    activity: str = ""
    place: str = ""
    metadata: dict = field(default_factory=dict)

    def matches(self, attribute_contexts: tuple[str, ...] | list[str]) -> float:
        if not attribute_contexts:
            return 0.5  # unscoped — moderate default
        if not self.tags:
            return 0.5
        overlap = set(t.lower() for t in self.tags) & set(c.lower() for c in attribute_contexts)
        if not overlap:
            return 0.15
        return min(1.0, 0.5 + 0.25 * len(overlap))


_HINTS = (
    (re.compile(r"\b(work|office|meeting)\b", re.I), "work"),
    (re.compile(r"\b(home|house)\b", re.I), "home"),
    (re.compile(r"\b(camp(?:ing)?|trail|outdoors)\b", re.I), "camping"),
    (re.compile(r"\b(code|programming|debug|repo)\b", re.I), "programming"),
    (re.compile(r"\b(fly\s*tying|woolly|hackle)\b", re.I), "fly_tying"),
)


def infer_context(text: str, current: ContextFrame | None = None) -> ContextFrame:
    tags: list[str] = list((current.tags if current else ()) or ())
    activity = current.activity if current else ""
    place = current.place if current else ""
    for pat, tag in _HINTS:
        if pat.search(text or ""):
            if tag not in tags:
                tags.append(tag)
            if tag in ("work", "home", "camping"):
                place = place or tag
            else:
                activity = activity or tag
    return ContextFrame(tags=tuple(tags), activity=activity, place=place)
