"""Censored / uncensored presentation rules for Gallery."""

from __future__ import annotations

from typing import Any

from jarvis.gallery_product.metadata import get_meta


def image_was_uncensored(name: str) -> bool:
    meta = get_meta(name)
    return bool(meta.get("uncensored"))


def is_restricted_for_viewer(name: str, *, viewer_uncensored: bool | None = None) -> bool:
    """True when asset was made uncensored but viewer is in standard mode."""
    if viewer_uncensored is None:
        try:
            from jarvis.config import is_uncensored

            viewer_uncensored = is_uncensored()
        except Exception:
            viewer_uncensored = False
    if viewer_uncensored:
        return False
    return image_was_uncensored(name)


def apply_visibility(item: dict[str, Any], *, viewer_uncensored: bool | None = None) -> dict[str, Any]:
    """Mutate/list-safe copy: hide thumbs/captions for restricted assets."""
    out = dict(item)
    name = out.get("name") or ""
    if not is_restricted_for_viewer(name, viewer_uncensored=viewer_uncensored):
        out["restricted"] = False
        return out
    out["restricted"] = True
    out["thumb_blocked"] = True
    # Do not leak captions / vision / prompts in censored view
    for k in (
        "caption",
        "vision_description",
        "prompt",
        "enhanced_prompt",
        "negative_prompt",
        "ocr_text",
        "tags",
    ):
        if k in out:
            out[k] = None
    out["preview_message"] = "Restricted — created in uncensored mode. Reveal requires uncensored profile."
    return out
