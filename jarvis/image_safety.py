"""Hard limit for every image path: no sexual or nude imagery involving minors.

Applies in standard and uncensored mode alike. Uncensored checkpoints such as
Lustify will render whatever they are asked for, so the refusal happens before
ComfyUI sees the prompt, and every negative prompt steers away from childlike
subjects.
"""
from __future__ import annotations

import re

MINOR_NEGATIVE = "child, children, minor, underage, teen, preteen, loli, shota, childlike body"

_MINOR = re.compile(
    r"\b(child|children|kids?|minors?|under[\s-]?age|teens?|teenage(?:d|rs?)?|pre[\s-]?teens?|"
    r"tweens?|toddlers?|infants?|school\s?(?:girls?|boys?|kids?)|elementary|middle\s?school|"
    r"loli(?:con|s)?|shota(?:con)?|jailbait|pubescent|prepubescent|little\s(?:girls?|boys?)|"
    r"(?:[1-9]|1[0-7])\s*(?:-|\s)?(?:years?|yrs?)(?:\s*|-)?old|(?:[1-9]|1[0-7])\s*(?:yo|y/o|y\.o\.))\b",
    re.IGNORECASE,
)
_SEXUAL = re.compile(
    r"\b(nude|nudity|naked|nsfw|sex|sexual|sexy|explicit|porn\w*|erotic\w*|topless|bottomless|"
    r"undress\w*|lingerie|genital\w*|penis|vagina|pussy|vulva|nipples?|breasts?|boobs?|"
    r"masturbat\w*|orgasm\w*|cum|aroused|seductive|spread\s+legs|rating_explicit|rating_questionable)\b",
    re.IGNORECASE,
)

REFUSAL = "ERROR: I won't create sexual or nude images involving minors."


def refusal_for(*texts: str) -> str | None:
    """REFUSAL when the prompt pairs a minor with nudity or sexual content, else None."""
    text = " ".join(t for t in texts if t)
    if _MINOR.search(text) and _SEXUAL.search(text):
        return REFUSAL
    return None


def with_minor_negative(negative: str) -> str:
    """Append the childlike-subject negatives (idempotent)."""
    negative = (negative or "").strip().rstrip(",")
    if MINOR_NEGATIVE in negative:
        return negative
    return f"{negative}, {MINOR_NEGATIVE}" if negative else MINOR_NEGATIVE


# ---------------------------------------------------------------- uploaded photos
# Uploads and chat attachments may show real people. Nude or sexual edits of them would be
# non-consensual intimate imagery, so they are refused; images ARIA generated stay fully
# editable. Edits made from an uploaded photo inherit its "external" mark.

REAL_PHOTO_REFUSAL = (
    "ERROR: I won't make nude or sexual edits of uploaded photos — they may show real people. "
    "Images ARIA generated can still be edited in uncensored mode."
)
REFUSALS = frozenset({REFUSAL, REAL_PHOTO_REFUSAL})

_UNDRESS = re.compile(
    r"\b(undress\w*|unclothed|strip(?:ped|ping)?|naked|nude|topless|bottomless|"
    r"(?:remove|take\s+off|without|no)\s+(?:(?:her|his|their|the|all)\s+)?"
    r"(?:clothes|clothing|outfit|shirt|top|bra|dress|bikini|swimsuit|underwear|panties|pants|skirt|lingerie))\b",
    re.IGNORECASE,
)


def _provenance_file():
    from jarvis.config import DATA_DIR

    return DATA_DIR / "gallery_external_images.json"


def _generated_dir():
    from jarvis.config import DATA_DIR

    return (DATA_DIR / "generated").resolve()


def _external_names() -> set[str]:
    import json

    try:
        return set(json.loads(_provenance_file().read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return set()


def mark_external(path) -> None:
    """Record a gallery image as coming from outside ARIA (an upload, or an edit of one)."""
    import json
    from pathlib import Path

    names = _external_names() | {Path(str(path)).name}
    target = _provenance_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(sorted(names), indent=1), encoding="utf-8")


def is_external_image(path) -> bool:
    """True unless the image is one ARIA generated (in data/generated and never marked external)."""
    from pathlib import Path

    p = Path(str(path)).expanduser()
    try:
        inside = p.resolve().parent == _generated_dir()
    except OSError:
        inside = False
    return not inside or p.name in _external_names()


def edit_refusal_for(image_path, prompt: str) -> str | None:
    """Refusal for an edit request, or None. Minors: always. Uploaded photos: no nude/sexual edits."""
    if refused := refusal_for(prompt):
        return refused
    if is_external_image(image_path) and (_SEXUAL.search(prompt or "") or _UNDRESS.search(prompt or "")):
        return REAL_PHOTO_REFUSAL
    return None


def inherit_provenance(source_path, result: str) -> str:
    """Mark an edit's output external when its source was; returns result unchanged."""
    if result and not str(result).startswith("ERROR:") and is_external_image(source_path):
        mark_external(result)
    return result
