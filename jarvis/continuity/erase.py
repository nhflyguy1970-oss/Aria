"""Explicit deletion of archived conversation content — plan first, then apply.

Nothing here runs on its own. Deletion is a two-step, owner-initiated act:

1. ``plan_erasure(...)`` is read-only. It lists every place the selected turns
   live — archive lines, index rows, continuity records derived from them,
   queued ACM work, and ACM experiences linked by ``episode:<id>`` — and
   returns a token that fingerprints exactly that plan.
2. ``apply_erasure(plan, confirm=token)`` executes that plan and nothing else.
   If anything changed since the plan was made, the token no longer matches
   and nothing is touched.

What applying does:
  * archive: the selected events' content is blanked in place (the file is
    rewritten atomically) and an ``erased`` event records which ids were
    erased and when — never what they said;
  * index: episode content is blanked and flagged erased; records derived
    only from erased turns are blanked; records that also cite other turns
    keep their other sources and drop the erased ids;
  * ACM: linked experiences are soft-forgotten through ACM's own forget path
    (never surfaced again). ACM's Memory Authority rule (P17) retains
    experience bodies; physically purging them would need an ACM-level
    change and is reported, not attempted.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from jarvis.continuity import store


class ErasureError(RuntimeError):
    pass


def _archive_events(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    out: list[tuple[Path, dict[str, Any]]] = []
    if not root.is_dir():
        return out
    for path in sorted(root.glob("*.jsonl")):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append((path, json.loads(line)))
                except json.JSONDecodeError:
                    continue
    return out


def plan_erasure(
    *,
    episode_ids: list[str] | None = None,
    branch: str | None = None,
    contains: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Read-only: everything that erasing the selected turns would touch."""
    from jarvis.continuity.ingest import archive_root

    if not (episode_ids or branch or contains):
        raise ErasureError("select turns by episode_ids, branch or contains")
    root = Path(root) if root is not None else archive_root()
    wanted = set(episode_ids or [])
    needle = (contains or "").lower()
    selected: dict[str, dict[str, Any]] = {}
    for path, event in _archive_events(root):
        if event.get("kind") not in ("message", "seed", "import"):
            continue
        eid = str(event.get("id") or "")
        if not eid or event.get("erased"):
            continue
        hit = (
            eid in wanted
            or (branch and event.get("branch") == branch)
            or (needle and needle in str(event.get("content") or "").lower())
        )
        if hit:
            selected[eid] = {"file": path.name, "branch": event.get("branch"), "ts": event.get("ts")}

    records: dict[str, dict[str, Any]] = {}
    outbox: list[str] = []
    for eid in selected:
        for rec in store.records_citing(eid):
            records[rec["id"]] = {
                "kind": rec["kind"],
                "only_erased_sources": set(rec["episode_ids"]) <= set(selected),
            }
        entry = store.outbox_entry(eid)
        if entry:
            outbox.append(eid)

    acm: list[dict[str, str]] = []
    try:
        from aria_core import acm_bridge

        if acm_bridge.acm_is_authoritative():
            for eid in selected:
                exp_id = acm_bridge.experience_for_episode(eid)
                if exp_id:
                    acm.append({"episode_id": eid, "experience_id": exp_id})
    except Exception as exc:  # noqa: BLE001 - the plan must say ACM was not checked
        acm.append({"error": f"ACM not checked: {type(exc).__name__}: {exc}"})

    plan = {
        "episodes": sorted(selected),
        "archive_files": sorted({v["file"] for v in selected.values()}),
        "records": records,
        "outbox": sorted(outbox),
        "acm_experiences": acm,
        "acm_note": (
            "ACM experiences are soft-forgotten via ACM's forget path; ACM's Memory "
            "Authority rule retains their bodies (no physical purge)."
        ),
        "selector": {"episode_ids": sorted(wanted), "branch": branch, "contains": contains},
    }
    plan["token"] = hashlib.sha256(
        json.dumps({k: plan[k] for k in ("episodes", "records", "acm_experiences")}, sort_keys=True)
        .encode()
    ).hexdigest()[:16]
    return plan


def apply_erasure(plan: dict[str, Any], *, confirm: str, root: Path | None = None) -> dict[str, Any]:
    """Execute a reviewed plan. Refuses if the plan is stale or unconfirmed."""
    from jarvis.continuity.ingest import archive_root
    from jarvis.live_data_guard import assert_live_write_allowed

    if not confirm or confirm != plan.get("token"):
        raise ErasureError("confirmation token does not match this plan")
    root = Path(root) if root is not None else archive_root()
    fresh = plan_erasure(**{k: v for k, v in plan["selector"].items() if v}, root=root)
    if fresh["token"] != plan["token"]:
        raise ErasureError("history changed since the plan was made; plan again")

    targets = set(plan["episodes"])
    now = time.time()
    # 1. Archive: blank content in place, atomically per file.
    for name in plan["archive_files"]:
        path = root / name
        assert_live_write_allowed(path)
        lines_out: list[str] = []
        erased_here: list[str] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    lines_out.append(line if line.endswith("\n") else line + "\n")
                    continue
                if str(event.get("id") or "") in targets and event.get("kind") in (
                    "message",
                    "seed",
                    "import",
                ):
                    event["content"] = ""
                    event["erased"] = True
                    erased_here.append(event["id"])
                lines_out.append(json.dumps(event, ensure_ascii=False) + "\n")
        lines_out.append(
            json.dumps(
                {"kind": "erased", "ids": erased_here, "ts_epoch": now}, ensure_ascii=False
            )
            + "\n"
        )
        tmp = path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.writelines(lines_out)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        # Byte offsets no longer line up with the rewritten file.
        store.set_position(f"archive:{name}", path.stat().st_size)

    # 2. Index and derived records.
    with store._conn() as conn:  # noqa: SLF001 - same package
        for eid in targets:
            conn.execute(
                "UPDATE episodes SET content='', erased=1, content_hash='' WHERE id=?", (eid,)
            )
    for rid, info in plan["records"].items():
        rec = store.get_record(rid)
        if rec is None:
            continue
        if info["only_erased_sources"]:
            store.update_record(rid, text="[erased]", detail={"erased_at": now})
        else:
            kept = [e for e in rec["episode_ids"] if e not in targets]
            with store._conn() as conn:  # noqa: SLF001
                conn.execute(
                    "UPDATE records SET episode_ids=? WHERE id=?", (json.dumps(kept), rid)
                )
    for eid in plan["outbox"]:
        store.mark_outbox(eid, status="skipped", error="erased", attempted=False)

    # 3. ACM, through its own forget path.
    acm_results = []
    for item in plan["acm_experiences"]:
        if "experience_id" not in item:
            continue
        try:
            from aria_core import acm_bridge

            out = acm_bridge.primary_forget(entry_id=item["experience_id"])
            acm_results.append({**item, "cooled": bool(out.get("cooled"))})
        except Exception as exc:  # noqa: BLE001 - reported
            acm_results.append({**item, "error": f"{type(exc).__name__}: {exc}"})

    return {
        "ok": True,
        "erased_episodes": len(targets),
        "records": len(plan["records"]),
        "acm": acm_results,
        "acm_note": plan["acm_note"],
    }
