"""Classify gallery files — stills vs artifacts."""

from __future__ import annotations

import re
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# Intentional generated stills (default library)
_STILL_RE = re.compile(r"^image_\d{8}_\d{6}", re.I)

# Supporting / intermediate artifacts — hidden from default inventory
_ARTIFACT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("keyframe", re.compile(r"(^|_)(keyframe|kf_|frame_)\d*", re.I)),
    ("storyboard", re.compile(r"storyboard|story_slide|kb_slide", re.I)),
    ("meme_bg", re.compile(r"^meme_bg_|_meme_bg|meme_background", re.I)),
    ("temp", re.compile(r"^(tmp_|temp_|preview_|mask_|inpaint_mask)", re.I)),
    ("upscale", re.compile(r"^jarvis_up\d*x_|^up2x_|^upscaled_", re.I)),
    ("edit", re.compile(r"^jarvis_(edit|inpaint)_", re.I)),
    ("intermediate", re.compile(r"_latent_|_preview\.|_thumb_", re.I)),
]


def classify_name(name: str) -> str:
    """Return inventory kind: still | upscale | edit | keyframe | … | other."""
    base = Path(name or "").name
    stem = Path(base).stem
    if _STILL_RE.match(stem) or _STILL_RE.match(base):
        return "still"
    for kind, pat in _ARTIFACT_PATTERNS:
        if pat.search(base):
            return kind
    # Default: treat unknown as still so user work isn't hidden
    return "still"


def is_intentional_still(name: str, *, include_edits: bool = True) -> bool:
    kind = classify_name(name)
    if kind == "still":
        return True
    if include_edits and kind in ("upscale", "edit"):
        return True
    return False


def artifact_kinds() -> list[str]:
    return [k for k, _ in _ARTIFACT_PATTERNS] + ["other"]
