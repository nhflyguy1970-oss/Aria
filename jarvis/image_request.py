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
        r"research(?:ing)?|use\s+(?:the\s+)?(?:web|internet|research)|tools?|the\s+(?:web|internet)|internet|online)\b"
        r"|\bno\s+(?:web\s+)?(?:search(?:es)?|citations?|sources|tools?)\b",
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


# Follow-ups to the image just made. "Again but at night" rebuilds the previous description
# with the change; "make the jet red" edits the image itself.
_LEAD = r"^(?:(?:ok(?:ay)?|now|great|nice|cool|good|perfect|thanks|hmm|alright|and|so|yes)[,!.]?\s+)*(?:please\s+|can\s+you\s+|could\s+you\s+|would\s+you\s+)?"
_KIND = r"(?:\s+(?:one|version|take|variation|variant|image|picture|photo|scene|shot|render))?"
_AGAIN = r"\s+(?:again|once\s+more)"
_REGEN = re.compile(
    _LEAD + r"(?:"
    # "make another one", "generate a new version", "do it again" — but "make it brighter" is an edit
    rf"(?:do|make|generate|create|render|draw|give\s+me|show\s+me)\s+(?:(?:an)?other|a\s+new|a\s+different|the\s+same){_KIND}(?:{_AGAIN})?"
    rf"|(?:do|make|generate|create|render|draw)\s+(?:it|that|this|one){_KIND}{_AGAIN}"
    rf"|(?:redo|re-?generate|re-?render|re-?draw|re-?make)(?:\s+(?:it|that|this|the\s+same|one){_KIND})?(?:{_AGAIN})?"
    r"|again|once\s+more|one\s+more(?:\s+(?:time|version|image|picture|one))?"
    r"|another(?:\s+(?:one|version|take|variation|variant|image|picture))?"
    r"|try\s+(?:it\s+|that\s+)?again|re-?roll"
    r"|same\s+(?:scene|image|picture|thing|prompt|idea|shot)(?:\s+again)?"
    r"|this\s+time|(?:a\s+)?new\s+version|(?:a\s+)?variation"
    r")\b[\s,:;.!-]*",
    re.IGNORECASE,
)
_CONNECTOR = re.compile(r"^(?:again|more|but|and|only|just|now|then|except|please|thanks|thank\s+you|"
                        r"(?:of\s+)?(?:those|these|that|this|it)\b|,|;|:|-|\.)\s*", re.IGNORECASE)
_EDIT_FOLLOWUP = re.compile(
    _LEAD + r"(?:add|remove|delete|erase|put|place|replace|swap|change|make|turn|give|move|recolou?r|darken|brighten)\s+\S",
    re.IGNORECASE,
)
# Things that are not part of a picture: "add milk to my list", "remove the file".
_NOT_VISUAL = re.compile(
    r"\b(?:list|reminder|calendar|event|task|todo|to-do|note|alarm|timer|file|folder|directory|song|playlist|"
    r"contact|email|e-mail|meeting|appointment|script|code|function|test|commit|repo|memory|thermostat|"
    r"lights?\s+(?:on|off)|volume|sandwich|coffee|dinner|lunch|breakfast)s?\b",
    re.IGNORECASE,
)
_SCENE_REF = re.compile(r"\b(?:that|the\s+same|this|the\s+previous|the\s+last)\s+(?:scene|image|picture|photo|shot|one|idea)\b", re.I)


def followup_change(text: str) -> tuple[str, str] | None:
    """("regenerate" | "edit", change) for a follow-up to the last image, else None.

    The caller decides whether an image is actually in play."""
    t = (text or "").strip()
    if not t or len(t) > 1200 or _NOT_VISUAL.search(t):
        return None
    if m := _REGEN.match(t):
        if (re.search(r"\b(?:image|picture|photo)\s*$", m.group(0).strip(" ,:;.!-"), re.I)
                and re.match(r"\s*(?:of|showing|depicting|with)\b", t[m.end():], re.I) and not _SCENE_REF.search(t)):
            return None  # "make another image of a dog" names a new subject: a new image
        rest = _SCENE_REF.sub(" ", t[m.end():])
        rest = re.sub(r"^\s*(?:of|showing)\b", " ", rest).strip()
        while (c := _CONNECTOR.match(rest)) and c.end():
            rest = rest[c.end():].strip()
        rest = re.sub(r"[\s,]*\b(?:please|thanks|thank\s+you)\b[\s.!]*$", "", rest, flags=re.I)
        return "regenerate", re.sub(r"\s{2,}", " ", rest).rstrip(" .!?")
    if (m := find_image_request(t)) and _SCENE_REF.search(t):
        # "Create another image of that scene at sunset"
        rest = _SCENE_REF.sub(" ", t[m.end():])
        rest = re.sub(r"^\s*(?:of|showing|with)?\s*", "", rest).strip()
        return "regenerate", re.sub(r"\s{2,}", " ", rest).rstrip(" .!?")
    if _EDIT_FOLLOWUP.match(t) and "?" not in t:
        return "edit", t
    return None


def merge_followup_fallback(base: str, change: str) -> str:
    """Previous description plus the requested change, when no model is available to merge them."""
    base, change = (base or "").strip(), (change or "").strip()
    if not change:
        return base
    return f"{base.rstrip('. ')}. Change from before: {change.rstrip('. ')}."

