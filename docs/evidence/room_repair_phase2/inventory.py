"""Read-only Tier 2 inventory of authorized deletion targets. Does not mutate."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path("/media/jeff/AI/jarvis")
DATA = ROOT / "data"
TOKENS = ("ARIA-REPAIR", "ARIA-FINAL", "oc-cert", "wf_probe")
TOKEN_RE = re.compile("|".join(re.escape(t) for t in TOKENS), re.I)
OUT = ROOT / "docs/evidence/room_repair_phase2/inventory.json"


def rows(conn, sql, args=()):
    cur = conn.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def health_inventory():
    db = DATA / "health_product" / "health.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    tables = [
        "medications",
        "dose_logs",
        "checkins",
        "activities",
        "vitals",
        "events",
        "backups",
        "restore_log",
        "schema_meta",
    ]
    out = {"db": str(db), "tables": {}}
    for t in tables:
        try:
            all_rows = rows(conn, f"SELECT * FROM {t}")
        except sqlite3.Error as e:
            out["tables"][t] = {"error": str(e)}
            continue
        out["tables"][t] = {"count": len(all_rows), "rows": all_rows}
    bak_dir = DATA / "health_product" / "backups"
    out["backup_files"] = [p.name for p in bak_dir.glob("*")] if bak_dir.exists() else []
    conn.close()
    return out


def planner_inventory():
    db = DATA / "planner.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    tasks = rows(conn, "SELECT * FROM tasks")
    wool = [t for t in tasks if "wool yarn" in str(t.get("text") or "").lower() or t.get("id") == "9e3ace063d"]
    qa = [t for t in tasks if TOKEN_RE.search(json.dumps(t, default=str))]
    conn.close()
    return {
        "db": str(db),
        "task_count": len(tasks),
        "wool": wool,
        "token_hits": qa,
        "all_texts": [{"id": t.get("id"), "text": t.get("text"), "deleted": t.get("deleted"), "completed": t.get("completed")} for t in tasks],
    }


def acm_inventory():
    db = DATA / "acm" / "cognitive.db"
    conn = sqlite3.connect(str(db))
    snaps = rows(conn, "SELECT id, kind, created, schema_version, length(payload) AS nbytes FROM snapshots ORDER BY id")
    token_snaps = []
    latest_hits = []
    latest_id = snaps[-1]["id"] if snaps else None
    for s in snaps:
        payload = conn.execute("SELECT payload FROM snapshots WHERE id=?", (s["id"],)).fetchone()[0]
        if not TOKEN_RE.search(payload or ""):
            continue
        token_snaps.append(s["id"])
        if s["id"] == latest_id:
            body = json.loads(payload).get("body") or {}
            for bucket, items in body.items():
                if isinstance(items, dict):
                    iterable = items.items()
                elif isinstance(items, list):
                    iterable = [(str(i), x) for i, x in enumerate(items)]
                else:
                    continue
                for key, val in iterable:
                    blob = json.dumps(val, default=str)
                    if TOKEN_RE.search(blob):
                        snippet = blob[:240]
                        latest_hits.append({"bucket": bucket, "key": key, "snippet": snippet})
    ops_hits = rows(conn, "SELECT id, op, substr(detail,1,200) AS detail FROM ops WHERE detail LIKE '%ARIA-REPAIR%' OR detail LIKE '%ARIA-FINAL%' OR detail LIKE '%oc-cert%' OR detail LIKE '%wf_probe%'")
    conn.close()
    return {
        "db": str(db),
        "snapshot_count": len(snaps),
        "snapshots": snaps,
        "token_snapshot_ids": token_snaps,
        "latest_id": latest_id,
        "latest_token_hits": latest_hits[:80],
        "latest_token_hit_count": len(latest_hits),
        "ops_hits": ops_hits,
    }


def main():
    payload = {
        "health": health_inventory(),
        "planner": planner_inventory(),
        "acm": acm_inventory(),
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"wrote {OUT}")
    h = payload["health"]["tables"]
    print("medications", h.get("medications", {}).get("count"))
    print("dose_logs", h.get("dose_logs", {}).get("count"))
    print("checkins", h.get("checkins", {}).get("count"))
    print("activities", h.get("activities", {}).get("count"))
    print("vitals", h.get("vitals", {}).get("count"))
    print("events", h.get("events", {}).get("count"))
    print("backups", h.get("backups", {}).get("count"))
    print("backup_files", payload["health"]["backup_files"])
    print("wool", payload["planner"]["wool"])
    print("planner tasks", payload["planner"]["task_count"])
    print("acm snaps", payload["acm"]["snapshot_count"], "token snaps", len(payload["acm"]["token_snapshot_ids"]))
    print("latest token hits", payload["acm"]["latest_token_hit_count"])


if __name__ == "__main__":
    main()
