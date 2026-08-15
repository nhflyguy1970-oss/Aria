"""Repair knowledge base — every repair becomes searchable knowledge."""

from __future__ import annotations

import time
from typing import Any

from jarvis.repair_product import store


def remember_from_history(row: dict[str, Any]) -> dict[str, Any]:
    """Upsert a knowledge article from a completed repair history row."""
    module_id = str(row.get("module_id") or "unknown")
    code = str(row.get("code") or row.get("title") or "unknown")
    key = f"{module_id}:{code}"
    articles = store.knowledge_articles()
    art = articles.get(key) or {
        "id": key,
        "module_id": module_id,
        "subsystem": row.get("subsystem"),
        "issue": row.get("title"),
        "code": code,
        "symptoms": [],
        "diagnoses": [],
        "evidence_samples": [],
        "repairs": [],
        "verifications": [],
        "related_subsystems": [],
        "created_at": time.time(),
    }
    if row.get("title") and row["title"] not in art["symptoms"]:
        art["symptoms"] = ([*art.get("symptoms", []), row["title"]])[-20:]
    diag = row.get("diagnosis")
    if diag and diag not in art["diagnoses"]:
        art["diagnoses"] = ([*art.get("diagnoses", []), diag])[-20:]
    for e in row.get("evidence") or []:
        if e not in art["evidence_samples"]:
            art["evidence_samples"] = ([*art.get("evidence_samples", []), e])[-30:]
    if row.get("plan_steps"):
        art["repairs"] = ([*art.get("repairs", []), row["plan_steps"]])[-20:]
    if row.get("message"):
        art["verifications"] = ([*art.get("verifications", []), row["message"][:240]])[-20:]
    if row.get("subsystem") and row["subsystem"] not in art["related_subsystems"]:
        art["related_subsystems"] = [*art.get("related_subsystems", []), row["subsystem"]]

    # Aggregates
    art["attempts"] = int(art.get("attempts") or 0) + 1
    if row.get("verified_ok"):
        art["successes"] = int(art.get("successes") or 0) + 1
        art["most_successful_repair"] = row.get("plan_steps") or art.get("most_successful_repair")
        durs = list(art.get("durations") or [])
        if row.get("duration_seconds") is not None:
            durs.append(float(row["duration_seconds"]))
            art["durations"] = durs[-50:]
            art["average_repair_time"] = round(sum(art["durations"]) / len(art["durations"]), 2)
    else:
        art["failures"] = int(art.get("failures") or 0) + 1
    attempts = max(1, int(art.get("attempts") or 1))
    art["average_success"] = round(int(art.get("successes") or 0) / attempts, 3)
    art["updated_at"] = time.time()
    art["history_ids"] = ([*art.get("history_ids", []), row.get("id")])[-40:]
    store.save_knowledge_article(key, art)
    return art


def search(query: str = "", *, subsystem: str = "", limit: int = 40) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    sub = (subsystem or "").strip().lower()
    out = []
    for art in store.knowledge_articles().values():
        if sub and str(art.get("subsystem") or "").lower() != sub:
            continue
        blob = " ".join(
            str(x)
            for x in (
                art.get("id"),
                art.get("issue"),
                art.get("module_id"),
                art.get("code"),
                " ".join(art.get("symptoms") or []),
                " ".join(art.get("diagnoses") or []),
                art.get("most_successful_repair"),
            )
        ).lower()
        if q and q not in blob:
            continue
        out.append(art)
    out.sort(key=lambda a: float(a.get("updated_at") or 0), reverse=True)
    return out[:limit]


def get(article_id: str) -> dict[str, Any] | None:
    return store.knowledge_articles().get(article_id)
