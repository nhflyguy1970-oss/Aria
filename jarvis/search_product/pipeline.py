"""One Search pipeline — every entry point executes this."""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from jarvis.search_product.history import record_query, source_frequency
from jarvis.search_product.intent import classify_intent, select_corpora
from jarvis.search_product.ranking import dedupe_results, rank_results
from jarvis.search_product.retrievers import RETRIEVERS
from jarvis.search_product.sessions import start_session, touch_session
from jarvis.search_product.settings import enabled_corpora_set, load_settings
from jarvis.search_product.status_bus import set_search_state

logger = logging.getLogger("jarvis.search_product.pipeline")


def run_search(
    query: str,
    *,
    facets: list[str] | None = None,
    limit: int | None = None,
    mode: str | None = None,
    code_mode: str | None = None,
    record_history: bool | None = None,
    context: dict[str, Any] | None = None,
    parallel: bool | None = None,
    session: bool = True,
) -> dict[str, Any]:
    """
    Query → Intent → Corpus selection → Parallel retrieval → Ranking →
    Dedup → Result contract → History / diagnostics.
    """
    q = (query or "").strip()
    settings = load_settings()
    if not q:
        return {"ok": False, "error": "query required", "results": [], "query": ""}

    limit_n = int(limit if limit is not None else settings.get("max_results") or 24)
    limit_n = max(1, min(50, limit_n))
    mode_s = mode or settings.get("default_mode") or "browse"
    code_mode_s = code_mode or settings.get("code_mode") or "auto"
    do_hist = settings.get("record_history", True) if record_history is None else bool(record_history)
    do_parallel = settings.get("parallel_retrieval", True) if parallel is None else bool(parallel)
    enabled = enabled_corpora_set(settings)

    intent = classify_intent(q)
    # Experimental answer vs browse auto
    if mode_s == "auto":
        mode_s = "answer" if intent.get("answer_leaning") and not intent.get("browse_leaning") else "browse"

    corpora = select_corpora(intent, facets=facets, enabled=enabled)
    # Facet aliases
    if "connections" in corpora and "graph" not in corpora and "graph" in enabled:
        pass  # connections retriever handles graph store
    if "graph" in corpora and "connections" in corpora:
        # avoid double-fetching same store
        corpora = [c for c in corpora if c != "connections"]

    set_search_state("searching", detail=q, last_query=q)
    t0 = time.perf_counter()
    per = max(2, limit_n // max(1, len(corpora)))

    raw: list[dict[str, Any]] = []
    searched: list[str] = []
    failures: list[dict[str, str]] = []

    def _one(corp: str) -> tuple[str, list[dict[str, Any]], str | None]:
        fn = RETRIEVERS.get(corp)
        if not fn:
            return corp, [], f"unknown corpus {corp}"
        try:
            if corp == "code":
                hits = fn(q, per, mode=code_mode_s)
            else:
                hits = fn(q, per)
            return corp, hits or [], None
        except Exception as exc:
            return corp, [], str(exc)

    # Always bound corpus work — a single heavy corpus (documents/code) used to
    # run with no timeout and could hang the owner Search UI indefinitely.
    _CORPUS_WALL_S = 12.0
    _CORPUS_ONE_S = 8.0

    if not corpora:
        failures.append({"corpus": "federation", "error": "no enabled corpora"})
    else:
        # Do not use `with ThreadPoolExecutor`: on timeout the context manager
        # waits for hung corpora (documents/code) and blocks the owner response.
        pool = ThreadPoolExecutor(max_workers=min(8, max(1, len(corpora))))
        try:
            futs = {pool.submit(_one, c): c for c in corpora}
            try:
                for fut in as_completed(futs, timeout=_CORPUS_WALL_S):
                    try:
                        corp, hits, err = fut.result(timeout=_CORPUS_ONE_S)
                    except Exception as exc:
                        corp = futs[fut]
                        failures.append({"corpus": corp, "error": str(exc)})
                        continue
                    if err:
                        failures.append({"corpus": corp, "error": err})
                        logger.warning("corpus %s: %s", corp, err)
                    searched.append(corp)
                    if hits:
                        searched.append(corp)
                        raw.extend(hits)
            except TimeoutError as exc:
                logger.warning("search corpus timeout: %s", exc)
                for fut, corp in list(futs.items()):
                    if fut.done():
                        continue
                    fut.cancel()
                    failures.append(
                        {
                            "corpus": corp,
                            "error": "corpus timed out — partial results returned",
                        }
                    )
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    searched = list(dict.fromkeys(searched))
    hist_boost = source_frequency()
    ranked = rank_results(raw, query=q, intent=intent, context=context or {}, history_boost=hist_boost)
    ranked = dedupe_results(ranked)[:limit_n]
    latency_ms = (time.perf_counter() - t0) * 1000.0
    failed_corpora = {f.get("corpus") for f in failures}
    all_failed = bool(corpora) and len(failed_corpora.intersection(corpora)) >= len(corpora)
    degraded = bool(failures) and not all_failed

    sess = None
    if session:
        sess = start_session(q, facets=searched or corpora, mode=mode_s)
        touch_session(sess["id"], result_ids=[r["id"] for r in ranked])

    if do_hist:
        record_query(q, facets=searched or corpora, hit_count=len(ranked), latency_ms=latency_ms, mode=mode_s)

    web_handoff = None
    if "web" in (facets or []) or "web" in searched:
        web_handoff = {
            "action": "web_search",
            "query": q,
            "hint": "Open in Chat for synthesized answer with sources. Search does not duplicate web synthesis.",
            "view": "chat",
        }

    state = "failed" if all_failed else ("degraded" if degraded else ("ready" if ranked else "empty"))
    set_search_state(
        state,
        detail=q,
        last_query=q,
        last_latency_ms=round(latency_ms, 2),
        last_hit_count=len(ranked),
        error="" if not failures else failures[0].get("error", ""),
        failures=failures,
        degraded=degraded,
    )

    return {
        "ok": not all_failed and bool(corpora),
        "degraded": degraded or all_failed,
        "error": failures[0].get("error", "") if all_failed and failures else "",
        "query": q,
        "mode": mode_s,
        "code_mode": code_mode_s,
        "intent": intent,
        "corpora": corpora,
        "facets_requested": list(facets or []),
        "searched": searched,
        "results": ranked,
        "hit_count": len(ranked),
        "latency_ms": round(latency_ms, 2),
        "failures": failures,
        "session_id": (sess or {}).get("id"),
        "web_handoff": web_handoff,
        "contract": "SearchResult",
        "pipeline": "shared_search_pipeline",
    }


def format_search_message(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Search failed: {result.get('error', 'unknown')}"
    hits = result.get("results") or []
    q = result.get("query", "")
    warnings = [
        f"{f.get('corpus')}: {f.get('error')}"
        for f in (result.get("failures") or [])
        if isinstance(f, dict)
    ]
    if not hits:
        suffix = f" Failed corpora: {'; '.join(warnings)}" if warnings else ""
        return f"No matches for **{q}** across federated sources.{suffix}"
    lines = [
        f"**Search:** _{q}_",
        f"_{len(hits)} result(s) from {', '.join(result.get('searched') or [])}_",
        "",
    ]
    if warnings:
        lines.append(f"_Partial search: {'; '.join(warnings)}_")
        lines.append("")
    for h in hits:
        label = h.get("source_label") or h.get("source")
        title = h.get("title") or "untitled"
        excerpt = (h.get("preview") or h.get("summary") or "")[:280]
        conf = h.get("confidence")
        conf_s = f" · conf {conf:.0%}" if isinstance(conf, (int, float)) else ""
        lines.append(f"- **[{label}]** {title}{conf_s} — {excerpt}")
    if result.get("web_handoff"):
        lines.append("")
        lines.append("_Web facet: ask Chat to synthesize an answer with sources._")
    return "\n".join(lines)
