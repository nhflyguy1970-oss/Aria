"""Standard assistant response payloads."""

import re

_MAX_STREAM_DIFF = 48_000
_MAX_STREAM_DIFF_LINES = 180


def ok(message: str, module: str | None = "general", **extra) -> dict:
    payload = {"ok": True, "message": message, **extra}
    if module:
        payload["module"] = module
    return payload


def err(message: str, module: str | None = "general") -> dict:
    payload: dict = {"ok": False, "message": message}
    if module:
        payload["module"] = module
    return payload


def _trim_proposal_message(message: str) -> str:
    """Drop embedded code fences when the UI renders a separate diff block."""
    text = re.sub(r"```[\s\S]*?```", "", message or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def cap_stream_payload(result: dict, *, lite_ui: bool = False) -> dict:
    """Keep SSE payloads small enough for WebKit/pywebview chat UI."""
    payload = dict(result)
    if payload.get("proposal_id") and payload.get("message"):
        payload["message"] = _trim_proposal_message(str(payload["message"]))
    if lite_ui and payload.get("proposal_id"):
        payload.pop("diff", None)
        payload["diff_omitted"] = True
        return payload
    diff = payload.get("diff")
    if isinstance(diff, str) and diff:
        lines = diff.splitlines()
        if len(lines) > _MAX_STREAM_DIFF_LINES:
            payload["diff"] = "\n".join(lines[:_MAX_STREAM_DIFF_LINES])
            payload["diff_truncated"] = True
            payload["diff_total_lines"] = len(lines)
        elif len(diff) > _MAX_STREAM_DIFF:
            payload["diff"] = diff[:_MAX_STREAM_DIFF]
            payload["diff_truncated"] = True
            payload["diff_total_lines"] = len(lines)
    return payload


def stream_done(result: dict, *, lite_ui: bool = False) -> dict:
    payload = cap_stream_payload(dict(result), lite_ui=lite_ui)
    if payload.get("type") and payload["type"] != "done":
        payload["result_type"] = payload["type"]
    payload["type"] = "done"
    return payload
