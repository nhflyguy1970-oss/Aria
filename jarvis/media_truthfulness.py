"""Guard against claiming media that was never produced.

ARIA must never say it created an image, meme or video unless a media capability
actually ran and produced the artifact. When intent routing sends a media request
to generic chat, the language model will happily answer "Sure! Here's your meme:"
and invent a placeholder image URL — a confident, entirely fabricated success.

Two checks, both applied at the single result choke point:

1. A response that is **not** an authoritative media outcome may not claim media
   was created, and may not present an image embed or asset link as the result.
2. A response that **is** a media outcome must have its artifact on disk before
   it is reported as a success.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Actions whose handlers genuinely produce media.
MEDIA_ACTIONS = frozenset({
    "generate_image",
    "edit_image",
    "inpaint_image",
    "upscale_image",
    "generate_meme",
    "generate_video",
    "storyboard_video",
})

# Result types a real media capability stamps on its output.
MEDIA_RESULT_TYPES = frozenset({"image_result", "video_result", "media_job"})

# Keys that name a produced artifact.
ARTIFACT_KEYS = ("image_path", "video_path", "output_path", "audio_path")

# "Here's your meme", "I generated the video", "I've upscaled the image", …
_MEDIA_CLAIM = re.compile(
    r"(?:here(?:'|’)?s|here is)\s+(?:your|the|a|an)\s+"
    r"(?:image|images|meme|memes|video|videos|picture|photo|gif|animation|render)\b"
    r"|(?:i(?:'|’)?(?:ve| have)?\s*)?"
    r"(?:created|generated|made|produced|rendered|drew|drawn|upscaled|enlarged|"
    r"edited|retouched|inpainted)\s+"
    r"(?:the|your|a|an|this)?\s*"
    r"(?:image|meme|video|picture|photo|gif|animation)\b",
    re.I,
)

# A markdown image embed or a link to a stand-in image service.
_FABRICATED_ASSET = re.compile(
    r"!\[[^\]]*\]\([^)]*\)"
    r"|https?://\S*(?:placeholder|placehold\.|dummyimage|example\.com|lorempixel|"
    r"picsum\.photos|via\.placeholder)\S*",
    re.I,
)

_HONEST_REPLACEMENT = (
    "I did not actually generate that — the request was answered as conversation "
    "rather than routed to the media tools, so no file was produced. "
    "Ask again with a direct instruction (for example **make a meme about X**, "
    "**generate an image of X**, or **upscale the image**), or use the matching "
    "studio panel, and I will run the real job and show you the result."
)


def _is_authoritative_media(result: dict[str, Any], action: str | None) -> bool:
    """True when this result came from a media capability rather than chat."""
    if action in MEDIA_ACTIONS:
        return True
    if str(result.get("type") or "") in MEDIA_RESULT_TYPES:
        return True
    if str(result.get("result_type") or "") in MEDIA_RESULT_TYPES:
        return True
    # A queued media job is authoritative: the work is genuinely under way.
    if result.get("job_id") and str(result.get("action") or "") in MEDIA_ACTIONS:
        return True
    return False


def _artifact_paths(result: dict[str, Any]) -> list[str]:
    out = []
    for key in ARTIFACT_KEYS:
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            out.append(val.strip())
    return out


def verify_media_claims(result: dict[str, Any], *, action: str | None = None) -> dict[str, Any]:
    """Strip fabricated media claims; refuse to call artifact-less media a success."""
    if not isinstance(result, dict):
        return result

    message = result.get("message")
    if not isinstance(message, str) or not message.strip():
        return result

    if _is_authoritative_media(result, action):
        # Real media path: it may only be reported as done if the file exists.
        if result.get("pending") or result.get("ok") is False:
            return result
        paths = _artifact_paths(result)
        if not paths:
            return result
        missing = [p for p in paths if not Path(p).is_file()]
        if missing:
            result = dict(result)
            result["ok"] = False
            result["artifact_missing"] = missing
            result["message"] = (
                "The media job reported success but its output is not on disk "
                f"({Path(missing[0]).name}). Not showing it as complete — "
                "please run it again."
            )
        return result

    # Not a media capability: any claim of having produced media is false.
    claims_media = bool(_MEDIA_CLAIM.search(message))
    fabricated_asset = bool(_FABRICATED_ASSET.search(message))
    if not (claims_media or fabricated_asset):
        return result

    result = dict(result)
    result["fabricated_media_claim_removed"] = True
    if claims_media:
        result["message"] = _HONEST_REPLACEMENT
    else:
        # Keep the prose, drop the invented asset.
        cleaned = _FABRICATED_ASSET.sub("", message).strip()
        result["message"] = (
            f"{cleaned}\n\n_(An image link was removed: nothing was actually generated.)_"
            if cleaned
            else _HONEST_REPLACEMENT
        )
    return result
