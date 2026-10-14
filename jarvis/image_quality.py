"""Fast or high-quality image generation, chosen from the request itself.

Simple requests ("a cat on a sofa") stay on the configured fast model (Flux Schnell, ~30 s).
Scenes that need exact counts, spatial relations, several distinct subjects or readable text
go to Qwen-Image (``jarvis.qwen_image``), which follows those constraints far more often but
takes minutes. The user can always say "quick"/"draft" or "high quality"/"accurate".

Only Regular mode with the default Flux checkpoint is auto-routed: Uncensored mode keeps
Lustify, and a checkpoint or workflow the user picked in Image Engine is always respected.
"""
from __future__ import annotations

import os
import re

_NUM = r"(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a\s+dozen|\d{1,2})"
_COUNT = re.compile(rf"\b(?:exactly\s+|precisely\s+|only\s+)?{_NUM}\s+(?:[a-z-]+\s+){{0,2}}[a-z]+s\b", re.I)
_EXACT = re.compile(r"\b(?:exactly|precisely|no\s+more\s+than|no\s+fewer\s+than|all\s+" + _NUM + r"|each\s+of\s+the|must\s+(?:be|show|have|appear))\b", re.I)
_RELATION = re.compile(
    r"\b(?:to\s+the\s+(?:left|right)\s+of|on\s+the\s+(?:left|right)(?:\s+side)?|left\s+of|right\s+of|behind|in\s+front\s+of|"
    r"above|below|beneath|underneath|between|next\s+to|beside|on\s+top\s+of|facing|toward(?:s)?|through\s+the|"
    r"around\s+the|in\s+the\s+(?:background|foreground|center|centre|corner)|holding|chasing|riding)\b",
    re.I,
)
_TEXT = re.compile(r"\b(?:that\s+(?:says|reads)|which\s+(?:says|reads)|reading|with\s+the\s+(?:words?|text|title)|"
                   r"(?:sign|label|title|caption|logo|banner|poster)\s+(?:that|with|saying)|lettering|typography)\b"
                   r"|[\"“][^\"”]{2,40}[\"”]", re.I)
_FAST_ASK = re.compile(r"\b(?:quick(?:ly)?\s+(?:image|picture|pic|one|version|draft|sketch|render|preview|mock-?up)|just\s+(?:a\s+)?quick|"
                       r"quickly|rough\s+(?:draft|sketch|version|idea)|(?:a\s+)?draft\s+(?:image|version|render)|"
                       r"fast\s+(?:mode|version|render|draft|one)|low[\s-]?quality)\b", re.I)
_QUALITY_ASK = re.compile(r"\b(?:high[\s-]?quality|best[\s-]?quality|maximum\s+quality|highest\s+quality|accurate(?:ly)?|"
                          r"take\s+your\s+time|detailed\s+and\s+accurate|precise(?:ly)?|hq)\b", re.I)
THRESHOLD = 3


def complexity(prompt: str) -> tuple[int, list[str]]:
    """A score and the reasons behind it."""
    text = prompt or ""
    reasons: list[str] = []
    score = 0
    counts = _COUNT.findall(text)
    if counts:
        score += 2
        reasons.append("object counts")
    if _EXACT.search(text):
        score += 2
        reasons.append("exact constraints")
    relations = len(_RELATION.findall(text))
    if relations:
        score += min(relations, 3)
        reasons.append(f"{relations} spatial relation{'s' if relations > 1 else ''}")
    if _TEXT.search(text):
        score += 2
        reasons.append("text in the image")
    words = len(re.findall(r"[A-Za-z']+", text))
    if words > 45:
        score += 1 if words <= 90 else 2
        reasons.append(f"{words}-word description")
    return score, reasons


def mode() -> str:
    """auto (default) | fast | quality — JARVIS_IMAGE_QUALITY_ROUTING."""
    raw = os.getenv("JARVIS_IMAGE_QUALITY_ROUTING", "auto").strip().lower()
    return raw if raw in ("auto", "fast", "quality") else "auto"


def auto_routing_applies(checkpoint: str | None = None, workflow: str | None = None) -> bool:
    """True when ARIA may pick the model: Regular mode, default Flux choice, nothing pinned."""
    if checkpoint or (workflow or "").strip():
        return False
    try:
        from jarvis.config import is_uncensored

        if is_uncensored():
            return False
    except Exception:  # noqa: BLE001
        return False
    from jarvis.comfyui_settings import effective_workflow_path, load_settings

    if os.getenv("JARVIS_COMFYUI_CKPT", "").strip() or effective_workflow_path():
        return False
    data = load_settings()
    return data.get("checkpoint") == "flux" and not (data.get("checkpoint_file") or "").strip()


def choose(prompt: str, *, checkpoint: str | None = None, workflow: str | None = None) -> dict:
    """{"tier": "fast"|"quality", "reasons": [...], "score": n}."""
    from jarvis import qwen_image

    score, reasons = complexity(prompt)
    out = {"tier": "fast", "score": score, "reasons": reasons}
    if not auto_routing_applies(checkpoint, workflow) or not qwen_image.installed():
        return out
    setting = mode()
    if setting == "fast" or (setting == "auto" and _FAST_ASK.search(prompt or "") and not _QUALITY_ASK.search(prompt or "")):
        out["reasons"] = ["fast requested"] if setting == "auto" else ["fast mode set"]
        return out
    if setting == "quality" or _QUALITY_ASK.search(prompt or ""):
        out.update(tier="quality", reasons=["high quality requested"] + reasons)
        return out
    if score >= THRESHOLD:
        out["tier"] = "quality"
    return out


def queued_hint(params: dict) -> str:
    """The "queued" message's time estimate, matching the model this request will use."""
    from jarvis import qwen_image
    from jarvis.modules.image import normalize_image_prompt

    params = params or {}
    if params.get("enhanced_prompt"):
        return ""
    prompt = " ".join(str(params.get(k) or "") for k in ("base_prompt", "change")).strip() or str(params.get("prompt") or "")
    out = choose(normalize_image_prompt(prompt), checkpoint=params.get("checkpoint"), workflow=params.get("workflow"))
    if out["tier"] != "quality":
        return ""
    why = ", ".join(out["reasons"][:3]) or "a complex scene"
    return f"high-quality model for this scene ({why}): {qwen_image.ETA}"
