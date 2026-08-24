"""Guard against claiming an action that was never performed.

ARIA must never say it created an image, a document, an export, or a calendar
event unless the corresponding capability actually ran. When routing sends such a
request to generic chat, the language model will answer "Sure! Here's your meme:"
or "I've added it to your calendar" and invent the evidence — a confident,
entirely fabricated success with an external side effect the user will act on.

The rule is deliberately narrow, because an over-broad guard is its own kind of
dishonesty: an earlier version replaced a correct answer to "How does video
generation work?" with a did-not-generate notice. Three states must stay distinct:

    asked about a capability  -> explain it
    requested an action       -> perform it
    action did not happen     -> say so

So a claim only counts when the response *delivers* a result in the first person
("I've added your meeting", "here's your PDF"), never when it describes how a
feature works ("the calendar tool can create events"). Model prose is never
evidence; evidence comes from the capability that ran.

Two checks, both at the single result choke point:

1. A response that is **not** an authoritative outcome of a capability family may
   not use that family's delivery phrasing, nor present an artifact link as the
   result.
2. A response that **is** such an outcome must have its artifact on disk before it
   is reported as a success.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------
# Capability families
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Family:
    """One externally consequential capability family."""

    name: str
    actions: frozenset[str]
    result_types: frozenset[str]
    artifact_keys: tuple[str, ...]
    claim: re.Pattern[str]
    honest: str


# Delivery phrasing only: first-person completion, or handing an artifact over.
# "the calendar tool can create events" describes; "I added it to your calendar"
# delivers. Only the second is a claim.
_MEDIA_CLAIM = re.compile(
    r"(?:here(?:'|’)?s|here is)\s+your\s+"
    r"(?:image|images|meme|memes|video|videos|picture|photo|gif|animation|render)\b"
    r"|i(?:'|’)?(?:ve| have)?\s*(?:just\s+)?"
    r"(?:created|generated|made|produced|rendered|drew|drawn|upscaled|enlarged|"
    r"edited|retouched|inpainted)\s+your\s+"
    r"(?:image|meme|video|picture|photo|gif|animation)\b",
    re.I,
)

_DOCUMENT_CLAIM = re.compile(
    r"(?:here(?:'|’)?s|here is)\s+(?:your|the)\s+"
    r"(?:pdf|document|report|letter|memo|docx|word\s+document|file)\b"
    r"|i(?:'|’)?(?:ve| have)?\s*(?:just\s+)?"
    r"(?:created|generated|written|wrote|saved|produced|built|made)\s+"
    r"(?:your|the|a|an)\s+"
    r"(?:pdf|document|report|letter|memo|docx|word\s+document|file)\b"
    r"|your\s+(?:pdf|document|report|file)\s+is\s+(?:ready|done|available|saved)\b",
    re.I,
)

_EXPORT_CLAIM = re.compile(
    r"(?:here(?:'|’)?s|here is)\s+(?:your|the)\s+"
    r"(?:csv|export|spreadsheet|xlsx|zip|archive|backup|json\s+file)\b"
    r"|i(?:'|’)?(?:ve| have)?\s*(?:just\s+)?"
    r"(?:exported|saved|written|wrote|created|generated|produced)\s+"
    r"(?:your|the|a|an|this)\s+"
    r"(?:csv|export|spreadsheet|xlsx|zip|archive|backup|data\s+to)\b"
    r"|your\s+(?:export|csv|spreadsheet|backup|archive)\s+is\s+"
    r"(?:ready|done|available|saved)\b",
    re.I,
)

_CALENDAR_CLAIM = re.compile(
    r"i(?:'|’)?(?:ve| have)?\s*(?:just\s+)?"
    r"(?:added|scheduled|created|booked|put|moved|rescheduled|cancelled|canceled|"
    r"deleted|removed|updated)\s+"
    r"(?:your|the|this|it|that|a|an)?\s*"
    r"(?:[\w\s'’-]{0,40}?)?"
    r"(?:\b(?:to|on|in)\s+your\s+calendar\b|\byour\s+calendar\b"
    r"|\b(?:event|meeting|appointment|reminder|alarm|timer)\b)"
    r"|your\s+(?:event|meeting|appointment)\s+is\s+(?:scheduled|booked|set|on\s+the\s+calendar)\b",
    re.I,
)

FAMILIES: tuple[Family, ...] = (
    Family(
        name="media",
        actions=frozenset({
            "generate_image", "edit_image", "inpaint_image", "upscale_image",
            "generate_meme", "generate_video", "storyboard_video",
        }),
        result_types=frozenset({"image_result", "video_result", "media_job"}),
        artifact_keys=("image_path", "video_path", "output_path", "audio_path"),
        claim=_MEDIA_CLAIM,
        honest=(
            "I did not actually generate that — the request was answered as "
            "conversation rather than routed to the media tools, so no file was "
            "produced. Ask again with a direct instruction (for example **make a "
            "meme about X**, **generate an image of X**, or **upscale the image**), "
            "or use the matching studio panel, and I will run the real job."
        ),
    ),
    Family(
        name="document",
        actions=frozenset({"data_export", "document_export", "journal_export"}),
        result_types=frozenset({"document_result", "export_result"}),
        artifact_keys=("doc_path", "export_path", "file_path", "output_path"),
        claim=_DOCUMENT_CLAIM,
        honest=(
            "I did not actually create that document — the request was answered as "
            "conversation rather than routed to a document capability, so no file "
            "exists. Ask again with a direct instruction (for example **export this "
            "to PDF**) and I will produce the real file."
        ),
    ),
    Family(
        name="export",
        actions=frozenset({"data_export", "health_export", "health_backup"}),
        result_types=frozenset({"export_result"}),
        artifact_keys=("export_path", "file_path", "output_path"),
        claim=_EXPORT_CLAIM,
        honest=(
            "I did not actually export anything — the request was answered as "
            "conversation rather than routed to an export capability, so no file "
            "was written. Ask again with a direct instruction (for example "
            "**export this as CSV**) and I will produce the real export."
        ),
    ),
    Family(
        name="calendar",
        actions=frozenset({
            "planner_add_event", "planner_add_task", "planner_set_alarm",
            "planner_set_timer", "journal_schedule",
        }),
        result_types=frozenset({"planner", "calendar_result"}),
        artifact_keys=(),  # a calendar write leaves a record, not a file
        claim=_CALENDAR_CLAIM,
        honest=(
            "I did not actually put that on your calendar — the request was answered "
            "as conversation rather than routed to the planner, so **nothing was "
            "scheduled**. Ask again with a direct instruction (for example "
            "**schedule X tomorrow at 3pm**) and I will create the real event."
        ),
    ),
)

# A markdown embed or a link to a stand-in asset service.
_FABRICATED_ASSET = re.compile(
    r"!\[[^\]]*\]\([^)]*\)"
    r"|https?://\S*(?:placeholder|placehold\.|dummyimage|example\.com|lorempixel|"
    r"picsum\.photos|via\.placeholder)\S*",
    re.I,
)

# A claim inside a hypothetical or a question is not a claim. "What would happen
# if I added this to my calendar?" must never be treated as a calendar write.
_HYPOTHETICAL = re.compile(
    r"\b(?:would|could|should|might|suppose|imagine|if\s+i|if\s+you|when\s+you|"
    r"whenever|in\s+order\s+to|to\s+do\s+(?:this|that)|for\s+example|e\.g\.)\b",
    re.I,
)


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?\n])\s+", text) if s.strip()]


def _claim_is_asserted(text: str, pattern: re.Pattern[str]) -> bool:
    """True when the claim appears as a plain assertion, not a question or a maybe."""
    for sentence in _sentences(text):
        if not pattern.search(sentence):
            continue
        if sentence.rstrip().endswith("?"):
            continue
        if _HYPOTHETICAL.search(sentence):
            continue
        return True
    return False


def _authoritative_family(result: dict[str, Any], action: str | None) -> Family | None:
    """The family whose capability actually produced this result, if any."""
    rtype = str(result.get("type") or "")
    rrtype = str(result.get("result_type") or "")
    for family in FAMILIES:
        if action in family.actions:
            return family
        if rtype in family.result_types or rrtype in family.result_types:
            return family
    return None


def _artifact_paths(result: dict[str, Any], family: Family) -> list[str]:
    out = []
    for key in family.artifact_keys:
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            out.append(val.strip())
    return out


def verify_capability_claims(
    result: dict[str, Any], *, action: str | None = None
) -> dict[str, Any]:
    """Strip claims no capability backs; refuse to call an artifact-less run a success."""
    if not isinstance(result, dict):
        return result

    message = result.get("message")
    if not isinstance(message, str) or not message.strip():
        return result

    family = _authoritative_family(result, action)
    if family is not None:
        # Real capability path: only report done when the artifact is really there.
        if result.get("pending") or result.get("ok") is False:
            return result
        paths = _artifact_paths(result, family)
        if not paths:
            return result
        missing = [p for p in paths if not Path(p).is_file()]
        if missing:
            result = dict(result)
            result["ok"] = False
            result["artifact_missing"] = missing
            result["message"] = (
                f"The {family.name} operation reported success but its output is not "
                f"on disk ({Path(missing[0]).name}). Not showing it as complete — "
                "please run it again."
            )
        return result

    # No capability produced this. Any delivery claim in it is false.
    for candidate in FAMILIES:
        if _claim_is_asserted(message, candidate.claim):
            result = dict(result)
            result["fabricated_claim_removed"] = candidate.name
            result["fabricated_media_claim_removed"] = True  # back-compat flag
            result["message"] = candidate.honest
            return result

    if _FABRICATED_ASSET.search(message):
        result = dict(result)
        result["fabricated_claim_removed"] = "asset"
        result["fabricated_media_claim_removed"] = True
        cleaned = _FABRICATED_ASSET.sub("", message).strip()
        result["message"] = (
            f"{cleaned}\n\n_(A file link was removed: nothing was actually produced.)_"
            if cleaned
            else FAMILIES[0].honest
        )
    return result


# Back-compat: the guard began life covering media only.
verify_media_claims = verify_capability_claims
