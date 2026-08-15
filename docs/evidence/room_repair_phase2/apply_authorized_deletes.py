"""Tier 2 authorized owner-data deletions. Run only with Jeff's explicit authorization.

Deletes:
1. Three Vitamin D3 residency/cert dose notes (not the medication)
2. Encrypted Health backup bak_7a69c9914d45 + file + backup event
3. Aug 6–8 Health vitals / check-in / walking + associated events
4. ACM probe snapshot content (ARIA-REPAIR / ARIA-FINAL / oc-cert / wf_probe)
5. Planner task "pick up wool yarn for fly tying" (all copies)
"""
from __future__ import annotations

import json
import re
import shutil
import sqlite3
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path("/media/jeff/AI/jarvis")
DATA = ROOT / "data"
EVIDENCE = ROOT / "docs/evidence/room_repair_phase2"
TOKENS = ("ARIA-REPAIR", "ARIA-FINAL", "oc-cert", "wf_probe")
TOKEN_RE = re.compile("|".join(re.escape(t) for t in TOKENS), re.I)

KEEP_MED = "med_39bcc7df3187"
KEEP_EVENT_VERBS = {("medications_upsert", "Vitamin D3")}
WOOL = "pick up wool yarn for fly tying"

DOSE_IDS = ("dose_d79ad2f5dce9", "dose_6b1d8df5280b", "dose_b7b3e3c3b1c1")
CHECKIN_IDS = ("chk_df57c3a42785",)
ACTIVITY_IDS = ("act_bc278fd2891d",)
BACKUP_ID = "bak_7a69c9914d45"


def _backup_file(src: Path) -> Path | None:
    if not src.exists():
        return None
    dest = EVIDENCE / "pre_delete" / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def delete_health() -> dict:
    sys.path.insert(0, str(ROOT))
    from jarvis.health_product import store

    _backup_file(store.DB_PATH)
    log: dict = {"deleted": [], "kept": [], "backup_file_removed": False}

    vitals = store.list_table("vitals", limit=500)
    vital_ids = [r["id"] for r in vitals]
    for table, ids in (
        ("dose_logs", DOSE_IDS),
        ("checkins", CHECKIN_IDS),
        ("activities", ACTIVITY_IDS),
        ("vitals", vital_ids),
        ("backups", (BACKUP_ID,)),
    ):
        for item_id in ids:
            if store.delete_by_id(table, item_id, force=True, log=False):
                log["deleted"].append({"table": table, "id": item_id})
            else:
                log["deleted"].append({"table": table, "id": item_id, "already_gone": True})

    events = store.list_table("events", limit=500)
    for ev in events:
        key = (str(ev.get("verb") or ""), str(ev.get("detail") or ""))
        if key in KEEP_EVENT_VERBS:
            log["kept"].append({"table": "events", "id": ev["id"], "verb": ev.get("verb"), "detail": ev.get("detail")})
            continue
        if store.delete_by_id("events", ev["id"], force=True, log=False):
            log["deleted"].append({"table": "events", "id": ev["id"], "verb": ev.get("verb")})

    bak_row = None
    try:
        bak_row = store.get_by_id("backups", BACKUP_ID)
    except Exception:
        bak_row = None
    bak_path = DATA / "health_product" / "backups" / "aria-health-20260808-092139.json"
    if bak_row and bak_row.get("path"):
        bak_path = Path(bak_row["path"])
    if bak_path.exists():
        bak_path.unlink()
        log["backup_file_removed"] = True
        log["deleted"].append({"file": str(bak_path)})

    med = store.get_by_id("medications", KEEP_MED)
    log["medication_kept"] = bool(med) and med.get("name") == "Vitamin D3"
    log["remaining"] = {
        "medications": len(store.list_table("medications", limit=200)),
        "dose_logs": len(store.list_table("dose_logs", limit=200)),
        "checkins": len(store.list_table("checkins", limit=200)),
        "activities": len(store.list_table("activities", limit=200)),
        "vitals": len(store.list_table("vitals", limit=200)),
        "events": len(store.list_table("events", limit=200)),
        "backups": len(store.list_table("backups", limit=200)),
    }
    return log


def delete_planner() -> dict:
    sys.path.insert(0, str(ROOT))
    from jarvis.planner_store import DB_PATH, delete_task

    _backup_file(DB_PATH)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, text, deleted, completed FROM tasks").fetchall()
    targets = [dict(r) for r in rows if str(r["text"] or "").strip().lower() == WOOL]
    conn.close()
    removed = []
    for t in targets:
        out = delete_task(t["id"], soft=False)
        removed.append({"id": t["id"], "ok": out.get("ok"), "was_deleted": t["deleted"], "was_completed": t["completed"]})
    conn = sqlite3.connect(str(DB_PATH))
    left = conn.execute(
        "SELECT id, text FROM tasks WHERE lower(text) = lower(?)",
        (WOOL,),
    ).fetchall()
    conn.close()
    return {"removed": removed, "remaining_wool_rows": [dict(r) for r in left]}


def _blob(obj) -> str:
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return str(obj)


def _drop_matching(mapping: dict) -> list[str]:
    dropped = []
    for key, val in list(mapping.items()):
        if TOKEN_RE.search(_blob(val)) or TOKEN_RE.search(str(key)):
            mapping.pop(key, None)
            dropped.append(str(key))
    return dropped


def _drop_matching_list(seq: list) -> tuple[list, int]:
    kept = []
    n = 0
    for item in seq:
        if TOKEN_RE.search(_blob(item)):
            n += 1
            continue
        kept.append(item)
    return kept, n


def clean_acm() -> dict:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "aria_acm"))
    from acm.persistence.sqlite import SqliteDurableStore

    db = DATA / "acm" / "cognitive.db"
    _backup_file(db)
    durable = SqliteDurableStore(db)
    store = durable.load_latest()
    before = {
        "experiences": len(store.experiences),
        "concepts": len(store.concepts),
        "associations": len(store.associations),
    }
    dropped = {
        "experiences": _drop_matching(store.experiences),
        "concepts": _drop_matching(store.concepts),
        "associations": _drop_matching(store.associations),
        "hierarchy_edges": _drop_matching(store.hierarchy_edges),
        "abstractions": _drop_matching(store.abstractions),
        "general_principles": _drop_matching(store.general_principles),
        "evidence_influences": _drop_matching(store.evidence_influences),
        "goals": _drop_matching(store.goals),
        "envelopes": _drop_matching(store.envelopes),
        "adaptations": _drop_matching(store.adaptations),
        "temporal_patterns": _drop_matching(store.temporal_patterns),
        "predictions": _drop_matching(store.predictions),
        "hypotheses": _drop_matching(store.hypotheses),
        "prediction_audits": _drop_matching(store.prediction_audits),
        "simulations": _drop_matching(store.simulations),
        "recombinations": _drop_matching(store.recombinations),
        "analogies": _drop_matching(store.analogies),
        "reconciliations": _drop_matching(store.reconciliations),
        "provenance": _drop_matching(store.provenance),
        "accessibility": _drop_matching(store.accessibility),
    }
    store.priority_events, n_pe = _drop_matching_list(list(store.priority_events))
    store.accessibility_events, n_ae = _drop_matching_list(list(store.accessibility_events))
    store.confidence_events, n_ce = _drop_matching_list(list(store.confidence_events))
    dropped["priority_events"] = n_pe
    dropped["accessibility_events"] = n_ae
    dropped["confidence_events"] = n_ce

    drop_ids = set()
    for bucket in ("experiences", "concepts", "associations", "goals", "envelopes"):
        drop_ids.update(dropped.get(bucket) or [])

    # Drop associations that point at removed artifacts.
    for aid, assoc in list(store.associations.items()):
        if getattr(assoc, "source_id", "") in drop_ids or getattr(assoc, "target_id", "") in drop_ids:
            store.associations.pop(aid, None)
            dropped.setdefault("associations_dangling", []).append(aid)

    # Strip deleted concept ids from remaining frozen experiences.
    for eid, exp in list(store.experiences.items()):
        cids = tuple(c for c in (getattr(exp, "concept_ids", ()) or ()) if c not in drop_ids)
        if cids != getattr(exp, "concept_ids", ()):
            store.experiences[eid] = replace(exp, concept_ids=cids)

    saved = durable.save(store, kind="tier2_probe_cleanup")
    conn = durable._conn
    cur = conn.execute("SELECT id FROM snapshots ORDER BY id DESC LIMIT 1")
    latest_id = cur.fetchone()[0]
    cur = conn.execute(
        "SELECT id FROM snapshots WHERE id != ? AND ("
        "payload LIKE '%ARIA-REPAIR%' OR payload LIKE '%ARIA-FINAL%' "
        "OR payload LIKE '%oc-cert%' OR payload LIKE '%wf_probe%')",
        (latest_id,),
    )
    old_ids = [r[0] for r in cur.fetchall()]
    if old_ids:
        conn.executemany("DELETE FROM snapshots WHERE id=?", [(i,) for i in old_ids])
        conn.commit()

    # Verify latest payload is clean.
    payload = conn.execute("SELECT payload FROM snapshots WHERE id=?", (latest_id,)).fetchone()[0]
    remaining = TOKEN_RE.findall(payload or "")
    durable.close()
    after = {
        "experiences": len(store.experiences),
        "concepts": len(store.concepts),
        "associations": len(store.associations),
    }
    return {
        "before": before,
        "after": after,
        "dropped_counts": {k: (len(v) if isinstance(v, list) else v) for k, v in dropped.items()},
        "saved": saved,
        "pruned_old_snapshot_ids": old_ids,
        "latest_id": latest_id,
        "latest_token_hits": remaining,
    }


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    result = {
        "health": delete_health(),
        "planner": delete_planner(),
        "acm": clean_acm(),
    }
    out = EVIDENCE / "deletion_log.json"
    out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    if result["acm"].get("latest_token_hits"):
        raise SystemExit("ACM latest snapshot still contains probe tokens")
    if result["planner"].get("remaining_wool_rows"):
        raise SystemExit("wool yarn planner rows remain")
    if not result["health"].get("medication_kept"):
        raise SystemExit("Vitamin D3 medication missing after cleanup")


if __name__ == "__main__":
    main()
