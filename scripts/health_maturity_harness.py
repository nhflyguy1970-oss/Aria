#!/usr/bin/env python3
"""Health V1 maturity harness — isolated decades-scale PHR. Never touches live data."""

from __future__ import annotations

import json
import os
import random
import tempfile
import time
import uuid
from datetime import date, timedelta
from pathlib import Path


def bind_temp_phr(root: Path | None = None) -> Path:
    root = root or Path(tempfile.mkdtemp(prefix="health_maturity_"))
    os.environ["JARVIS_DATA_DIR"] = str(root)
    os.environ["JARVIS_HEALTH_STEP_UP"] = "0"
    os.environ["JARVIS_HEALTH_READONLY"] = "0"
    import jarvis.config as config

    config.DATA_DIR = root
    from jarvis.health_product import store

    store.reset_migration_cache()
    store.HEALTH_DIR = root / "health_product"
    store.DB_PATH = root / "health_product" / "health.db"
    store.DOCS_DIR = root / "health_product" / "documents"
    store.ensure_dirs()
    store.connect().close()
    return root


def _nid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def store_count(table: str) -> int:
    from jarvis.health_product import store

    return store.table_row_count(table)


def seed_decades(*, years: int = 20, scale: str = "full") -> dict:
    """Bulk-seed an isolated PHR. scale=full is heavy; scale=fast is CI-friendly."""
    from jarvis.health_product import store

    rng = random.Random(42)
    today = date.today()
    start = today - timedelta(days=365 * years)
    t0 = time.perf_counter()

    store.set_profile(
        {
            "name": "Jeff (Maturity Sim)",
            "dob": "1975-04-12",
            "blood_type": "O+",
            "primary_physician": "Dr. Rivera",
            "specialists": "Dr. Cho (cardio); Dr. Patel (endo)",
            "emergency_contacts": "Alex — 555-0100",
            "height_in": 70,
        }
    )

    for rel, cond, age in (
        ("father", "Diabetes", "52"),
        ("father", "Heart disease", "58"),
        ("mother", "High blood pressure", "48"),
        ("maternal_grandmother", "Alzheimer's", "78"),
        ("brother", "High cholesterol", "45"),
    ):
        store.upsert_family_history(
            {"relation": rel, "condition": cond, "age_at_diagnosis": age, "hereditary": True, "confirmed": 1}
        )

    if scale == "fast":
        bp_n, sugar_n, weight_n = 800, 800, 400
        workout_n, nutrition_n, symptom_n = 400, 600, 200
        visit_n, med_n, doc_n = 40, 40, 30
        checkin_n = 400
    else:
        bp_n, sugar_n, weight_n = 4000, 3500, 2000
        workout_n, nutrition_n, symptom_n = 2500, 3000, 800
        visit_n, med_n, doc_n = 180, 120, 120
        checkin_n = 2500

    conn = store.connect()
    try:
        now = time.time()

        def bulk(sql: str, rows: list[tuple]):
            conn.executemany(sql, rows)
            conn.commit()

        rows = []
        for i in range(bp_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, bp_n)))
            sys = 148 - min(18, i // 200) + rng.randint(-6, 6)
            dia = 92 - min(10, i // 250) + rng.randint(-4, 4)
            rows.append((_nid("vit"), "blood_pressure", d.isoformat(), now - (bp_n - i), float(sys), float(dia), "mmHg", ""))
        bulk(
            "INSERT INTO vitals(id,kind,day,recorded_at,value,value2,units,notes) VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )

        rows = []
        for i in range(sugar_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, sugar_n)))
            val = 145 - min(25, i // 150) + rng.randint(-12, 12)
            rows.append((_nid("vit"), "blood_sugar", d.isoformat(), now - (sugar_n - i), float(val), None, "mg/dL", ""))
        bulk(
            "INSERT INTO vitals(id,kind,day,recorded_at,value,value2,units,notes) VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )

        rows = []
        w0 = 248.0
        for i in range(weight_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, weight_n)))
            w = w0 - min(28, i / max(1, weight_n) * 28) + rng.uniform(-1.2, 1.2)
            rows.append((_nid("vit"), "weight", d.isoformat(), now - (weight_n - i), round(w, 1), None, "lb", ""))
        bulk(
            "INSERT INTO vitals(id,kind,day,recorded_at,value,value2,units,notes) VALUES (?,?,?,?,?,?,?,?)",
            rows,
        )

        rows = []
        for i in range(checkin_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, checkin_n)))
            payload = {
                "day": d.isoformat(),
                "overall": rng.randint(5, 9),
                "energy": rng.randint(4, 9),
                "mood": rng.randint(4, 9),
                "stress": rng.randint(2, 8),
                "pain": rng.randint(0, 5),
                "sleep_hours": round(rng.uniform(5.0, 8.5), 1),
                "water": f"{rng.randint(40, 100)} oz",
                "exercise": rng.choice(["", "walk", "bands", "stretch"]),
            }
            rows.append((_nid("chk"), d.isoformat(), now - (checkin_n - i), json.dumps(payload)))
        bulk("INSERT INTO checkins(id,day,recorded_at,payload) VALUES (?,?,?,?)", rows)

        meds = [
            ("Metformin", "500 mg", "current"),
            ("Lisinopril", "10 mg", "current"),
            ("Atorvastatin", "20 mg", "current"),
            ("Aspirin", "81 mg", "current"),
            ("Omeprazole", "20 mg", "stopped"),
            ("Sertraline", "50 mg", "stopped"),
        ]
        for i in range(med_n):
            name, strength, status = meds[i % len(meds)]
            if i >= len(meds):
                name = f"{name} #{i}"
                status = "stopped"
            start_d = (start + timedelta(days=rng.randint(0, years * 300))).isoformat()
            cols = store.table_columns_safe("medications")
            base = {
                "id": _nid("med"),
                "name": name,
                "strength": strength,
                "dose": "1 tab",
                "frequency": "daily",
                "status": status if i < 20 else "stopped",
                "start_date": start_d,
                "updated_at": now,
            }
            if "provenance" in cols:
                base["provenance"] = "manual"
                base["confidence"] = "user_confirmed"
                base["confirmed"] = 1
            keys = [k for k in base if k in cols]
            conn.execute(
                f"INSERT INTO medications({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})",
                [base[k] for k in keys],
            )
        conn.commit()

        for name in ("Vitamin D", "Fish Oil", "Magnesium", "CoQ10", "Multivitamin"):
            conn.execute(
                "INSERT INTO supplements(id,name,dose,frequency,status,updated_at) VALUES (?,?,?,?,?,?)",
                (_nid("sup"), name, "1", "daily", "current", now),
            )
        conn.commit()

        for name, spec in (
            ("Dr. Rivera", "primary"),
            ("Dr. Cho", "cardiology"),
            ("Dr. Patel", "endocrinology"),
            ("Dr. Kim", "ophthalmology"),
        ):
            conn.execute(
                "INSERT INTO providers(id,specialty,name,phone,last_visit,next_visit,updated_at) VALUES (?,?,?,?,?,?,?)",
                (
                    _nid("prv"),
                    spec,
                    name,
                    "555-0100",
                    (today - timedelta(days=90)).isoformat(),
                    (today + timedelta(days=60)).isoformat(),
                    now,
                ),
            )
        conn.commit()

        rows = []
        for i in range(visit_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, visit_n)))
            rows.append(
                (
                    _nid("vis"),
                    d.isoformat(),
                    "Follow-up",
                    rng.choice(["Dr. Rivera", "Dr. Cho", "Dr. Patel"]),
                    "Routine follow-up",
                    "Discussed labs and BP",
                    "Continue meds",
                    "Return in 6 months",
                    "Ask about A1C",
                    "A1C improved",
                    (d + timedelta(days=180)).isoformat(),
                    "",
                    "",
                    now,
                )
            )
        bulk(
            "INSERT INTO visits(id,day,title,physician,reason,summary,instructions,follow_up,questions_asked,questions_answered,next_appointment,document_ids,notes,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )

        rows = []
        for i in range(workout_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, workout_n)))
            rows.append(
                (
                    _nid("wo"),
                    d.isoformat(),
                    rng.choice(["Upper body", "Walk", "Bands", "Core"]),
                    rng.choice(["push", "walk", "full_body"]),
                    "upper",
                    35.0,
                    "moderate",
                    None,
                    "",
                    now,
                )
            )
        bulk(
            "INSERT INTO workouts(id,day,title,template,body_part,duration_min,difficulty,pain,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            rows,
        )

        rows = []
        for i in range(nutrition_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, nutrition_n)))
            kind = rng.choice(["meal", "meal", "water", "alcohol"])
            desc = {
                "meal": rng.choice(["oatmeal", "chicken salad", "pizza", "eggs"]),
                "water": f"{rng.randint(40, 100)} oz water",
                "alcohol": f"{rng.randint(1, 3)} beers",
            }[kind]
            rows.append(
                (
                    _nid("nut"),
                    d.isoformat(),
                    now,
                    kind,
                    "breakfast" if kind == "meal" else "",
                    desc,
                    "",
                    None,
                    "",
                    "",
                    "",
                    now,
                    "manual",
                    "user_entered",
                    0,
                )
            )
        bulk(
            "INSERT INTO nutrition_log(id,day,recorded_at,kind,meal_slot,description,items,quantity,units,tags,notes,created_at,provenance,confidence,confirmed) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            rows,
        )

        rows = []
        for i in range(symptom_n):
            d = start + timedelta(days=int(i * (years * 365) / max(1, symptom_n)))
            name = rng.choice(["headache", "knee pain", "fatigue", "shoulder ache", "dizziness"])
            rows.append((_nid("sym"), name, d.isoformat(), now - (symptom_n - i), None, "", "1 day"))
        bulk(
            "INSERT INTO symptoms(id,name,day,recorded_at,severity,notes,duration) VALUES (?,?,?,?,?,?,?)",
            rows,
        )

        for y in range(years):
            d = (start + timedelta(days=y * 365 + 30)).isoformat()
            a1c = round(7.2 - y * 0.05 + rng.uniform(-0.1, 0.1), 1)
            conn.execute(
                "INSERT INTO labs(id,name,day,recorded_at,value,value_text,units,ref_low,ref_high,physician,notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (_nid("lab"), "A1C", d, now, a1c, "", "%", None, None, "Dr. Patel", ""),
            )
        conn.commit()

        for item in (
            ("Colonoscopy", "colonoscopy", "2018-05-01", 120),
            ("Eye exam", "eye", "2024-11-01", 24),
            ("Dental cleaning", "dental", "2026-01-15", 6),
            ("Physical exam", "physical", "2025-09-01", 12),
            ("PSA", "psa", "2025-09-01", 12),
        ):
            name, slug, last, interval = item
            conn.execute(
                "INSERT INTO preventive_care(id,name,slug,category,interval_months,last_done,next_due,status,source_kind,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (_nid("prv"), name, slug, "screening", interval, last, None, "planned", "user", now, now),
            )
        conn.commit()

        store.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        for i in range(doc_n):
            p = store.DOCS_DIR / f"lab_report_{i}.txt"
            p.write_text(f"Lab report #{i}\nA1C and lipids summary\n", encoding="utf-8")
            conn.execute(
                "INSERT INTO documents(id,day,title,kind,path,extracted_text,notes,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    _nid("doc"),
                    (start + timedelta(days=i * 40)).isoformat(),
                    f"Lab report {i}",
                    "lab",
                    str(p),
                    p.read_text(),
                    "",
                    now,
                ),
            )
        conn.commit()

        store.add_doctor_question("Discuss A1C trend")
        store.add_doctor_question("Ask about knee pain after walking")
        store.upsert_condition({"name": "Type 2 diabetes", "status": "active"})
        store.upsert_condition({"name": "Hypertension", "status": "active"})
        store.upsert_allergy({"name": "Penicillin", "kind": "drug", "reaction": "rash"})
        store.upsert_vaccination({"name": "COVID-19", "day": "2024-10-01"})
        store.upsert_vaccination({"name": "Influenza", "day": "2025-10-15"})
        store.upsert_goal({"title": "Lose 20 pounds", "kind": "weight", "target_value": 220, "status": "active"})
        store.upsert_goal({"title": "Walk most days", "kind": "exercise", "per_week": 5, "status": "active"})

    finally:
        conn.close()

    elapsed = time.perf_counter() - t0
    return {
        "vitals": store_count("vitals"),
        "checkins": store_count("checkins"),
        "workouts": store_count("workouts"),
        "nutrition": store_count("nutrition_log"),
        "symptoms": store_count("symptoms"),
        "visits": store_count("visits"),
        "medications": store_count("medications"),
        "documents": store_count("documents"),
        "years": years,
        "seed_seconds": round(elapsed, 2),
        "scale": scale,
    }


def timed(label: str, fn, budget_s: float = 5.0) -> dict:
    t0 = time.perf_counter()
    result = fn()
    dt = time.perf_counter() - t0
    ok_result = True
    if isinstance(result, dict) and "ok" in result:
        ok_result = bool(result.get("ok"))
    return {
        "label": label,
        "seconds": round(dt, 3),
        "ok": dt <= budget_s and ok_result,
        "budget": budget_s,
    }


def run_maturity(*, years: int = 20, scale: str = "fast") -> dict:
    root = bind_temp_phr()
    counts = seed_decades(years=years, scale=scale)

    from jarvis.health_product import store
    from jarvis.health_product.backup import create, integrity_report, restore, verify
    from jarvis.health_product.dashboard import dashboard_payload
    from jarvis.health_product.engine import emergency_summary, graph_summary, ingest_message, search_summary
    from jarvis.health_product import gate
    from jarvis.health_product.patterns import FORBIDDEN_PHRASINGS, build_insights
    from jarvis.health_product.reports import report_html
    from jarvis.health_product.second_opinion import preview_second_opinion
    from jarvis.health_product.timeline import build_timeline
    from jarvis.health_product.visit_prep import build_visit_prep

    # Recent vitals must not be decade-old when history is capped
    recent_bp = store.list_vitals(kind="blood_pressure", limit=5)
    recent_ok = bool(recent_bp) and recent_bp[-1]["day"] >= (date.today() - timedelta(days=120)).isoformat()

    timings = []
    timings.append(timed("dashboard", dashboard_payload, 5.0))
    timings.append(timed("timeline", lambda: build_timeline(limit=250), 5.0))
    timings.append(timed("graph_bp", lambda: graph_summary("blood_pressure"), 3.0))
    timings.append(timed("graph_weight", lambda: graph_summary("weight"), 3.0))
    timings.append(timed("search_metformin", lambda: search_summary("Metformin"), 3.0))
    timings.append(timed("search_diabetes", lambda: search_summary("diabetes"), 3.0))
    timings.append(timed("visit_prep", build_visit_prep, 5.0))
    timings.append(timed("insights", build_insights, 8.0))
    timings.append(timed("emergency", emergency_summary, 2.0))
    timings.append(timed("export_complete", store.export_bundle, 30.0 if scale == "full" else 15.0))

    reports = {}
    for kind in ("doctor_visit", "visit_prep", "emergency", "medications", "blood_pressure", "labs"):
        t0 = time.perf_counter()
        html = report_html(kind)
        dt = time.perf_counter() - t0
        low = html.lower()
        reports[kind] = {
            "seconds": round(dt, 3),
            "bytes": len(html),
            "has_disclaimer": "not a physician" in low or "does not diagnose" in low,
            "ok": dt < 5.0 and len(html) > 200,
        }

    chat = {}
    for q in (
        "What medications am I taking?",
        "How's my blood pressure?",
        "Prepare me for tomorrow's appointment.",
        "Does diabetes run in my family?",
        "When was my last colonoscopy?",
        "Do you see any patterns?",
        "How am I doing?",
    ):
        out = ingest_message(q)
        msg = (out.get("message") or "").lower()
        # Evaluate educational body only — strip boundary + disclaimer (they deny diagnosis)
        body = msg
        for marker in ("these are educational observations", "aria is not a physician"):
            if marker in body:
                body = body.split(marker)[0]
        banned = [
            b
            for b in FORBIDDEN_PHRASINGS
            if b.lower() in body
            and b.lower() not in ("disease",)
            and not any(d in body for d in ("not a diagnos", "not diagnos", "does not diagnos", "not causation", "not a proven"))
        ]
        chat[q] = {
            "intent": out.get("intent"),
            "ok": out.get("ok", True) is not False,
            "no_diagnosis": not banned,
            "has_disclaimer": "not a physician" in msg or "informational" in msg or bool(out.get("disclaimer")),
            "has_substance": ("observation:" in msg) or ("window:" in msg and "no clear co-occurrence" not in msg),
        }

    so = preview_second_opinion("Have my labs improved over five years?")
    second_opinion = {
        "ok": so.get("ok", True) is not False,
        "leaves_only_after_approval": "nothing leaves" in (so.get("message") or "").lower()
        or (so.get("information_sent_preview") or {}).get("note", "").lower().startswith("nothing leaves"),
        "preview_only": so.get("status") in (None, "preview") or so.get("intent") == "second_opinion_preview",
    }

    os.environ["JARVIS_HEALTH_STEP_UP"] = "1"
    security = {
        "step_up_blocks_export": bool((gate.require(None, "export_record") or {}).get("step_up_required")),
        "step_up_blocks_delete": bool((gate.require(None, "delete_record") or {}).get("step_up_required")),
        "step_up_blocks_med_edit": bool((gate.require(None, "edit_medications") or {}).get("step_up_required")),
        "step_up_blocks_allergy": bool((gate.require(None, "edit_allergies") or {}).get("step_up_required")),
        "step_up_blocks_cloud": bool((gate.require(None, "cloud_consult") or {}).get("step_up_required")),
        "step_up_blocks_restore": bool((gate.require(None, "backup_restore") or {}).get("step_up_required")),
    }
    os.environ["JARVIS_HEALTH_STEP_UP"] = "0"

    backup = {"ok": False}
    try:
        vitals_before = store_count("vitals")
        export = store.export_bundle()
        b1 = create(password="maturity-pass-42", kind="manual")
        b2 = create(password="maturity-pass-42", kind="manual")
        v1 = verify(b1["backup"]["id"])
        refused = restore(password="maturity-pass-42", backup_id=b1["backup"]["id"], confirm=False)
        wrong_ok = True
        try:
            from jarvis.health_product import backup as bmod

            bmod.decrypt_bundle(json.loads(Path(b1["backup"]["path"]).read_text()), "wrong-password")
            wrong_ok = False
        except Exception:
            wrong_ok = True

        # Destructive-ish round trip on isolated DB: wipe vitals then restore
        with store._lock:
            conn = store.connect()
            try:
                conn.execute("DELETE FROM vitals")
                conn.commit()
            finally:
                conn.close()
        assert store_count("vitals") == 0
        restored = restore(password="maturity-pass-42", backup_id=b1["backup"]["id"], confirm=True)
        vitals_after = store_count("vitals")
        integ = integrity_report()
        backup = {
            "ok": (
                b1["ok"]
                and b2["ok"]
                and v1["ok"]
                and refused.get("confirm_required")
                and wrong_ok
                and integ["ok"]
                and export.get("complete") is True
                and restored.get("ok") is True
                and vitals_after == vitals_before
                and b1["backup"]["filename"] != b2["backup"]["filename"]
            ),
            "two_distinct_files": b1["backup"]["filename"] != b2["backup"]["filename"],
            "verify": v1["ok"],
            "no_silent_overwrite": refused.get("confirm_required") is True,
            "wrong_password_rejected": wrong_ok,
            "export_complete": export.get("complete") is True,
            "export_vitals": (export.get("record_counts") or {}).get("vitals"),
            "restore_vitals": vitals_after,
            "vitals_before": vitals_before,
            "integrity_ok_count": integ.get("ok_count"),
            "safety_backup": bool(restored.get("safety_backup")),
        }
    except Exception as exc:
        backup = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    slow = [t for t in timings if not t["ok"]]
    report_fail = [k for k, v in reports.items() if not v["ok"] or not v["has_disclaimer"]]
    chat_fail = [k for k, v in chat.items() if not v["ok"] or not v["no_diagnosis"]]

    trust = {
        "lifetime_history": counts.get("vitals", 0) > 100 and counts.get("visits", 0) > 5 and recent_ok,
        "doctor_visit_ready": reports.get("visit_prep", {}).get("ok") and chat.get("Prepare me for tomorrow's appointment.", {}).get("ok"),
        "emergency_ready": reports.get("emergency", {}).get("ok") and reports.get("emergency", {}).get("has_disclaimer"),
        "backups_trusted": backup.get("ok") is True,
        "reports_trusted": not report_fail,
        "search_trusted": timings[4]["ok"] and timings[5]["ok"],
        "ai_observations_trusted": (
            not chat_fail
            and chat.get("Do you see any patterns?", {}).get("no_diagnosis")
            and chat.get("Do you see any patterns?", {}).get("has_substance")
        ),
        "privacy_default": all(security.values()) and second_opinion["leaves_only_after_approval"],
        "responsive": not slow,
    }
    certified = all(trust.values())

    return {
        "root": str(root),
        "counts": counts,
        "recent_vitals_ok": recent_ok,
        "timings": timings,
        "reports": reports,
        "chat": chat,
        "second_opinion": second_opinion,
        "security": security,
        "backup": backup,
        "trust": trust,
        "certified": certified,
        "friction": {
            "slow_ops": slow,
            "report_issues": report_fail,
            "chat_issues": chat_fail,
            "recent_vitals_ok": recent_ok,
        },
    }


if __name__ == "__main__":
    import pprint
    import sys

    scale = "fast" if "--fast" in sys.argv else "full"
    out = run_maturity(years=20, scale=scale)
    pprint.pp({k: out[k] for k in ("counts", "certified", "trust", "friction", "backup", "security", "second_opinion")})
    print("--- timings ---")
    for t in out["timings"]:
        print(f"  {t['label']}: {t['seconds']}s ok={t['ok']}")
    print("CERTIFIED" if out["certified"] else "NOT CERTIFIED")
    Path("/tmp/health_maturity_report.json").write_text(json.dumps(out, indent=2, default=str))
    print("wrote /tmp/health_maturity_report.json")
