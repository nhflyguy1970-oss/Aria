"""Recognise natural-language image-generation requests and keep their full description.

2026-10-13 incident: one fighter-pilot-and-witches request reached three wrong tools —
a briefing-headline fuzzy match (news research about NH/VT), a stale "display it" →
last-file follow-up (pyproject.toml), and a prompt extractor that kept only the tail of
one line (", not a written description." → a generated mountain lake). This module is
the single place that decides "this is a request to make an image" and what the image
should show.
"""
from __future__ import annotations

import re

_NOUN = r"(?:image|picture|photo|photograph|pic|illustration|artwork|wallpaper|portrait|render(?:ing)?|drawing|painting)s?"
_VERB = r"(?:generate|create|draw|make|paint|render|produce|design)"
# Words between the verb and the noun ("an original, photorealistic cinematic image").
_FILLER = r"(?:[\w'’-]+,?\s+){0,6}"
_REQUEST = re.compile(
    rf"\b{_VERB}\s+(?:me\s+|us\s+)?(?:an?\s+|the\s+|some\s+|another\s+)?{_FILLER}{_NOUN}\b",
    re.IGNORECASE,
)
# "make the previous image brighter" / "make it a portrait" are edits, not new images.
_REFERS_TO_EXISTING = re.compile(
    r"\b(?:previous|last|latest|this|that|these|those|same|current|existing|my|your|it|its|uploaded|attached)\b",
    re.IGNORECASE,
)
_NEGATED_BEFORE = re.compile(r"(?:\bdon'?t|\bdo\s+not|\bno\s+need\s+to|\bwithout|\bnever|\bnot)\s+(?:[\w'’]+\s+){0,2}$", re.I)
_CAPABILITY_QUESTION = re.compile(r"^\s*(?:how|what|why|which|where|when|is|are|does|do|did|can\s+you\s+tell)\b", re.I)


def find_image_request(text: str) -> re.Match | None:
    """The first phrase that asks for a NEW image, or None.

    Skips edits of an existing image, negated asks ("don't create an image") and
    capability questions ("how do you create images?")."""
    if not text:
        return None
    for m in _REQUEST.finditer(text):
        between = m.group(0)
        if _REFERS_TO_EXISTING.search(between.split(None, 1)[1] if " " in between else ""):
            continue
        if _NEGATED_BEFORE.search(text[: m.start()][-40:]):
            continue
        return m
    return None


def is_image_generation_request(text: str) -> bool:
    m = find_image_request(text)
    if not m:
        return False
    lower = text.lower()
    if _CAPABILITY_QUESTION.match(lower) and "?" in text and not re.search(rf"\b{_NOUN}\s+(?:of|showing|depicting)\b", lower):
        return False  # "how do you create images?" asks about the feature
    return True


# Instructions addressed to ARIA, not part of what the picture shows.
_META_PATTERNS = (
    r"\*\*?\s*image\s+generation\s+only\b[^\n]*",
    r"(?:^|(?<=[.!\n]))[^.!\n]*\b(?:do\s+not|don'?t|no)\b[^.!\n]*\b(?:search|web|research|citations?|sources?|browse|look\s+up|tools?)\b[^.!\n]*[.!]?",
    r"(?:^|(?<=[.!\n]))[^.!\n]*\bnot\s+(?:a\s+)?(?:written\s+)?(?:description|text|essay|explanation)\b[^.!\n]*[.!]?",
    r"\b(?:using|with|via|in|through)\s+comfy\s?ui\b",
)


def clean_image_prompt(text: str) -> str:
    """Keep the whole visual description (case, every paragraph); drop markdown and the
    instructions to ARIA itself ("do not search the web", "using ComfyUI", …)."""
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    for pat in _META_PATTERNS:
        t = re.sub(pat, " ", t, flags=re.IGNORECASE)
    t = re.sub(r"(\*\*|__|`+|^#+\s*)", "", t, flags=re.MULTILINE)
    lines = [ln.strip(" \t-•*") for ln in t.split("\n")]
    t = " ".join(ln if re.search(r"[.!?:;]$", ln) else (ln + "." if ln else "") for ln in lines)
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    t = re.sub(r"([.!?])(?:\s*[.,;:!?])+", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" .,;:")
    return t


def negates_web_search(text: str) -> bool:
    """"Do not search the web" — an instruction NOT to use web tools."""
    return bool(re.search(
        r"\b(?:do\s+not|don'?t|never|no|without)\s+(?:\w+\s+){0,2}(?:search(?:ing)?|browse|browsing|look(?:ing)?\s+up|"
        r"research(?:ing)?|use\s+(?:the\s+)?(?:web|internet|research))\b"
        r"|\bno\s+(?:web\s+)?(?:search(?:es)?|citations?|sources)\b",
        text or "",
        re.IGNORECASE,
    ))


# Explicit aspect ratios → SDXL/Flux-friendly sizes (multiples of 64, ~1 MP).
_RATIOS = {
    (1, 1): (1024, 1024), (16, 9): (1344, 768), (9, 16): (768, 1344), (4, 3): (1152, 896),
    (3, 4): (896, 1152), (3, 2): (1216, 832), (2, 3): (832, 1216), (21, 9): (1536, 640),
    (9, 21): (640, 1536), (5, 4): (1088, 896), (4, 5): (896, 1088),
}


def requested_dimensions(text: str) -> tuple[int, int] | None:
    """Width/height for an explicit ratio ("16:9", "9:16 vertical", "square"), else None."""
    lower = (text or "").lower()
    if m := re.search(r"\b(\d{1,2})\s*[:x×]\s*(\d{1,2})\b", lower):
        dims = _RATIOS.get((int(m.group(1)), int(m.group(2))))
        if dims:
            return dims
    if re.search(r"\bwidescreen\b|\bwide\s*screen\b|\bcinemascope\b", lower):
        return _RATIOS[(16, 9)]
    if re.search(r"\bsquare\b", lower) and not re.search(r"\bsquare\s+(?:jaw|feet|foot|meters?|miles?|mile)\b", lower):
        return _RATIOS[(1, 1)]
    return None
