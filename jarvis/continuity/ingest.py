"""Ingestion — archive → episodes → continuity records → ACM, idempotently.

Order of authority:
  1. The Phase 1 conversation archive is the record of what was said. It is
     append-only and written before context pruning.
  2. This module reads it incrementally (per-file byte offsets) into the
     continuity index. Episode ids are the archive event ids, so re-reading a
     file after a crash or restart cannot create duplicates.
  3. User statements that carry continuity (decisions, ideas, rejections,
     corrections, work) are queued in an outbox and encoded into ACM with
     user-statement provenance and an ``episode:<id>`` tag linking back to the
     source turn. The outbox survives restarts; ACM is checked for the episode
     tag before encoding, so a crash between encode and acknowledgement cannot
     double-encode. Failures stay in the outbox, visible and retryable.

Assistant turns never go to ACM: ACM's ingestion policy (D046) only admits the
user's own statements, and an assistant suggestion is not something the user
said. Suggestions, tool and mission outcomes live here, labelled by actor.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from jarvis.continuity import store
from jarvis.continuity.classify import classify, key_terms

log = logging.getLogger("jarvis.continuity")

# How far back a user's decision or rejection looks for the suggestion it answers.
LINK_WINDOW_S = 6 * 3600
LINK_LOOKBACK = 8

_sync_lock = threading.Lock()
_state: dict[str, Any] = {
    "last_sync": None,
    "last_drain": None,
    "last_error": None,
    "acm_encoded": 0,
    "acm_failed": 0,
    "acm_skipped": 0,
}


def archive_root() -> Path:
    from jarvis.branches import BRANCHES_FILE
    from jarvis.conversation_archive import ARCHIVE_DIRNAME

    return BRANCHES_FILE.parent / ARCHIVE_DIRNAME


# ------------------------------------------------------------------ archive


def _ts(event: dict[str, Any]) -> float:
    from datetime import datetime

    raw = event.get("ts")
    try:
        return datetime.fromisoformat(str(raw)).timestamp()
    except (TypeError, ValueError):
        return time.time()


def sync_archives(root: Path | None = None) -> dict[str, int]:
    """Index any archive lines not yet seen. Safe to call often; idempotent."""
    root = Path(root) if root is not None else archive_root()
    totals = {"files": 0, "events": 0, "episodes": 0, "records": 0}
    if not root.is_dir():
        return totals
    with _sync_lock:
        for path in sorted(root.glob("*.jsonl")):
            totals["files"] += 1
            source = f"archive:{path.name}"
            position = store.get_position(source)
            size = path.stat().st_size
            if size < position:
                # The file shrank: never expected for an append-only archive.
                # Re-read from the start; episode ids keep this idempotent.
                log.warning("Archive %s shrank (%d < %d); re-indexing", path, size, position)
                position = 0
            if size == position:
                continue
            with open(path, "rb") as fh:
                fh.seek(position)
                chunk = fh.read()
            consumed = 0
            for raw in chunk.splitlines(keepends=True):
                if not raw.endswith(b"\n"):
                    break  # a line still being written; pick it up next time
                consumed += len(raw)
                line = raw.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    log.warning("Unreadable archive line in %s at %d", path, position + consumed)
                    continue
                totals["events"] += 1
                added = _ingest_event(event)
                totals["episodes"] += added[0]
                totals["records"] += added[1]
            store.set_position(source, position + consumed)
    _state["last_sync"] = time.time()
    return totals


def _ingest_event(event: dict[str, Any]) -> tuple[int, int]:
    kind = event.get("kind")
    if kind == "retracted":
        _handle_retraction(event)
        return 0, 0
    if kind not in ("message", "seed", "import") or event.get("erased"):
        return 0, 0
    role = str(event.get("role") or "")
    if role not in ("user", "assistant"):
        return 0, 0
    episode_id = str(event.get("id") or "")
    if not episode_id:
        return 0, 0
    content = str(event.get("content") or "")
    branch = str(event.get("branch") or "main")
    ts = _ts(event)
    project = str(event.get("project") or "")
    inserted = store.add_episode(
        episode_id,
        branch=branch,
        ts=ts,
        role=role,
        kind=kind,
        content=content,
        origin=str(event.get("origin") or ""),
        project=project,
    )
    if not inserted:
        return 0, 0
    return 1, derive_records(
        episode_id,
        role=role,
        content=content,
        branch=branch,
        ts=ts,
        project=project,
        episode_kind=kind,
        # Only turns spoken since the archive existed are encoded into ACM.
        # Seeded and imported history is indexed locally; promoting it into
        # ACM is a separate, approved step.
        encode=kind == "message",
    )


def derive_records(
    episode_id: str,
    *,
    role: str,
    content: str,
    branch: str,
    ts: float,
    project: str = "",
    encode: bool = True,
    episode_kind: str = "message",
) -> int:
    """Classify one episode and record what it means for continuity."""
    result = classify(role, content)
    if result.kind is None:
        return 0
    actor = store.USER if role == "user" else store.ASSISTANT
    record_id = store.add_record(
        result.kind,
        content.strip(),
        actor=actor,
        status=result.status,
        ts=ts,
        project=project,
        branch=branch,
        episode_ids=[episode_id],
        source_ref=f"episode:{episode_id}",
        detail={"episode_kind": episode_kind},
    )
    if actor == store.USER:
        _link(record_id, result.kind, result.status, content, branch=branch, ts=ts)
    if result.acm_eligible and encode:
        from jarvis.health_product.context import is_health_chat
        from jarvis.trust_memory import is_test_artifact

        # Health owns medical facts; they are never encoded into ACM.
        if not is_test_artifact(content) and not is_health_chat(content):
            store.enqueue(episode_id, record_kind=result.kind)
    return 1


def _link(record_id: str, kind: str, status: str, content: str, *, branch: str, ts: float) -> None:
    """Connect a user's response to what it responds to.

    A decision or rejection settles the assistant suggestion it overlaps with;
    a correction supersedes the earlier user record it corrects; reporting
    something finished closes the open task it matches. Lexical overlap only —
    when nothing matches clearly, nothing is linked.
    """
    terms = key_terms(content)
    if not terms:
        return
    recent = store.list_records(
        branch=branch, start=ts - LINK_WINDOW_S, end=ts, limit=LINK_LOOKBACK * 4
    )
    recent = [r for r in recent if r["id"] != record_id]

    def best(candidates: list[dict[str, Any]], minimum: int) -> dict[str, Any] | None:
        scored = [(len(terms & key_terms(r["text"])), r) for r in candidates]
        scored = [s for s in scored if s[0] >= minimum]
        return max(scored, key=lambda s: (s[0], s[1]["ts"]))[1] if scored else None

    if kind in (store.DECISION, store.REJECTION):
        suggestions = [
            r for r in recent if r["kind"] == store.SUGGESTION and r["status"] == store.PROPOSED
        ][:LINK_LOOKBACK]
        target = best(suggestions, 1)
        if target is not None:
            outcome = store.ACCEPTED if kind == store.DECISION else store.REJECTED
            store.update_record(
                target["id"],
                status=outcome,
                detail={**target["detail"], "settled_by": record_id},
            )
            mine = store.get_record(record_id) or {}
            store.update_record(
                record_id, detail={**(mine.get("detail") or {}), "responds_to": target["id"]}
            )
    if kind == store.CORRECTION:
        earlier = [
            r
            for r in recent
            if r["actor"] == store.USER
            and r["kind"] in (store.DECISION, store.IDEA, store.TASK, store.CORRECTION)
            and r["status"] in (store.OPEN, store.DONE)
        ][:LINK_LOOKBACK]
        target = best(earlier, 1)
        if target is not None:
            store.update_record(target["id"], status=store.SUPERSEDED, superseded_by=record_id)
    if kind == store.TASK and status == store.DONE:
        open_tasks = [
            r for r in recent if r["kind"] == store.TASK and r["status"] == store.OPEN
        ][:LINK_LOOKBACK]
        target = best(open_tasks, 2)
        if target is not None:
            store.update_record(target["id"], status=store.DONE, superseded_by=record_id)


def _handle_retraction(event: dict[str, Any]) -> None:
    """A withdrawn turn stays in history but is not encoded into ACM."""
    content = str(event.get("content") or "")
    branch = str(event.get("branch") or "main")
    for ep in store.episodes_between(branch=branch, limit=5):
        if ep["role"] == "user" and ep["content"] == content:
            entry = store.outbox_entry(ep["id"])
            if entry and entry["status"] in ("pending", "failed"):
                store.mark_outbox(ep["id"], status="skipped", error="retracted", attempted=False)
            return


# ------------------------------------------------------------------ outcomes


def record_tool_outcome(
    tool_id: str, task: str, *, ok: bool, summary: str = "", run_id: str = ""
) -> str:
    """A managed tool's run, as reported by the tool. Reported, not verified."""
    text = f"[tool:{tool_id}] {'completed' if ok else 'failed'}: {task}".strip()
    if summary:
        text += f"\n{summary}"
    return store.add_record(
        store.OUTCOME,
        text,
        actor=store.TOOL,
        status=store.DONE if ok else store.FAILED,
        source_ref=f"tool:{tool_id}:{run_id}" if run_id else "",
        detail={"tool": tool_id, "run_id": run_id, "reported_ok": ok},
    )


def sync_missions(limit: int = 200) -> dict[str, int]:
    """Mirror mission state: open missions are open work, finished ones outcomes."""
    from jarvis.missions import store as mission_store

    counts = {"open": 0, "outcomes": 0}
    for mission in mission_store.list_missions(limit=limit):
        mid = mission["id"]
        state = mission["state"]
        steps = f"{mission.get('completed_steps', 0)}/{mission.get('total_steps', 0)} steps"
        open_ref = f"mission:{mid}:open"
        if state in mission_store.TERMINAL_STATES:
            existing_open = store.record_by_source(open_ref)
            done = state == mission_store.COMPLETED
            rid = store.add_record(
                store.OUTCOME,
                f"Mission {state}: {mission['objective']} ({steps})"
                + (f" — {mission['error']}" if mission.get("error") else ""),
                actor=store.MISSION,
                status=store.DONE if done else store.FAILED,
                ts=float(mission.get("updated_at") or time.time()),
                source_ref=f"mission:{mid}",
                detail={"mission_id": mid, "state": state, "kind": mission.get("kind")},
            )
            if existing_open and existing_open["status"] == store.OPEN:
                store.update_record(
                    existing_open["id"],
                    status=store.DONE if done else store.FAILED,
                    superseded_by=rid,
                )
            counts["outcomes"] += 1
        else:
            store.add_record(
                store.TASK,
                f"Mission {state}: {mission['objective']} ({steps})",
                actor=store.MISSION,
                status=store.OPEN,
                ts=float(mission.get("created_at") or time.time()),
                source_ref=open_ref,
                detail={"mission_id": mid, "state": state, "kind": mission.get("kind")},
            )
            counts["open"] += 1
    return counts


# ------------------------------------------------------------------ ACM outbox


def drain_outbox(limit: int = 10) -> dict[str, int]:
    """Encode queued user statements into ACM. Failures stay queued and visible."""
    from aria_core import acm_bridge

    totals = {"encoded": 0, "skipped": 0, "failed": 0, "deferred": 0}
    if not acm_bridge.acm_is_authoritative():
        # Not an error: ACM is in legacy/rollback mode. Nothing is lost.
        totals["deferred"] = len(store.pending_outbox(limit=limit))
        return totals
    for entry in store.pending_outbox(limit=limit):
        episode_id = entry["episode_id"]
        episode = store.get_episode(episode_id)
        if episode is None or episode["erased"]:
            store.mark_outbox(episode_id, status="skipped", error="episode missing or erased")
            totals["skipped"] += 1
            continue
        try:
            out = acm_bridge.encode_continuity_statement(
                episode["content"],
                kind=entry["record_kind"],
                episode_id=episode_id,
                branch=episode["branch"],
                project=episode["project"],
                ts=episode["ts"],
            )
        except Exception as exc:  # noqa: BLE001 - kept in the outbox, reported
            error = f"{type(exc).__name__}: {exc}"
            store.mark_outbox(episode_id, status="failed", error=error)
            _state["last_error"] = error
            _state["acm_failed"] += 1
            totals["failed"] += 1
            log.warning("ACM encode failed for episode %s: %s", episode_id, error)
            continue
        acm_id = str(out.get("experience_id") or "")
        if out.get("encoded") and acm_id:
            store.mark_outbox(episode_id, status="done", acm_id=acm_id)
            record = store.record_by_source(f"episode:{episode_id}")
            if record is not None and acm_id not in record["acm_ids"]:
                store.update_record(record["id"], acm_ids=[*record["acm_ids"], acm_id])
            _state["acm_encoded"] += 1
            totals["encoded"] += 1
        else:
            # ACM declined it (trust policy, test artifact, read-only mode).
            # A refusal is an answer, not a failure to retry.
            store.mark_outbox(
                episode_id, status="skipped", error=str(out.get("reason") or "not encoded")
            )
            _state["acm_skipped"] += 1
            totals["skipped"] += 1
    _state["last_drain"] = time.time()
    return totals


def sync_all(*, missions: bool = True, drain: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {"archive": sync_archives()}
    if missions:
        try:
            out["missions"] = sync_missions()
        except Exception as exc:  # noqa: BLE001 - reported, archive sync still counts
            out["missions_error"] = f"{type(exc).__name__}: {exc}"
            _state["last_error"] = out["missions_error"]
    if drain:
        out["acm"] = drain_outbox()
    return out


def status() -> dict[str, Any]:
    try:
        counts = store.counts()
    except Exception as exc:  # noqa: BLE001
        counts = {"error": f"{type(exc).__name__}: {exc}"}
    return {**counts, **_state, "worker_running": _worker_running()}


# ------------------------------------------------------------------ background worker

_stop = threading.Event()
_thread: threading.Thread | None = None
POLL_S = 5.0
MISSION_SYNC_EVERY_S = 60.0


def _loop() -> None:
    last_missions = 0.0
    while not _stop.is_set():
        try:
            now = time.time()
            sync_all(missions=now - last_missions >= MISSION_SYNC_EVERY_S)
            if now - last_missions >= MISSION_SYNC_EVERY_S:
                last_missions = now
        except Exception as exc:  # noqa: BLE001 - the worker must never die
            _state["last_error"] = f"{type(exc).__name__}: {exc}"
            log.exception("Continuity sync failed")
        _stop.wait(POLL_S)


def start() -> bool:
    global _thread
    if _thread and _thread.is_alive():
        return False
    _stop.clear()
    _thread = threading.Thread(target=_loop, daemon=True, name="jarvis-continuity")
    _thread.start()
    return True


def stop(timeout: float = 5.0) -> None:
    _stop.set()
    if _thread and _thread.is_alive():
        _thread.join(timeout=timeout)


def _worker_running() -> bool:
    return bool(_thread and _thread.is_alive())
