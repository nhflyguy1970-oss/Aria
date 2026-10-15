"""Read an edit instruction as one local object operation, when it is one.

"Remove exactly one helicopter" or "replace the left helicopter with a dragon" touch one kind of
object; the rest of the picture must stay as it is. Whole-image editors cannot do that: on
2026-10-14 FLUX.2 Klein, asked to remove exactly one of three helicopters, removed all three and
redrew every pixel (24.6 dB PSNR outside the target). A local edit locates the object on the
RX 7600, edits only a crop around it and pastes back just the masked area (see
comfyui_local_edit). Anything else — several changes, style or lighting, adding objects — stays a
whole-image edit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_NUMBERS = {"a": 1, "an": 1, "one": 1, "single": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "a pair of": 2, "a couple of": 2}
_NUM = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a\s+pair\s+of|a\s+couple\s+of|single|an?)"
# Words that pick one object among several. Order matters for "small distant" (first wins).
POSITIONS = ("leftmost", "rightmost", "left", "right", "topmost", "top", "upper", "bottom", "lower", "middle",
             "center", "centre", "smallest", "tiniest", "small", "distant", "farthest", "furthest", "background",
             "largest", "biggest", "big", "large", "closest", "nearest", "foreground", "extra")
_ADJ = r"(?:[a-z][a-z'’-]*\s+){0,3}?"
_DET = r"(?:the\s+|that\s+|this\s+|those\s+|these\s+|his\s+|her\s+|their\s+|its\s+|my\s+)"
_LOC = (r"(?P<loc>\s+(?:on|in|at|to)\s+the\s+(?:far\s+)?(?:left|right|top|bottom|middle|center|centre|background|"
        r"foreground)(?:\s+(?:side|edge|corner))?)?")
# What ends the object's name: punctuation, or a clause about it ("the man who is fishing" is a man).
_STOP = (r"(?=\s*(?:[,.;:!?()]|$|\s+(?:so|from|in|on|at|and|but|that|which|who|whose|where|while|to|leaving|"
         r"keeping|without|with|then|behind|near|next|is|are|was|wearing|holding|standing|sitting|flying|"
         r"floating|swimming|walking|running|fishing|riding|carrying|looking|by|under|over|above|below|"
         r"too|also|as|again|please|now|out|entirely|completely)\b))")
_REMOVE = re.compile(
    r"\b(?:remove|delete|erase|eliminate|take\s+out|get\s+rid\s+of|paint\s+out|cut\s+out)\s+"
    rf"(?P<all>all\s+(?:of\s+)?(?:the\s+)?|every\s+|both\s+(?:of\s+)?(?:the\s+)?)?"
    rf"(?:(?:exactly|just|only)\s+)?(?P<num>{_NUM}|the|that|this|those|these|his|her|their|its)?\s*"
    rf"(?:of\s+(?:the|these|those)\s+)?(?P<phrase>{_ADJ}[a-z][a-z-]+){_LOC}{_STOP}"
    # "take that person out", "cut the dog out"
    rf"|\b(?:take|cut|paint|edit)\s+(?P<num2>the|that|this|those|these|a|an|one)\s+(?P<phrase2>{_ADJ}[a-z][a-z-]+)"
    rf"{_LOC.replace('?P<loc>', '?P<loc2>')}\s+out\b",
    re.IGNORECASE,
)
_REPLACE = re.compile(
    rf"\b(?:replace|swap)\s+{_DET}?(?P<phrase>{_ADJ}[a-z][a-z-]+){_LOC}\s+(?:with|for)\s+(?P<repl>[^.;\n]+)"
    rf"|\b(?:change|turn)\s+{_DET}(?P<phrase2>{_ADJ}[a-z][a-z-]+)"
    rf"{_LOC.replace('?P<loc>', '?P<loc2>')}\s+(?:into|to)\s+(?P<repl2>[^.;\n]+)",
    re.IGNORECASE,
)
COLORS = ("red", "orange", "yellow", "green", "blue", "purple", "violet", "pink", "brown", "black", "white", "grey",
          "gray", "silver", "gold", "golden", "beige", "teal", "turquoise", "navy", "maroon", "crimson", "cyan",
          "magenta", "tan", "cream", "bronze", "copper")
_SHADE = r"(?:(?:bright|dark|light|pale|deep|neon|metallic|matte|glossy|shiny|dull|pastel|vivid)\s+)?"
_ATTR = (rf"(?P<attr>{_SHADE}(?:{'|'.join(COLORS)})(?:\s+and\s+{_SHADE}(?:{'|'.join(COLORS)}))?"
         r"|bigger|smaller|larger|taller|shorter|brighter|darker|older|younger|wider|narrower|cleaner|rustier|shinier)")
# A word of an object's name in a colour change: never "to", "on the left" or a shade ("dark" green).
_WORD = (r"(?!(?:to|into|be|on|in|at|the|of|bright|dark|light|pale|deep|neon|metallic|matte|glossy|shiny|dull|"
         r"pastel|vivid)\b)[a-z][a-z'’-]*")
# "make the car red", "paint the boat dark blue", "change the car to red"
_CHANGE = re.compile(
    rf"\b(?:make|paint|colou?r|recolou?r|turn|change|dye)\s+{_DET}(?P<phrase>(?:{_WORD}\s+){{0,3}}?{_WORD})"
    rf"{_LOC}\s+(?:(?:to|into)\s+(?:be\s+)?)?{_ATTR}(?:\s+(?:instead|now|please|too))?\s*(?=$|[,.;:!?]|\s+and\b|\s+but\b)",
    re.IGNORECASE,
)
# "move the boat to the left", "move the car a little to the right"
_MOVE = re.compile(
    rf"\b(?:move|shift|slide|push)\s+{_DET}?(?P<phrase>(?:{_WORD}\s+){{0,3}}?{_WORD}){_LOC}\s+"
    r"(?P<amount>(?:a\s+(?:little|bit|lot)\s+|slightly\s+|far\s+|further\s+)?)"
    r"(?:(?:over\s+)?(?:to\s+(?:the\s+)?)?)(?P<dir>left|right|up|down|higher|lower|upwards|downwards)\b",
    re.IGNORECASE,
)
_TARGET = re.compile(rf"\b(?:so\s+(?:that\s+)?|leaving\s+|until\s+)(?:only\s+|exactly\s+|just\s+)?(?P<n>{_NUM})\s+"
                     r"(?:[a-z-]+\s+){0,2}?(?:remains?|are\s+left|is\s+left|stay|left\b|in\s+the\b|visible)", re.I)
_TARGET2 = re.compile(rf"\bleaving\s+(?:only\s+|exactly\s+|just\s+)?(?P<n>{_NUM})\b", re.I)
_CLAIM = re.compile(rf"\bthere\s+(?:are|is)\s+(?:currently\s+|now\s+|still\s+)?(?P<n>{_NUM})\s+(?P<noun>[a-z-]+)", re.I)
# "only the man" / "just the rod": do not take along what it holds, its shadow or reflection.
_ONLY = re.compile(r"\b(?:only|just)\s+(?:the\s+)?(?:\w+\s+){0,2}?(?:itself|alone)?\b|\b(?:itself|alone|by\s+itself)\b", re.I)
# Other changes in the same instruction make it a whole-image edit. Negated phrases
# ("do not change anything else", "without adding") and keep/preserve clauses are protection, not changes.
_NEGATED = re.compile(r"\b(?:do\s+not|don't|dont|never|without|no\s+need\s+to|nor)\s+(?:\w+\s+){0,1}\w+", re.I)
_OTHER_CHANGE = re.compile(r"\b(?:add|insert|put|place|move|make|turn|recolou?r|colou?r|paint|change|replace|swap|"
                           r"remove|delete|erase|brighten|darken|restyle|convert|fix|correct|enlarge|shrink|rotate)\b",
                           re.I)
_NOT_OBJECTS = {"it", "them", "this", "that", "everything", "anything", "all", "background", "image", "picture",
                "photo", "scene", "composition", "noise", "blur", "watermark", "text", "color", "colour", "lighting",
                "rest", "others", "other", "one", "ones", "sky", "photo", "style", "whole", "entire"}
_DROP = {"the", "that", "this", "those", "these", "his", "her", "their", "its", "my", "a", "an", "one"}


@dataclass
class EditPlan:
    op: str                         # "remove" | "replace" | "change" | "move"
    noun: str                       # singular head noun ("rod"), used for counting
    phrase: str                     # the words that name it ("fishing rod on the left")
    count: int | None = None        # how many to remove; None = "the <noun>" (ask when several)
    remove_all: bool = False
    which: str = ""                 # a position word that picks among several
    target_total: int | None = None  # "so that exactly three remain"
    claimed_total: int | None = None  # "there are four helicopters"
    replacement: str = ""           # replace: the new object; change: the new attribute ("red")
    direction: str = ""             # move: left | right | up | down
    amount: str = ""                # move: "a little" | "" | "far"
    with_attached: bool = True      # remove: also what it holds, its shadow and reflection
    instruction: str = ""

    @property
    def target(self) -> str:
        """What to ask the vision model to find: "fishing rod", "red car" (no position words)."""
        words = [w for w in self.phrase.lower().split() if w not in POSITIONS and w not in _DROP
                 and w not in ("on", "in", "at", "to", "side", "edge", "corner", "far")]
        if words:
            words[-1] = singular(words[-1])
        return " ".join(words[-3:]) or self.noun
def _num(word: str | None) -> int | None:
    if not word:
        return None
    w = re.sub(r"\s+", " ", word.strip().lower())
    return int(w) if w.isdigit() else _NUMBERS.get(w)


def singular(word: str) -> str:
    w = word.lower().strip("-")
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if re.search(r"(?:ches|shes|xes|sses|zes)$", w):
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def _split_phrase(phrase: str, loc: str = "") -> tuple[str, str]:
    words = phrase.lower().split()
    noun = singular(words[-1])
    which = next((p for p in POSITIONS if p in words[:-1] + (loc or "").lower().split()), "")
    return noun, which


def _rest_has_other_change(text: str, m) -> bool:
    rest = text[: m.start()] + " " + text[m.end():]
    rest = re.sub(r"\b(?:keep|preserve|leave|maintain)\b[^.;\n]*", " ", rest, flags=re.I)
    return bool(_OTHER_CHANGE.search(_NEGATED.sub(" ", rest)))


def plan(instruction: str) -> EditPlan | None:
    """The single local operation in ``instruction``, or None for a whole-image edit."""
    text = re.sub(r"\s+", " ", instruction or "").strip()
    if not text or len(text) > 1500:
        return None
    found = [("remove", m) for m in _REMOVE.finditer(text)] + [("replace", m) for m in _REPLACE.finditer(text)] \
        + [("change", m) for m in _CHANGE.finditer(text)] + [("move", m) for m in _MOVE.finditer(text)]
    # "change the car to red" matches both replace and change: the colour reading wins.
    spans = {(m.start(), m.end()) for op, m in found if op == "change"}
    found = [(op, m) for op, m in found if not (op == "replace" and any(a <= m.start() < b for a, b in spans))]
    if len(found) != 1:
        return None
    op, m = found[0]
    if _rest_has_other_change(text, m):
        return None  # several changes at once: whole-image edit
    g = m.groupdict()
    raw_phrase = g.get("phrase") or g.get("phrase2") or ""
    loc = g.get("loc") or g.get("loc2") or ""
    noun, which = _split_phrase(raw_phrase, loc)
    if noun in _NOT_OBJECTS or len(noun) < 3:
        return None
    phrase = (raw_phrase + loc).strip()
    if op == "remove":
        num_word = (g.get("num") or g.get("num2") or "").lower()
        count = _num(num_word) if num_word not in _DROP - {"a", "an", "one"} and num_word else None
        plural = raw_phrase.lower().split()[-1] != noun
        m_all = bool(g.get("all")) or (num_word in ("the", "those", "these", "his", "her", "their") and plural)
        target = _TARGET.search(text) or _TARGET2.search(text)
        claim = next((c for c in _CLAIM.finditer(text) if singular(c.group("noun")) == noun), None)
        return EditPlan(op="remove", noun=noun, phrase=phrase, count=count, remove_all=m_all, which=which,
                        target_total=_num(target.group("n")) if target else None,
                        claimed_total=_num(claim.group("n")) if claim else None,
                        with_attached=not _ONLY.search(text), instruction=text)
    if op == "move":
        d = g["dir"].lower()
        d = {"higher": "up", "upwards": "up", "lower": "down", "downwards": "down"}.get(d, d)
        return EditPlan(op="move", noun=noun, phrase=phrase, count=1, which=which, direction=d,
                        amount=(g.get("amount") or "").strip().lower(), instruction=text)
    if op == "change":
        return EditPlan(op="change", noun=noun, phrase=phrase, count=1, which=which,
                        replacement=g["attr"].strip().lower(), instruction=text)
    repl = (g.get("repl") or g.get("repl2") or "").strip().rstrip(" .!")
    if not repl:
        return None
    return EditPlan(op="replace", noun=noun, phrase=phrase, count=1, which=which, replacement=repl, instruction=text)


# Changes that are about the whole picture: a whole-image edit is the right tool, no confirmation.
_GLOBAL = re.compile(
    r"\b(?:style|styled|lighting|lit|night(?:time)?|day(?:time|light)?|sunset|sunrise|dusk|dawn|golden\s+hour|"
    r"seasons?|winter|summer|autumn|spring|snow(?:y|ing)?|rain(?:y|ing)?|fog(?:gy)?|mist(?:y)?|weather|"
    r"colou?r\s+grad(?:e|ing)|palette|tones?|mood|atmosphere|cinematic|painting|painted|watercolou?r|oil\s+paint|"
    r"anime|cartoon|sketch|pencil|black\s+and\s+white|monochrome|sepia|vintage|retro|"
    r"(?:whole|entire)\s+(?:image|picture|photo|scene)|overall|brighter|darker|contrast|saturat\w*|warmer|cooler|"
    r"exposure|sharper|sharpen|bokeh|hdr|sky|background)\b",
    re.IGNORECASE,
)
_ADDING = re.compile(r"\b(?:add|insert|put|place|include|draw\s+in)\b", re.IGNORECASE)
_CONFIRM = re.compile(r"\b(?:full\s+redraw|redraw\s+(?:it|the\s+(?:whole|entire)\s+(?:image|picture))|"
                      r"regenerate\s+the\s+(?:whole|entire)\s+(?:image|picture))\b", re.IGNORECASE)


def whole_image_reason(instruction: str) -> str:
    """'' when a whole-image edit is the natural tool (style, lighting, weather, sky…) or the owner
    already asked for a full redraw; otherwise why a local edit cannot do it, to ask first."""
    text = re.sub(r"\s+", " ", instruction or "").strip()
    if _CONFIRM.search(text):
        return ""
    found = sum(len(list(rx.finditer(text))) for rx in (_REMOVE, _REPLACE, _CHANGE, _MOVE)) \
        + len(_ADDING.findall(text))
    if found > 1 or len(re.findall(r"(?m)^\s*\d+[.)]\s", instruction or "")) > 1:
        return "it asks for several changes at once — a local edit handles one object at a time"
    if _ADDING.search(text):
        return "adding a new object needs a full redraw — a local edit can only change what is already there"
    if _GLOBAL.search(text):
        return ""
    return "I can only edit locally when you remove, replace, recolour or move one object"
