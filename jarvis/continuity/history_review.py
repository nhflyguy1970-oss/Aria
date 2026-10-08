"""Reviewing recovered history before import — genuine conversation or test traffic?

The August backup's importable turns came overwhelmingly from automated
acceptance runs: a coding agent driving ARIA through its API and browser. The
content alone cannot tell those apart from real use — a real person may well
ask how to wipe a disk — so this review decides on *provenance*:

* agent-driven: the user turn was issued verbatim inside a coding agent's tool
  call (curl payloads, browser automation, scripted chat) recorded in that
  agent's session transcript. Test prompts the owner wrote into a test plan
  for the agent count as agent-driven too: the agent typed them into ARIA.
* untraced: the turn appears in no transcript, test file or plan. That is
  necessary but not sufficient for "genuine"; untraced turns are accepted only
  by a recorded human judgment, otherwise they stay uncertain.

The unit of decision is the conversation (branch): an assistant reply belongs
with the user turn it answers. Uncertain records are never imported.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ACCEPTED = "accepted"
REJECTED = "rejected"
UNCERTAIN = "uncertain"


def _key(text: str) -> str:
    return (text or "").strip()[:70]


def trace_in_transcripts(texts: list[str], transcript_dirs: list[Path]) -> dict[str, dict[str, int]]:
    """For each text, count where it occurs in agent session transcripts.

    Roles: ``agent_tool_call`` (the agent issued it) or ``human_plan`` (it is
    in a message the human wrote to the agent). Read-only.
    """
    keys = {_key(t): t for t in texts if len(_key(t)) >= 4}
    found: dict[str, Counter[str]] = {k: Counter() for k in keys}
    for root in transcript_dirs:
        for path in Path(root).rglob("*.jsonl"):
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    hits = [k for k in keys if k in line or json.dumps(k)[1:-1] in line]
                    if not hits:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    parts = (event.get("message") or {}).get("content") or []
                    for part in parts if isinstance(parts, list) else []:
                        if not isinstance(part, dict):
                            continue
                        blob = json.dumps(part)
                        for k in hits:
                            if k not in blob and json.dumps(k)[1:-1] not in blob:
                                continue
                            if part.get("type") == "tool_use":
                                found[k]["agent_tool_call"] += 1
                            elif event.get("role") == "user" and "<user_query>" in blob:
                                found[k]["human_plan"] += 1
    return {k: dict(v) for k, v in found.items()}


def review(
    manifest: dict[str, Any],
    backup_dir: Path | str,
    *,
    transcript_dirs: list[Path],
    judgments: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Classify every importable turn. ``judgments`` are recorded human decisions.

    A judgment is keyed ``"<branch>"`` or ``"<branch>#<position>"`` with
    ``{"decision": accepted|rejected|uncertain, "reason": str,
    "approx_date": str (optional)}``; it applies only to turns the provenance
    trace left untraced or that it names explicitly.
    """
    judgments = judgments or {}
    backup_dir = Path(backup_dir)
    data = json.loads((backup_dir / "chat_branches.json").read_text(encoding="utf-8"))
    branches = data.get("branches") or {}

    # Every user turn in each candidate branch, including ones excluded from
    # import as duplicates — they still tell us who drove the conversation.
    candidate_branches = {e["branch"] for e in manifest["entries"] if e["status"] == "importable"}
    user_turns: dict[tuple[str, int], str] = {}
    for bid in candidate_branches:
        position = 0
        for message in branches[bid].get("messages") or []:
            if message.get("role") not in ("user", "assistant"):
                continue
            if message["role"] == "user":
                user_turns[(bid, position)] = message.get("content") or ""
            position += 1
    traces = trace_in_transcripts(list(user_turns.values()), transcript_dirs)

    def traced(text: str) -> dict[str, int]:
        return traces.get(_key(text), {})

    reviewed: list[dict[str, Any]] = []
    for entry in manifest["entries"]:
        if entry["status"] != "importable":
            continue
        bid, pos = entry["branch"], entry["position"]
        # The user turn this entry is or answers: nearest user turn at/before it.
        answering = max((p for (b, p) in user_turns if b == bid and p <= pos), default=None)
        user_text = user_turns.get((bid, answering), "") if answering is not None else ""
        trace = traced(user_text) if user_text else {}
        judgment = judgments.get(f"{bid}#{pos}") or (
            judgments.get(f"{bid}#{answering}") if answering is not None else None
        )
        if judgment is None and not trace.get("agent_tool_call"):
            judgment = judgments.get(bid)
        if trace.get("agent_tool_call") and not judgment:
            decision = REJECTED
            reason = "user turn was issued by a coding agent's tool call (automated test run)"
            if trace.get("human_plan"):
                reason += "; the prompt comes from a written test plan"
        elif judgment:
            decision = judgment["decision"]
            reason = judgment["reason"]
        elif not user_text:
            decision = UNCERTAIN
            reason = "no user turn in this conversation to establish who drove it"
        else:
            decision = UNCERTAIN
            reason = "untraced and not reviewed"
        reviewed.append(
            {
                **{k: entry[k] for k in ("provenance", "branch", "branch_name", "position",
                                         "role", "chars", "sha256", "preview")},
                "branch_created": entry["branch_created"],
                "answers_user_turn": answering,
                "decision": decision,
                "reason": reason,
                "evidence": trace,
                "approx_date": (judgment or {}).get("approx_date")
                or (entry["branch_created"][:10] if entry["branch_created"] else ""),
            }
        )

    summary = {
        "backup": str(backup_dir),
        "source_manifest_token": manifest.get("token"),
        "turns": len(reviewed),
        "by_decision": dict(Counter(r["decision"] for r in reviewed)),
        "conversations": dict(
            Counter(
                d
                for d in (
                    _branch_decision([r for r in reviewed if r["branch"] == b])
                    for b in {r["branch"] for r in reviewed}
                )
            )
        ),
        "transcripts_searched": [str(p) for p in transcript_dirs],
        "judgments": judgments,
    }
    out = {"summary": summary, "entries": reviewed}
    out["token"] = hashlib.sha256(
        json.dumps([[r["sha256"], r["decision"]] for r in reviewed]).encode()
    ).hexdigest()[:16]
    return out


def _branch_decision(rows: list[dict[str, Any]]) -> str:
    decisions = {r["decision"] for r in rows}
    if decisions == {REJECTED}:
        return "rejected"
    if decisions == {ACCEPTED}:
        return "accepted"
    if decisions == {UNCERTAIN}:
        return "uncertain"
    return "mixed"
